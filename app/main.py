from fastapi import FastAPI

from app.api.v1.routes.auth import router as auth_router

from app.api.v1.routes.admin import router as admin_router

from app.api.v1.routes.products import router as products_router

from app.api.v1.routes.inventory import router as inventory_router

app = FastAPI(
    title="OrderFlow API",
    description="Distributed Order Processing Backend",
    version="1.0.0",
)

app.include_router(
    inventory_router,
    prefix="/api/v1",
)

app.include_router(
    products_router,
    prefix="/api/v1",
)

app.include_router(
    admin_router,
    prefix="/api/v1",
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