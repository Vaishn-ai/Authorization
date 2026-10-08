from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.admin.models import Admin
from src.configs.security import hash_password
from src.configs.redis import redis_client


# ==========================================
# ADMIN UNIQUE DATA VALIDATION
# ==========================================

async def validate_admin_unique_data(
    db: AsyncSession,
    username: str,
    email: str,
    admin_id: int | None = None
):
    # Check username
    username_result = await db.execute(
        select(Admin).where(
            Admin.username == username
        )
    )

    existing_username = (
        username_result.scalar_one_or_none()
    )

    if (
        existing_username
        and existing_username.id != admin_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # Check email
    email_result = await db.execute(
        select(Admin).where(
            Admin.email == email
        )
    )

    existing_email = (
        email_result.scalar_one_or_none()
    )

    if (
        existing_email
        and existing_email.id != admin_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )


# ==========================================
# CREATE ADMIN
# ==========================================

async def create_admin(
    db: AsyncSession,
    username: str,
    email: str,
    password: str
):
    # ======================================
    # CHECK EMAIL VERIFICATION
    # ======================================

    verification_key = f"email_verified:{email}"

    email_verified = await redis_client.get(
        verification_key
    )

    if email_verified != "true":
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first"
        )

    # ======================================
    # CHECK DUPLICATE USERNAME / EMAIL
    # ======================================

    await validate_admin_unique_data(
        db=db,
        username=username,
        email=email
    )

    # ======================================
    # HASH PASSWORD
    # ======================================

    hashed_password = hash_password(
        password
    )

    # ======================================
    # CREATE ADMIN
    # ======================================

    admin = Admin(
        username=username,
        email=email,
        password=hashed_password
    )

    db.add(admin)

    await db.commit()

    await db.refresh(admin)

    # ======================================
    # REMOVE VERIFICATION FLAG
    # ======================================

    await redis_client.delete(
        verification_key
    )

    return admin


# ==========================================
# GET ALL ADMINS
# ==========================================

async def get_admins(
    db: AsyncSession
):
    result = await db.execute(
        select(Admin)
    )

    return result.scalars().all()


# ==========================================
# UPDATE ADMIN
# ==========================================

async def update_admin(
    db: AsyncSession,
    admin_id: int,
    current_user_id: int,
    current_user_role: str,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None
):
    # ======================================
    # AUTHORIZATION
    # ======================================

    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can update admin details"
        )

    # Admin can update only their own details
    if admin_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can update only your own details"
        )

    # ======================================
    # FIND ADMIN
    # ======================================

    result = await db.execute(
        select(Admin).where(
            Admin.id == admin_id
        )
    )

    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    # ======================================
    # CHECK DUPLICATE USERNAME
    # ======================================

    if username is not None:

        username_result = await db.execute(
            select(Admin).where(
                Admin.username == username,
                Admin.id != admin_id
            )
        )

        existing_username = (
            username_result.scalar_one_or_none()
        )

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

        admin.username = username

    # ======================================
    # CHECK DUPLICATE EMAIL
    # ======================================

    if email is not None:

        email_result = await db.execute(
            select(Admin).where(
                Admin.email == email,
                Admin.id != admin_id
            )
        )

        existing_email = (
            email_result.scalar_one_or_none()
        )

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

        admin.email = email

    # ======================================
    # UPDATE PASSWORD
    # ======================================

    if password is not None:
        admin.password = hash_password(
            password
        )

    # ======================================
    # SAVE CHANGES
    # ======================================

    await db.commit()

    await db.refresh(admin)

    return admin