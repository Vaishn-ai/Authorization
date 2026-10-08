import re

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


# ==========================================
# CREATE STUDENT
# ==========================================

class StudentCreate(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )

    age: int = Field(
        ...,
        ge=5,
        le=100
    )

    ph_no: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):

        value = value.strip()

        if not re.fullmatch(
            r"[A-Za-z ]+",
            value
        ):
            raise ValueError(
                "Name can contain only letters and spaces"
            )

        return value

    @field_validator("ph_no")
    @classmethod
    def validate_phone(cls, value: str):

        value = value.strip()

        if not re.fullmatch(
            r"\+?[0-9]{10,15}",
            value
        ):
            raise ValueError(
                "Invalid phone number"
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):

        if not re.search(
            r"[A-Z]",
            value
        ):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not re.search(
            r"[a-z]",
            value
        ):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        if not re.search(
            r"[0-9]",
            value
        ):
            raise ValueError(
                "Password must contain at least one number"
            )

        if not re.search(
            r"[@$!%*?&]",
            value
        ):
            raise ValueError(
                "Password must contain at least one special character"
            )

        return value


# ==========================================
# STUDENT RESPONSE
# ==========================================

class StudentResponse(BaseModel):

    id: int
    name: str
    email: EmailStr
    age: int
    ph_no: str
    profile_image: str | None = None

    model_config = {
        "from_attributes": True
    }