import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String(255), nullable=False)
    template_name = Column(String(100), nullable=False)
    template_language = Column(String(5), default="ar")
    status = Column(String(20), default="draft")
    target_segment = Column(JSON)
    target_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime)
    prayer_time_aware = Column(Boolean, default=True)
    consent_type_required = Column(String(30), default="marketing")
    only_consented = Column(Boolean, default=True)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    opt_out_count = Column(Integer, default=0)

    business = relationship("Business", back_populates="campaigns")