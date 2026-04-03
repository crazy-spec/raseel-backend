from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.product import Product
import uuid

router = APIRouter()


class ProductCreate(BaseModel):
    name_en: str
    name_ar: str
    description_en: str = ""
    description_ar: str = ""
    category: str = ""
    price: float
    price_before_vat: Optional[float] = None
    is_available: bool = True
    stock_quantity: Optional[int] = None
    image_url: str = ""


class ProductResponse(BaseModel):
    id: str
    name_en: str
    name_ar: str
    description_en: Optional[str] = ""
    description_ar: Optional[str] = ""
    category: Optional[str] = ""
    price: float
    price_before_vat: Optional[float] = None
    is_available: bool = True
    stock_quantity: Optional[int] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=ProductResponse)
def create_product(business_id: str, data: ProductCreate, db: Session = Depends(get_db)):
    if not data.price_before_vat:
        data.price_before_vat = round(data.price / 1.15, 2)
    product = Product(
        id=str(uuid.uuid4()),
        business_id=business_id,
        name_en=data.name_en,
        name_ar=data.name_ar,
        description_en=data.description_en,
        description_ar=data.description_ar,
        category=data.category,
        price=data.price,
        price_before_vat=data.price_before_vat,
        is_available=data.is_available,
        stock_quantity=data.stock_quantity,
        image_url=data.image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/", response_model=List[ProductResponse])
def list_products(business_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.business_id == business_id
    ).all()
    return products


@router.get("/available", response_model=List[ProductResponse])
def list_available_products(business_id: str, category: str = None, db: Session = Depends(get_db)):
    query = db.query(Product).filter(
        Product.business_id == business_id,
        Product.is_available == True,
    )
    if category:
        query = query.filter(Product.category == category)
    return query.all()


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    if not data.price_before_vat:
        product.price_before_vat = round(data.price / 1.15, 2)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"status": "deleted", "product_id": product_id}


