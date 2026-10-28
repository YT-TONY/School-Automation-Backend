# app/services/whatsapp.py

import json
import httpx
import redis.asyncio as aioredis
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.school import School
from app.models.student import Student
from app.models.result import Result, ResultStatus
from app.models.pin import ResultPin

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

class WhatsAppBotService:

    @staticmethod
    async def get_session(phone_number: str) -> Optional[Dict[str, Any]]:
        data = await redis_client.get(f"wa_session:{phone_number}")
        return json.loads(data) if data else None

    @staticmethod
    async def set_session(phone_number: str, session_data: Dict[str, Any], ttl: int = 600):
        await redis_client.setex(f"wa_session:{phone_number}", ttl, json.dumps(session_data))

    @staticmethod
    async def clear_session(phone_number: str):
        await redis_client.delete(f"wa_session:{phone_number}")

    @staticmethod
    async def send_message(to_phone: str, text: str, access_token: str, phone_number_id: str):
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(url, json=payload, headers=headers)
            except Exception as e:
                print(f"[WhatsApp API Error]: Failed to send message to {to_phone}: {str(e)}")

    @classmethod
    async def process_incoming_message(cls, message_data: dict, phone_number_id: str, db: AsyncSession):
        sender_phone = message_data.get("from")
        text_body = message_data.get("text", {}).get("body", "").strip()

        if not sender_phone or not text_body:
            return

        # 1. Tenant Resolution: Match phone_number_id to an active Tier 2 School
        query = select(School).where(
            School.whatsapp_phone_number_id == phone_number_id,
            School.is_active == True,
            School.tier == 2
        )
        res = await db.execute(query)
        school = res.scalars().first()

        if not school or not school.settings.get("enable_whatsapp_bot", False):
            # Non-Tier 2 or unconfigured number; ignore silently
            return

        access_token = school.whatsapp_access_token or settings.WHATSAPP_TOKEN
        if not access_token:
            return

        # 2. Retrieve or Initialize Conversation Session
        session = await cls.get_session(sender_phone)
        command = text_body.upper()

        if command in ["HI", "HELLO", "MENU", "CANCEL", "START", "0"]:
            await cls.clear_session(sender_phone)
            menu_text = (
                f"🏫 *Welcome to {school.name} Portal Bot*\n"
                f"-----------------------------------------\n"
                f"Please reply with a number to choose an option:\n\n"
                f"1️⃣ *Check Student Result*\n"
                f"2️⃣ *Check Fee Balance*\n"
                f"0️⃣ *Main Menu / Cancel*\n\n"
                f"_Powered by White-Label School OS_"
            )
            await cls.send_message(sender_phone, menu_text, access_token, phone_number_id)
            await cls.set_session(sender_phone, {"step": "MAIN_MENU", "school_id": str(school.id)})
            return

        step = session.get("step") if session else None

        # 3. Main Menu Branching
        if step == "MAIN_MENU" or not session:
            if text_body == "1":
                msg = "📄 *Result Checker*\nPlease enter the Student's *Admission Number* (e.g. 2024/001):"
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                await cls.set_session(sender_phone, {"step": "AWAITING_RESULT_ADM", "school_id": str(school.id)})
            elif text_body == "2":
                msg = "💰 *Fee Balance Checker*\nPlease enter the Student's *Admission Number* (e.g. 2024/001):"
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                await cls.set_session(sender_phone, {"step": "AWAITING_FEE_ADM", "school_id": str(school.id)})
            else:
                msg = "❓ *Unrecognized option.* Reply *1* to Check Result, *2* for Fee Balance, or *0* for Main Menu."
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
            return

        # 4. Result Check Flow - Step A: Admission Number
        if step == "AWAITING_RESULT_ADM":
            adm_no = text_body.strip()
            student_query = select(Student).where(
                Student.school_id == school.id,
                Student.admission_number.ilike(adm_no)
            )
            student_res = await db.execute(student_query)
            student = student_res.scalars().first()

            if not student:
                msg = f"❌ Student with Admission Number *{adm_no}* was not found.\nPlease re-enter a valid Admission Number or reply *0* to cancel:"
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                return

            msg = f"✅ Student Found: *{student.first_name} {student.last_name}*\n🔑 Please enter your 12-digit *Scratch PIN Code*:"
            await cls.send_message(sender_phone, msg, access_token, phone_number_id)
            await cls.set_session(sender_phone, {
                "step": "AWAITING_PIN",
                "school_id": str(school.id),
                "student_id": str(student.id),
                "student_name": f"{student.first_name} {student.last_name}",
                "admission_number": student.admission_number
            })
            return

        # 4. Result Check Flow - Step B: PIN Validation & Score Output
        if step == "AWAITING_PIN":
            pin_code = text_body.strip().upper()
            student_id = session.get("student_id")

            # Validate PIN
            pin_query = select(ResultPin).where(
                ResultPin.school_id == school.id,
                ResultPin.pin_code == pin_code,
                ResultPin.is_active == True
            )
            pin_res = await db.execute(pin_query)
            pin = pin_res.scalars().first()

            if not pin or pin.times_used >= pin.max_uses:
                msg = "❌ *Invalid or exhausted Scratch PIN.* Please check the PIN code and try again, or reply *0* to cancel:"
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                return

            current_session = school.settings.get("current_session", "2025/2026")
            current_term = school.settings.get("current_term", "First Term")

            # Fetch Published Results
            results_query = select(Result).where(
                Result.school_id == school.id,
                Result.student_id == student_id,
                Result.session == current_session,
                Result.term == current_term,
                Result.status == ResultStatus.PUBLISHED
            )
            results_res = await db.execute(results_query)
            student_results = results_res.scalars().all()

            if not student_results:
                msg = f"⚠️ No published results found for *{session.get('student_name')}* for {current_session} {current_term}."
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                await cls.clear_session(sender_phone)
                return

            # Deduct PIN usage
            pin.times_used += 1
            await db.commit()

            # Build Clean Text Summary Output
            total_score = sum(r.total_score for r in student_results)
            avg_score = total_score / len(student_results) if student_results else 0.0

            lines = [
                f"🌟 *{school.name.upper()}*",
                f"-----------------------------------------",
                f"👤 *Student:* {session.get('student_name')}",
                f"🆔 *Adm No:* {session.get('admission_number')}",
                f"📅 *Term:* {current_session} | {current_term}",
                f"-----------------------------------------"
            ]

            for r in student_results:
                lines.append(f"• *{r.subject_name}*: {r.total_score:.1f}% ({r.grade_letter})")

            portal_domain = school.custom_domain or f"{school.subdomain}.portal.com" if school.subdomain else "portal.com"
            cdn_pdf_url = f"https://{portal_domain}/results/download/{student_id}?session={current_session}&term={current_term}"

            lines.append(f"-----------------------------------------")
            lines.append(f"📊 *Total:* {total_score:.1f} | *Average:* {avg_score:.1f}%")
            lines.append(f"\n📄 *Download Signed Official PDF Card:*\n{cdn_pdf_url}")

            await cls.send_message(sender_phone, "\n".join(lines), access_token, phone_number_id)
            await cls.clear_session(sender_phone)
            return

        # 5. Fee Balance Check Flow
        if step == "AWAITING_FEE_ADM":
            adm_no = text_body.strip()
            student_query = select(Student).where(
                Student.school_id == school.id,
                Student.admission_number.ilike(adm_no)
            )
            student_res = await db.execute(student_query)
            student = student_res.scalars().first()

            if not student:
                msg = f"❌ Student with Admission Number *{adm_no}* was not found.\nPlease re-enter Admission Number or reply *0* to cancel:"
                await cls.send_message(sender_phone, msg, access_token, phone_number_id)
                return

            # Demo Fee Summary Output (Points to Portal for Payment)
            portal_domain = school.custom_domain or f"{school.subdomain}.portal.com" if school.subdomain else "portal.com"
            portal_pay_url = f"https://{portal_domain}/portal/login"

            fee_msg = (
                f"💰 *Fee Account Balance Summary*\n"
                f"-----------------------------------------\n"
                f"👤 *Student:* {student.first_name} {student.last_name}\n"
                f"🆔 *Adm No:* {student.admission_number}\n"
                f"-----------------------------------------\n"
                f"• Tuition Fee: ₦120,000.00\n"
                f"• ICT & Portal Charge: ₦15,000.00\n"
                f"• Amount Paid: ₦90,000.00\n"
                f"-----------------------------------------\n"
                f"🔴 *Outstanding Balance:* ₦45,000.00\n\n"
                f"💳 *To view itemized invoices or make a secure payment, please visit your portal:*\n{portal_pay_url}"
            )
            await cls.send_message(sender_phone, fee_msg, access_token, phone_number_id)
            await cls.clear_session(sender_phone)
            return