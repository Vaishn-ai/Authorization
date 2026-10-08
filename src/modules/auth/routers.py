from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Form,
    HTTPException,
    Response,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.database import get_db

from src.modules.auth.functions import (
    login_user,
    refresh_access_token,
    create_email_otp,
    verify_email_otp,
    send_otp_email,
)


router = APIRouter()


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    tokens = await login_user(
        db=db,
        email=email,
        password=password,
    )

    if not tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return {
        "message": "Login successful",
    }


# =========================================================
# REFRESH ACCESS TOKEN
# =========================================================

@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None
    ),
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing",
        )

    new_access_token = refresh_access_token(
        refresh_token
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 60,
    )

    return {
        "message": "Access token refreshed successfully",
    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
async def logout(
    response: Response,
):
    response.delete_cookie(
        key="access_token"
    )

    response.delete_cookie(
        key="refresh_token"
    )

    return {
        "message": "Logout successful",
    }


# =========================================================
# SEND EMAIL OTP
# =========================================================

@router.post("/send-otp")
async def send_otp(
    email: str = Form(...),
):
    otp = await create_email_otp(
        email=email
    )

    await send_otp_email(
        email=email,
        otp=otp,
    )

    return {
        "message": "OTP sent successfully",
    }


# =========================================================
# VERIFY EMAIL OTP
# =========================================================

@router.post("/verify-otp")
async def verify_otp(
    email: str = Form(...),
    otp: str = Form(...),
):
    await verify_email_otp(
        email=email,
        otp=otp,
    )

    return {
        "message": "Email verified successfully",
    }