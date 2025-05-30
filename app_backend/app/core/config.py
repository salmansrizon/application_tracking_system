from pydantic_settings import BaseSettings
import os
from typing import Optional, List # Added List just in case, Optional was already there

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Qdrant Settings
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6334)) # Default HTTP port
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_RESUME_COLLECTION: str = os.getenv("QDRANT_RESUME_COLLECTION", "user_resumes")

    # Email Settings (for fastapi-mail)
    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME", None)
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD", None)
    MAIL_FROM: Optional[str] = os.getenv("MAIL_FROM", None) # e.g. your_app@example.com
    MAIL_FROM_NAME: Optional[str] = os.getenv("MAIL_FROM_NAME", "Application Tracker")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: Optional[str] = os.getenv("MAIL_SERVER", None) # e.g. smtp.mailgun.org
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
    MAIL_TEMPLATES_DIR: Optional[str] = os.getenv("MAIL_TEMPLATES_DIR", None) # e.g. app/templates/email

    # Secret for triggering admin tasks like deadline checks
    BACKGROUND_TASK_ADMIN_SECRET: str = os.getenv("BACKGROUND_TASK_ADMIN_SECRET", "SUPER_SECRET_KEY_CHANGE_ME")

    # Add a default JWT secret if needed for local token generation/validation,
    # but Supabase's own JWTs are usually validated against their JWKS endpoint.
    # For this example, we'll rely on Supabase's own token generation.
    # JWT_SECRET_KEY: str = "your_super_secret_jwt_key"
    # ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
