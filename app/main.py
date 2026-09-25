from fastapi import FastAPI

from app.api.v1.routes.auth import router as auth_router

app = FastAPI(
    title="OrderFlow API",
    description="Distributed Order Processing Backend",
    version="1.0.0",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "orderflow",
    }