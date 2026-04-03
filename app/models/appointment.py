import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="requested")
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(String(10), default="30")
    service_type = Column(String(100))
    staff_member = Column(String(100))
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    preferred_gender_staff = Column(String(10))