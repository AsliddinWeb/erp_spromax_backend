import json
import uuid
import threading
from starlette.types import ASGIApp, Receive, Scope, Send
from app.core.security import decode_token
from app.database import SessionLocal
from app.services.audit_log_service import AuditLogService

LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}


def _save_log(method, path, status_code, user_id, username, ip):
    print(f"_save_log called: {method} {path} status={status_code} user={username}", flush=True)
    try:
        db = SessionLocal()
        try:
            AuditLogService(db).create(
                method=method,
                path=path,
                status_code=str(status_code),
                user_id=user_id,
                username=username,
                request_body=None,
                ip_address=ip,
            )
        finally:
            db.close()
    except Exception as e:
        print(f"AUDIT LOG ERROR: {type(e).__name__}: {e}", flush=True)


class AuditMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        should_log = (
            method in LOGGED_METHODS
            and not any(path.startswith(s) for s in SKIP_PATHS)
        )

        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper if should_log else send)

        if not should_log:
            return

        # Token dan user ma'lumotlarini olish
        user_id = None
        username = None
        try:
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")
            if auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1]
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

        # IP manzil
        ip = None
        try:
            client = scope.get("client")
            ip = client[0] if client else None
        except Exception:
            pass

        print(f"AUDIT THREAD START: {method} {path}", flush=True)
        # Alohida threadda saqlaymiz (response allaqachon yuborilgan)
        t = threading.Thread(
            target=_save_log,
            args=(method, path, status_code, user_id, username, ip),
            daemon=True,
        )
        t.start()
