from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User
from app.models.warehouse import RawMaterial


class ProductionLine(BaseModel):
    """Ishlab chiqarish liniyalari jadvali"""
    __tablename__ = "production_lines"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    capacity_per_hour = Column(Numeric(10, 2), nullable=True)

    # Relationships
    machines = relationship("Machine", back_populates="production_line")
    shifts = relationship("Shift", back_populates="production_line")

    def __repr__(self):
        return f"<ProductionLine {self.name}>"


class Machine(BaseModel):
    """Stanoklar (uskunalar) jadvali"""
    __tablename__ = "machines"

    name = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=True, unique=True)
    production_line_id = Column(UUID(as_uuid=True), ForeignKey('production_lines.id'), nullable=False)
    status = Column(String(20), nullable=False, default='active')

    # Relationships
    production_line = relationship("ProductionLine", back_populates="machines")
    shift_machines = relationship("ShiftMachine", back_populates="machine")
    # Bu relationship'ni `app.models.maintenance` modulida yaratamiz
    maintenance_requests = relationship("MaintenanceRequest", back_populates="machine", lazy="dynamic")

    def __repr__(self):
        return f"<Machine {self.name}>"


class FinishedProduct(BaseModel):
    """Tayyor mahsulotlar katalogi jadvali"""
    __tablename__ = "finished_products"

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=False)
    standard_price = Column(Numeric(10, 2), nullable=True)

    # Relationships
    production_outputs = relationship("ProductionOutput", back_populates="finished_product")
    finished_product_stock = relationship("FinishedProductStock", back_populates="finished_product", uselist=False)

    def __repr__(self):
        return f"<FinishedProduct {self.name}>"


class Shift(BaseModel):
    """Smenalar jadvali"""
    __tablename__ = "shifts"

    production_line_id = Column(UUID(as_uuid=True), ForeignKey('production_lines.id'), nullable=False)
    operator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='active')
    notes = Column(Text, nullable=True)

    # Relationships
    production_line = relationship("ProductionLine", back_populates="shifts")
    operator = relationship("User", foreign_keys=[operator_id])
    shift_machines = relationship("ShiftMachine", back_populates="shift", cascade="all, delete-orphan")
    production_records = relationship("ProductionRecord", back_populates="shift", cascade="all, delete-orphan")
    production_outputs = relationship("ProductionOutput", back_populates="shift", cascade="all, delete-orphan")
    defective_products = relationship("DefectiveProduct", back_populates="shift", cascade="all, delete-orphan")
    shift_handover = relationship("ShiftHandover", back_populates="shift", uselist=False, cascade="all, delete-orphan")
    pauses = relationship("ShiftPause", back_populates="shift", cascade="all, delete-orphan")
    scrap_usages = relationship("ShiftScrapUsage", back_populates="shift", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shift {self.id}: {self.status}>"


class ShiftMachine(BaseModel):
    """Smena-stanok mapping jadvali"""
    __tablename__ = "shift_machines"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    machine_id = Column(UUID(as_uuid=True), ForeignKey('machines.id'), nullable=False)

    # Relationships
    shift = relationship("Shift", back_populates="shift_machines")
    machine = relationship("Machine", back_populates="shift_machines")

    def __repr__(self):
        return f"<ShiftMachine shift:{self.shift_id} machine:{self.machine_id}>"


class ProductionRecord(BaseModel):
    """Xom-ashyo ishlatish yozuvlari jadvali"""
    __tablename__ = "production_records"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=False)
    quantity_used = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    shift = relationship("Shift", back_populates="production_records")
    raw_material = relationship("RawMaterial")

    def __repr__(self):
        return f"<ProductionRecord {self.id}>"


class ProductionOutput(BaseModel):
    """Ishlab chiqarilgan mahsulotlar jadvali"""
    __tablename__ = "production_outputs"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=False)
    quantity_produced = Column(Numeric(10, 2), nullable=False)
    produced_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    shift = relationship("Shift", back_populates="production_outputs")
    finished_product = relationship("FinishedProduct", back_populates="production_outputs")

    def __repr__(self):
        return f"<ProductionOutput {self.id}>"


class DefectReason(BaseModel):
    """Brak sabablari katalogi jadvali"""
    __tablename__ = "defect_reasons"

    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    defective_products = relationship("DefectiveProduct", back_populates="defect_reason")

    def __repr__(self):
        return f"<DefectReason {self.name}>"


