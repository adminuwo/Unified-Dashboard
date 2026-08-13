from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    APP_NAME: str = "unified-service"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "*"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "unified_service_db"

    JWT_SECRET: str = "super-secret-jwt-key-change-this-in-production-32-bytes"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PAYMENT_SECRET_KEY: str = "sk_test_mock_payment_provider_secret_key_12345"
    PAYMENT_WEBHOOK_SECRET: str = "whsec_mock_payment_webhook_secret_key_67890"

    EMAIL_API_KEY: str = "mock_email_api_key_abc123"
    EXTERNAL_API_KEY: str = "mock_external_service_key_xyz789"

    # Google Play Store Reporting & Analytics Configuration
    GOOGLE_PLAY_SERVICE_ACCOUNT_JSON: str | None = None
    GOOGLE_PLAY_PROJECT_ID: str | None = None
    GOOGLE_PLAY_GCS_BUCKET_ID: str | None = None
    PLAY_STORE_SYNC_INTERVAL_HOURS: int = 24

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
