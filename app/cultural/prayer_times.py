import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import pytz

RIYADH_TZ = pytz.timezone("Asia/Riyadh")


class PrayerTimesService:
    def __init__(self):
        self._cache = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def get_prayer_times(self, city: str = "Riyadh") -> Dict[str, str]:
        try:
            now = datetime.now(RIYADH_TZ)
            resp = await self.http_client.get(
                f"https://api.aladhan.com/v1/timingsByCity/{now.strftime('%d-%m-%Y')}",
                params={"city": city, "country": "SA", "method": 4},
            )
            resp.raise_for_status()
            timings = resp.json()["data"]["timings"]
            return {k: timings[k] for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]}
        except Exception:
            return {"Fajr": "04:45", "Dhuhr": "12:00", "Asr": "15:20", "Maghrib": "17:55", "Isha": "19:25"}

    async def is_prayer_time(self, city: str = "Riyadh") -> Tuple[bool, Optional[str], Optional[int]]:
        now = datetime.now(RIYADH_TZ)
        times = await self.get_prayer_times(city)
        for name, time_str in times.items():
            try:
                h, m = map(int, time_str.split(":"))
                prayer_dt = now.replace(hour=h, minute=m, second=0)
                if prayer_dt - timedelta(minutes=5) <= now <= prayer_dt + timedelta(minutes=20):
                    mins_left = int((prayer_dt + timedelta(minutes=20) - now).total_seconds() / 60)
                    return True, name, mins_left
            except (ValueError, TypeError):
                continue
        return False, None, None

    def get_contextual_greeting(self, language: str = "ar") -> str:
        now = datetime.now(RIYADH_TZ)
        if language == "ar":
            if 5 <= now.hour < 12: return "صباح الخير ☀️"
            elif 12 <= now.hour < 17: return "مساء الخير 🌤️"
            else: return "مساء النور 🌙"
        else:
            if 5 <= now.hour < 12: return "Good morning ☀️"
            elif 12 <= now.hour < 17: return "Good afternoon 🌤️"
            else: return "Good evening 🌙"

    async def close(self):
        await self.http_client.aclose()


prayer_service = PrayerTimesService()