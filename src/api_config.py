from fastapi.routing import APIRouter
from src.user.views import router as user_router
from src.auth.views import router as auth_router
from src.super_admin.views import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(user_router, prefix="/user", tags=["User"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
