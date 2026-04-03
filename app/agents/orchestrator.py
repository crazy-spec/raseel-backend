import re
import time
from typing import Optional, List
from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from app.ai.model_router import model_router
from app.utils.logger import get_logger

logger = get_logger()

# ============================================================
# STOP / UNSUBSCRIBE DETECTION
# ============================================================
STOP_WORDS_EN = {"stop", "unsubscribe", "opt out", "cancel", "remove me", "no more"}
STOP_WORDS_AR = {"توقف", "قف", "إلغاء", "الغاء الاشتراك", "ما أبي رسائل", "لا تراسلني", "وقف"}

def detect_stop(text):
    return text.strip().lower() in STOP_WORDS_EN or text.strip().lower() in STOP_WORDS_AR

# ============================================================
# HUMAN ESCALATION DETECTION
# ============================================================
HUMAN_WORDS_EN = {"human", "agent", "real person", "speak to someone", "manager", "supervisor", "representative"}
HUMAN_WORDS_AR = {"بشري", "موظف", "شخص حقيقي", "أبي أكلم أحد", "مدير", "مسؤول", "ممثل", "كلم شخص"}

def detect_human_request(text):
    cleaned = text.strip().lower()
    for word in HUMAN_WORDS_EN | HUMAN_WORDS_AR:
        if word in cleaned:
            return True
    return False

# ============================================================
# LANGUAGE DETECTION
# ============================================================
def detect_message_language(text):
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    if arabic_chars > 0 and arabic_chars >= latin_chars:
        return "ar"
    if latin_chars > 0:
        return "en"
    return "ar"

