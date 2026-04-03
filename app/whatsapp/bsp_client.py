from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class WhatsAppMessage:
    to: str
    message_type: str = "text"
    text: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = None
    template_params: Optional[List[str]] = None
    business_id: Optional[str] = None


class WhatsAppClient:
    async def send_message(self, message: WhatsAppMessage) -> Dict:
        return {"success": True, "message_id": "dev-mode", "status": "development"}

    async def send_template(self, message: WhatsAppMessage) -> Dict:
        return {"success": True, "message_id": "dev-mode", "status": "development"}

    async def close(self):
        pass


whatsapp_client = WhatsAppClient()