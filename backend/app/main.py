from fastapi import FastAPI

app = FastAPI(
    title="GlobalSearch API",
    description="Worldwide AI-powered Job Discovery and Application Platform",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {
        "project": "GlobalSearch",
        "message": "GlobalSearch API is running",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "GlobalSearch Backend"
    }