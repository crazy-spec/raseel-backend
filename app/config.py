import os
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        override=True,
    )
except ImportError:
    pass


class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "raseel-platform")
        self.app_version = os.getenv("APP_VERSION", "2.0.0")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.data_region = os.getenv("DATA_REGION", "Saudi Arabia")

        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./raseel_dev.db")
        self.secret_key = os.getenv("SECRET_KEY", "raseel-secret-key-change-in-production-2026")

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "")
        self.whatsapp_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "raseel-webhook-verify-2026")
        self.unifonic_app_id = os.getenv("UNIFONIC_APP_ID", "")
        self.unifonic_sender_id = os.getenv("UNIFONIC_SENDER_ID", "")
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "raseel-encryption-key-2026")


@lru_cache()
def get_settings():
    return Settings()
