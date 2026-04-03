from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.appointment import Appointment
from datetime import datetime
import uuid

router = APIRouter()


class AppointmentCreate(BaseModel):
    business_id: str
    customer_id: str
    scheduled_at: str
    service_type: str = ""
    duration_minutes: str = "30"
    staff_member: str = ""
    notes: str = ""
    preferred_gender_staff: str = ""


@router.post("/")
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    """Book an appointment."""
    try:
        scheduled = datetime.fromisoformat(data.scheduled_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format: 2025-03-15T10:00:00")

    appt = Appointment(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        customer_id=data.customer_id,
        scheduled_at=scheduled,
        service_type=data.service_type,
        duration_minutes=data.duration_minutes,
        staff_member=data.staff_member,
        notes=data.notes,
        preferred_gender_staff=data.preferred_gender_staff,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return {"id": appt.id, "status": appt.status, "scheduled_at": data.scheduled_at,
            "service_type": data.service_type}


@router.get("/{business_id}")
def list_appointments(business_id: str, status: str = None, db: Session = Depends(get_db)):
    """List appointments for a business."""
    query = db.query(Appointment).filter(Appointment.business_id == business_id)
    if status:
        query = query.filter(Appointment.status == status)
    appts = query.order_by(Appointment.scheduled_at).all()
    return [
        {"id": a.id, "status": a.status,
         "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else "",
         "service_type": a.service_type, "staff_member": a.staff_member}
        for a in appts
    ]


@router.put("/{appointment_id}/status")
def update_appointment_status(appointment_id: str, status: str, db: Session = Depends(get_db)):
    """Update: requested, confirmed, reminded, completed, no_show, cancelled, rescheduled."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = status
    db.commit()
    return {"appointment_id": appointment_id, "new_status": status}