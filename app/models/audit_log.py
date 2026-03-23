import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.utils.datetime_utils import get_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(150), nullable=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(String(5), nullable=True)
    request_body = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=get_now, nullable=False, index=True)
