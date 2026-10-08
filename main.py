from fastapi import FastAPI

from src.routes.users import router as user_router
from src.routes.admin import router as admin_router
from src.routes.auth import router as auth_router


app = FastAPI(
    title="Student Management System"
)


app.include_router(user_router)
app.include_router(admin_router)
app.include_router(auth_router)