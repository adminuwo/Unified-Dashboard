import os
# Auto-reloaded for updated Revenue & KPI Overview endpoints

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.responses import RedirectResponse, JSONResponse  # type: ignore

from src.config.settings import settings
from src.database.connection import init_db, get_db, check_db_connection

from src.applications.router import router as applications_router
from src.modules.auth.router import router as auth_router
from src.verification.router import router as verification_router
from src.payment.router import router as payment_router
from src.logs.router import router as logs_router
from src.admin.router import router as admin_router
from src.telemetry.router import router as telemetry_router
from src.analytics.router import router as analytics_router
from src.unified_analytics.router import router as unified_analytics_router
from src.modules.revenue.router import router as revenue_router, public_revenue_router
from src.unified_analytics.scheduler import (
    start_unified_analytics_scheduler,
    shutdown_unified_analytics_scheduler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    is_test = settings.ENVIRONMENT.lower() == "testing" or os.environ.get("ENVIRONMENT", "").lower() == "testing"
    if not is_test:
        init_db()
        try:
            start_unified_analytics_scheduler()
        except Exception as e:
            print(f"[lifespan] Note: Unified analytics scheduler initialization: {e}")
    yield
    if not is_test:
        try:
            shutdown_unified_analytics_scheduler()
        except Exception:
            pass


# Disable Swagger UI & OpenAPI schema in production environment for security hardening
is_prod = settings.ENVIRONMENT.lower() == "production"

app = FastAPI(
    title="Unified Service Backend",
    description="Centralized Shared Infrastructure Authorization & Identity Backend Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json"
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure all unexpected errors return a structured JSON response."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )


# Enable Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Explicitly whitelisted platform origins including aimall24.com
DEFAULT_CORS_ORIGINS = [
    "https://aimall24.com",
    "https://www.aimall24.com",
    "http://aimall24.com",
    "http://www.aimall24.com",
    "https://aisa24.com",
    "https://beta.aisa24.com",
    "https://www.aisa24.com",
    "http://aisa24.com",
    "https://uwo24.com",
    "https://admin.uwo24.com",
    "https://yugamc.com",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

configured_origins = settings.cors_origins
if configured_origins != ["*"]:
    for o in configured_origins:
        if o not in DEFAULT_CORS_ORIGINS:
            DEFAULT_CORS_ORIGINS.append(o)

# Enable CORS Middleware with configurable origins & regex for all platform domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_CORS_ORIGINS,
    allow_origin_regex=r"https?://(.*\.)?(uwo24\.com|aisa24\.com|aimall24\.com|yugamc\.com|localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api prefix
app.include_router(applications_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(analytics_router)
app.include_router(unified_analytics_router, prefix="/api")
app.include_router(revenue_router, prefix="/api")
app.include_router(public_revenue_router, prefix="/api")


from fastapi.responses import RedirectResponse, JSONResponse, FileResponse  # type: ignore

# Mount frontend static assets and SPA fallback
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
frontend_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(frontend_dist_dir):
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/app/assets", StaticFiles(directory=assets_dir), name="app_assets")
        app.mount("/assets", StaticFiles(directory=assets_dir), name="dist_assets")
    app.mount("/app", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend_dist")
else:
    app.mount("/app", StaticFiles(directory=frontend_src_dir, html=True), name="frontend_src")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to the Web Dashboard."""
    return RedirectResponse(url="/app/")


@app.get("/app/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str = ""):
    """Serve Single Page Application (SPA) index.html for dashboard routes."""
    if os.path.exists(frontend_dist_dir):
        if full_path:
            clean_path = os.path.normpath(os.path.join(frontend_dist_dir, full_path.lstrip("/")))
            if os.path.exists(clean_path) and os.path.isfile(clean_path):
                return FileResponse(clean_path)
        index_path = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return RedirectResponse(url="/app/")





@app.get("/api/health", tags=["Health Check"])
def health_check(db=Depends(get_db)):
    """Health check endpoint verifying backend and database connectivity."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": check_db_connection(db)
    }
