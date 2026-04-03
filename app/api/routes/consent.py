from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models.consent import ConsentRecord
from app.models.customer import Customer
from app.compliance.encryption import encrypt_pii, hash_for_lookup
from datetime import datetime, timedelta
import uuid

router = APIRouter()


class ConsentRequest(BaseModel):
    business_id: str
    customer_id: str = ""
    customer_phone: str = ""
    consent_types: List[str]
    channel: str = "whatsapp"


@router.post("/grant")
def grant_consent(data: ConsentRequest, db: Session = Depends(get_db)):
    """Grant consent - auto-creates customer if needed."""
    customer_id = data.customer_id

    # If customer_id not provided but phone is, find or create customer
    if not customer_id and data.customer_phone:
        phone_hash = hash_for_lookup(data.customer_phone)
        customer = db.query(Customer).filter(
            Customer.business_id == data.business_id,
            Customer.phone_hash == phone_hash,
        ).first()
        if not customer:
            customer = Customer(
                id=str(uuid.uuid4()),
                business_id=data.business_id,
                phone_encrypted=encrypt_pii(data.customer_phone),
                phone_hash=phone_hash,
            )
            db.add(customer)
            db.flush()
        customer_id = customer.id
    elif customer_id:
        # Check if customer exists, create if not
        existing = db.query(Customer).filter(Customer.id == customer_id).first()
        if not existing:
            existing = db.query(Customer).filter(
                Customer.business_id == data.business_id,
            ).first()
            if existing:
                customer_id = existing.id
            else:
                # Create a placeholder customer
                new_customer = Customer(
                    id=customer_id if len(customer_id) == 36 else str(uuid.uuid4()),
                    business_id=data.business_id,
                    phone_encrypted=encrypt_pii("unknown"),
                    phone_hash=hash_for_lookup("unknown_" + customer_id),
                )
                db.add(new_customer)
                db.flush()
                customer_id = new_customer.id

    records = []
    for ct in data.consent_types:
        record = ConsentRecord(
            id=str(uuid.uuid4()),
            business_id=data.business_id,
            customer_id=customer_id,
            consent_type=ct,
            action="granted",
            channel=data.channel,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        db.add(record)
        records.append({"id": record.id, "type": ct, "action": "granted"})

    db.commit()
    return {"status": "success", "records": records, "customer_id": customer_id}


@router.post("/revoke")
def revoke_consent(data: ConsentRequest, db: Session = Depends(get_db)):
    """Revoke consent."""
    customer_id = data.customer_id

    # Find customer if needed
    if not customer_id and data.customer_phone:
        phone_hash = hash_for_lookup(data.customer_phone)
        customer = db.query(Customer).filter(
            Customer.business_id == data.business_id,
            Customer.phone_hash == phone_hash,
        ).first()
        if customer:
            customer_id = customer.id

    if not customer_id:
        raise HTTPException(status_code=404, detail="Customer not found")

    revoked = []
    for ct in data.consent_types:
        record = ConsentRecord(
            id=str(uuid.uuid4()),
            business_id=data.business_id,
            customer_id=customer_id,
            consent_type=ct,
            action="revoked",
            channel=data.channel,
        )
        db.add(record)
        revoked.append(ct)

    db.commit()
    return {"status": "success", "action": "revoked", "types": revoked}


@router.get("/check/{business_id}/{customer_id}/{consent_type}")
def check_consent(business_id: str, customer_id: str, consent_type: str, db: Session = Depends(get_db)):
    """Check if consent is active."""
    record = db.query(ConsentRecord).filter(
        ConsentRecord.business_id == business_id,
        ConsentRecord.customer_id == customer_id,
        ConsentRecord.consent_type == consent_type,
    ).order_by(ConsentRecord.created_at.desc()).first()

    has_consent = False
    if record and record.action == "granted":
        if record.expires_at and record.expires_at > datetime.utcnow():
            has_consent = True
        elif not record.expires_at:
            has_consent = True

    return {"has_consent": has_consent, "consent_type": consent_type}