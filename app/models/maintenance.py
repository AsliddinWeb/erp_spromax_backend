from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Date, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User
from app.models.production import Machine


class MaintenanceRequest(BaseModel):
    """Texnik xizmat so'rovlari jadvali"""
    __tablename__ = "maintenance_requests"
    
    machine_id = Column(UUID(as_uuid=True), ForeignKey('machines.id'), nullable=False)
    request_type = Column(String(50), nullable=False)  # repair, maintenance, inspection
    priority = Column(String(20), nullable=False, default='medium')  # low, medium, high, urgent
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, in_progress, completed, cancelled
    
    # Dates
    requested_date = Column(DateTime, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Foreign Keys
    requested_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    machine = relationship("Machine", back_populates="maintenance_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    technician = relationship("User", foreign_keys=[assigned_to])
    maintenance_logs = relationship("MaintenanceLog", back_populates="request")
    spare_parts_used = relationship("SparePartUsage", back_populates="request")
    
    def __repr__(self):
        return f"<MaintenanceRequest {self.id} - {self.machine_id}>"


class MaintenanceLog(BaseModel):
    """Texnik xizmat jurnali jadvali"""
    __tablename__ = "maintenance_logs"
    
    request_id = Column(UUID(as_uuid=True), ForeignKey('maintenance_requests.id'), nullable=False)
    log_date = Column(DateTime, nullable=False)
    work_description = Column(Text, nullable=False)
    hours_spent = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign Keys
    performed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    request = relationship("MaintenanceRequest", back_populates="maintenance_logs")
    performer = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<MaintenanceLog {self.id}>"


class SparePart(BaseModel):
    """Ehtiyot qismlar jadvali"""
    __tablename__ = "spare_parts"
    
    name = Column(String(200), nullable=False)
    part_number = Column(String(100), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=True)
    quantity_in_stock = Column(Numeric(10, 2), nullable=False, default=0)
    min_stock_level = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Relationships
    usage_records = relationship("SparePartUsage", back_populates="spare_part")
    
    def __repr__(self):
        return f"<SparePart {self.name}>"


class SparePartUsage(BaseModel):
    """Ehtiyot qismlar ishlatish jadvali"""
    __tablename__ = "spare_part_usage"
    
    request_id = Column(UUID(as_uuid=True), ForeignKey('maintenance_requests.id'), nullable=False)
    spare_part_id = Column(UUID(as_uuid=True), ForeignKey('spare_parts.id'), nullable=False)
    quantity_used = Column(Numeric(10, 2), nullable=False)
    usage_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    request = relationship("MaintenanceRequest", back_populates="spare_parts_used")
    spare_part = relationship("SparePart", back_populates="usage_records")
    
    def __repr__(self):
        return f"<SparePartUsage {self.id}>"


class MaintenanceSchedule(BaseModel):
    """Rejali texnik xizmat jadvali"""
    __tablename__ = "maintenance_schedules"
    
    machine_id = Column(UUID(as_uuid=True), ForeignKey('machines.id'), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    description = Column(Text, nullable=False)
    interval_days = Column(Integer, nullable=False)  # Har necha kunda
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    # is_active = Column(String(20), nullable=False, default='active')  # active, inactive
    
    # Relationships
    machine = relationship("Machine")
    
    def __repr__(self):
        return f"<MaintenanceSchedule {self.machine_id}>"