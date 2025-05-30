from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    # Add a default JWT secret if needed for local token generation/validation,
    # but Supabase's own JWTs are usually validated against their JWKS endpoint.
    # For this example, we'll rely on Supabase's own token generation.
    # JWT_SECRET_KEY: str = "your_super_secret_jwt_key"
    # ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
