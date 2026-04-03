import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    consent_type = Column(String(30), nullable=False)
    action = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    consent_text_en = Column(Text, nullable=False, default="")
    consent_text_ar = Column(Text, nullable=False, default="")
    message_id = Column(String(100))
    ip_address = Column(String(45))
    legal_basis = Column(String(50), default="consent")
    metadata_extra = Column(JSON, default=dict)
    version = Column(String(20), default="1.0")

    business = relationship("Business", back_populates="consent_records")
    customer = relationship("Customer", back_populates="consent_records")