from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.customer import Customer
from datetime import datetime
import uuid

router = APIRouter()


class OrderItem(BaseModel):
    product_id: str
    quantity: int = 1


class OrderCreate(BaseModel):
    business_id: str
    customer_id: str
    items: List[OrderItem]
    delivery_address: str = ""
    notes: str = ""


@router.post("/")
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    order_items = []
    subtotal = 0.0

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product " + item.product_id + " not found")
        if not product.is_available:
            raise HTTPException(status_code=400, detail="Product " + product.name_en + " is not available")

        line_total = product.price * item.quantity
        subtotal += line_total
        order_items.append({
            "product_id": product.id,
            "name_en": product.name_en,
            "name_ar": product.name_ar,
            "name": product.name_en,
            "price": product.price,
            "quantity": item.quantity,
            "qty": item.quantity,
            "line_total": line_total,
        })

    vat_rate = 0.15
    price_before_vat = round(subtotal / (1 + vat_rate), 2)
    vat_amount = round(subtotal - price_before_vat, 2)
    order_number = "ORD-" + datetime.utcnow().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()

    order = Order(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        customer_id=data.customer_id,
        order_number=order_number,
        status="pending",
        items=order_items,
        subtotal=price_before_vat,
        vat_amount=vat_amount,
        total=subtotal,
        delivery_address=data.delivery_address,
        notes=data.notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "items": order.items,
        "subtotal": order.subtotal,
        "vat_amount": order.vat_amount,
        "total": order.total,
        "currency": "SAR",
        "created_at": order.created_at.isoformat() if order.created_at else "",
    }


@router.get("/{business_id}")
def list_orders(business_id: str, status: str = None, db: Session = Depends(get_db)):
    query = db.query(Order).filter(Order.business_id == business_id)
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).all()

    results = []
    for o in orders:
        customer_name = None
        if o.customer_id:
            cust = db.query(Customer).filter(Customer.id == o.customer_id).first()
            if cust and cust.name_encrypted and not cust.name_encrypted.startswith("+"):
                customer_name = cust.name_encrypted

        items = o.items or []
        results.append({
            "id": o.id,
            "order_number": o.order_number or o.id[:8],
            "customer_name": customer_name or "Guest",
            "status": o.status,
            "items": items,
            "total": float(o.total) if o.total else 0,
            "vat_amount": float(o.vat_amount) if o.vat_amount else 0,
            "created_at": o.created_at.isoformat() if o.created_at else "",
        })

    return results


@router.put("/{order_id}/status")
def update_order_status(order_id: str, status: str, db: Session = Depends(get_db)):
    valid = ["pending", "confirmed", "preparing", "ready", "delivering", "delivered", "completed", "cancelled", "refunded"]
    if status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    return {"order_id": order_id, "new_status": status}
