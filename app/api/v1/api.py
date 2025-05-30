from fastapi import APIRouter

from app.api.v1.endpoints import users, auth, admin
from app.core.config import Settings

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
