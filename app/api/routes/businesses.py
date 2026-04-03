from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.business import Business
from app.models.user import User
from app.auth.dependencies import get_current_user, get_optional_user, require_super_admin
import uuid

router = APIRouter()


class BusinessCreate(BaseModel):
    name_en: str
    name_ar: Optional[str] = None
    sector: str
    city: str = "Riyadh"
    whatsapp_phone: Optional[str] = ""
    default_language: Optional[str] = "ar"


class BusinessUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    city: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    default_language: Optional[str] = None
    is_active: Optional[bool] = None


def business_to_dict(b):
    return {
        "id": b.id,
        "name": b.name_en,
        "name_en": b.name_en,
        "name_ar": b.name_ar or b.name_en,
        "sector": b.sector,
        "city": b.city,
        "access_code": b.access_code,
        "whatsapp_phone": b.whatsapp_phone or "",
        "is_active": b.is_active,
        "default_language": b.default_language or "ar",
        "tier": b.tier or "starter",
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


@router.post("/")
def create_business(
    data: BusinessCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    access_code = "RS-" + uuid.uuid4().hex[:8].upper()

    business = Business(
        id=str(uuid.uuid4()),
        name_en=data.name_en,
        name_ar=data.name_ar or data.name_en,
        sector=data.sector,
        city=data.city,
        whatsapp_phone=data.whatsapp_phone or "",
        default_language=data.default_language or "ar",
        access_code=access_code,
    )
    db.add(business)
    db.flush()

    # Link business to user if they don't have one
    if not user.business_id:
        user.business_id = business.id
        db.add(user)

    db.commit()
    db.refresh(business)

    return business_to_dict(business)


@router.get("/")
def list_businesses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role == "super_admin":
        businesses = db.query(Business).filter(Business.is_active == True).all()
    else:
        if user.business_id:
            businesses = db.query(Business).filter(
                Business.id == user.business_id,
                Business.is_active == True
            ).all()
        else:
            businesses = []

    return [business_to_dict(b) for b in businesses]


@router.get("/{access_code}")
def get_business(access_code: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.access_code == access_code).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business_to_dict(business)


@router.put("/{business_id}")
def update_business(
    business_id: str,
    data: BusinessUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Only super_admin or the owner can update
    if user.role != "super_admin" and user.business_id != business_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if data.name_en is not None:
        business.name_en = data.name_en
    if data.name_ar is not None:
        business.name_ar = data.name_ar
    if data.city is not None:
        business.city = data.city
    if data.whatsapp_phone is not None:
        business.whatsapp_phone = data.whatsapp_phone
    if data.default_language is not None:
        business.default_language = data.default_language
    if data.is_active is not None and user.role == "super_admin":
        business.is_active = data.is_active

    db.commit()
    db.refresh(business)
    return business_to_dict(business)


@router.delete("/{business_id}")
def delete_business(
    business_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin)
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    db.delete(business)
    db.commit()
    return {"status": "deleted", "id": business_id}
