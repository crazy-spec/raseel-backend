import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=False)
    sector = Column(String(50), nullable=False)
    tier = Column(String(20), default="starter")
    commercial_registration = Column(String(20))
    vat_number = Column(String(20))
    city = Column(String(100), default="Riyadh")
    region = Column(String(100))
    whatsapp_phone = Column(String(20))
    whatsapp_business_id = Column(String(100))
    whatsapp_quality_rating = Column(String(20), default="GREEN")
    access_code = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    default_language = Column(String(5), default="ar")
    timezone = Column(String(50), default="Asia/Riyadh")
    ai_personality = Column(Text)
    sector_prompt_template = Column(Text)
    agent_config = Column(JSON, default=dict)
    confidence_threshold = Column(Float, default=0.85)
    prayer_pause_enabled = Column(Boolean, default=True)
    ramadan_mode_enabled = Column(Boolean, default=True)
    gender_routing_enabled = Column(Boolean, default=False)
    human_handoff_enabled = Column(Boolean, default=True)
    voice_messages_enabled = Column(Boolean, default=False)
    dpo_name = Column(String(255))
    dpo_email = Column(String(255))
    monthly_conversation_limit = Column(Integer, default=500)
    conversations_used_this_month = Column(Integer, default=0)

    customers = relationship("Customer", back_populates="business")
    conversations = relationship("Conversation", back_populates="business")
    products = relationship("Product", back_populates="business")
    campaigns = relationship("Campaign", back_populates="business")
    consent_records = relationship("ConsentRecord", back_populates="business")
    audit_logs = relationship("AuditLog", back_populates="business")