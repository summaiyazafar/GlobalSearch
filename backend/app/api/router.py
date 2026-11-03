from fastapi import APIRouter

from app.core.config import settings

from app.api.routes.auth import router as auth_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.profile_data import router as profile_data_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router


api_router = APIRouter(
    prefix=settings.API_PREFIX,
)

api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(profile_data_router)
api_router.include_router(preferences_router)
api_router.include_router(jobs_router)
api_router.include_router(resumes_router)