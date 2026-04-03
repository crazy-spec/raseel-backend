import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, ForeignKey, Integer
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    order_number = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default="pending")
    items = Column(JSON, nullable=False)
    subtotal = Column(Float, nullable=False)
    vat_amount = Column(Float, nullable=False)
    vat_rate = Column(Float, default=0.15)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="SAR")
    delivery_address = Column(Text)
    notes = Column(Text)