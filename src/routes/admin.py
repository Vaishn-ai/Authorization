from fastapi import APIRouter

from src.modules.admin.routers import router as admin_router


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

router.include_router(admin_router)