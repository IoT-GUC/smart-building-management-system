import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_FILE: str = os.getenv("DB_FILE", "smarthome.db")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")
    TTN_BASE: str = os.getenv("TTN_BASE_URL", "https://eu1.cloud.thethings.network")
    APP_ID: str = os.getenv("TTN_APP_ID", "")
    API_KEY: str = os.getenv("TTN_API_KEY", "")
    JOIN_EUI: str = os.getenv("JOIN_EUI", "0000000000000000")
    ALERT_EMAIL_SENDER: str = os.getenv("ALERT_EMAIL_SENDER", "")
    ALERT_EMAIL_PASSWORD: str = os.getenv("ALERT_EMAIL_PASSWORD", "")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
