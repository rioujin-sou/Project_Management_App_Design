from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Project Management API"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    
    # CORS
    # Accepts a JSON list of URLs  e.g. '["http://localhost:3000"]'
    # or the wildcard string '["*"]' for development/testing.
    # ⚠️  WARNING: Using "*" disables origin checking entirely — never use this
    #    in production as it exposes the API to cross-site request attacks.
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            # Comma-separated string  e.g. "http://localhost:3000,http://localhost:8000"
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            parsed = json.loads(v)
            # Allow the wildcard origin for development convenience
            if parsed == ["*"] or parsed == "*":
                return ["*"]
            return parsed
        elif isinstance(v, list):
            if v == ["*"]:
                return ["*"]
            return v
        raise ValueError(v)
    
    # Email Configuration
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    
    # Admin User
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "changeme"


settings = Settings()
