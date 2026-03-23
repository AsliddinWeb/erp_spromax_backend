import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api.v1 import auth, users, warehouse, production, sales, finance, hr, maintenance, analytics, notifications
from app.api.v1 import system_settings, audit_log, export
from app.core.rate_limit import limiter
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.middleware.audit_middleware import AuditMiddleware
from app.utils.datetime_utils import set_timezone

# Sentry — faqat SENTRY_DSN .env da bo'lsa ishga tushadi
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.2,   # 20% so'rovlarni performance trace
        send_default_pii=False,   # foydalanuvchi ma'lumotlarini yubormaslik
        environment="production" if not settings.DEBUG else "development",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: DB dan timezone ni o'qib qo'llash"""
    # Default timezone ni config dan o'rnatish
    set_timezone(settings.TIMEZONE)

    # DB dan override qilish (agar system_settings jadval mavjud bo'lsa)
    try:
        from app.database import SessionLocal
        from app.services.system_settings_service import SystemSettingsService
        db = SessionLocal()
        try:
            service = SystemSettingsService(db)
            service.initialize_defaults()
            tz = service.load_timezone_from_db()
        finally:
            db.close()
    except Exception:
        pass  # Jadval hali yaratilmagan bo'lishi mumkin

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Audit middleware
app.add_middleware(AuditMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(warehouse.router, prefix=settings.API_V1_PREFIX)
app.include_router(production.router, prefix=settings.API_V1_PREFIX)
app.include_router(sales.router, prefix=settings.API_V1_PREFIX)
app.include_router(finance.router, prefix=settings.API_V1_PREFIX)
app.include_router(hr.router, prefix=settings.API_V1_PREFIX)
app.include_router(maintenance.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(system_settings.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_log.router, prefix=settings.API_V1_PREFIX)
app.include_router(export.router, prefix=settings.API_V1_PREFIX)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        routes=app.routes,
    )

    # Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Barcha endpointlarga BearerAuth qo'shish
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    return {
        "message": "S PROMAX PLAST ERP API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }