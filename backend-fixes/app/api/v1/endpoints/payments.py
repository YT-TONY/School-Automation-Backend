# app/api/v1/endpoints/payments.py  (drop-in replacement)
#
# Changes from your version:
#   1. The server sets the price for ONLINE_PIN purchases (the browser's amount is ignored).
#   2. The webhook checks that the amount paid matches the transaction, locks the row so a payment
#      cannot be fulfilled twice, and runs before answering so a failure makes Paystack retry.
#   3. The receipt's items_summary now contains the PIN codes ("pins") and the quantity.
#   4. References are longer (96 bits), because anyone holding a reference can read its receipt.

import hashlib
import hmac
import logging
import secrets
import string
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_optional_current_user
from app.core.tenant import require_tenant_id
from app.models.payment import PaymentReceipt, PaymentStatus, PaymentTransaction, PaymentType
from app.models.pin import ResultPin
from app.models.school import School
from app.models.user import User
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentReceiptResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_PINS_PER_PURCHASE = 20


def _verify_paystack_signature(raw_body: bytes, signature_header: str):
    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()
    if not hmac.compare_digest(computed_signature, signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Paystack security signature.")


# --- 1. Payment Initialization (supports guest PIN purchases and portal payments) ---
@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    payload: PaymentInitializeRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    school = None

    if current_user and current_user.school_id:
        res = await db.execute(select(School).where(School.id == current_user.school_id))
        school = res.scalars().first()

    if not school:
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                query = select(School).where(School.id == uuid.UUID(tenant_id))
            except ValueError:
                query = select(School).where(School.slug == tenant_id)
            res = await db.execute(query)
            school = res.scalars().first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School portal context not found. Please log in or provide a valid X-Tenant-ID header.",
        )

    if not school.paystack_subaccount_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This school has not configured a bank subaccount for online payments.",
        )

    # The server decides the price. Never trust the amount or quantity the browser sends for PINs.
    school_settings = school.settings or {}
    quantity = payload.quantity
    if payload.payment_type == PaymentType.ONLINE_PIN:
        if not school_settings.get("allow_parent_pin_purchase", True):
            raise HTTPException(status_code=400, detail="Online PIN purchasing is currently disabled by this school.")
        if quantity > MAX_PINS_PER_PURCHASE:
            raise HTTPException(status_code=400, detail=f"You can buy at most {MAX_PINS_PER_PURCHASE} PINs at a time.")
        base_amount = float(school_settings.get("pin_price_amount", 1500.0)) * quantity
    else:
        quantity = 1
        base_amount = payload.amount  # TODO: derive from the invoice for SCHOOL_FEES / HOSTEL_FEE

    # Platform markup by tier: Tier 1 = N500, Tier 2 = N1,000
    platform_markup_naira = 500.0 if getattr(school, "tier", 1) == 1 else 1000.0
    platform_markup_kobo = int(platform_markup_naira * 100)
    total_amount_naira = base_amount + platform_markup_naira
    total_amount_kobo = int(round(total_amount_naira * 100))

    reference = f"PAY-{secrets.token_hex(12).upper()}"

    paystack_payload = {
        "email": payload.payer_email,
        "amount": total_amount_kobo,
        "subaccount": school.paystack_subaccount_code,
        "transaction_charge": platform_markup_kobo,
        "bearer": "account",
        "reference": reference,
        "metadata": {
            "school_id": str(school.id),
            "student_id": str(payload.student_id) if payload.student_id else None,
            "invoice_id": str(payload.invoice_id) if payload.invoice_id else None,
            "payment_type": payload.payment_type.value,
            "quantity": quantity,
        },
    }
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post("https://api.paystack.co/transaction/initialize", json=paystack_payload, headers=headers)
            res_data = resp.json()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to reach payment gateway. Please try again.")

    if not res_data.get("status"):
        raise HTTPException(status_code=400, detail=res_data.get("message", "Payment initialization failed."))

    db.add(PaymentTransaction(
        school_id=school.id,
        student_id=payload.student_id,
        invoice_id=payload.invoice_id,
        reference=reference,
        paystack_access_code=res_data["data"]["access_code"],
        amount_total=total_amount_naira,
        amount_school=base_amount,
        platform_fee=platform_markup_naira,
        payment_type=payload.payment_type,
        status=PaymentStatus.PENDING,
        payer_email=payload.payer_email,
        metadata_json=paystack_payload["metadata"],
    ))
    await db.commit()

    return PaymentInitializeResponse(
        authorization_url=res_data["data"]["authorization_url"],
        access_code=res_data["data"]["access_code"],
        reference=reference,
        total_charged=total_amount_naira,
        platform_markup=platform_markup_naira,
    )


# --- 2. Fulfillment (called by the webhook) ---
async def _fulfill_payment(data: dict, db: AsyncSession) -> None:
    reference = data.get("reference")
    if not reference:
        return

    # Lock the row so two deliveries of the same webhook cannot fulfil a payment twice
    res = await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference).with_for_update()
    )
    tx = res.scalars().first()
    if not tx or tx.status == PaymentStatus.SUCCESS:
        return  # unknown reference, or already fulfilled

    # The amount Paystack says was paid (in kobo) must match what we asked for
    expected_kobo = int(round(tx.amount_total * 100))
    if data.get("status") != "success" or data.get("amount") != expected_kobo:
        logger.error("Payment %s rejected: status=%s paid=%s expected=%s",
                     reference, data.get("status"), data.get("amount"), expected_kobo)
        tx.status = PaymentStatus.FAILED
        await db.commit()
        return

    tx.status = PaymentStatus.SUCCESS
    tx.channel = data.get("channel")
    local_meta = tx.metadata_json or {}  # use our own record, not data sent back by the gateway

    items = {
        "payment_type": tx.payment_type.value,
        "amount_school": tx.amount_school,
        "platform_fee": tx.platform_fee,
        "reference": tx.reference,
        "channel": tx.channel,
    }

    if tx.payment_type == PaymentType.ONLINE_PIN:
        qty = int(local_meta.get("quantity", 1))
        batch_no = f"ONL-{uuid.uuid4().hex[:6].upper()}"
        codes = []
        for _ in range(qty):
            code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            serial = "SN-" + "".join(secrets.choice(string.digits) for _ in range(10))
            db.add(ResultPin(
                school_id=tx.school_id, pin_code=code, serial_number=serial, batch_number=batch_no,
                max_uses=5, times_used=0, is_active=True,
            ))
            codes.append(code)
        items["quantity"] = qty
        items["pins"] = codes  # the buyer sees these on the receipt

    db.add(PaymentReceipt(
        school_id=tx.school_id,
        transaction_id=tx.id,
        receipt_number=f"RCT-{uuid.uuid4().hex[:10].upper()}",
        payer_name=local_meta.get("payer_name") or tx.payer_email.split("@")[0],
        payer_email=tx.payer_email,
        amount_paid=tx.amount_total,
        items_summary=items,
    ))
    await db.commit()


# --- 3. Paystack Webhook ---
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not x_paystack_signature:
        raise HTTPException(status_code=400, detail="Missing signature header.")

    raw_body = await request.body()
    _verify_paystack_signature(raw_body, x_paystack_signature)

    payload = await request.json()
    if payload.get("event") == "charge.success":
        # Done before answering: if it fails, an error is returned and Paystack retries the webhook
        await _fulfill_payment(payload["data"], db)

    return {"status": "success", "message": "Webhook received"}


# --- 4. Fetch Digital Receipts ---
@router.get("/receipts/{reference}", response_model=PaymentReceiptResponse)
async def get_payment_receipt(
    reference: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db),
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
