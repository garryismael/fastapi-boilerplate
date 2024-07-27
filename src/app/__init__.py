from fastapi import APIRouter

from app.routers.v1 import v1_router as v1_router

router = APIRouter(prefix="/api")
router.include_router(v1_router)
