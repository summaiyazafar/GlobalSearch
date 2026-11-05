
from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.profile_data import router as profile_data_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.ai import router as ai_router
from app.api.routes.applications import router as applications_router
from app.api.routes.job_sources import router as job_sources_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.matching import router as matching_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(profile_data_router)
api_router.include_router(preferences_router)
api_router.include_router(jobs_router)
api_router.include_router(resumes_router)
api_router.include_router(ai_router)
api_router.include_router(applications_router)
api_router.include_router(job_sources_router)
api_router.include_router(discovery_router)
api_router.include_router(matching_router)
