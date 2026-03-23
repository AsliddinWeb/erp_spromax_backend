from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        method: str,
        path: str,
        status_code: str = None,
        user_id: str = None,
        username: str = None,
        request_body: str = None,
        ip_address: str = None,
    ) -> AuditLog:
        log = AuditLog(
            method=method,
            path=path,
            status_code=status_code,
            user_id=user_id,
            username=username,
            request_body=request_body,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_logs(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
