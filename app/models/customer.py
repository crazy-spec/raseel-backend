import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    phone_encrypted = Column(Text, nullable=False)
    phone_hash = Column(String(64), nullable=False)
    name_encrypted = Column(Text)
    email_encrypted = Column(Text)
    preferred_language = Column(String(5), default="ar")
    status = Column(String(20), default="active")
    lead_score = Column(String(20), default="cold")
    sentiment_score = Column(Float, default=0.0)
    lifetime_value = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    is_vip = Column(Boolean, default=False)
    last_message_at = Column(DateTime)
    total_conversations = Column(Integer, default=0)
    gender = Column(String(10))
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    consent_status = Column(String(20), default="pending")
    consent_granted_at = Column(DateTime)
    consent_revoked_at = Column(DateTime)
    data_deletion_requested_at = Column(DateTime)
    data_deletion_completed_at = Column(DateTime)

    business = relationship("Business", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer")
    consent_records = relationship("ConsentRecord", back_populates="customer")