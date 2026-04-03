import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    category = Column(String(30), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    description_ar = Column(Text)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(100))
    actor_ip = Column(String(45))
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    metadata_extra = Column(JSON, default=dict)
    risk_level = Column(String(20), default="low")

    business = relationship("Business", back_populates="audit_logs")