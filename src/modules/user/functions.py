import os
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.user.models import Student
from src.configs.security import hash_password
from src.configs.redis import redis_client


# ==========================================
# PROFILE IMAGE CONFIGURATION
# ==========================================

UPLOAD_DIR = "uploads/profile_images"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


# ==========================================
# IMAGE VALIDATION
# ==========================================

async def validate_profile_image(
    profile_image: UploadFile
):
    if profile_image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG and WEBP images are allowed"
        )

    image_data = await profile_image.read()

    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Profile image must be less than 5 MB"
        )

    await profile_image.seek(0)


# ==========================================
# STUDENT UNIQUE DATA VALIDATION
# ==========================================

async def validate_student_unique_data(
    db: AsyncSession,
    email: str,
    ph_no: str,
    student_id: int | None = None
):
    # Check email
    email_result = await db.execute(
        select(Student).where(
            Student.email == email
        )
    )

    existing_email = email_result.scalar_one_or_none()

    if (
        existing_email
        and existing_email.id != student_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    # Check phone number
    phone_result = await db.execute(
        select(Student).where(
            Student.ph_no == ph_no
        )
    )

    existing_phone = phone_result.scalar_one_or_none()

    if (
        existing_phone
        and existing_phone.id != student_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Phone number already exists"
        )


# ==========================================
# CREATE STUDENT
# ==========================================

async def create_student(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
    age: int,
    ph_no: str,
    profile_image: UploadFile
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
    # CHECK DUPLICATE EMAIL AND PHONE
    # ======================================

    await validate_student_unique_data(
        db=db,
        email=email,
        ph_no=ph_no
    )

    # ======================================
    # VALIDATE IMAGE
    # ======================================

    await validate_profile_image(
        profile_image
    )

    # ======================================
    # HASH PASSWORD
    # ======================================

    hashed_password = hash_password(
        password
    )

    # ======================================
    # GET IMAGE EXTENSION
    # ======================================

    file_extension = os.path.splitext(
        profile_image.filename
    )[1].lower()

    # ======================================
    # GENERATE UNIQUE FILE NAME
    # ======================================

    file_name = (
        f"{uuid.uuid4()}{file_extension}"
    )

    # ======================================
    # COMPLETE FILE PATH
    # ======================================

    file_path = os.path.join(
        UPLOAD_DIR,
        file_name
    )

    # ======================================
    # SAVE IMAGE
    # ======================================

    with open(
        file_path,
        "wb"
    ) as image_file:

        image_file.write(
            await profile_image.read()
        )

    # ======================================
    # CREATE STUDENT
    # ======================================

    student = Student(
        name=name,
        email=email,
        password=hashed_password,
        age=age,
        ph_no=ph_no,
        profile_image=file_path
    )

    db.add(student)

    await db.commit()

    await db.refresh(student)

    # ======================================
    # DELETE VERIFICATION FLAG
    # ======================================

    await redis_client.delete(
        verification_key
    )

    return student


# ==========================================
# GET ALL STUDENTS
# ==========================================

async def get_students(
    db: AsyncSession
):
    result = await db.execute(
        select(Student)
    )

    return result.scalars().all()


# ==========================================
# UPDATE STUDENT
# ==========================================

async def update_student(
    db: AsyncSession,
    student_id: int,
    current_user_id: int,
    current_user_role: str,
    name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    age: int | None = None,
    ph_no: str | None = None,
    profile_image: UploadFile | None = None
):

    # ======================================
    # AUTHORIZATION
    # ======================================

    if current_user_role == "student":

        if student_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="You can update only your own details"
            )

    elif current_user_role != "admin":

        raise HTTPException(
            status_code=403,
            detail="You do not have permission"
        )

    # ======================================
    # FIND STUDENT
    # ======================================

    result = await db.execute(
        select(Student).where(
            Student.id == student_id
        )
    )

    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    # ======================================
    # CHECK DUPLICATE EMAIL
    # ======================================

    if email is not None:

        email_result = await db.execute(
            select(Student).where(
                Student.email == email,
                Student.id != student_id
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

        student.email = email

    # ======================================
    # CHECK DUPLICATE PHONE
    # ======================================

    if ph_no is not None:

        phone_result = await db.execute(
            select(Student).where(
                Student.ph_no == ph_no,
                Student.id != student_id
            )
        )

        existing_phone = (
            phone_result.scalar_one_or_none()
        )

        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail="Phone number already exists"
            )

        student.ph_no = ph_no

    # ======================================
    # UPDATE NAME
    # ======================================

    if name is not None:
        student.name = name

    # ======================================
    # UPDATE PASSWORD
    # ======================================

    if password is not None:

        student.password = hash_password(
            password
        )

    # ======================================
    # UPDATE AGE
    # ======================================

    if age is not None:
        student.age = age

    # ======================================
    # UPDATE PROFILE IMAGE
    # ======================================

    if profile_image is not None:

        await validate_profile_image(
            profile_image
        )

        file_extension = os.path.splitext(
            profile_image.filename
        )[1].lower()

        file_name = (
            f"{uuid.uuid4()}{file_extension}"
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            file_name
        )

        with open(
            file_path,
            "wb"
        ) as image_file:

            image_file.write(
                await profile_image.read()
            )

        student.profile_image = file_path

    # ======================================
    # SAVE CHANGES
    # ======================================

    await db.commit()

    await db.refresh(student)

    return student