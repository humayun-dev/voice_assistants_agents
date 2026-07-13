"""
Central configuration. Every environment variable the app needs is loaded
here, once — nothing else in the codebase should call os.getenv() directly.
This makes it obvious at a glance what the app depends on, and makes it
trivial to swap in a real secrets manager later without touching other files.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # WhatsApp Cloud API
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_API_URL: str = (
        f"https://graph.facebook.com/v25.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")

    # Business rules
    MAX_DISCOUNT_PERCENT: int = int(os.getenv("MAX_DISCOUNT_PERCENT", "10"))


settings = Settings()
