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

    # Revenue & Currency Configuration
    REVENUE_REPORTING_CURRENCY: str = "INR"

    # Razorpay Live Configuration
    RAZORPAY_ENABLED: bool = True
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None
    RAZORPAY_WEBHOOK_SECRET: str | None = None
    RAZORPAY_MODE: str = "live"

    # Razorpay EFV Account Configuration
    RAZORPAY_EFV_ENABLED: bool = True
    RAZORPAY_EFV_KEY_ID: str | None = None
    RAZORPAY_EFV_KEY_SECRET: str | None = None
    RAZORPAY_EFV_WEBHOOK_SECRET: str | None = None

    # Cashfree Gateway Configuration
    CASHFREE_ENABLED: bool = True
    CASHFREE_APP_ID: str | None = None
    CASHFREE_SECRET_KEY: str | None = None
    CASHFREE_ENVIRONMENT: str = "production"

    # Google Play Store & Cloud Configuration
    GOOGLE_PLAY_ENABLED: bool = True
    GOOGLE_PLAY_SERVICE_ACCOUNT_JSON: str | None = None
    GOOGLE_PLAY_PROJECT_ID: str | None = None
    GOOGLE_PLAY_GCS_BUCKET_ID: str | None = None
    GOOGLE_PAY_MERCHANT_ID: str | None = None
    PLAY_STORE_SYNC_INTERVAL_HOURS: int = 6

    # Google Analytics 4 (GA4) Configuration
    GA4_PROPERTY_ID: str | None = None
    GA4_CREDENTIALS_JSON: str | None = None

    # Apple App Store Connect Configuration
    APPLE_APP_STORE_ENABLED: bool = True
    APP_STORE_CONNECT_ISSUER_ID: str | None = None
    APP_STORE_CONNECT_KEY_ID: str | None = None
    APP_STORE_CONNECT_PRIVATE_KEY_PATH: str | None = None
    APP_STORE_KEY_ID: str | None = None
    APP_STORE_ISSUER_ID: str | None = None
    APP_STORE_PRIVATE_KEY: str | None = None
    APP_STORE_APP_ID: str | None = None
    APPLE_KEY_ID: str | None = None
    APPLE_TEAM_ID: str | None = None
    APPLE_VENDOR_NUMBER: str | None = None

    # App Mappings
    AISA_APPLE_APP_ID: str | None = None
    AISA_BUNDLE_ID: str | None = None
    AI_LEGAL_APPLE_APP_ID: str | None = None
    AI_LEGAL_BUNDLE_ID: str | None = None

    # Google Cloud Platform (GCP) Monitoring Configuration
    GCP_PROJECT_ID: str | None = None
    GCP_SERVICE_ACCOUNT_JSON: str | None = None

    # Firebase Mobile Analytics Configuration
    FIREBASE_PROJECT_ID: str | None = None
    FIREBASE_CREDENTIALS_JSON: str | None = None

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
