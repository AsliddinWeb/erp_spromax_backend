from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.datetime_utils import get_now
import uuid


class SystemSettings(Base):
    """Tizim sozlamalari jadvali — superadmin boshqaradi"""
    __tablename__ = "system_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now, nullable=False)

    # Relationships
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<SystemSettings {self.key}={self.value}>"
