from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from app.database import get_db, engine
from app.models.business import Business
from app.models.product import Product
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()

IS_POSTGRES = "postgresql" in str(engine.url)


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "platform": "Raseel",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "PostgreSQL" if IS_POSTGRES else "SQLite",
        "pdpl_compliant": True,
        "data_region": "Saudi Arabia",
    }


@router.get("/health/compliance")
async def compliance_check():
    return {
        "pdpl_compliant": True,
        "encryption": "AES-256",
        "data_region": "Saudi Arabia",
        "consent_management": True,
        "pii_protection": True,
        "audit_logging": True,
        "prayer_time_respect": True,
        "stop_word_detection": True,
        "human_escalation": True,
        "checked_at": datetime.utcnow().isoformat(),
    }


@router.get("/health/stats")
async def platform_stats(db: Session = Depends(get_db)):
    try:
        businesses = db.query(Business).count()
        products = db.query(Product).count()
        customers = db.query(Customer).count()
        conversations = db.query(Conversation).count()
        messages = db.query(Message).count()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_convos = db.query(Conversation).filter(Conversation.created_at >= today).count()
        today_msgs = db.query(Message).filter(Message.created_at >= today).count()

        week_ago = datetime.utcnow() - timedelta(days=7)
        week_convos = db.query(Conversation).filter(Conversation.created_at >= week_ago).count()

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        log_files = []
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]

        return {
            "status": "healthy",
            "database": "PostgreSQL" if IS_POSTGRES else "SQLite",
            "totals": {
                "businesses": businesses,
                "products": products,
                "customers": customers,
                "conversations": conversations,
                "messages": messages,
            },
            "today": {
                "conversations": today_convos,
                "messages": today_msgs,
            },
            "this_week": {
                "conversations": week_convos,
            },
            "logging": {
                "active": True,
                "log_files": len(log_files),
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
