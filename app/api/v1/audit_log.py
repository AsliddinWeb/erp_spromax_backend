from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_log_service import AuditLogService
from app.core.exceptions import ForbiddenException

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.get("/")
def get_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Audit loglarni ko'rish (faqat superadmin)"""
    auth_service = AuthService(db)
    current_user = auth_service.get_current_user(token)
    if current_user.role.name not in ("superadmin", "admin"):
        raise ForbiddenException("Bu sahifani ko'rishga ruxsat yo'q")

    logs = AuditLogService(db).get_logs(skip=skip, limit=limit)
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": log.username,
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