@router.post("/seed/{business_id}")
def seed_sample_products(business_id: str, db: Session = Depends(get_db)):
    from app.models.business import Business

    existing = db.query(Product).filter(Product.business_id == business_id).count()
    if existing >= 5:
        return {"status": "skipped", "message": "Already has products", "products_created": 0}

    biz = db.query(Business).filter(Business.id == business_id).first()
    sector = biz.sector if biz else "restaurant"

    SECTOR_PRODUCTS = {
        "restaurant": [
            {"name_en": "Broasted Chicken Meal", "name_ar": "\u0648\u062c\u0628\u0629 \u062f\u062c\u0627\u062c \u0628\u0631\u0648\u0633\u062a\u062f", "category": "Chicken", "price": 34.50, "description_en": "Crispy broasted chicken with fries and coleslaw", "description_ar": "\u062f\u062c\u0627\u062c \u0628\u0631\u0648\u0633\u062a\u062f \u0645\u0642\u0631\u0645\u0634 \u0645\u0639 \u0628\u0637\u0627\u0637\u0633 \u0648\u0633\u0644\u0637\u0629"},
            {"name_en": "Spicy Chicken Meal", "name_ar": "\u0648\u062c\u0628\u0629 \u062f\u062c\u0627\u062c \u062d\u0627\u0631", "category": "Chicken", "price": 36.00, "description_en": "Spicy broasted chicken with fries", "description_ar": "\u062f\u062c\u0627\u062c \u0628\u0631\u0648\u0633\u062a\u062f \u062d\u0627\u0631 \u0645\u0639 \u0628\u0637\u0627\u0637\u0633"},
            {"name_en": "Chicken Strips", "name_ar": "\u0633\u062a\u0631\u0628\u0633 \u062f\u062c\u0627\u062c", "category": "Chicken", "price": 28.00, "description_en": "6 pieces crispy strips", "description_ar": "6 \u0642\u0637\u0639 \u0633\u062a\u0631\u0628\u0633 \u0645\u0642\u0631\u0645\u0634"},
            {"name_en": "Family Meal (8 pcs)", "name_ar": "\u0648\u062c\u0628\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 8 \u0642\u0637\u0639", "category": "Family", "price": 89.00, "description_en": "8 pieces chicken with large fries", "description_ar": "8 \u0642\u0637\u0639 \u062f\u062c\u0627\u062c \u0645\u0639 \u0628\u0637\u0627\u0637\u0633 \u0643\u0628\u064a\u0631"},
            {"name_en": "Family Meal (12 pcs)", "name_ar": "\u0648\u062c\u0628\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 12 \u0642\u0637\u0639\u0629", "category": "Family", "price": 129.00, "description_en": "12 pieces chicken with salads", "description_ar": "12 \u0642\u0637\u0639\u0629 \u062f\u062c\u0627\u062c \u0645\u0639 \u0633\u0644\u0637\u0627\u062a"},
            {"name_en": "Shrimp Meal", "name_ar": "\u0648\u062c\u0628\u0629 \u0631\u0628\u064a\u0627\u0646", "category": "Seafood", "price": 42.00, "description_en": "Crispy fried shrimp", "description_ar": "\u0631\u0628\u064a\u0627\u0646 \u0645\u0642\u0644\u064a \u0645\u0642\u0631\u0645\u0634"},
            {"name_en": "Fish Fillet Meal", "name_ar": "\u0648\u062c\u0628\u0629 \u0641\u064a\u0644\u064a\u0647 \u0633\u0645\u0643", "category": "Seafood", "price": 38.00, "description_en": "Golden fish fillet with fries", "description_ar": "\u0641\u064a\u0644\u064a\u0647 \u0633\u0645\u0643 \u0630\u0647\u0628\u064a"},
            {"name_en": "French Fries (Regular)", "name_ar": "\u0628\u0637\u0627\u0637\u0633 \u0639\u0627\u062f\u064a", "category": "Sides", "price": 8.00, "description_en": "Crispy golden fries", "description_ar": "\u0628\u0637\u0627\u0637\u0633 \u0645\u0642\u0644\u064a\u0629"},
            {"name_en": "French Fries (Large)", "name_ar": "\u0628\u0637\u0627\u0637\u0633 \u0643\u0628\u064a\u0631", "category": "Sides", "price": 12.00, "description_en": "Large portion fries", "description_ar": "\u0628\u0637\u0627\u0637\u0633 \u062d\u062c\u0645 \u0643\u0628\u064a\u0631"},
            {"name_en": "Coleslaw", "name_ar": "\u0633\u0644\u0637\u0629 \u0643\u0648\u0644 \u0633\u0644\u0648", "category": "Sides", "price": 6.00, "description_en": "Fresh creamy coleslaw", "description_ar": "\u0633\u0644\u0637\u0629 \u0643\u0648\u0644 \u0633\u0644\u0648 \u0637\u0627\u0632\u062c\u0629"},
            {"name_en": "Garlic Sauce", "name_ar": "\u062b\u0648\u0645\u064a\u0629", "category": "Sides", "price": 3.00, "description_en": "Creamy garlic dip", "description_ar": "\u0635\u0648\u0635 \u062b\u0648\u0645\u064a\u0629"},
            {"name_en": "Pepsi", "name_ar": "\u0628\u064a\u0628\u0633\u064a", "category": "Drinks", "price": 5.00, "description_en": "Cold Pepsi", "description_ar": "\u0628\u064a\u0628\u0633\u064a \u0628\u0627\u0631\u062f"},
            {"name_en": "Miranda Orange", "name_ar": "\u0645\u064a\u0631\u0646\u062f\u0627 \u0628\u0631\u062a\u0642\u0627\u0644", "category": "Drinks", "price": 5.00, "description_en": "Cold Miranda Orange", "description_ar": "\u0645\u064a\u0631\u0646\u062f\u0627 \u0628\u0631\u062a\u0642\u0627\u0644"},
            {"name_en": "Water Bottle", "name_ar": "\u0645\u0648\u064a\u0647", "category": "Drinks", "price": 2.00, "description_en": "500ml water", "description_ar": "\u0642\u0627\u0631\u0648\u0631\u0629 \u0645\u0627\u0621"},
            {"name_en": "Kunafa", "name_ar": "\u0643\u0646\u0627\u0641\u0629", "category": "Desserts", "price": 15.00, "description_en": "Traditional cheese kunafa", "description_ar": "\u0643\u0646\u0627\u0641\u0629 \u0628\u0627\u0644\u062c\u0628\u0646"},
            {"name_en": "Basbousa", "name_ar": "\u0628\u0633\u0628\u0648\u0633\u0629", "category": "Desserts", "price": 10.00, "description_en": "Sweet semolina cake", "description_ar": "\u0628\u0633\u0628\u0648\u0633\u0629 \u0628\u0627\u0644\u0642\u0637\u0631"},
        ],
        "salon": [
            {"name_en": "Women's Haircut", "name_ar": "\u0642\u0635 \u0634\u0639\u0631 \u0646\u0633\u0627\u0626\u064a", "category": "Hair", "price": 80.00, "description_en": "Professional haircut and styling", "description_ar": "\u0642\u0635 \u0648\u062a\u0633\u0631\u064a\u062d \u0634\u0639\u0631 \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
            {"name_en": "Hair Coloring", "name_ar": "\u0635\u0628\u063a\u0629 \u0634\u0639\u0631", "category": "Hair", "price": 200.00, "description_en": "Full hair coloring service", "description_ar": "\u0635\u0628\u063a\u0629 \u0634\u0639\u0631 \u0643\u0627\u0645\u0644\u0629"},
            {"name_en": "Highlights", "name_ar": "\u0647\u0627\u064a\u0644\u0627\u064a\u062a", "category": "Hair", "price": 250.00, "description_en": "Partial or full highlights", "description_ar": "\u0647\u0627\u064a\u0644\u0627\u064a\u062a \u062c\u0632\u0626\u064a \u0623\u0648 \u0643\u0627\u0645\u0644"},
            {"name_en": "Keratin Treatment", "name_ar": "\u0639\u0644\u0627\u062c \u0643\u064a\u0631\u0627\u062a\u064a\u0646", "category": "Hair", "price": 500.00, "description_en": "Smoothing keratin treatment", "description_ar": "\u0639\u0644\u0627\u062c \u0643\u064a\u0631\u0627\u062a\u064a\u0646 \u0644\u0644\u0634\u0639\u0631"},
            {"name_en": "Blowdry", "name_ar": "\u0633\u0634\u0648\u0627\u0631", "category": "Hair", "price": 60.00, "description_en": "Professional blowdry styling", "description_ar": "\u0633\u0634\u0648\u0627\u0631 \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
            {"name_en": "Facial Treatment", "name_ar": "\u062a\u0646\u0638\u064a\u0641 \u0628\u0634\u0631\u0629", "category": "Skin", "price": 150.00, "description_en": "Deep cleansing facial", "description_ar": "\u062a\u0646\u0638\u064a\u0641 \u0628\u0634\u0631\u0629 \u0639\u0645\u064a\u0642"},
            {"name_en": "Hydra Facial", "name_ar": "\u0647\u064a\u062f\u0631\u0627 \u0641\u064a\u0634\u0644", "category": "Skin", "price": 300.00, "description_en": "Hydra facial for glowing skin", "description_ar": "\u0647\u064a\u062f\u0631\u0627 \u0641\u064a\u0634\u0644 \u0644\u0628\u0634\u0631\u0629 \u0645\u0634\u0631\u0642\u0629"},
            {"name_en": "Acne Treatment", "name_ar": "\u0639\u0644\u0627\u062c \u062d\u0628 \u0627\u0644\u0634\u0628\u0627\u0628", "category": "Skin", "price": 200.00, "description_en": "Professional acne treatment", "description_ar": "\u0639\u0644\u0627\u062c \u062d\u0628 \u0627\u0644\u0634\u0628\u0627\u0628 \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
            {"name_en": "Manicure", "name_ar": "\u0645\u0627\u0646\u064a\u0643\u064a\u0631", "category": "Nails", "price": 70.00, "description_en": "Classic manicure service", "description_ar": "\u0645\u0627\u0646\u064a\u0643\u064a\u0631 \u0643\u0644\u0627\u0633\u064a\u0643"},
            {"name_en": "Pedicure", "name_ar": "\u0628\u062f\u064a\u0643\u064a\u0631", "category": "Nails", "price": 80.00, "description_en": "Classic pedicure service", "description_ar": "\u0628\u062f\u064a\u0643\u064a\u0631 \u0643\u0644\u0627\u0633\u064a\u0643"},
            {"name_en": "Gel Nails", "name_ar": "\u0623\u0638\u0627\u0641\u0631 \u062c\u0644", "category": "Nails", "price": 120.00, "description_en": "Gel nail application", "description_ar": "\u062a\u0631\u0643\u064a\u0628 \u0623\u0638\u0627\u0641\u0631 \u062c\u0644"},
            {"name_en": "Full Body Wax", "name_ar": "\u0648\u0627\u0643\u0633 \u0643\u0627\u0645\u0644", "category": "Waxing", "price": 250.00, "description_en": "Full body waxing service", "description_ar": "\u0648\u0627\u0643\u0633 \u0643\u0627\u0645\u0644 \u0644\u0644\u062c\u0633\u0645"},
            {"name_en": "Eyebrow Threading", "name_ar": "\u062a\u0634\u0642\u064a\u0631 \u062d\u0648\u0627\u062c\u0628", "category": "Waxing", "price": 25.00, "description_en": "Eyebrow shaping", "description_ar": "\u062a\u0634\u0643\u064a\u0644 \u062d\u0648\u0627\u062c\u0628"},
            {"name_en": "Bridal Package", "name_ar": "\u0628\u0627\u0642\u0629 \u0639\u0631\u0648\u0633", "category": "Packages", "price": 1500.00, "description_en": "Complete bridal beauty package", "description_ar": "\u0628\u0627\u0642\u0629 \u0639\u0631\u0648\u0633 \u0643\u0627\u0645\u0644\u0629"},
            {"name_en": "Makeup Application", "name_ar": "\u0645\u0643\u064a\u0627\u062c", "category": "Makeup", "price": 200.00, "description_en": "Professional makeup", "description_ar": "\u0645\u0643\u064a\u0627\u062c \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
        ],
        "medical": [
            {"name_en": "General Consultation", "name_ar": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0639\u0627\u0645\u0629", "category": "Consultations", "price": 150.00, "description_en": "General doctor consultation", "description_ar": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0637\u0628\u064a\u0628 \u0639\u0627\u0645"},
            {"name_en": "Specialist Consultation", "name_ar": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0623\u062e\u0635\u0627\u0626\u064a", "category": "Consultations", "price": 250.00, "description_en": "Specialist doctor visit", "description_ar": "\u0632\u064a\u0627\u0631\u0629 \u0637\u0628\u064a\u0628 \u0623\u062e\u0635\u0627\u0626\u064a"},
            {"name_en": "Dental Cleaning", "name_ar": "\u062a\u0646\u0638\u064a\u0641 \u0623\u0633\u0646\u0627\u0646", "category": "Dental", "price": 200.00, "description_en": "Professional dental cleaning", "description_ar": "\u062a\u0646\u0638\u064a\u0641 \u0623\u0633\u0646\u0627\u0646 \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
            {"name_en": "Dental Filling", "name_ar": "\u062d\u0634\u0648\u0629 \u0623\u0633\u0646\u0627\u0646", "category": "Dental", "price": 300.00, "description_en": "Composite dental filling", "description_ar": "\u062d\u0634\u0648\u0629 \u0623\u0633\u0646\u0627\u0646 \u062a\u062c\u0645\u064a\u0644\u064a\u0629"},
            {"name_en": "Teeth Whitening", "name_ar": "\u062a\u0628\u064a\u064a\u0636 \u0623\u0633\u0646\u0627\u0646", "category": "Dental", "price": 800.00, "description_en": "Professional teeth whitening", "description_ar": "\u062a\u0628\u064a\u064a\u0636 \u0623\u0633\u0646\u0627\u0646 \u0627\u062d\u062a\u0631\u0627\u0641\u064a"},
            {"name_en": "Blood Test (CBC)", "name_ar": "\u062a\u062d\u0644\u064a\u0644 \u062f\u0645 \u0634\u0627\u0645\u0644", "category": "Lab", "price": 100.00, "description_en": "Complete blood count test", "description_ar": "\u062a\u062d\u0644\u064a\u0644 \u062f\u0645 \u0634\u0627\u0645\u0644"},
            {"name_en": "Vitamin D Test", "name_ar": "\u062a\u062d\u0644\u064a\u0644 \u0641\u064a\u062a\u0627\u0645\u064a\u0646 \u062f", "category": "Lab", "price": 120.00, "description_en": "Vitamin D level check", "description_ar": "\u0641\u062d\u0635 \u0645\u0633\u062a\u0648\u0649 \u0641\u064a\u062a\u0627\u0645\u064a\u0646 \u062f"},
            {"name_en": "Thyroid Panel", "name_ar": "\u062a\u062d\u0644\u064a\u0644 \u063a\u062f\u0629 \u062f\u0631\u0642\u064a\u0629", "category": "Lab", "price": 180.00, "description_en": "Thyroid function test", "description_ar": "\u0641\u062d\u0635 \u0648\u0638\u0627\u0626\u0641 \u0627\u0644\u063a\u062f\u0629 \u0627\u0644\u062f\u0631\u0642\u064a\u0629"},
            {"name_en": "X-Ray", "name_ar": "\u0623\u0634\u0639\u0629 \u0633\u064a\u0646\u064a\u0629", "category": "Imaging", "price": 150.00, "description_en": "Digital X-Ray imaging", "description_ar": "\u062a\u0635\u0648\u064a\u0631 \u0628\u0627\u0644\u0623\u0634\u0639\u0629 \u0627\u0644\u0633\u064a\u0646\u064a\u0629"},
            {"name_en": "Ultrasound", "name_ar": "\u0633\u0648\u0646\u0627\u0631", "category": "Imaging", "price": 250.00, "description_en": "Ultrasound scan", "description_ar": "\u0641\u062d\u0635 \u0628\u0627\u0644\u0633\u0648\u0646\u0627\u0631"},
            {"name_en": "Physiotherapy Session", "name_ar": "\u062c\u0644\u0633\u0629 \u0639\u0644\u0627\u062c \u0637\u0628\u064a\u0639\u064a", "category": "Wellness", "price": 200.00, "description_en": "Physical therapy session", "description_ar": "\u062c\u0644\u0633\u0629 \u0639\u0644\u0627\u062c \u0637\u0628\u064a\u0639\u064a"},
            {"name_en": "Vaccination", "name_ar": "\u062a\u0637\u0639\u064a\u0645", "category": "Wellness", "price": 80.00, "description_en": "Standard vaccination", "description_ar": "\u062a\u0637\u0639\u064a\u0645 \u0639\u0627\u062f\u064a"},
        ],
        "hotel": [
            {"name_en": "Standard Room", "name_ar": "\u063a\u0631\u0641\u0629 \u0639\u0627\u062f\u064a\u0629", "category": "Rooms", "price": 450.00, "description_en": "Comfortable standard room per night", "description_ar": "\u063a\u0631\u0641\u0629 \u0639\u0627\u062f\u064a\u0629 \u0645\u0631\u064a\u062d\u0629 \u0644\u0644\u064a\u0644\u0629"},
            {"name_en": "Deluxe Room", "name_ar": "\u063a\u0631\u0641\u0629 \u062f\u064a\u0644\u0648\u0643\u0633", "category": "Rooms", "price": 750.00, "description_en": "Spacious deluxe room with city view", "description_ar": "\u063a\u0631\u0641\u0629 \u062f\u064a\u0644\u0648\u0643\u0633 \u0645\u0639 \u0625\u0637\u0644\u0627\u0644\u0629"},
            {"name_en": "Executive Suite", "name_ar": "\u062c\u0646\u0627\u062d \u062a\u0646\u0641\u064a\u0630\u064a", "category": "Rooms", "price": 1200.00, "description_en": "Premium executive suite", "description_ar": "\u062c\u0646\u0627\u062d \u062a\u0646\u0641\u064a\u0630\u064a \u0645\u0645\u064a\u0632"},
            {"name_en": "Royal Suite", "name_ar": "\u062c\u0646\u0627\u062d \u0645\u0644\u0643\u064a", "category": "Rooms", "price": 2500.00, "description_en": "Luxury royal suite", "description_ar": "\u062c\u0646\u0627\u062d \u0645\u0644\u0643\u064a \u0641\u0627\u062e\u0631"},
            {"name_en": "Airport Transfer", "name_ar": "\u062a\u0648\u0635\u064a\u0644 \u0645\u0637\u0627\u0631", "category": "Services", "price": 150.00, "description_en": "Private airport transfer", "description_ar": "\u062a\u0648\u0635\u064a\u0644 \u062e\u0627\u0635 \u0644\u0644\u0645\u0637\u0627\u0631"},
            {"name_en": "Laundry Service", "name_ar": "\u062e\u062f\u0645\u0629 \u063a\u0633\u064a\u0644", "category": "Services", "price": 50.00, "description_en": "Same day laundry", "description_ar": "\u063a\u0633\u064a\u0644 \u0645\u0644\u0627\u0628\u0633 \u0646\u0641\u0633 \u0627\u0644\u064a\u0648\u0645"},
            {"name_en": "Room Service Breakfast", "name_ar": "\u0641\u0637\u0648\u0631 \u063a\u0631\u0641\u0629", "category": "Dining", "price": 85.00, "description_en": "Full breakfast in room", "description_ar": "\u0641\u0637\u0648\u0631 \u0643\u0627\u0645\u0644 \u0641\u064a \u0627\u0644\u063a\u0631\u0641\u0629"},
            {"name_en": "Dinner Buffet", "name_ar": "\u0628\u0648\u0641\u064a\u0647 \u0639\u0634\u0627\u0621", "category": "Dining", "price": 180.00, "description_en": "International dinner buffet", "description_ar": "\u0628\u0648\u0641\u064a\u0647 \u0639\u0634\u0627\u0621 \u0639\u0627\u0644\u0645\u064a"},
            {"name_en": "Spa Massage (60 min)", "name_ar": "\u0645\u0633\u0627\u062c 60 \u062f\u0642\u064a\u0642\u0629", "category": "Spa", "price": 350.00, "description_en": "Relaxing full body massage", "description_ar": "\u0645\u0633\u0627\u062c \u0627\u0633\u062a\u0631\u062e\u0627\u0626\u064a \u0643\u0627\u0645\u0644"},
            {"name_en": "Pool & Gym Access", "name_ar": "\u0645\u0633\u0628\u062d \u0648\u0646\u0627\u062f\u064a", "category": "Spa", "price": 100.00, "description_en": "Day pass for pool and gym", "description_ar": "\u062f\u062e\u0648\u0644 \u064a\u0648\u0645\u064a \u0644\u0644\u0645\u0633\u0628\u062d \u0648\u0627\u0644\u0646\u0627\u062f\u064a"},
            {"name_en": "Meeting Room (Half Day)", "name_ar": "\u0642\u0627\u0639\u0629 \u0627\u062c\u062a\u0645\u0627\u0639\u0627\u062a", "category": "Business", "price": 500.00, "description_en": "Meeting room rental", "description_ar": "\u0625\u064a\u062c\u0627\u0631 \u0642\u0627\u0639\u0629 \u0627\u062c\u062a\u0645\u0627\u0639\u0627\u062a"},
            {"name_en": "Late Checkout", "name_ar": "\u062a\u0623\u062e\u064a\u0631 \u0645\u063a\u0627\u062f\u0631\u0629", "category": "Services", "price": 200.00, "description_en": "Checkout extended to 4 PM", "description_ar": "\u062a\u0645\u062f\u064a\u062f \u0627\u0644\u0645\u063a\u0627\u062f\u0631\u0629 \u0644\u0644\u0633\u0627\u0639\u0629 4"},
        ],
        "retail": [
            {"name_en": "iPhone 16 Pro Max", "name_ar": "آيفون 16 برو ماكس", "category": "Electronics", "price": 5299.00, "description_en": "Latest 2026 iPhone flagship", "description_ar": "\u0623\u062d\u062f\u062b \u0622\u064a\u0641\u0648\u0646 \u0628\u0631\u0648"},
            {"name_en": "Samsung Galaxy S25 Ultra", "name_ar": "سامسونج جالكسي S25 ألترا", "category": "Electronics", "price": 4699.00, "description_en": "Samsung 2026 flagship", "description_ar": "\u0647\u0627\u062a\u0641 \u0633\u0627\u0645\u0633\u0648\u0646\u062c \u0627\u0644\u0631\u0627\u0626\u062f"},
            {"name_en": "AirPods Pro", "name_ar": "\u0625\u064a\u0631\u0628\u0648\u062f\u0632 \u0628\u0631\u0648", "category": "Electronics", "price": 999.00, "description_en": "Wireless noise-cancelling earbuds", "description_ar": "\u0633\u0645\u0627\u0639\u0627\u062a \u0644\u0627\u0633\u0644\u0643\u064a\u0629"},
            {"name_en": "iPad Air M3", "name_ar": "\u0622\u064a\u0628\u0627\u062f \u0625\u064a\u0631", "category": "Electronics", "price": 2799.00, "description_en": "iPad Air M3 2026 model", "description_ar": "آيباد إير بمعالج M3"},
            {"name_en": "PS5 Pro", "name_ar": "بلايستيشن 5 برو", "category": "Gaming", "price": 2499.00, "description_en": "PlayStation 5 Pro 2026", "description_ar": "\u062c\u0647\u0627\u0632 \u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5"},
            {"name_en": "Xbox Series X", "name_ar": "\u0625\u0643\u0633 \u0628\u0648\u0643\u0633 \u0633\u064a\u0631\u064a\u0632", "category": "Gaming", "price": 1999.00, "description_en": "Xbox Series X console", "description_ar": "\u062c\u0647\u0627\u0632 \u0625\u0643\u0633 \u0628\u0648\u0643\u0633"},
            {"name_en": "Nintendo Switch", "name_ar": "\u0646\u064a\u0646\u062a\u0646\u062f\u0648 \u0633\u0648\u064a\u062a\u0634", "category": "Gaming", "price": 1299.00, "description_en": "Nintendo Switch OLED", "description_ar": "\u0646\u064a\u0646\u062a\u0646\u062f\u0648 \u0633\u0648\u064a\u062a\u0634 OLED"},
            {"name_en": "Gaming Headset", "name_ar": "\u0633\u0645\u0627\u0639\u0629 \u0642\u064a\u0645\u0646\u0642", "category": "Gaming", "price": 399.00, "description_en": "Wireless gaming headset", "description_ar": "\u0633\u0645\u0627\u0639\u0629 \u0642\u064a\u0645\u0646\u0642 \u0644\u0627\u0633\u0644\u0643\u064a\u0629"},
            {"name_en": "Desk Organizer", "name_ar": "\u0645\u0646\u0638\u0645 \u0645\u0643\u062a\u0628", "category": "Office", "price": 89.00, "description_en": "Wooden desk organizer", "description_ar": "\u0645\u0646\u0638\u0645 \u0645\u0643\u062a\u0628 \u062e\u0634\u0628\u064a"},
            {"name_en": "Notebook Set", "name_ar": "\u0637\u0642\u0645 \u062f\u0641\u0627\u062a\u0631", "category": "Office", "price": 45.00, "description_en": "Premium notebook set of 3", "description_ar": "\u0637\u0642\u0645 3 \u062f\u0641\u0627\u062a\u0631 \u0641\u0627\u062e\u0631\u0629"},
            {"name_en": "Phone Case", "name_ar": "\u0643\u0641\u0631 \u062c\u0648\u0627\u0644", "category": "Accessories", "price": 79.00, "description_en": "Premium phone case", "description_ar": "\u0643\u0641\u0631 \u062c\u0648\u0627\u0644 \u0641\u0627\u062e\u0631"},
            {"name_en": "Power Bank 20000mAh", "name_ar": "\u0634\u0627\u062d\u0646 \u0645\u062a\u0646\u0642\u0644", "category": "Accessories", "price": 149.00, "description_en": "Fast charging power bank", "description_ar": "\u0634\u0627\u062d\u0646 \u0645\u062a\u0646\u0642\u0644 \u0633\u0631\u064a\u0639"},
        ],
        "education": [
            {"name_en": "English Course (Beginner)", "name_ar": "\u062f\u0648\u0631\u0629 \u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0645\u0628\u062a\u062f\u0626", "category": "Languages", "price": 1200.00, "description_en": "8-week beginner English course", "description_ar": "\u062f\u0648\u0631\u0629 \u0625\u0646\u062c\u0644\u064a\u0632\u064a 8 \u0623\u0633\u0627\u0628\u064a\u0639"},
            {"name_en": "English Course (Advanced)", "name_ar": "\u062f\u0648\u0631\u0629 \u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0645\u062a\u0642\u062f\u0645", "category": "Languages", "price": 1500.00, "description_en": "8-week advanced English", "description_ar": "\u062f\u0648\u0631\u0629 \u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0645\u062a\u0642\u062f\u0645 8 \u0623\u0633\u0627\u0628\u064a\u0639"},
            {"name_en": "IELTS Preparation", "name_ar": "\u062a\u062d\u0636\u064a\u0631 \u0622\u064a\u0644\u062a\u0633", "category": "Languages", "price": 2000.00, "description_en": "IELTS exam preparation", "description_ar": "\u062a\u062d\u0636\u064a\u0631 \u0644\u0627\u062e\u062a\u0628\u0627\u0631 \u0622\u064a\u0644\u062a\u0633"},
            {"name_en": "Python Programming", "name_ar": "\u0628\u0631\u0645\u062c\u0629 \u0628\u0627\u064a\u062b\u0648\u0646", "category": "Technology", "price": 1800.00, "description_en": "12-week Python course", "description_ar": "\u062f\u0648\u0631\u0629 \u0628\u0627\u064a\u062b\u0648\u0646 12 \u0623\u0633\u0628\u0648\u0639"},
            {"name_en": "Web Development", "name_ar": "\u062a\u0637\u0648\u064a\u0631 \u0645\u0648\u0627\u0642\u0639", "category": "Technology", "price": 2500.00, "description_en": "Full stack web development", "description_ar": "\u062a\u0637\u0648\u064a\u0631 \u0645\u0648\u0627\u0642\u0639 \u0645\u062a\u0643\u0627\u0645\u0644"},
            {"name_en": "Data Science", "name_ar": "\u0639\u0644\u0645 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a", "category": "Technology", "price": 3000.00, "description_en": "Data science bootcamp", "description_ar": "\u0645\u0639\u0633\u0643\u0631 \u0639\u0644\u0645 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a"},
            {"name_en": "Kids English (5-8)", "name_ar": "\u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0623\u0637\u0641\u0627\u0644 5-8", "category": "Kids", "price": 800.00, "description_en": "Fun English for young kids", "description_ar": "\u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0645\u0645\u062a\u0639 \u0644\u0644\u0623\u0637\u0641\u0627\u0644"},
            {"name_en": "Kids Coding (8-12)", "name_ar": "\u0628\u0631\u0645\u062c\u0629 \u0623\u0637\u0641\u0627\u0644 8-12", "category": "Kids", "price": 1000.00, "description_en": "Scratch and basic coding", "description_ar": "\u0628\u0631\u0645\u062c\u0629 \u0633\u0643\u0631\u0627\u062a\u0634 \u0644\u0644\u0623\u0637\u0641\u0627\u0644"},
            {"name_en": "Kids Robotics", "name_ar": "\u0631\u0648\u0628\u0648\u062a\u0627\u062a \u0623\u0637\u0641\u0627\u0644", "category": "Kids", "price": 1200.00, "description_en": "Robotics for kids 8-14", "description_ar": "\u0631\u0648\u0628\u0648\u062a\u0627\u062a \u0644\u0644\u0623\u0637\u0641\u0627\u0644 8-14"},
            {"name_en": "Business English", "name_ar": "\u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0623\u0639\u0645\u0627\u0644", "category": "Professional", "price": 2200.00, "description_en": "Business English for professionals", "description_ar": "\u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0623\u0639\u0645\u0627\u0644 \u0644\u0644\u0645\u062d\u062a\u0631\u0641\u064a\u0646"},
            {"name_en": "Leadership Training", "name_ar": "\u062a\u062f\u0631\u064a\u0628 \u0642\u064a\u0627\u062f\u064a", "category": "Professional", "price": 3500.00, "description_en": "Leadership skills workshop", "description_ar": "\u0648\u0631\u0634\u0629 \u0645\u0647\u0627\u0631\u0627\u062a \u0642\u064a\u0627\u062f\u064a\u0629"},
            {"name_en": "PMP Preparation", "name_ar": "\u062a\u062d\u0636\u064a\u0631 PMP", "category": "Professional", "price": 4000.00, "description_en": "PMP certification prep", "description_ar": "\u062a\u062d\u0636\u064a\u0631 \u0644\u0634\u0647\u0627\u062f\u0629 PMP"},
        ],
    }

    products_list = SECTOR_PRODUCTS.get(sector, SECTOR_PRODUCTS["restaurant"])
    created = []
    for p in products_list:
        product = Product(
            id=str(uuid.uuid4()),
            business_id=business_id,
            name_en=p["name_en"],
            name_ar=p["name_ar"],
            description_en=p["description_en"],
            description_ar=p["description_ar"],
            category=p["category"],
            price=p["price"],
            price_before_vat=round(p["price"] / 1.15, 2),
            is_available=True,
        )
        db.add(product)
        created.append(p["name_en"])
    db.commit()
    return {"status": "success", "sector": sector, "products_created": len(created), "products": created}

