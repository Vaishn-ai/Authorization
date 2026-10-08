from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.auth import get_current_user
from src.configs.database import get_db

from src.modules.user.functions import (
    create_student,
    get_students,
    update_student,
)

from src.modules.user.interface import (
    StudentCreate,
    StudentResponse,
)


router = APIRouter()


# ==========================================
# CREATE STUDENT
# ==========================================

@router.post(
    "/students",
    response_model=StudentResponse
)
async def register_student(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    age: int = Form(...),
    ph_no: str = Form(...),

    profile_image: UploadFile = File(...),

    db: AsyncSession = Depends(get_db)
):
    student_data = StudentCreate(
        name=name,
        email=email,
        password=password,
        age=age,
        ph_no=ph_no
    )

    return await create_student(
        db=db,
        name=student_data.name,
        email=student_data.email,
        password=student_data.password,
        age=student_data.age,
        ph_no=student_data.ph_no,
        profile_image=profile_image
    )


# ==========================================
# GET STUDENTS
# ==========================================

@router.get(
    "/students",
    response_model=list[StudentResponse]
)
async def get_all_students(
    db: AsyncSession = Depends(get_db)
):
    return await get_students(db)


# ==========================================
# UPDATE STUDENT
# ==========================================

@router.put(
    "/students/{student_id}",
    response_model=StudentResponse
)
async def update_student_details(
    student_id: int,

    name: str | None = Form(default=None),
    email: str | None = Form(default=None),
    password: str | None = Form(default=None),
    age: int | None = Form(default=None),
    ph_no: str | None = Form(default=None),

    profile_image: UploadFile | None = File(default=None),

    current_user: dict = Depends(
        get_current_user
    ),

    db: AsyncSession = Depends(get_db)
):
    return await update_student(
        db=db,
        student_id=student_id,
        current_user_id=current_user["user_id"],
        current_user_role=current_user["role"],
        name=name,
        email=email,
        password=password,
        age=age,
        ph_no=ph_no,
        profile_image=profile_image
    )