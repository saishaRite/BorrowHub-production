import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BorrowHub"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = int(os.environ.get("PORT", 3000))
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:12345@localhost:3306/borrowhub?charset=utf8mb4"

    # Admin Management
    ADMIN_EMAILS: List[str] = [
        "u25cs136@coed.svnit.ac.in",
        "u23cs136@coed.svnit.ac.in",
        "admin@svnit.ac.in",
    ]

    # Security
    JWT_SECRET_KEY: str = "borrowhub_super_secret_jwt_key_svnit_campus_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    OTP_EXPIRY_MINUTES: int = 15

    # Cloudinary Image Upload
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # SMTP / Real Email Sending
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@borrowhub.svnit.ac.in"
    SMTP_FROM_NAME: str = "BorrowHub SVNIT"
    SMTP_TLS: bool = True

    # Brevo Transactional Email API
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = ""

    # Public Application URL
    PUBLIC_APP_URL: str = "http://127.0.0.1:8000"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
