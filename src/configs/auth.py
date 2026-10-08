
from fastapi import Cookie, HTTPException
from jose import jwt, JWTError

from .security import (
    SECRET_KEY,
    ALGORITHM,
)


async def get_current_user(
    access_token: str | None = Cookie(default=None)
):

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Access token missing"
        )

    try:

        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")

        if not user_id or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        if token_type != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid access token"
            )

        return {
            "user_id": int(user_id),
            "role": role
        }

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token"
        )