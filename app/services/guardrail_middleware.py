from app.services.guardrails import check_blocked_topic, get_system_guardrail_prompt

def apply_guardrail(message_text):
    is_blocked, category, refusal = check_blocked_topic(message_text)
    if is_blocked:
        return {"blocked": True, "category": category, "response": refusal}
    return {"blocked": False, "category": None, "response": None}

def get_ai_system_prompt(business_name="", sector="restaurant"):
    base = get_system_guardrail_prompt()
    if business_name:
        base = base + "\nBusiness name: " + business_name
    if sector:
        base = base + "\nBusiness type: " + sector
    return base
