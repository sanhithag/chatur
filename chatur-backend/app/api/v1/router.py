from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.content_admin import router as content_admin_router
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.parents import router as parents_router
from app.api.v1.search import router as search_router
from app.api.v1.students import router as students_router
from app.api.v1.teachers import router as teachers_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(students_router, prefix="/students", tags=["Students"])
api_router.include_router(teachers_router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(parents_router, prefix="/parents", tags=["Parents"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(curriculum_router, prefix="/curriculum", tags=["Curriculum"])
api_router.include_router(content_admin_router, prefix="/admin/content", tags=["Admin Content"])
