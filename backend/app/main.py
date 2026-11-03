import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import GlobalSearchError
from app.core.logging import configure_logging
from app.core.security import generate_request_id
from app.database.connection import initialize_database


configure_logging()

logger = logging.getLogger("globalsearch.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GlobalSearch API")

    if settings.APP_ENV.lower() == "development":
        initialize_database()
        logger.info("Development database initialized")

    yield

    logger.info("Shutting down GlobalSearch API")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)


@app.middleware("http")
async def request_tracking(request: Request, call_next):
    request_id = (
        request.headers.get("X-Request-ID")
        or generate_request_id()
    )

    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        logger.exception(
            "Unhandled request error | request_id=%s",
            request_id,
        )
        raise

    duration = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "%s %s | status=%s | duration=%.4fs | request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration,
        request_id,
    )

    return response


@app.exception_handler(GlobalSearchError)
async def global_search_exception_handler(
    request: Request,
    exc: GlobalSearchError,
):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
            "request_id": getattr(
                request.state,
                "request_id",
                None,
            ),
        },
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "message": "GlobalSearch API is running",
        "status": "active",
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "GlobalSearch Backend",
        "version": settings.VERSION,
    }


@app.get("/api/v1/health", tags=["System"])
async def api_health_check():
    return {
        "status": "healthy",
        "api_version": "v1",
    }


# Register API routes
app.include_router(api_router)