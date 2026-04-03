from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.business import Business
from app.models.customer import Customer
from app.models.conversation import Conversation, Message
from app.models.order import Order
from app.models.consent import ConsentRecord
from app.models.product import Product
from app.models.agent import AgentAction
from app.models.audit import AuditLog
from datetime import datetime

router = APIRouter()


@router.get("/dashboard/{business_id}")
def get_dashboard(business_id: str, db: Session = Depends(get_db)):
    """Complete business dashboard with all metrics."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return {"error": "Business not found"}

    total_customers = db.query(Customer).filter(Customer.business_id == business_id).count()
    total_conversations = db.query(Conversation).filter(Conversation.business_id == business_id).count()
    active_conversations = db.query(Conversation).filter(
        Conversation.business_id == business_id, Conversation.status == "active"
    ).count()
    total_messages = db.query(Message).filter(Message.business_id == business_id).count()
    total_products = db.query(Product).filter(Product.business_id == business_id).count()
    total_orders = db.query(Order).filter(Order.business_id == business_id).count()
    total_consents = db.query(ConsentRecord).filter(ConsentRecord.business_id == business_id).count()
    total_audit_logs = db.query(AuditLog).filter(AuditLog.business_id == business_id).count()

    # Revenue
    revenue_result = db.query(func.sum(Order.total)).filter(
        Order.business_id == business_id,
        Order.status.notin_(["cancelled", "refunded"]),
    ).scalar()
    total_revenue = float(revenue_result) if revenue_result else 0.0
    vat_collected = round(total_revenue - (total_revenue / 1.15), 2)

    # Consent breakdown
    granted = db.query(ConsentRecord).filter(
        ConsentRecord.business_id == business_id, ConsentRecord.action == "granted"
    ).count()
    revoked = db.query(ConsentRecord).filter(
        ConsentRecord.business_id == business_id, ConsentRecord.action == "revoked"
    ).count()

    # VIP customers
    vip_count = db.query(Customer).filter(
        Customer.business_id == business_id, Customer.is_vip == True
    ).count()

    return {
        "business": {
            "id": business.id,
            "name_en": business.name_en,
            "name_ar": business.name_ar,
            "sector": business.sector,
            "city": business.city,
        },
        "customers": {
            "total": total_customers,
            "vip": vip_count,
        },
        "conversations": {
            "total": total_conversations,
            "active": active_conversations,
            "total_messages": total_messages,
        },
        "products": {
            "total": total_products,
        },
        "orders": {
            "total": total_orders,
            "revenue_sar": total_revenue,
            "vat_collected_sar": vat_collected,
        },
        "compliance": {
            "consent_records": total_consents,
            "consents_granted": granted,
            "consents_revoked": revoked,
            "audit_log_entries": total_audit_logs,
            "pdpl_compliant": True,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/platform-stats")
def platform_stats(db: Session = Depends(get_db)):
    """Platform-wide statistics (admin view)."""
    return {
        "total_businesses": db.query(Business).count(),
        "total_customers": db.query(Customer).count(),
        "total_conversations": db.query(Conversation).count(),
        "total_messages": db.query(Message).count(),
        "total_orders": db.query(Order).count(),
        "total_products": db.query(Product).count(),
        "total_consent_records": db.query(ConsentRecord).count(),
        "total_audit_logs": db.query(AuditLog).count(),
        "platform": "Raseel",
        "version": "2.0.0",
        "pdpl_compliant": True,
    }
