import os
import random

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import JWTError, jwt
from aiosmtplib import SMTP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.admin.models import Admin
from src.modules.user.models import Student

from src.configs.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
)

from src.configs.redis import redis_client


load_dotenv()


# =========================================================
# SMTP CONFIGURATION
# =========================================================

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(
    os.getenv("SMTP_PORT", "587")
)
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# =========================================================
# LOGIN
# =========================================================

async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
):
    # ==========================================
    # CHECK ADMIN
    # ==========================================

    result = await db.execute(
        select(Admin).where(Admin.email == email)
    )

    admin = result.scalar_one_or_none()

    if admin:

        if not verify_password(
            password,
            admin.password
        ):
            return None

        return {
            "access_token": create_access_token(
                user_id=admin.id,
                role="admin",
            ),
            "refresh_token": create_refresh_token(
                user_id=admin.id,
                role="admin",
            ),
        }

    # ==========================================
    # CHECK STUDENT
    # ==========================================

    result = await db.execute(
        select(Student).where(Student.email == email)
    )

    student = result.scalar_one_or_none()

    if student:

        if not verify_password(
            password,
            student.password
        ):
            return None

        return {
            "access_token": create_access_token(
                user_id=student.id,
                role="student",
            ),
            "refresh_token": create_refresh_token(
                user_id=student.id,
                role="student",
            ),
        }

    return None


# =========================================================
# REFRESH ACCESS TOKEN
# =========================================================

def refresh_access_token(
    refresh_token: str,
):

    try:

        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")

        if not user_id or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        if token_type != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        return create_access_token(
            user_id=int(user_id),
            role=role,
        )

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Refresh token expired or invalid",
        )


# =========================================================
# GENERATE OTP
# =========================================================

def generate_otp() -> str:
    """
    Generate a 6-digit OTP.
    """

    return str(
        random.randint(100000, 999999)
    )


# =========================================================
# CREATE AND STORE OTP
# =========================================================

async def create_email_otp(
    email: str,
):
    """
    Generate OTP and store it in Redis
    for 5 minutes.
    """

    otp = generate_otp()

    redis_key = f"email_otp:{email}"

    await redis_client.set(
        redis_key,
        otp,
        ex=300,
    )

    return otp


# =========================================================
# VERIFY OTP
# =========================================================

async def verify_email_otp(
    email: str,
    otp: str,
):
    """
    Verify OTP stored in Redis.

    OTP automatically expires after 5 minutes.
    """

    redis_key = f"email_otp:{email}"

    stored_otp = await redis_client.get(
        redis_key
    )

    if stored_otp is None:

        raise HTTPException(
            status_code=400,
            detail="OTP expired or not found",
        )

    if stored_otp != otp:

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP",
        )

    # Delete OTP after successful verification
    await redis_client.delete(
        redis_key
    )

    # Store temporary email verification
    await redis_client.set(
        f"email_verified:{email}",
        "true",
        ex=600,
    )

    return True


# =========================================================
# SEND OTP EMAIL
# =========================================================

async def send_otp_email(
    email: str,
    otp: str,
):
    """
    Send OTP to user's email.
    """

    smtp = SMTP(
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
    )

    await smtp.connect()

    await smtp.login(
        SMTP_USERNAME,
        SMTP_PASSWORD,
    )

    message = f"""\
From: {SMTP_USERNAME}
To: {email}
Subject: Email Verification OTP

Your email verification OTP is: {otp}

This OTP will expire in 5 minutes.

If you did not request this OTP, please ignore this email.
"""

    await smtp.sendmail(
        SMTP_USERNAME,
        email,
        message,
    )

    await smtp.quit()