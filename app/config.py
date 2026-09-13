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
    TTN_APP_ID: str = "smart-building-lora-2"
    TTN_API_KEY: str = ""
    JOIN_EUI: str = "0000000000000000"
    LORAWAN_APP_KEY: str = ""
    LORAWAN_FREQUENCY_PLAN_ID: str = "EU_863_870_TTN"
    LORAWAN_VERSION: str = "MAC_V1_0_3"
    LORAWAN_PHY_VERSION: str = "PHY_V1_0_3_REV_A"
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
    DEVICE_STALE_AFTER_SECONDS: int = 300
    DEVICE_OFFLINE_AFTER_SECONDS: int = 86400

    # Ceiling on devices sitting in the unplaced discovery inbox. Zero-touch
    # discovery creates a row per unknown DevEUI, so anyone able to reach the
    # webhook could otherwise grow the devices table without bound. Existing
    # devices are unaffected; only new discoveries are refused at the cap.
    MAX_UNPLACED_DISCOVERED_DEVICES: int = 500


settings = Settings()
