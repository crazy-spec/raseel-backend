from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.customer import Customer

router = APIRouter(prefix="", tags=["customers"])


@router.get("/{business_id}")
async def get_customers(business_id: str, db: Session = Depends(get_db)):
    """Get all customers for a business."""
    customers = db.query(Customer).filter(
        Customer.business_id == business_id
    ).order_by(Customer.created_at.desc()).all()
    
    results = []
    for c in customers:
        results.append({
            "id": str(c.id),
            "name": getattr(c, 'name', None) or getattr(c, 'customer_name', None) or "Unknown",
            "phone": getattr(c, 'phone_hash', '')[-4:] if getattr(c, 'phone_hash', '') else "****",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "business_id": str(c.business_id),
        })
    
    return results


@router.get("/detail/{customer_id}")
async def get_customer_detail(customer_id: str, db: Session = Depends(get_db)):
    """Get single customer detail."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "id": str(customer.id),
        "name": getattr(customer, 'name', None) or getattr(customer, 'customer_name', None) or "Unknown",
        "phone": getattr(customer, 'phone_hash', '')[-4:] if getattr(customer, 'phone_hash', '') else "****",
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "business_id": str(customer.business_id),
    }

