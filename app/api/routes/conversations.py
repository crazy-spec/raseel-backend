from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import re
import hashlib

from app.database import get_db
from app.models.business import Business
from app.models.product import Product
from app.models.customer import Customer
from app.models.conversation import Conversation, Message
from app.agents.orchestrator import AgentOrchestrator
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="", tags=["conversations"])


class IncomingMessage(BaseModel):
    business_id: str
    customer_phone: str
    message_text: str
    message_language: Optional[str] = None


class ChatResponse(BaseModel):
    response_text: str
    agent_name: Optional[str] = None
    confidence: Optional[float] = None
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    detected_intent: Optional[str] = None
    suggested_buttons: Optional[list] = None
    customer_name: Optional[str] = None


def detect_language(text):
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    if arabic_chars > 0 and arabic_chars >= latin_chars:
        return "ar"
    return "en"


GREETINGS_EN = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "sup", "yo", "howdy"}
GREETINGS_AR = {"مرحبا", "اهلا", "هلا", "السلام عليكم", "سلام", "صباح الخير", "مساء الخير", "اهلين", "هلا والله", "حياك", "حياك الله"}


def is_greeting(text):
    cleaned = text.strip().lower().rstrip("!.?")
    cleaned_ar = text.strip().rstrip("!.?")
    if cleaned in GREETINGS_EN or cleaned_ar in GREETINGS_AR:
        return True
    for g in GREETINGS_EN | GREETINGS_AR:
        if cleaned.startswith(g) or cleaned_ar.startswith(g):
            return True
    return False


