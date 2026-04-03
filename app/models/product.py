import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=False)
    description_en = Column(Text)
    description_ar = Column(Text)
    category = Column(String(100))
    sku = Column(String(50))
    price = Column(Float, nullable=False)
    price_before_vat = Column(Float)
    currency = Column(String(3), default="SAR")
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer)
    image_url = Column(String(500))
    tags = Column(JSON, default=list)
    custom_attributes = Column(JSON, default=dict)

    business = relationship("Business", back_populates="products")