import json
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.security import decode_token
from app.database import SessionLocal
from app.services.audit_log_service import AuditLogService

LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"AUDIT DISPATCH: {request.method} {request.url.path}", flush=True)
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
                    raw_id = payload.get("sub")
                    try:
                        user_id = uuid.UUID(str(raw_id)) if raw_id else None
                    except Exception:
                        user_id = None
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
                log = AuditLogService(db).create(
                    method=request.method,
                    path=path,
                    status_code=str(response.status_code),
                    user_id=user_id,
                    username=username,
                    request_body=body_text,
                    ip_address=ip,
                )
                print(f"AUDIT SAVED: {request.method} {path} user={username} id={log.id}", flush=True)
            finally:
                db.close()
        except Exception as e:
            print(f"AUDIT LOG ERROR: {type(e).__name__}: {e}", flush=True)

        return response
