from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    DB_FILE: str = "smarthome.db"

    TTN_BASE_URL: str = "https://eu1.cloud.thethings.network"
    TTN_APP_ID: str = ""
    TTN_API_KEY: str = ""
    JOIN_EUI: str = "0000000000000000"
    TTN_WEBHOOK_SECRET: str = ""

    THINGSBOARD_URL: str = "http://localhost:8080"
    TB_USERNAME: str = "tenant@thingsboard.org"
    TB_PASSWORD: str = "tenant"

    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_FROM: str = ""
    ALERT_EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    ADMIN_EMAIL: str = "admin@system.local"
    ADMIN_PASSWORD: str = "change-me"
    SESSION_TTL_SECONDS: int = 28800
    PASSWORD_PBKDF2_ITERATIONS: int = 200000
    COOKIE_SECURE: bool = False

    LOCAL_TEST_MODE: bool = False
    CORS_ORIGINS: str = ""


settings = Settings()
