import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal, seed_reference_data
import backend.app.models  # ensure models are registered
from backend.app.routes import (
    auth, items, borrow, loans, payments,
    notifications, reviews, disputes, admin, upload
)

# Ensure database tables and reference data exist
try:
    Base.metadata.create_all(bind=engine)
    init_session = SessionLocal()
    try:
        seed_reference_data(init_session)
    finally:
        init_session.close()
except Exception as exc:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BorrowHub – Complete Full-Stack Campus Resource Sharing Platform for SVNIT Surat",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS (including allow_private_network for direct local file testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

# Prevent browser from caching static assets during development
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/uploads"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Static files for uploaded images
static_uploads = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(static_uploads, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=static_uploads), name="uploads")

# Mount API routers
app.include_router(auth.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(borrow.router, prefix="/api")
app.include_router(loans.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(disputes.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(upload.router, prefix="/api")


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }


# Mount frontend static directory if present
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
