import httpx
import os
import logging

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"


class WhatsAppService:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    async def send_text_message(self, to_number, message_text):
        if not self.access_token or not self.phone_number_id:
            logger.info("WhatsApp not configured - skip send")
            return {"success": False, "error": "not configured"}

        url = WHATSAPP_API_URL + "/" + self.phone_number_id + "/messages"
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"preview_url": False, "body": message_text}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                if response.status_code == 200:
                    result = response.json()
                    msg_id = result.get("messages", [{}])[0].get("id", "")
                    return {"success": True, "message_id": msg_id}
                else:
                    return {"success": False, "error": response.json()}
        except Exception as e:
            logger.error("WhatsApp send error: " + str(e))
            return {"success": False, "error": str(e)}

    async def send_interactive_buttons(self, to_number, body_text, buttons):
        if not self.access_token or not self.phone_number_id:
            return {"success": False}

        url = WHATSAPP_API_URL + "/" + self.phone_number_id + "/messages"
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }

        button_list = []
        for i in range(min(len(buttons), 3)):
            button_list.append({
                "type": "reply",
                "reply": {"id": "btn_" + str(i), "title": buttons[i][:20]}
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": button_list}
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                return {"success": response.status_code == 200}
        except Exception as e:
            logger.error("Button send error: " + str(e))
            return {"success": False}

    async def mark_as_read(self, message_id):
        if not self.access_token or not self.phone_number_id:
            return

        url = WHATSAPP_API_URL + "/" + self.phone_number_id + "/messages"
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, headers=headers, json=payload, timeout=10.0)
        except Exception as e:
            logger.error("Mark read error: " + str(e))


whatsapp_service = WhatsAppService()