def build_greeting_response(business, products, lang):
    if lang == "ar":
        name = business.name_ar or business.name_en
        text = "\u0623\u0647\u0644\u0627\u064b \u0648\u0633\u0647\u0644\u0627\u064b \u0628\u0643 \u0641\u064a " + name + "! \U0001F31F\n\n\u0643\u064a\u0641 \u0623\u0642\u062f\u0631 \u0623\u0633\u0627\u0639\u062f\u0643 \u0627\u0644\u064a\u0648\u0645\u061f"
        sector_buttons = {
            "restaurant": ["\U0001F37D\uFE0F \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0637\u0639\u0627\u0645", "\u2B50 \u0627\u0644\u0623\u0637\u0628\u0627\u0642 \u0627\u0644\u0645\u0645\u064a\u0632\u0629", "\U0001F6F5 \u062a\u0648\u0635\u064a\u0644 \u0637\u0644\u0628", "\U0001F4B0 \u0627\u0644\u0623\u0633\u0639\u0627\u0631"],
            "medical": ["\U0001F468\u200D\u2695\uFE0F \u062d\u062c\u0632 \u0645\u0648\u0639\u062f", "\U0001F3E5 \u062e\u062f\u0645\u0627\u062a\u0646\u0627", "\U0001F4B0 \u0627\u0644\u0623\u0633\u0639\u0627\u0631", "\u23F0 \u0623\u0648\u0642\u0627\u062a \u0627\u0644\u0639\u0645\u0644"],
            "hotel": ["\U0001F6CF\uFE0F \u062d\u062c\u0632 \u063a\u0631\u0641\u0629", "\U0001F486 \u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0633\u0628\u0627", "\U0001F37D\uFE0F \u0645\u0637\u0639\u0645 \u0627\u0644\u0641\u0646\u062f\u0642", "\U0001F4B0 \u0627\u0644\u0623\u0633\u0639\u0627\u0631"],
            "retail": ["\U0001F4F1 \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a\u0627\u062a", "\U0001F3AE \u0627\u0644\u0623\u0644\u0639\u0627\u0628", "\U0001F4DA \u0627\u0644\u0643\u062a\u0628", "\U0001F4B0 \u0627\u0644\u0639\u0631\u0648\u0636"],
            "salon": ["\U0001F487\u200D\u2640\uFE0F \u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0634\u0639\u0631", "\U0001F485 \u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0628\u0627\u0644\u0623\u0638\u0627\u0641\u0631", "\U0001F486\u200D\u2640\uFE0F \u0627\u0644\u0639\u0646\u0627\u064a\u0629 \u0628\u0627\u0644\u0628\u0634\u0631\u0629", "\U0001F4B0 \u0627\u0644\u0623\u0633\u0639\u0627\u0631"],
            "education": ["\U0001F4DA \u0627\u0644\u062f\u0648\u0631\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629", "\U0001F4BB \u062f\u0648\u0631\u0627\u062a \u0627\u0644\u062a\u0642\u0646\u064a\u0629", "\U0001F476 \u0628\u0631\u0627\u0645\u062c \u0627\u0644\u0623\u0637\u0641\u0627\u0644", "\U0001F4B0 \u0627\u0644\u0631\u0633\u0648\u0645"],
        }
        buttons = sector_buttons.get(business.sector, ["\U0001F4CB \u0627\u0644\u062e\u062f\u0645\u0627\u062a", "\U0001F4B0 \u0627\u0644\u0623\u0633\u0639\u0627\u0631"])
    else:
        name = business.name_en or business.name_ar
        text = "Welcome to " + name + "! \U0001F31F\n\nHow can I help you today?"
        sector_buttons = {
            "restaurant": ["\U0001F37D\uFE0F View Menu", "\u2B50 Popular Items", "\U0001F6F5 Place Order", "\U0001F4B0 Prices"],
            "medical": ["\U0001F468\u200D\u2695\uFE0F Book Appointment", "\U0001F3E5 Our Services", "\U0001F4B0 Prices", "\u23F0 Working Hours"],
            "hotel": ["\U0001F6CF\uFE0F Book Room", "\U0001F486 Spa Services", "\U0001F37D\uFE0F Restaurant", "\U0001F4B0 Rates"],
            "retail": ["\U0001F4F1 Electronics", "\U0001F3AE Gaming", "\U0001F4DA Books", "\U0001F4B0 Deals"],
            "salon": ["\U0001F487\u200D\u2640\uFE0F Hair Services", "\U0001F485 Nails", "\U0001F486\u200D\u2640\uFE0F Skincare", "\U0001F4B0 Prices"],
            "education": ["\U0001F4DA Courses", "\U0001F4BB Tech Programs", "\U0001F476 Kids Programs", "\U0001F4B0 Fees"],
        }
        buttons = sector_buttons.get(business.sector, ["\U0001F4CB Services", "\U0001F4B0 Prices"])

    return {
        "response_text": text,
        "agent_name": "GreetingAgent",
        "confidence": 1.0,
        "should_escalate": False,
        "escalation_reason": None,
        "detected_intent": "greeting",
        "suggested_buttons": buttons,
        "customer_name": None,
    }