# ============================================================
# SYSTEM PROMPT BUILDER — STRICT LANGUAGE ENFORCEMENT
# ============================================================
def build_system_prompt(business_config, products, customer_name=None, language="ar"):
    sector = business_config.get("sector", "general")
    name_en = business_config.get("name_en", "Our Business")
    name_ar = business_config.get("name_ar", name_en)
    city = business_config.get("city", "Riyadh")

    sector_personalities = {
        "restaurant": {
            "role_ar": "مساعد مطعم " + name_ar + " الذكي في " + city,
            "role_en": "the smart assistant for " + name_en + " restaurant in " + city,
            "style_ar": "رحب بالعميل بحرارة، اقترح الأطباق المميزة، ساعده في الطلب",
            "style_en": "Welcome warmly, suggest popular dishes, help place orders",
            "upsell_ar": "اقترح المشروبات أو الحلويات مع الوجبة",
            "upsell_en": "Suggest drinks or desserts with the meal",
        },
        "medical": {
            "role_ar": "مساعد " + name_ar + " في " + city,
            "role_en": "the assistant for " + name_en + " in " + city,
            "style_ar": "كن مهنياً ومطمئناً، ساعد في حجز المواعيد والاستفسار عن الخدمات",
            "style_en": "Be professional and reassuring, help book appointments and answer about services",
            "upsell_ar": "اقترح الفحوصات الشاملة أو الخدمات الإضافية المناسبة",
            "upsell_en": "Suggest comprehensive checkups or relevant additional services",
        },
        "hotel": {
            "role_ar": "مساعد " + name_ar + " في " + city,
            "role_en": "the concierge for " + name_en + " in " + city,
            "style_ar": "كن فخماً ومرحباً، ساعد في حجز الغرف وخدمات الفندق",
            "style_en": "Be luxurious and welcoming, help with room bookings and hotel services",
            "upsell_ar": "اقترح ترقية الغرفة أو خدمات السبا أو المطعم",
            "upsell_en": "Suggest room upgrades, spa services, or dining",
        },
        "retail": {
            "role_ar": "مساعد " + name_ar + " في " + city,
            "role_en": "the shopping assistant for " + name_en + " in " + city,
            "style_ar": "ساعد العميل في إيجاد المنتج المناسب، اقترح البدائل",
            "style_en": "Help find the right product, suggest alternatives",
            "upsell_ar": "اقترح الإكسسوارات أو المنتجات المكملة",
            "upsell_en": "Suggest accessories or complementary products",
        },
        "salon": {
            "role_ar": "مساعدة " + name_ar + " في " + city,
            "role_en": "the beauty consultant for " + name_en + " in " + city,
            "style_ar": "كوني ودودة ومحترفة، ساعدي في اختيار الخدمات والحجز",
            "style_en": "Be friendly and professional, help choose services and book",
            "upsell_ar": "اقترحي خدمات العناية بالبشرة أو الأظافر",
            "upsell_en": "Suggest skincare or nail services",
        },
        "education": {
            "role_ar": "مساعد " + name_ar + " في " + city,
            "role_en": "the enrollment advisor for " + name_en + " in " + city,
            "style_ar": "كن متحمساً ومفيداً، ساعد في اختيار الدورات والتسجيل",
            "style_en": "Be enthusiastic and helpful, assist with course selection and enrollment",
            "upsell_ar": "اقترح الدورات المكملة أو الباقات",
            "upsell_en": "Suggest complementary courses or packages",
        },
    }

    default_p = {
        "role_ar": "مساعد " + name_ar + " الذكي",
        "role_en": "the smart assistant for " + name_en,
        "style_ar": "كن ودوداً ومحترفاً",
        "style_en": "Be friendly and professional",
        "upsell_ar": "اقترح الخدمات الإضافية",
        "upsell_en": "Suggest additional services",
    }

    p = sector_personalities.get(sector, default_p)

    # Build product catalog text
    product_text = ""
    if products:
        categories = {}
        for prod in products:
            cat = prod.get("category", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(prod)
        for cat, items in categories.items():
            product_text = product_text + "\n--- " + cat + " ---\n"
            for prod in items:
                price = prod.get("price", 0)
                vat_price = round(price * 1.15, 2)
                if language == "ar":
                    line = "- " + prod.get("name_ar", prod.get("name_en", "")) + ": " + str(vat_price) + " ريال شامل الضريبة"
                else:
                    line = "- " + prod.get("name_en", "") + ": " + str(vat_price) + " SAR (VAT included)"
                product_text = product_text + line + "\n"

    # Customer name instruction
    name_inst = ""
    if customer_name:
        if language == "ar":
            name_inst = "\nاسم العميل: " + customer_name + ". استخدم اسمه في الردود بشكل طبيعي."
        else:
            name_inst = "\nCustomer name: " + customer_name + ". Use their name naturally in responses."
    else:
        if language == "ar":
            name_inst = "\nالعميل لم يذكر اسمه بعد. لا تسأله عن اسمه - انتظر حتى يذكره بنفسه."
        else:
            name_inst = "\nCustomer has not shared their name yet. Do NOT ask for their name - wait until they share it."

    # ============================================================
    # BUILD THE PROMPT WITH STRICT LANGUAGE ENFORCEMENT
    # ============================================================
    if language == "ar":
        prompt = "أنت " + p["role_ar"] + "\n\n"
        prompt = prompt + "=== تعليمات اللغة (إلزامي) ===\n"
        prompt = prompt + "يجب أن تكون جميع ردودك باللغة العربية فقط.\n"
        prompt = prompt + "ممنوع منعاً باتاً استخدام أي كلمة إنجليزية.\n"
        prompt = prompt + "لا تكتب Hello أو Welcome أو Thank you أو أي كلمة إنجليزية.\n"
        prompt = prompt + "حتى لو كتب العميل بالإنجليزية، يجب أن ترد بالعربية فقط.\n"
        prompt = prompt + "استخدم أرقام عربية (1، 2، 3) وعملة ريال.\n\n"
        prompt = prompt + "الشخصية: " + p["style_ar"] + "\n"
        prompt = prompt + "البيع الذكي: " + p["upsell_ar"] + "\n"
        prompt = prompt + name_inst + "\n\n"
        prompt = prompt + "القواعد:\n"
        prompt = prompt + "1. رد بالعربية فقط - بدون أي كلمة إنجليزية\n"
        prompt = prompt + "2. لا تذكر منتج غير موجود في القائمة أدناه\n"
        prompt = prompt + "3. الأسعار المذكورة تشمل 15% ضريبة القيمة المضافة\n"
        prompt = prompt + "4. كن ودوداً ومحترماً مع لمسة ضيافة سعودية\n"
        prompt = prompt + "5. إذا سأل عن شيء غير متوفر اعتذر واقترح البديل\n"
        prompt = prompt + "6. لا تخترع معلومات أو أسعار غير موجودة\n"
        prompt = prompt + "7. اجعل ردودك قصيرة ومفيدة (3-5 أسطر)\n\n"
        if product_text:
            prompt = prompt + "المنتجات المتوفرة:\n" + product_text
        else:
            prompt = prompt + "لا توجد منتجات حالياً.\n"
    else:
        prompt = "You are " + p["role_en"] + "\n\n"
        prompt = prompt + "=== LANGUAGE RULES (MANDATORY) ===\n"
        prompt = prompt + "ALL your responses MUST be in English ONLY.\n"
        prompt = prompt + "Do NOT use ANY Arabic words whatsoever.\n"
        prompt = prompt + "Do NOT say Marhaba, Ahlan, Shukran, Habibi, or any Arabic greeting.\n"
        prompt = prompt + "Do NOT mix Arabic and English. English ONLY.\n"
        prompt = prompt + "Even if the customer writes in Arabic, respond in English.\n"
        prompt = prompt + "Use SAR for currency.\n\n"
        prompt = prompt + "Personality: " + p["style_en"] + "\n"
        prompt = prompt + "Smart selling: " + p["upsell_en"] + "\n"
        prompt = prompt + name_inst + "\n\n"
        prompt = prompt + "RULES:\n"
        prompt = prompt + "1. Respond in English ONLY - no Arabic words at all\n"
        prompt = prompt + "2. NEVER mention products not in the catalog below\n"
        prompt = prompt + "3. All prices include 15% VAT\n"
        prompt = prompt + "4. Be warm with friendly hospitality\n"
        prompt = prompt + "5. If unavailable, apologize and suggest alternatives\n"
        prompt = prompt + "6. NEVER invent information or prices\n"
        prompt = prompt + "7. Keep responses short and helpful (3-5 lines)\n\n"
        if product_text:
            prompt = prompt + "Available Products:\n" + product_text
        else:
            prompt = prompt + "No products currently available.\n"

    return prompt


# ============================================================
# AGENT CLASSES
# ============================================================
class SalesAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SalesAgent",
            capabilities=["product_inquiry", "ordering", "pricing"],
            confidence_threshold=0.6
        )

    async def process(self, context=None):
        return AgentResponse(agent_name=self.name, response_text="", confidence=0.0)


