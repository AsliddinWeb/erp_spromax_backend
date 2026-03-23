import uuid
import threading
from starlette.types import ASGIApp, Receive, Scope, Send
from app.core.security import decode_token
from app.database import SessionLocal
from app.services.audit_log_service import AuditLogService

LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS_EXACT = {"/health", "/", "/openapi.json"}
SKIP_PATHS_PREFIX = {"/docs", "/redoc"}


def _save_log(method, path, status_code, user_id, username, ip):
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
            print(f"AUDIT OK: {method} {path} {status_code} user={username}", flush=True)
        finally:
            db.close()
    except Exception as e:
        print(f"AUDIT ERROR: {type(e).__name__}: {e}", flush=True)


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
            and path not in SKIP_PATHS_EXACT
            and not any(path.startswith(s) for s in SKIP_PATHS_PREFIX)
        )

        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        exc_to_raise = None
        try:
            await self.app(scope, receive, send_wrapper if should_log else send)
        except BaseException as e:
            exc_to_raise = e

        if should_log:
            print(f"AUDIT CHECK: method={method} path={path} status={status_code} should_log={should_log}", flush=True)
            if status_code:
                user_id = None
                username = None
                ip = None
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
                    client = scope.get("client")
                    ip = client[0] if client else None
                except Exception:
                    pass

                threading.Thread(
                    target=_save_log,
                    args=(method, path, status_code, user_id, username, ip),
                    daemon=True,
                ).start()

        if exc_to_raise is not None:
            raise exc_to_raise
