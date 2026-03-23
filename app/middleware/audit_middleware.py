import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.security import decode_token
from app.database import SessionLocal
from app.services.audit_log_service import AuditLogService

LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method not in LOGGED_METHODS:
            return response

        path = request.url.path
        if any(path.startswith(skip) for skip in SKIP_PATHS):
            return response

        user_id = None
        username = None
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub")
                    username = payload.get("username")
        except Exception:
            pass

        body_text = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                parsed = json.loads(body_bytes)
                # Remove sensitive fields
                parsed.pop("password", None)
                parsed.pop("old_password", None)
                parsed.pop("new_password", None)
                body_text = json.dumps(parsed, ensure_ascii=False)[:2000]
        except Exception:
            pass

        ip = request.client.host if request.client else None

        try:
            db = SessionLocal()
            try:
                AuditLogService(db).create(
                    method=request.method,
                    path=path,
                    status_code=str(response.status_code),
                    user_id=user_id,
                    username=username,
                    request_body=body_text,
                    ip_address=ip,
                )
            finally:
                db.close()
        except Exception:
            pass

        return response
