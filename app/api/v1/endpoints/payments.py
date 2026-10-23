# app/api/v1/endpoints/payments.py

import hashlib
import hmac
import httpx
import secrets
import string
import uuid
from typing import List, Set, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_optional_current_user
from app.core.tenant import require_tenant_id
from app.models.payment import PaymentTransaction, PaymentReceipt, PaymentStatus, PaymentType
from app.models.pin import ResultPin
from app.models.school import School
from app.models.student import Student
from app.models.user import User
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentReceiptResponse,
    TransactionStatusResponse,
)

router = APIRouter()

# In-Memory Idempotency Lock Set (Use Redis in multi-worker production)
PROCESSED_REFERENCES: Set[str] = set()

def _verify_paystack_signature(raw_body: bytes, signature_header: str):
    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512
    ).hexdigest()
    if not hmac.compare_digest(computed_signature, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Paystack security signature."
        )

# --- 1. Payment Initialization Endpoint (Supports Guest PINs & Portal Payments) ---
@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    payload: PaymentInitializeRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    school = None

    # Step 1: Resolve school from logged-in user session if authenticated (Tier 2)
    if current_user and current_user.school_id:
        query = select(School).where(School.id == current_user.school_id)
        res = await db.execute(query)
        school = res.scalars().first()

    # Step 2: Fallback to Tenant Header/Subdomain for Guest Checkouts (Tier 1 PINs)
    if not school:
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                tenant_uuid = uuid.UUID(tenant_id)
                query = select(School).where(School.id == tenant_uuid)
            except ValueError:
                query = select(School).where(School.slug == tenant_id)
            res = await db.execute(query)
            school = res.scalars().first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School portal context not found. Please log in or provide a valid X-Tenant-ID header."
        )

    if not school.paystack_subaccount_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This school has not configured a bank subaccount for online payments."
        )

    # Dynamic Platform Markup by Tier Level
    # Tier 1 = ₦500 markup, Tier 2 = ₦1,000 markup
    tier_level = getattr(school, "tier", 1)
    platform_markup_naira = 500.0 if tier_level == 1 else 1000.0
    platform_markup_kobo = int(platform_markup_naira * 100)

    total_amount_naira = payload.amount + platform_markup_naira
    total_amount_kobo = int(total_amount_naira * 100)

    reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"

    paystack_payload = {
        "email": payload.payer_email,
        "amount": total_amount_kobo,
        "subaccount": school.paystack_subaccount_code,
        "transaction_charge": platform_markup_kobo,
        "bearer": "account",  # "account" forces Paystack fees to deduct from platform markup, leaving school payout exact
        "reference": reference,
        "metadata": {
            "school_id": str(school.id),
            "student_id": str(payload.student_id) if payload.student_id else None,
            "invoice_id": str(payload.invoice_id) if payload.invoice_id else None,
            "payment_type": payload.payment_type.value,
            "quantity": payload.quantity
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post("https://api.paystack.co/transaction/initialize", json=paystack_payload, headers=headers)
            res_data = res.json()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to reach payment gateway. Please try again.")

    if not res_data.get("status"):
        raise HTTPException(status_code=400, detail=res_data.get("message", "Payment initialization failed."))

    # Store local transaction record in PENDING state
    transaction = PaymentTransaction(
        school_id=school.id,
        student_id=payload.student_id,
        invoice_id=payload.invoice_id,
        reference=reference,
        paystack_access_code=res_data["data"]["access_code"],
        amount_total=total_amount_naira,
        amount_school=payload.amount,
        platform_fee=platform_markup_naira,
        payment_type=payload.payment_type,
        status=PaymentStatus.PENDING,
        payer_email=payload.payer_email,
        metadata_json=paystack_payload["metadata"]
    )
    db.add(transaction)
    await db.commit()

    return PaymentInitializeResponse(
        authorization_url=res_data["data"]["authorization_url"],
        access_code=res_data["data"]["access_code"],
        reference=reference,
        total_charged=total_amount_naira,
        platform_markup=platform_markup_naira
    )

# --- 2. Asynchronous Webhook Fulfillment Engine ---
async def _process_payment_fulfillment(data: dict, db_factory):
    reference = data.get("reference")
    if not reference or reference in PROCESSED_REFERENCES:
        return

    PROCESSED_REFERENCES.add(reference)

    async for db in db_factory():
        query = select(PaymentTransaction).where(PaymentTransaction.reference == reference)
        res = await db.execute(query)
        tx = res.scalars().first()

        if not tx or tx.status == PaymentStatus.SUCCESS:
            return

        metadata = data.get("metadata", {})
        tx.status = PaymentStatus.SUCCESS
        tx.channel = data.get("channel")

        # Auto-Fulfill Scratch PIN Purchases
        if tx.payment_type == PaymentType.ONLINE_PIN:
            qty = metadata.get("quantity", 1)
            batch_no = f"ONL-{uuid.uuid4().hex[:6].upper()}"
            for _ in range(qty):
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
                serial = f"SN-{''.join(secrets.choice(string.digits) for _ in range(10))}"
                
                pin = ResultPin(
                    school_id=tx.school_id,
                    pin_code=code,
                    serial_number=serial,
                    batch_number=batch_no,
                    max_uses=5,
                    times_used=0,
                    is_active=True
                )
                db.add(pin)

        # Generate Digital Receipt
        receipt_num = f"RCT-{''.join(secrets.choice(string.digits) for _ in range(4))}{uuid.uuid4().hex[:4].upper()}"
        receipt = PaymentReceipt(
            school_id=tx.school_id,
            transaction_id=tx.id,
            receipt_number=receipt_num,
            payer_name=metadata.get("payer_name", tx.payer_email.split("@")[0]),
            payer_email=tx.payer_email,
            amount_paid=tx.amount_total,
            items_summary={
                "payment_type": tx.payment_type.value,
                "amount_school": tx.amount_school,
                "platform_fee": tx.platform_fee,
                "reference": tx.reference,
                "channel": tx.channel
            }
        )
        db.add(receipt)
        await db.commit()
        break

# --- 3. Non-Blocking High-Traffic Webhook Receiver ---
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_paystack_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not x_paystack_signature:
        raise HTTPException(status_code=400, detail="Missing signature header.")

    raw_body = await request.body()
    _verify_paystack_signature(raw_body, x_paystack_signature)

    payload = await request.json()
    event = payload.get("event")

    if event == "charge.success":
        background_tasks.add_task(_process_payment_fulfillment, payload["data"], get_db)

    return {"status": "success", "message": "Webhook received"}

# --- 4. Fetch Digital Receipts ---
@router.get("/receipts/{reference}", response_model=PaymentReceiptResponse)
async def get_payment_receipt(
    reference: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(PaymentReceipt)
        .join(PaymentTransaction, PaymentReceipt.transaction_id == PaymentTransaction.id)
        .where(PaymentTransaction.reference == reference, PaymentReceipt.school_id == tenant_id)
    )
    res = await db.execute(query)
    receipt = res.scalars().first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Payment receipt not found.")

    return receipt