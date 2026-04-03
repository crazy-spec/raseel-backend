from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "raseel-webhook-verify-2026")
    logger.info("Webhook verify attempt: mode=" + str(hub_mode) + " token=" + str(hub_verify_token))

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook verified OK")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("Webhook verify FAILED: expected=" + verify_token + " got=" + str(hub_verify_token))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_whatsapp_message(request: Request):
    try:
        body = await request.json()

        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "statuses" in value:
            return {"status": "ok"}

        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}

        message = messages[0]
        contacts = value.get("contacts", [{}])
        contact = contacts[0] if contacts else {}

        customer_number = message.get("from", "")
        customer_name = contact.get("profile", {}).get("name", "")
        message_id = message.get("id", "")
        msg_type = message.get("type", "text")

        if msg_type == "text":
            customer_text = message.get("text", {}).get("body", "")
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                customer_text = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                customer_text = interactive.get("list_reply", {}).get("title", "")
            else:
                customer_text = "[interactive message]"
        else:
            customer_text = "[" + msg_type + " message]"

        logger.info("WhatsApp from " + customer_number + ": " + customer_text)

        # Check guardrails first
        from app.services.guardrails import check_blocked_topic
        is_blocked, category, refusal = check_blocked_topic(customer_text)

        if is_blocked:
            ai_reply = {"text": refusal, "buttons": None}
        else:
            ai_reply = await generate_reply(customer_text, customer_name)

        # Mark as read
        await mark_read(message_id)

        # Send reply
        if ai_reply.get("buttons"):
            await send_buttons(customer_number, ai_reply["text"], ai_reply["buttons"])
        else:
            await send_text(customer_number, ai_reply["text"])

        return {"status": "ok"}

    except Exception as e:
        logger.error("Webhook error: " + str(e))
        return {"status": "ok"}


async def generate_reply(message_text, customer_name):
    import httpx

    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    from app.services.guardrails import get_system_guardrail_prompt
    system_prompt = get_system_guardrail_prompt()
    system_prompt = system_prompt + "\nCustomer name: " + (customer_name or "unknown")

    if groq_key and len(groq_key) > 10:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": "Bearer " + groq_key, "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message_text}
                        ],
                        "max_tokens": 300,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                if r.status_code == 200:
                    text = r.json()["choices"][0]["message"]["content"]
                    return {"text": text, "buttons": None}
        except Exception as e:
            logger.error("Groq error: " + str(e))

    if gemini_key and len(gemini_key) > 10:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + gemini_key,
                    json={"contents": [{"parts": [{"text": system_prompt + "\n\nCustomer: " + message_text}]}]},
                    timeout=30.0
                )
                if r.status_code == 200:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return {"text": text, "buttons": None}
        except Exception as e:
            logger.error("Gemini error: " + str(e))

    return smart_fallback(message_text, customer_name)


def smart_fallback(message_text, customer_name):
    text_lower = message_text.lower().strip()
    is_arabic = any(ord(c) > 1536 and ord(c) < 1792 for c in message_text)

    greetings_ar = ["السلام", "مرحبا", "هلا", "اهلا", "مساء", "صباح"]
    greetings_en = ["hi", "hello", "hey", "good morning", "good evening"]

    if any(g in text_lower for g in greetings_ar):
        name_part = ""
        if customer_name:
            name_part = " " + customer_name
        return {
            "text": "أهلاً وسهلاً" + name_part + "! 👋\n\nكيف أقدر أساعدك؟\n📋 القائمة\n🛒 طلب جديد\n📞 تواصل",
            "buttons": ["📋 القائمة", "🛒 طلب جديد", "📞 تواصل"]
        }

    if any(g in text_lower for g in greetings_en):
        name_part = ""
        if customer_name:
            name_part = " " + customer_name
        return {
            "text": "Welcome" + name_part + "! 👋\n\nHow can I help?\n📋 Menu\n🛒 New Order\n📞 Contact",
            "buttons": ["📋 Menu", "🛒 Order", "📞 Contact"]
        }

    if any(w in text_lower for w in ["menu", "قائمة", "المنيو", "منيو"]):
        if is_arabic:
            return {
                "text": "📋 قائمتنا:\n🍔 برجر كلاسيك — 35 ر.س\n🍟 بطاطس — 15 ر.س\n🥤 مشروب — 10 ر.س\n🍗 دجاج مقرمش — 40 ر.س\n\nشامل الضريبة 15%",
                "buttons": ["🛒 اطلب الآن"]
            }
        return {
            "text": "📋 Our Menu:\n🍔 Classic Burger — 35 SAR\n🍟 Fries — 15 SAR\n🥤 Drink — 10 SAR\n🍗 Crispy Chicken — 40 SAR\n\nAll prices include 15% VAT",
            "buttons": ["🛒 Order Now"]
        }

    if is_arabic:
        return {
            "text": "شكراً لتواصلك! 🙏\nكيف أقدر أساعدك؟",
            "buttons": ["📋 القائمة", "🛒 طلب", "📞 تواصل"]
        }
    return {
        "text": "Thanks for reaching out! 🙏\nHow can I help?",
        "buttons": ["📋 Menu", "🛒 Order", "📞 Contact"]
    }


async def send_text(to_number, text):
    import httpx
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_id:
        logger.info("WhatsApp not configured — reply: " + text[:50])
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://graph.facebook.com/v21.0/" + phone_id + "/messages",
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": text}},
                timeout=30.0
            )
    except Exception as e:
        logger.error("Send text error: " + str(e))


async def send_buttons(to_number, body_text, buttons):
    import httpx
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_id:
        logger.info("WhatsApp not configured — buttons reply: " + body_text[:50])
        return

    button_list = []
    for i in range(min(len(buttons), 3)):
        button_list.append({"type": "reply", "reply": {"id": "btn_" + str(i), "title": buttons[i][:20]}})

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://graph.facebook.com/v21.0/" + phone_id + "/messages",
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to_number,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": body_text},
                        "action": {"buttons": button_list}
                    }
                },
                timeout=30.0
            )
    except Exception as e:
        logger.error("Send buttons error: " + str(e))


async def mark_read(message_id):
    import httpx
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_id:
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://graph.facebook.com/v21.0/" + phone_id + "/messages",
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "status": "read", "message_id": message_id},
                timeout=10.0
            )
    except Exception as e:
        logger.error("Mark read error: " + str(e))
