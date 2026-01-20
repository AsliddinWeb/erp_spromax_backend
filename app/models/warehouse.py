from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User  # BU QATORNI QO'SHING


class Supplier(BaseModel):
    """Yetkazib beruvchilar jadvali"""
    __tablename__ = "suppliers"
    
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    inn = Column(String(9), nullable=True)  # STIR
    
    # Relationships
    warehouse_receipts = relationship("WarehouseReceipt", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier {self.name}>"


class RawMaterial(BaseModel):
    """Xom-ashyo katalogi jadvali"""
    __tablename__ = "raw_materials"
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=False)  # kg, metr, dona, etc.
    minimum_stock = Column(Numeric(10, 2), nullable=False, default=0)  # Minimal qoldiq
    
    # Relationships
    warehouse_receipts = relationship("WarehouseReceipt", back_populates="raw_material")
    warehouse_stock = relationship("WarehouseStock", back_populates="raw_material", uselist=False)
    material_requests = relationship("MaterialRequest", back_populates="raw_material")
    
    def __repr__(self):
        return f"<RawMaterial {self.name}>"


class WarehouseReceipt(BaseModel):
    """Qabul qilish jadvali (Xom-ashyo kirim)"""
    __tablename__ = "warehouse_receipts"
    
    supplier_id = Column(UUID(as_uuid=True), ForeignKey('suppliers.id'), nullable=False)
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    batch_number = Column(String(50), nullable=False, unique=True)
    receipt_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="warehouse_receipts")
    raw_material = relationship("RawMaterial", back_populates="warehouse_receipts")
    
    def __repr__(self):
        return f"<WarehouseReceipt {self.batch_number}>"


class WarehouseStock(BaseModel):
    """Ombor qoldiqlari jadvali"""
    __tablename__ = "warehouse_stock"
    
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=False, unique=True)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    last_updated = Column(DateTime, nullable=False)
    
    # Relationships
    raw_material = relationship("RawMaterial", back_populates="warehouse_stock")
    
    def __repr__(self):
        return f"<WarehouseStock {self.raw_material.name if self.raw_material else 'N/A'}: {self.quantity}>"


class MaterialRequest(BaseModel):
    """Xom-ashyo so'rovlari jadvali (Ishlab chiqarishdan)"""
    __tablename__ = "material_requests"
    
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=False)
    requested_quantity = Column(Numeric(10, 2), nullable=False)
    approved_quantity = Column(Numeric(10, 2), nullable=True)
    request_status = Column(String(20), nullable=False, default='pending')  # pending, approved, rejected, partially_approved
    requested_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    request_date = Column(DateTime, nullable=False)
    approval_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    raw_material = relationship("RawMaterial", back_populates="material_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<MaterialRequest {self.id}: {self.request_status}>"