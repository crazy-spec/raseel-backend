import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="active")
    window_opens_at = Column(DateTime)
    window_expires_at = Column(DateTime)
    current_agent = Column(String(50))
    assigned_human = Column(String(36))
    escalation_reason = Column(Text)
    sector_context = Column(String(50))
    conversation_summary = Column(Text)
    detected_language = Column(String(5), default="ar")
    detected_dialect = Column(String(20))
    overall_sentiment = Column(Float, default=0.0)
    sentiment_trend = Column(String(20))
    message_count = Column(Integer, default=0)

    business = relationship("Business", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    direction = Column(String(10), nullable=False)
    message_type = Column(String(20), default="text")
    sender_type = Column(String(20), nullable=False)
    content = Column(Text)
    media_url = Column(String(500))
    whatsapp_message_id = Column(String(100))
    whatsapp_status = Column(String(20))
    ai_agent = Column(String(50))
    ai_model_used = Column(String(50))
    ai_confidence = Column(Float)
    ai_processing_time_ms = Column(Integer)
    ai_was_reviewed = Column(Boolean, default=False)
    ai_was_edited = Column(Boolean, default=False)
    ai_original_response = Column(Text)
    sentiment_score = Column(Float)
    detected_emotion = Column(String(30))
    template_name = Column(String(100))

    conversation = relationship("Conversation", back_populates="messages")