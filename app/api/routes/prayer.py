from fastapi import APIRouter
from app.cultural.prayer_times import prayer_service

router = APIRouter()


@router.get("/prayer-times/{city}")
async def get_prayer_times(city: str = "Riyadh"):
    """Get today's prayer times for a Saudi city."""
    times = await prayer_service.get_prayer_times(city)
    is_prayer, prayer_name, minutes_left = await prayer_service.is_prayer_time(city)
    greeting = prayer_service.get_contextual_greeting("ar")
    greeting_en = prayer_service.get_contextual_greeting("en")

    return {
        "city": city,
        "prayer_times": times,
        "is_prayer_time_now": is_prayer,
        "current_prayer": prayer_name,
        "minutes_until_resume": minutes_left,
        "greeting_ar": greeting,
        "greeting_en": greeting_en,
        "messaging_paused": is_prayer,
    }


@router.get("/should-pause/{city}")
async def should_pause_messaging(city: str = "Riyadh"):
    """Quick check if messaging should be paused for prayer."""
    is_prayer, prayer_name, minutes_left = await prayer_service.is_prayer_time(city)
    return {
        "should_pause": is_prayer,
        "reason": f"Prayer time: {prayer_name}" if is_prayer else None,
        "resume_in_minutes": minutes_left,
    }