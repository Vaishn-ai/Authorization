from fastapi import (
    APIRouter,
    Depends,
    Form,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.auth import get_current_user
from src.configs.database import get_db

from src.modules.admin.functions import (
    create_admin,
    get_admins,
    update_admin,
)

from src.modules.admin.interface import (
    AdminCreate,
    AdminResponse,
)


router = APIRouter()


# ==========================================
# CREATE ADMIN
# ==========================================

@router.post(
    "/admins",
    response_model=AdminResponse
)
async def register_admin(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),

    db: AsyncSession = Depends(get_db)
):
    admin_data = AdminCreate(
        username=username,
        email=email,
        password=password
    )

    return await create_admin(
        db=db,
        username=admin_data.username,
        email=admin_data.email,
        password=admin_data.password
    )


# ==========================================
# GET ADMINS
# ==========================================

@router.get(
    "/admins",
    response_model=list[AdminResponse]
)
async def get_all_admins(
    db: AsyncSession = Depends(get_db)
):
    return await get_admins(db)


# ==========================================
# UPDATE ADMIN
# ==========================================

@router.put(
    "/admins/{admin_id}",
    response_model=AdminResponse
)
async def update_admin_details(
    admin_id: int,

    username: str | None = Form(default=None),
    email: str | None = Form(default=None),
    password: str | None = Form(default=None),

    current_user: dict = Depends(
        get_current_user
    ),

    db: AsyncSession = Depends(get_db)
):
    return await update_admin(
        db=db,
        admin_id=admin_id,
        current_user_id=current_user["user_id"],
        current_user_role=current_user["role"],
        username=username,
        email=email,
        password=password
    )