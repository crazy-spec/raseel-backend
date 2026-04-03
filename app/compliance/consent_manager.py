from datetime import datetime, timedelta
from app.models.consent import ConsentRecord
import uuid


class ConsentManager:
    def check_consent(self, db, business_id: str, customer_id: str, consent_type: str) -> bool:
        record = db.query(ConsentRecord).filter(
            ConsentRecord.business_id == business_id,
            ConsentRecord.customer_id == customer_id,
            ConsentRecord.consent_type == consent_type,
        ).order_by(ConsentRecord.created_at.desc()).first()
        if not record or record.action != "granted":
            return False
        if record.expires_at and record.expires_at < datetime.utcnow():
            return False
        return True

    def record_consent(self, db, business_id, customer_id, consent_type, action, channel, message_id=None):
        record = ConsentRecord(
            id=str(uuid.uuid4()), business_id=business_id, customer_id=customer_id,
            consent_type=consent_type, action=action, channel=channel, message_id=message_id,
            expires_at=datetime.utcnow() + timedelta(days=365) if action == "granted" else None,
        )
        db.add(record)
        db.commit()
        return record

    def handle_stop_message(self, db, business_id, customer_id, message_id):
        self.record_consent(db, business_id, customer_id, "marketing", "revoked", "whatsapp", message_id)

    def request_consent(self, db, business_id, customer_id, consent_types):
        return {
            "ar": "نحتاج موافقتك للمتابعة. أرسل 'موافق'",
            "en": "We need your consent. Send 'AGREE'",
            "combined": "نحتاج موافقتك للمتابعة. أرسل 'موافق'\nWe need your consent. Send 'AGREE'",
        }


consent_manager = ConsentManager()