def extract_customer_name(message_text):
    text = message_text.strip()
    words = text.split()
    if 1 <= len(words) <= 3:
        skip_words = {"yes", "no", "hi", "hello", "ok", "okay", "نعم", "لا", "مرحبا",
                      "اهلا", "شكرا", "menu", "order", "price", "thanks", "help",
                      "stop", "قف", "توقف", "skip"}
        if text.lower() not in skip_words:
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
            if arabic_chars > 0 or (words[0][0].isupper() if words[0] else False):
                name = " ".join(w.strip(".,!?") for w in words)
                return name
    patterns = [
        r"(?:my name is|i'm|i am|call me|this is)\s+([A-Za-z\s]{2,30})",
        r"(?:اسمي|أنا|انا)\s+([\u0600-\u06FF\s]{2,30})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def find_or_create_customer(db, business_id, phone):
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()
    customer = db.query(Customer).filter(
        Customer.business_id == business_id,
        Customer.phone_hash == phone_hash
    ).first()
    if not customer:
        customer = db.query(Customer).filter(Customer.phone_hash == phone).first()
    if not customer:
        try:
            customer = Customer(
                business_id=business_id,
                phone_hash=phone_hash,
                phone_encrypted=phone,
                preferred_language="ar",
                status="active",
                created_at=datetime.utcnow()
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            logger.info("New customer | biz=" + business_id[:8] + " | hash=" + phone_hash[:12])
        except Exception as e:
            db.rollback()
            logger.error("Customer create failed: " + str(e))
            customer = None
    return customer


def find_active_conversation(db, business_id, customer_id):
    if not customer_id:
        return None
    cutoff = datetime.utcnow() - timedelta(hours=24)
    return db.query(Conversation).filter(
        Conversation.business_id == business_id,
        Conversation.customer_id == customer_id,
        Conversation.status == "active",
        Conversation.created_at >= cutoff
    ).order_by(Conversation.created_at.desc()).first()


def get_or_create_conversation(db, business_id, customer_id):
    if not customer_id:
        return None
    convo = find_active_conversation(db, business_id, customer_id)
    if convo:
        return convo
    try:
        convo = Conversation(
            business_id=business_id,
            customer_id=customer_id,
            status="active",
            detected_language="ar",
            message_count=0,
            created_at=datetime.utcnow()
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)
        logger.info("New conversation | biz=" + business_id[:8] + " | cust=" + customer_id[:8])
        return convo
    except Exception as e:
        db.rollback()
        logger.error("Conversation create failed: " + str(e))
        return None


def save_messages(db, convo, business_id, user_text, ai_text, agent_name=None):
    try:
        user_msg = Message(
            conversation_id=convo.id,
            business_id=business_id,
            direction="inbound",
            sender_type="customer",
            message_type="text",
            content=user_text,
            created_at=datetime.utcnow()
        )
        db.add(user_msg)

        ai_msg = Message(
            conversation_id=convo.id,
            business_id=business_id,
            direction="outbound",
            sender_type="ai",
            message_type="text",
            content=ai_text,
            ai_agent=agent_name or "SalesAgent",
            created_at=datetime.utcnow()
        )
        db.add(ai_msg)

        convo.message_count = (convo.message_count or 0) + 2
        convo.updated_at = datetime.utcnow()

        db.commit()
        logger.info("Messages saved | convo=" + convo.id[:8] + " | count=" + str(convo.message_count))
    except Exception as e:
        db.rollback()
        logger.error("Message save failed: " + str(e))


@router.post("/process", response_model=ChatResponse)
async def process_message(msg: IncomingMessage, db: Session = Depends(get_db)):

    business = db.query(Business).filter(Business.id == msg.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    products = db.query(Product).filter(
        Product.business_id == msg.business_id,
        Product.is_available == True
    ).all()

    customer = find_or_create_customer(db, msg.business_id, msg.customer_phone)
    if not customer:
        raise HTTPException(status_code=500, detail="Could not create customer")

    saved_name = None
    if customer.name_encrypted and not customer.name_encrypted.startswith("+") and not customer.name_encrypted.isdigit():
        saved_name = customer.name_encrypted

    lang = msg.message_language or detect_language(msg.message_text)

    convo = get_or_create_conversation(db, msg.business_id, customer.id)

    if is_greeting(msg.message_text):
        greeting = build_greeting_response(business, products, lang)
        greeting["customer_name"] = saved_name
        if convo:
            save_messages(db, convo, msg.business_id, msg.message_text, greeting["response_text"], "GreetingAgent")
        return ChatResponse(**greeting)

    conversation_history = []
    if convo:
        try:
            recent_messages = db.query(Message).filter(
                Message.conversation_id == convo.id
            ).order_by(Message.created_at.asc()).limit(20).all()

            for m in recent_messages:
                if m.direction == "inbound":
                    role = "user"
                else:
                    role = "assistant"
                conversation_history.append({"role": role, "content": m.content or ""})
        except Exception:
            conversation_history = []

    if customer and not saved_name:
        asked_for_name = False
        for h in conversation_history[-4:]:
            if h["role"] == "assistant":
                cl = h["content"].lower()
                if any(phrase in cl for phrase in ["your name", "اسمك", "ممكن اعرف"]):
                    asked_for_name = True
        if asked_for_name:
            extracted = extract_customer_name(msg.message_text)
            if extracted:
                saved_name = extracted
                try:
                    customer.name_encrypted = extracted
                    db.commit()
                    logger.info("Name saved: " + extracted)
                except Exception:
                    db.rollback()

    business_config = {
        "name_en": business.name_en,
        "name_ar": business.name_ar,
        "city": business.city or "Riyadh",
        "sector": business.sector or "general",
    }

    product_list = []
    for p in products:
        product_list.append({
            "name_en": p.name_en,
            "name_ar": p.name_ar,
            "price": float(p.price) if p.price else 0,
            "category": p.category or "",
            "description_en": p.description_en or "",
            "description_ar": p.description_ar or "",
        })

    orchestrator = AgentOrchestrator()
    try:
        result = await orchestrator.process(
            message=msg.message_text,
            business_id=msg.business_id,
            customer_id=customer.id,
            business_config=business_config,
            products=product_list,
            conversation_history=conversation_history,
            customer_name=saved_name,
            language=lang,
            db=db
        )
    except Exception as e:
        logger.error("Orchestrator error: " + str(e))
        if lang == "ar":
            fallback = "\u0623\u0647\u0644\u0627\u064b \u0628\u0643 \u0641\u064a " + business_config.get("name_ar", "") + "! \u0643\u064a\u0641 \u0623\u0642\u062f\u0631 \u0623\u0633\u0627\u0639\u062f\u0643\u061f"
        else:
            fallback = "Welcome to " + business_config.get("name_en", "") + "! How can I help you?"
        result = {
            "response_text": fallback,
            "agent_name": "FallbackAgent",
            "confidence": 0.5,
            "should_escalate": False,
            "escalation_reason": None,
            "detected_intent": "unknown",
        }

    response_text = result.get("response_text", "")
    agent_name = result.get("agent_name", "SalesAgent")
    if convo:
        save_messages(db, convo, msg.business_id, msg.message_text, response_text, agent_name)

    return ChatResponse(
        response_text=response_text,
        agent_name=agent_name,
        confidence=result.get("confidence"),
        should_escalate=result.get("should_escalate", False),
        escalation_reason=result.get("escalation_reason"),
        detected_intent=result.get("detected_intent"),
        suggested_buttons=result.get("suggested_buttons"),
        customer_name=saved_name,
    )


@router.get("/stats/{business_id}")
async def get_conversation_stats(business_id: str, db: Session = Depends(get_db)):
    total = db.query(Conversation).filter(Conversation.business_id == business_id).count()
    active = db.query(Conversation).filter(Conversation.business_id == business_id, Conversation.status == "active").count()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Conversation).filter(Conversation.business_id == business_id, Conversation.created_at >= today).count()
    return {"total_conversations": total, "active_conversations": active, "today_conversations": today_count}


@router.get("/history/{business_id}")
async def get_conversation_history(business_id: str, limit: int = 50, db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(
        Conversation.business_id == business_id
    ).order_by(Conversation.created_at.desc()).limit(limit).all()

    results = []
    for c in conversations:
        last_msgs = db.query(Message).filter(
            Message.conversation_id == c.id
        ).order_by(Message.created_at.desc()).limit(1).all()

        last_message = last_msgs[0].content if last_msgs else ""
        msg_count = c.message_count or db.query(Message).filter(Message.conversation_id == c.id).count()

        customer_name = None
        customer_phone = None
        if c.customer_id:
            cust = db.query(Customer).filter(Customer.id == c.customer_id).first()
            if cust:
                if cust.name_encrypted and not cust.name_encrypted.startswith("+"):
                    customer_name = cust.name_encrypted
                customer_phone = (cust.phone_hash or "")[:12]

        results.append({
            "id": str(c.id),
            "customer_id": str(c.customer_id) if c.customer_id else None,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "status": c.status,
            "channel": "whatsapp",
            "last_message": (last_message or "")[:100],
            "message_count": msg_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return results


@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": str(m.id),
            "role": "user" if m.direction == "inbound" else "assistant",
            "content": m.content or "",
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
