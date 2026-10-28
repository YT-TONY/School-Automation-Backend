# app/api/v1/endpoints/whatsapp.py

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.whatsapp import WhatsAppBotService

router = APIRouter()

async def _async_process_webhook_payload(payload: dict, db_factory):
    async for db in db_factory():
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    metadata = value.get("metadata", {})
                    phone_number_id = metadata.get("phone_number_id")
                    messages = value.get("messages", [])

                    for msg in messages:
                        await WhatsAppBotService.process_incoming_message(msg, phone_number_id, db)
        except Exception as e:
            print(f"[WhatsApp Webhook Processing Exception]: {str(e)}")
        break

# --- 1. Meta Webhook Handshake Verification Endpoint ---
@router.get("/webhook")
async def verify_whatsapp_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        # Meta expects the exact challenge returned as a raw plain text string
        return PlainTextResponse(content=challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch."
    )

# --- 2. Non-Blocking High-Traffic Inbound Message Endpoint (<20ms response time) ---
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_whatsapp_message(
    request: Request,
    background_tasks: BackgroundTasks
):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}

    # Offload execution to background thread immediately so Meta receives HTTP 200 OK under 20ms
    background_tasks.add_task(_async_process_webhook_payload, payload, get_db)
    
    return {"status": "success"}