import re
import logging

logger = logging.getLogger(__name__)

BLOCKED_TOPICS = {
    "politics": [
        "سياسة", "سياسي", "حكومة", "ملك", "أمير", "رئيس", "انتخاب",
        "politics", "government", "president", "election",
        "mbs", "saudi government", "iran", "israel", "palestine", "war",
        "حرب", "إيران", "إسرائيل", "فلسطين", "ترامب", "trump", "biden"
    ],
    "religion_debate": [
        "كافر", "شرك", "ملحد", "تكفير",
        "kafir", "infidel", "atheist",
        "which religion is best", "religion is wrong",
        "god doesn't exist", "الله غير موجود", "الدين غلط"
    ],
    "adult": [
        "porn", "xxx", "nude", "naked", "عري",
        "hookup", "escort"
    ],
    "illegal": [
        "cocaine", "weed", "marijuana", "مخدرات", "حشيش", "كوكايين",
        "hack", "crack", "pirate", "اختراق",
        "fake id", "هوية مزورة", "تزوير", "gambling", "قمار",
        "weapon", "bomb", "سلاح", "قنبلة"
    ],
    "competitor": [
        "build me a bot", "make me an app", "code for me",
        "ابني لي تطبيق", "سوي لي برنامج",
        "write my essay", "do my homework"
    ],
    "personal_ai": [
        "who created you", "are you alive", "are you sentient",
        "مين صنعك", "هل أنت حي", "do you have feelings", "هل عندك مشاعر"
    ]
}

REFUSAL_MESSAGES = {
    "politics": {
        "ar": "عذراً، لا أستطيع مناقشة المواضيع السياسية. 🙏\nأنا هنا لمساعدتك في طلباتك.\n\nكيف أقدر أساعدك؟ 😊",
        "en": "Sorry, I can't discuss political topics. 🙏\nI'm here to help with our services.\n\nHow can I help you? 😊"
    },
    "religion_debate": {
        "ar": "عذراً، لا أستطيع الخوض في نقاشات دينية. 🙏\nكيف أقدر أساعدك في طلبك؟",
        "en": "Sorry, I can't engage in religious debates. 🙏\nHow can I help with your order?"
    },
    "adult": {
        "ar": "عذراً، هذا المحتوى غير مناسب. 🚫\nكيف أقدر أساعدك في طلبك؟",
        "en": "Sorry, this content is inappropriate. 🚫\nHow can I help with your order?"
    },
    "illegal": {
        "ar": "عذراً، لا أستطيع المساعدة في هذا. 🚫\nهل تحتاج مساعدة في طلب؟",
        "en": "Sorry, I cannot assist with this. 🚫\nNeed help with an order?"
    },
    "competitor": {
        "ar": "أنا مساعد رسيل، متخصص في خدمة هذا المتجر فقط. 😊\nكيف أقدر أساعدك؟",
        "en": "I'm Raseel AI, specialized in this business only. 😊\nHow can I help?"
    },
    "personal_ai": {
        "ar": "أنا مساعد رسيل الذكي 🤖 هنا لمساعدتك في طلباتك!\nكيف أقدر أخدمك؟ 😊",
        "en": "I'm Raseel AI Assistant 🤖 here to help with orders!\nHow can I help? 😊"
    }
}


def detect_language(text):
    arabic_chars = sum(1 for c in text if ord(c) > 1536 and ord(c) < 1792)
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return "en"
    if arabic_chars / total_alpha > 0.3:
        return "ar"
    return "en"


def check_blocked_topic(message_text):
    text_lower = message_text.lower().strip()
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)

    for category, keywords in BLOCKED_TOPICS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if len(keyword_lower) <= 3:
                words = text_clean.split()
                if keyword_lower in words:
                    lang = detect_language(message_text)
                    refusal = REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["illegal"])
                    logger.info("BLOCKED: " + category + " keyword: " + keyword)
                    return (True, category, refusal[lang])
            else:
                if keyword_lower in text_clean:
                    lang = detect_language(message_text)
                    refusal = REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["illegal"])
                    logger.info("BLOCKED: " + category + " keyword: " + keyword)
                    return (True, category, refusal[lang])

    return (False, None, None)


def get_system_guardrail_prompt():
    return """
STRICT RULES:
1. You are a BUSINESS assistant ONLY for menu, orders, prices, hours.
2. NEVER discuss politics, government, religion debates, adult content, drugs, weapons, illegal activities.
3. NEVER give personal opinions on controversial topics.
4. If asked who made you: "I'm Raseel AI assistant."
5. NEVER generate code, write essays, or do non-business tasks.
6. Keep focus on products, ordering, prices, business hours, delivery.
7. Be respectful of Saudi culture and Islamic values.
8. All prices include 15% VAT per Saudi law.
"""
