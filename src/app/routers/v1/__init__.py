from fastapi import APIRouter

from app.routers.v1.auth_endpoints import router as auth_router
from app.routers.v1.user_endpoints import router as user_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router, prefix="/auth")
v1_router.include_router(user_router, prefix="/users")