class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SupportAgent",
            capabilities=["complaint", "issue", "refund"],
            confidence_threshold=0.5
        )

    async def process(self, context=None):
        return AgentResponse(agent_name=self.name, response_text="", confidence=0.0)


# ============================================================
# ORCHESTRATOR — Main AI Processing
# ============================================================
class AgentOrchestrator:
    def __init__(self):
        self.sales_agent = SalesAgent()
        self.support_agent = SupportAgent()

    async def process(self, message, business_id, customer_id=None,
                      business_config=None, products=None,
                      conversation_history=None, customer_name=None,
                      language="ar", db=None):
        business_config = business_config or {}
        products = products or []
        conversation_history = conversation_history or []
        start_time = time.time()

        biz_name = business_config.get("name_en", "unknown")

        # ---- STOP detection ----
        if detect_stop(message):
            logger.info("STOP detected | biz=" + biz_name + " | msg=" + message[:50])
            if language == "ar":
                return {"response_text": "تم إلغاء اشتراكك بنجاح. لن نرسل لك رسائل تسويقية بعد الآن. شكراً لك!", "agent_name": "SystemAgent", "confidence": 1.0, "should_escalate": False, "escalation_reason": None, "detected_intent": "unsubscribe"}
            return {"response_text": "You have been unsubscribed successfully. No more marketing messages will be sent. Thank you!", "agent_name": "SystemAgent", "confidence": 1.0, "should_escalate": False, "escalation_reason": None, "detected_intent": "unsubscribe"}

        # ---- Human escalation detection ----
        if detect_human_request(message):
            logger.info("HUMAN REQUEST | biz=" + biz_name + " | msg=" + message[:50])
            if language == "ar":
                return {"response_text": "بالتأكيد! سأحولك لأحد أعضاء فريقنا الآن. يرجى الانتظار لحظة...", "agent_name": "EscalationAgent", "confidence": 1.0, "should_escalate": True, "escalation_reason": "Customer requested human agent", "detected_intent": "human_escalation"}
            return {"response_text": "Of course! Transferring you to a team member right now. Please hold...", "agent_name": "EscalationAgent", "confidence": 1.0, "should_escalate": True, "escalation_reason": "Customer requested human agent", "detected_intent": "human_escalation"}

        # ---- Detect support vs sales ----
        support_keywords = {"complaint", "problem", "issue", "refund", "broken", "bad", "terrible", "شكوى", "مشكلة", "استرجاع", "سيء", "خراب"}
        is_support = any(kw in message.lower() for kw in support_keywords)
        agent_name = "SupportAgent" if is_support else "SalesAgent"

        # ---- Build system prompt ----
        system_prompt = build_system_prompt(business_config, products, customer_name, language)

        # ---- Build conversation history for AI ----
        history_for_ai = []
        for h in conversation_history[-16:]:
            history_for_ai.append({"role": h["role"], "content": h["content"]})

        # ---- Call AI ----
        try:
            logger.info("AI CALL | biz=" + biz_name + " | lang=" + language + " | agent=" + agent_name + " | msg=" + message[:80])

            response = await model_router.generate(
                system_prompt=system_prompt,
                user_message=message,
                conversation_history=history_for_ai,
                temperature=0.7,
                max_tokens=500
            )
            response_text = response.text

            elapsed = round(time.time() - start_time, 2)
            logger.info("AI RESPONSE | biz=" + biz_name + " | time=" + str(elapsed) + "s | len=" + str(len(response_text)) + " | resp=" + response_text[:100])

        except Exception as e:
            logger.error("AI ERROR | biz=" + biz_name + " | error=" + str(e))
            name = business_config.get("name_ar" if language == "ar" else "name_en", "")
            if language == "ar":
                response_text = "عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى أو الاتصال بـ " + name + " مباشرة."
            else:
                response_text = "Sorry, a technical error occurred. Please try again or contact " + name + " directly."

        # ---- Detect intent ----
        intent = "general_inquiry"
        ml = message.lower()
        if any(w in ml for w in ["price", "cost", "how much", "سعر", "كم", "بكم", "اسعار"]):
            intent = "pricing"
        elif any(w in ml for w in ["order", "buy", "want", "طلب", "أبي", "ابي", "أبغى", "ابغى", "اطلب"]):
            intent = "ordering"
        elif any(w in ml for w in ["book", "appointment", "reserve", "حجز", "موعد", "احجز"]):
            intent = "booking"
        elif any(w in ml for w in ["menu", "products", "what do you have", "show", "قائمة", "منتجات", "عندكم", "وش عندكم"]):
            intent = "catalog_browse"
        elif any(w in ml for w in ["thanks", "thank", "شكر", "مشكور", "يعطيك العافية"]):
            intent = "thanks"
        elif any(w in ml for w in ["bye", "goodbye", "مع السلامة", "باي", "الله يسلمك"]):
            intent = "farewell"
        elif is_support:
            intent = "support"

        return {
            "response_text": response_text,
            "agent_name": agent_name,
            "confidence": 0.85,
            "should_escalate": False,
            "escalation_reason": None,
            "detected_intent": intent,
        }
