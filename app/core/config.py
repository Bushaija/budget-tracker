from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(object):
	"""Application settings"""
	PROJECT_NAME: str = "HIV Tracker API"
	VERSION: str = "1.0.0"
	ENVIRONMENT: str = "development"
	DEBUG: bool = True

	# security settings
	SECRET_KEY: str = secrets.token_urlsafe(32)
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	ALGORITHM: str = "HS256"

	# database settings
	DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/hivtracker"
	DATABASE_TEST_URL: Optional[str] = None

	# CORS Settings
	BACKEND_CORS_ORIGINS: list[str] = ["http:://localhost:3000", "http://localhost:8080"]

	# Email settings (for notification)
	SMTP_TLS: bool = True
	SMTP_PORT: Optional[int] = 587
	SMTP_HOST: Optional[str] = None
	SMTP_USER: Optional[str] = None
	SMTP_PASSWORD: Optional[str] = None
	EMAILS_FROM_EMAIL: Optional[str] = None
	EMAILS_FROM_NAME: Optional[str] = None

	# Rate limiting
	RATE_LIMIT_REQUESTS: int = 100
	RATE_LIMIT_WINDOW: int = 60  # seconds
	
	# File upload settings
	MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
	UPLOAD_DIRECTORY: str = "uploads"
	
	# Logging
	LOG_LEVEL: str = "INFO"
	LOG_FILE: str = "app.log"
	
	class Config:
		env_file = ".env"
		case_sensitive = True

settings = Settings()
