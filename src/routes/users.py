from fastapi import APIRouter

from src.modules.user.routers import router as user_router


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

router.include_router(user_router)