class DefectiveProduct(BaseModel):
    """Yaroqsiz (brak) mahsulotlar jadvali"""
    __tablename__ = "defective_products"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=False)
    defect_reason_id = Column(UUID(as_uuid=True), ForeignKey('defect_reasons.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    shift = relationship("Shift", back_populates="defective_products")
    finished_product = relationship("FinishedProduct")
    defect_reason = relationship("DefectReason", back_populates="defective_products")

    def __repr__(self):
        return f"<DefectiveProduct {self.id}>"


class ShiftHandover(BaseModel):
    """Smena topshirish jadvali"""
    __tablename__ = "shift_handovers"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False, unique=True)
    handover_notes = Column(Text, nullable=True)
    equipment_status = Column(Text, nullable=True)
    pending_issues = Column(Text, nullable=True)
    next_shift_instructions = Column(Text, nullable=True)
    handover_time = Column(DateTime, nullable=False)

    # Relationships
    shift = relationship("Shift", back_populates="shift_handover")

    def __repr__(self):
        return f"<ShiftHandover {self.id}>"


class FinishedProductStock(BaseModel):
    """Tayyor mahsulot ombori jadvali"""
    __tablename__ = "finished_product_stock"

    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=False, unique=True)
    quantity_total = Column(Numeric(10, 2), nullable=False, default=0)
    quantity_available = Column(Numeric(10, 2), nullable=False, default=0)
    quantity_reserved = Column(Numeric(10, 2), nullable=False, default=0)
    last_updated = Column(DateTime, nullable=False)

    # Relationships
    finished_product = relationship("FinishedProduct", back_populates="finished_product_stock")

    def __repr__(self):
        return f"<FinishedProductStock {self.finished_product.name if self.finished_product else 'N/A'}>"


class ShiftPause(BaseModel):
    """Smena to'xtatish jadvali"""
    __tablename__ = "shift_pauses"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    paused_at = Column(DateTime, nullable=False)
    resumed_at = Column(DateTime, nullable=True)
    reason = Column(String(200), nullable=False)  # breakdown, lunch, other
    notes = Column(Text, nullable=True)

    # Relationships
    shift = relationship("Shift", back_populates="pauses")

    def __repr__(self):
        return f"<ShiftPause shift:{self.shift_id} reason:{self.reason}>"


class ScrapStock(BaseModel):
    """Atxot mini sklad — 2 tur:
      - brak     : smenadan tushgan yaroqsiz TAYYOR MAHSULOTLAR (finished_product_id)
      - recycled : tegirmondan chiqqan QAYTA ISHLANGAN XOM ASHYO (raw_material_id)

    Brak  → finished_product_id to'ldiriladi, raw_material_id = NULL
    Recycled → raw_material_id to'ldiriladi, finished_product_id = NULL
    """
    __tablename__ = "scrap_stock"

    # Brak uchun (tayyor mahsulot)
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=True)
    # Recycled uchun (xom ashyo — asosiy ombor GA EMAS, atxot skladda)
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=True)

    stock_type = Column(String(20), nullable=False, default='brak')  # 'brak' | 'recycled'
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    last_updated = Column(DateTime, nullable=False)

    __table_args__ = (
        # Brak: (finished_product_id, stock_type) unique
        # Recycled: (raw_material_id, stock_type) unique
        # Oddiy unique constraint emas, check qilinadi service da
    )

    # Relationships
    finished_product = relationship("FinishedProduct")
    raw_material = relationship("RawMaterial")
    transactions = relationship("ScrapStockTransaction", back_populates="scrap_stock")

    @property
    def product_name(self):
        if self.finished_product:
            return self.finished_product.name
        if self.raw_material:
            return self.raw_material.name
        return "Noma'lum"

    @property
    def product_unit(self):
        if self.finished_product:
            return self.finished_product.unit
        if self.raw_material:
            return self.raw_material.unit
        return ""

    def __repr__(self):
        pid = self.finished_product_id or self.raw_material_id
        return f"<ScrapStock {pid} [{self.stock_type}]: {self.quantity}>"


class ScrapStockTransaction(BaseModel):
    """Atxot sklad kirdi/chiqdi tarixi"""
    __tablename__ = "scrap_stock_transactions"

    scrap_stock_id = Column(UUID(as_uuid=True), ForeignKey('scrap_stock.id'), nullable=False)
    # Brak tranzaksiyalar uchun
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=True)
    # Recycled tranzaksiyalar uchun
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=True)

    transaction_type = Column(String(20), nullable=False)
    # Qiymatlar:
    #   'brak_in'      — smenadan brak tushdi       (finished_product_id)
    #   'brak_out'     — brak tegirmonga ketdi       (finished_product_id)
    #   'recycled_in'  — tegirmondan granula kirim   (raw_material_id)
    #   'recycled_out' — recycled smenada ishlatildi (raw_material_id)
    stock_type = Column(String(20), nullable=False, default='brak')
    quantity = Column(Numeric(10, 2), nullable=False)
    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, nullable=False)

    # Relationships
    scrap_stock = relationship("ScrapStock", back_populates="transactions")
    finished_product = relationship("FinishedProduct")
    raw_material = relationship("RawMaterial")
    shift = relationship("Shift")

    def __repr__(self):
        return f"<ScrapStockTransaction {self.transaction_type}: {self.quantity}>"


class ShiftScrapUsage(BaseModel):
    """Smena davomida atxot skladdan olingan material"""
    __tablename__ = "shift_scrap_usage"

    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=False)
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=True)
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey('raw_materials.id'), nullable=True)
    quantity_used = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    shift = relationship("Shift", back_populates="scrap_usages")
    finished_product = relationship("FinishedProduct")
    raw_material = relationship("RawMaterial")

    def __repr__(self):
        return f"<ShiftScrapUsage {self.id}>"