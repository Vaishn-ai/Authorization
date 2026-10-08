from fastapi import APIRouter

from src.modules.auth.routers import router as auth_router


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

router.include_router(auth_router)