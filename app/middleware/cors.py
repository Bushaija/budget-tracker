from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings

def setup_cors(app: FastAPI):
    """configure CORS for the app"""
    if Settings.ENVIRONMENT == "development":
        allowed_origins = ["*"]
    else:
        allowed_origins = Settings.BACKEND_CORS_ORIGINS or []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

