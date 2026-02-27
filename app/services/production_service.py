from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.models.production import (
    ProductionLine,
    Machine,
    FinishedProduct,
    Shift,
    ShiftMachine,
    ProductionRecord,
    ProductionOutput,
    DefectReason,
    DefectiveProduct,
    ShiftHandover,
    FinishedProductStock,
    ShiftPause,
    ScrapStock,
    ScrapStockTransaction,
    ShiftScrapUsage,
)
from app.schemas.production import (
    ProductionLineCreate,
    ProductionLineUpdate,
    MachineCreate,
    MachineUpdate,
    FinishedProductCreate,
    FinishedProductUpdate,
    ShiftCreate,
    ShiftComplete,
    ProductionRecordCreate,
    ProductionOutputCreate,
    DefectReasonCreate,
    DefectReasonUpdate,
    DefectiveProductCreate,
    ShiftHandoverCreate,
    ShiftStatistics,
    ProductionLinePerformance,
    ProductionStatistics,
    ShiftPauseCreate,
    ShiftScrapUsageCreate,
    ScrapTransferCreate,
    ShiftCloseRequest,
)
from app.repositories.production_repository import (
    ProductionLineRepository,
    MachineRepository,
    FinishedProductRepository,
    ShiftRepository,
    ProductionRecordRepository,
    ProductionOutputRepository,
    DefectReasonRepository,
    DefectiveProductRepository,
    ShiftHandoverRepository,
    FinishedProductStockRepository
)
from app.repositories.warehouse_repository import WarehouseStockRepository
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    InsufficientStockException
)
from app.utils.helpers import calculate_efficiency


class ProductionService:
    def __init__(self, db: Session):
        self.db = db
        self.line_repo = ProductionLineRepository(db)
        self.machine_repo = MachineRepository(db)
        self.product_repo = FinishedProductRepository(db)
        self.shift_repo = ShiftRepository(db)
        self.record_repo = ProductionRecordRepository(db)
        self.output_repo = ProductionOutputRepository(db)
        self.defect_reason_repo = DefectReasonRepository(db)
        self.defective_repo = DefectiveProductRepository(db)
        self.handover_repo = ShiftHandoverRepository(db)
        self.finished_stock_repo = FinishedProductStockRepository(db)
        self.warehouse_stock_repo = WarehouseStockRepository(db)

    # ============ PRODUCTION LINE METHODS ============

    def create_production_line(self, line_data: ProductionLineCreate) -> ProductionLine:
        """Yangi ishlab chiqarish liniyasi yaratish"""
        existing = self.line_repo.get_by_name(line_data.name)
        if existing:
            raise ConflictException(detail=f"'{line_data.name}' nomli liniya mavjud")

        new_line = ProductionLine(**line_data.model_dump())
        return self.line_repo.create(new_line)

    def get_production_line(self, line_id: UUID) -> ProductionLine:
        """Liniya olish"""
        line = self.line_repo.get_by_id(line_id)
        if not line:
            raise NotFoundException(detail="Liniya topilmadi")
        return line

    def get_all_production_lines(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[
        ProductionLine]:
        """Barcha liniyalar"""
        if include_inactive:
            return self.db.query(ProductionLine).offset(skip).limit(limit).all()
        return self.line_repo.get_all(skip=skip, limit=limit)

    def update_production_line(self, line_id: UUID, line_data: ProductionLineUpdate) -> ProductionLine:
        """Liniya yangilash"""
        line = self.get_production_line(line_id)

        if line_data.name and line_data.name != line.name:
            existing = self.line_repo.get_by_name(line_data.name)
            if existing:
                raise ConflictException(detail=f"'{line_data.name}' nomli liniya mavjud")

        update_data = line_data.model_dump(exclude_unset=True)
        return self.line_repo.update(line, update_data)

    def delete_production_line(self, line_id: UUID) -> bool:
        """Liniya o'chirish"""
        return self.line_repo.delete(line_id)

    # ============ MACHINE METHODS ============

    def create_machine(self, machine_data: MachineCreate) -> Machine:
        """Yangi mashina yaratish"""
        # Liniya mavjudligini tekshirish
        line = self.get_production_line(machine_data.production_line_id)

        new_machine = Machine(**machine_data.model_dump())
        return self.machine_repo.create(new_machine)

    def get_machine(self, machine_id: UUID) -> Machine:
        """Mashina olish"""
        machine = self.machine_repo.get_by_id(machine_id)
        if not machine:
            raise NotFoundException(detail="Mashina topilmadi")
        return machine

    def get_all_machines(self, skip: int = 0, limit: int = 100, include_inactive: bool = False):
        """Barcha mashinalar"""
        if include_inactive:
            return self.db.query(Machine).offset(skip).limit(limit).all()
        return self.machine_repo.get_all(skip=skip, limit=limit)

    # def update_machine(self, machine_id: UUID, machine_data: MachineUpdate) -> Machine:
    #     """Mashina yangilash"""
    #     machine = self.get_machine(machine_id)
    #
    #     if machine_data.production_line_id:
    #         line = self.get_production_line(machine_data.production_line_id)
    #
    #     update_data = machine_data.model_dump(exclude_unset=True)
    #     return self.machine_repo.update(machine, update_data)

    # 2-update machine
    def update_machine(self, machine_id: UUID, machine_data: MachineUpdate) -> Machine:
        """Mashina yangilash"""
        # is_active filter siz topamiz
        machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise NotFoundException(detail="Mashina topilmadi")

        if machine_data.production_line_id:
            line = self.get_production_line(machine_data.production_line_id)

        update_data = machine_data.model_dump(exclude_unset=True)
        return self.machine_repo.update(machine, update_data)

    def delete_machine(self, machine_id: UUID) -> bool:
        """Mashina o'chirish"""
        return self.machine_repo.delete(machine_id)

    # ============ FINISHED PRODUCT METHODS ============

    def create_finished_product(self, product_data: FinishedProductCreate) -> FinishedProduct:
        """Yangi tayyor mahsulot yaratish"""
        existing = self.product_repo.get_by_name(product_data.name)
        if existing:
            raise ConflictException(detail=f"'{product_data.name}' nomli mahsulot mavjud")

        new_product = FinishedProduct(**product_data.model_dump())
        product = self.product_repo.create(new_product)

        # Stock yaratish
        stock = FinishedProductStock(
            finished_product_id=product.id,
            quantity_total=Decimal("0"),
            quantity_available=Decimal("0"),
            quantity_reserved=Decimal("0"),
            last_updated=datetime.utcnow()
        )
        self.finished_stock_repo.create(stock)

        return product

    def get_finished_product(self, product_id: UUID) -> FinishedProduct:
        """Tayyor mahsulot olish"""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Mahsulot topilmadi")
        return product

    def get_all_finished_products(self, skip: int = 0, limit: int = 100) -> List[FinishedProduct]:
        """Barcha tayyor mahsulotlar"""
        return self.product_repo.get_all_with_stock(skip=skip, limit=limit)

    # def update_finished_product(self, product_id: UUID, product_data: FinishedProductUpdate) -> FinishedProduct:
    #     """Tayyor mahsulot yangilash"""
    #     product = self.get_finished_product(product_id)
    #
    #     if product_data.name and product_data.name != product.name:
    #         existing = self.product_repo.get_by_name(product_data.name)
    #         if existing:
    #             raise ConflictException(detail=f"'{product_data.name}' nomli mahsulot mavjud")
    #
    #     update_data = product_data.model_dump(exclude_unset=True)
    #     return self.product_repo.update(product, update_data)

    def update_finished_product(self, product_id: UUID, product_data: FinishedProductUpdate) -> FinishedProduct:
        """Tayyor mahsulot yangilash"""
        product = self.db.query(FinishedProduct).filter(FinishedProduct.id == product_id).first()
        if not product:
            raise NotFoundException(detail="Mahsulot topilmadi")

        update_data = product_data.model_dump(exclude_unset=True)
        return self.product_repo.update(product, update_data)

    def delete_finished_product(self, product_id: UUID) -> bool:
        """Tayyor mahsulot o'chirish"""
        return self.product_repo.delete(product_id)

    # ============ SHIFT METHODS ============

    def create_shift(self, shift_data: ShiftCreate, operator_id: UUID) -> Shift:
        """Yangi smena boshlash"""
        # Liniya mavjudligini tekshirish
        line = self.get_production_line(shift_data.production_line_id)

        # Mashinalarni tekshirish
        machines = []
        for machine_id in shift_data.machine_ids:
            machine = self.get_machine(machine_id)
            if machine.status != 'active':
                raise BadRequestException(detail=f"Mashina '{machine.name}' faol emas")
            machines.append(machine)

        # Smena yaratish
        new_shift = Shift(
            production_line_id=shift_data.production_line_id,
            operator_id=operator_id,
            start_time=shift_data.start_time,
            status='active',
            notes=shift_data.notes
        )
        shift = self.shift_repo.create(new_shift)

        # Mashinalarni biriktirish
        for machine in machines:
            shift_machine = ShiftMachine(
                shift_id=shift.id,
                machine_id=machine.id
            )
            self.db.add(shift_machine)

        self.db.commit()
        self.db.refresh(shift)

        return shift

    def get_shift(self, shift_id: UUID) -> Shift:
        """Smena olish"""
        shift = self.shift_repo.get_with_relations(shift_id)
        if not shift:
            raise NotFoundException(detail="Smena topilmadi")
        return shift

    def get_all_shifts(self, skip: int = 0, limit: int = 100) -> List[Shift]:
        """Barcha smenalar"""
        return self.shift_repo.get_all(skip=skip, limit=limit)

    def get_my_shifts(self, operator_id: UUID, skip: int = 0, limit: int = 100) -> List[Shift]:
        """Mening smenalarim"""
        return self.shift_repo.get_by_operator(operator_id, skip=skip, limit=limit)

    def complete_shift(
            self,
            shift_id: UUID,
            complete_data: ShiftComplete,
            handover_data: Optional[ShiftHandoverCreate] = None
    ) -> Shift:
        """Smenani yakunlash"""
        shift = self.get_shift(shift_id)

        if shift.status != 'active':
            raise BadRequestException(detail="Smena allaqachon yakunlangan")

        # Smena yakunlash
        shift.end_time = complete_data.end_time
        shift.status = 'completed'
        if complete_data.notes:
            shift.notes = complete_data.notes

        self.db.commit()

        # Handover yaratish
        if handover_data:
            handover = ShiftHandover(
                shift_id=shift.id,
                handover_notes=handover_data.handover_notes,
                equipment_status=handover_data.equipment_status,
                pending_issues=handover_data.pending_issues,
                next_shift_instructions=handover_data.next_shift_instructions,
                handover_time=datetime.utcnow()
            )
            self.handover_repo.create(handover)

        self.db.refresh(shift)
        return shift

    # ============ PRODUCTION RECORD METHODS ============

    def record_material_usage(
            self,
            shift_id: UUID,
            record_data: ProductionRecordCreate
    ) -> ProductionRecord:
        """Xom-ashyo ishlatishni yozish"""
        # Smena tekshirish
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenada xom-ashyo ishlatish mumkin")

        # Stock tekshirish (warehouse)
        stock = self.warehouse_stock_repo.get_by_material(record_data.raw_material_id)
        if not stock or stock.quantity < record_data.quantity_used:
            raise InsufficientStockException(
                detail=f"Omborda yetarli xom-ashyo yo'q. Mavjud: {stock.quantity if stock else 0}"
            )

        # Record yaratish
        new_record = ProductionRecord(
            shift_id=shift_id,
            raw_material_id=record_data.raw_material_id,
            quantity_used=record_data.quantity_used,
            recorded_at=datetime.utcnow(),
            notes=record_data.notes
        )
        record = self.record_repo.create(new_record)

        # Warehouse stock kamaytirish
        stock.quantity -= record_data.quantity_used
        stock.last_updated = datetime.utcnow()
        self.db.commit()

        return record

    def get_shift_material_usage(self, shift_id: UUID) -> List[ProductionRecord]:
        """Smena xom-ashyo ishlatish tarixi"""
        return self.record_repo.get_by_shift(shift_id)

    # ============ PRODUCTION OUTPUT METHODS ============

    def record_production_output(
            self,
            shift_id: UUID,
            output_data: ProductionOutputCreate
    ) -> ProductionOutput:
        """Ishlab chiqarishni yozish"""
        # Smena tekshirish
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenada ishlab chiqarish yozish mumkin")

        # Mahsulot tekshirish
        product = self.get_finished_product(output_data.finished_product_id)

        # Output yaratish
        new_output = ProductionOutput(
            shift_id=shift_id,
            finished_product_id=output_data.finished_product_id,
            quantity_produced=output_data.quantity_produced,
            produced_at=datetime.utcnow(),
            notes=output_data.notes
        )
        output = self.output_repo.create(new_output)

        # Finished product stock oshirish
        self._update_finished_stock_add(output_data.finished_product_id, output_data.quantity_produced)

        return output

    def get_shift_production_output(self, shift_id: UUID) -> List[ProductionOutput]:
        """Smena ishlab chiqarish tarixi"""
        return self.output_repo.get_by_shift(shift_id)

    # ============ DEFECT METHODS ============

    def create_defect_reason(self, reason_data: DefectReasonCreate) -> DefectReason:
        """Yangi brak sababi yaratish"""
        existing = self.defect_reason_repo.get_by_name(reason_data.name)
        if existing:
            raise ConflictException(detail=f"'{reason_data.name}' nomli sabab mavjud")

        new_reason = DefectReason(**reason_data.model_dump())
        return self.defect_reason_repo.create(new_reason)

    def get_all_defect_reasons(self, skip: int = 0, limit: int = 100) -> List[DefectReason]:
        """Barcha brak sabablari"""
        return self.defect_reason_repo.get_all(skip=skip, limit=limit)

    def record_defective_product(
            self,
            shift_id: UUID,
            defect_data: DefectiveProductCreate
    ) -> DefectiveProduct:
        """Brak yozish"""
        # Smena tekshirish
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenada brak yozish mumkin")

        # Mahsulot va sabab tekshirish
        product = self.get_finished_product(defect_data.finished_product_id)
        reason = self.defect_reason_repo.get_by_id(defect_data.defect_reason_id)
        if not reason:
            raise NotFoundException(detail="Brak sababi topilmadi")

        # Defect yaratish
        new_defect = DefectiveProduct(
            shift_id=shift_id,
            finished_product_id=defect_data.finished_product_id,
            defect_reason_id=defect_data.defect_reason_id,
            quantity=defect_data.quantity,
            recorded_at=datetime.utcnow(),
            notes=defect_data.notes
        )

        return self.defective_repo.create(new_defect)

    def get_shift_defects(self, shift_id: UUID) -> List[DefectiveProduct]:
        """Smena braklari"""
        return self.defective_repo.get_by_shift(shift_id)

    # ============ STATISTICS METHODS ============

    def get_shift_statistics(self, shift_id: UUID) -> ShiftStatistics:
        """Smena statistikasi"""
        total_materials = self.record_repo.get_total_used_in_shift(shift_id)
        total_output = self.output_repo.get_total_output_in_shift(shift_id)
        total_defects = self.defective_repo.get_total_defects_in_shift(shift_id)

        # Efficiency hisoblash (soddalashtirilgan)
        # Real formula: (Output / (Material_Used * Conversion_Rate)) * 100
        efficiency = Decimal("0")
        if total_materials > 0:
            efficiency = (total_output / total_materials) * 100

        # Defect rate
        defect_rate = Decimal("0")
        if total_output > 0:
            defect_rate = (total_defects / (total_output + total_defects)) * 100

        return ShiftStatistics(
            shift_id=shift_id,
            total_raw_materials_used=total_materials,
            total_production_output=total_output,
            total_defects=total_defects,
            efficiency_percentage=efficiency,
            defect_rate_percentage=defect_rate
        )

    def get_production_statistics(self) -> ProductionStatistics:
        """Umumiy ishlab chiqarish statistikasi"""
        total_lines = self.line_repo.count()
        total_machines = self.machine_repo.count()
        active_shifts = len(self.shift_repo.get_active_shifts())
        completed_today = self.shift_repo.get_completed_today()
        output_today = self.output_repo.get_total_output_today()
        defects_today = self.defective_repo.get_total_defects_today()

        # Average efficiency (soddalashtirilgan)
        avg_efficiency = Decimal("85.0")  # Placeholder

        return ProductionStatistics(
            total_production_lines=total_lines,
            total_machines=total_machines,
            active_shifts=active_shifts,
            completed_shifts_today=completed_today,
            total_output_today=output_today,
            total_defects_today=defects_today,
            average_efficiency_today=avg_efficiency
        )

    # ============ PRIVATE HELPER METHODS ============

    def _update_finished_stock_add(self, product_id: UUID, quantity: Decimal):
        """Tayyor mahsulot stock qo'shish"""
        stock = self.finished_stock_repo.get_by_product(product_id)

        if not stock:
            stock = FinishedProductStock(
                finished_product_id=product_id,
                quantity_total=quantity,
                quantity_available=quantity,
                quantity_reserved=Decimal("0"),
                last_updated=datetime.utcnow()
            )
            self.finished_stock_repo.create(stock)
        else:
            stock.quantity_total += quantity
            stock.quantity_available += quantity
            stock.last_updated = datetime.utcnow()
            self.db.commit()

    # ============ SHIFT PAUSE METHODS ============

    def pause_shift(self, shift_id: UUID, data: ShiftPauseCreate) -> ShiftPause:
        """Smenani to'xtatish"""
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenani to'xtatish mumkin")

        # Ochiq pauza bormi tekshirish
        open_pause = self.db.query(ShiftPause).filter(
            ShiftPause.shift_id == shift_id,
            ShiftPause.resumed_at == None
        ).first()
        if open_pause:
            raise BadRequestException(detail="Smena allaqachon to'xtatilgan")

        pause = ShiftPause(
            shift_id=shift_id,
            paused_at=datetime.utcnow(),
            reason=data.reason,
            notes=data.notes,
        )
        self.db.add(pause)
        self.db.commit()
        self.db.refresh(pause)
        return pause

    def resume_shift(self, shift_id: UUID) -> ShiftPause:
        """Smenani davom ettirish"""
        shift = self.get_shift(shift_id)
        pause = self.db.query(ShiftPause).filter(
            ShiftPause.shift_id == shift_id,
            ShiftPause.resumed_at == None
        ).first()
        if not pause:
            raise BadRequestException(detail="To'xtatilgan pauza topilmadi")

        pause.resumed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pause)
        return pause

    def get_shift_pauses(self, shift_id: UUID) -> List[ShiftPause]:
        """Smena pauzalari ro'yxati"""
        return self.db.query(ShiftPause).filter(
            ShiftPause.shift_id == shift_id
        ).order_by(ShiftPause.paused_at).all()

    # ============ SCRAP STOCK METHODS ============

    def get_all_scrap_stock(self) -> List[ScrapStock]:
        """Barcha atxot qoldiqlari (brak va recycled alohida)"""
        from sqlalchemy.orm import joinedload
        return self.db.query(ScrapStock).options(
            joinedload(ScrapStock.finished_product)
        ).order_by(ScrapStock.stock_type, ScrapStock.finished_product_id).all()

    def get_scrap_transactions(self, product_id=None, stock_type=None) -> List[ScrapStockTransaction]:
        """Atxot tarixi"""
        from sqlalchemy.orm import joinedload
        q = self.db.query(ScrapStockTransaction).options(
            joinedload(ScrapStockTransaction.finished_product)
        )
        if product_id:
            q = q.filter(ScrapStockTransaction.finished_product_id == product_id)
        if stock_type:
            q = q.filter(ScrapStockTransaction.stock_type == stock_type)
        return q.order_by(ScrapStockTransaction.recorded_at.desc()).limit(200).all()

    def transfer_scrap_to_grinder(self, data: ScrapTransferCreate) -> dict:
        """
        Brak mahsulotni tegirmonga o'tkazish → boshqa mahsulot (granula) chiqadi.

        Jarayon:
        1. input_product (brak) qoldiqdan kamaytirish
        2. output_product (recycled) — BOSHQA mahsulot — qo'shiladi
        3. Har ikki tranzaksiya yoziladi

        Tizim hisoblamaydi — operator output_quantity ni o'zi kiritadi.
        """
        # 1. Brak qoldiqni tekshirish (input mahsulot)
        brak_stock = self.db.query(ScrapStock).filter(
            ScrapStock.finished_product_id == data.input_product_id,
            ScrapStock.stock_type == 'brak'
        ).first()

        if not brak_stock:
            raise NotFoundException(detail="Brak atxot qoldiq topilmadi")
        if brak_stock.quantity < data.input_quantity:
            raise BadRequestException(
                detail=f"Yetarli brak yo'q. Mavjud: {brak_stock.quantity}, So'ralgan: {data.input_quantity}"
            )

        now = datetime.utcnow()

        # 2. Brak kamaytirish
        brak_stock.quantity -= data.input_quantity
        brak_stock.last_updated = now

        out_txn = ScrapStockTransaction(
            scrap_stock_id=brak_stock.id,
            finished_product_id=data.input_product_id,
            transaction_type='brak_out',
            stock_type='brak',
            quantity=data.input_quantity,
            notes=data.notes,
            recorded_at=now,
        )
        self.db.add(out_txn)

        # 3. Output mahsulotni recycled sifatida atxot skladga qo'shish
        # (output_product_id != input_product_id bo'lishi mumkin)
        recycled_stock = self.db.query(ScrapStock).filter(
            ScrapStock.finished_product_id == data.output_product_id,
            ScrapStock.stock_type == 'recycled'
        ).first()

        if not recycled_stock:
            recycled_stock = ScrapStock(
                finished_product_id=data.output_product_id,
                stock_type='recycled',
                quantity=data.output_quantity,
                last_updated=now,
            )
            self.db.add(recycled_stock)
            self.db.flush()
        else:
            recycled_stock.quantity += data.output_quantity
            recycled_stock.last_updated = now

        in_txn = ScrapStockTransaction(
            scrap_stock_id=recycled_stock.id,
            finished_product_id=data.output_product_id,
            transaction_type='recycled_in',
            stock_type='recycled',
            quantity=data.output_quantity,
            notes=data.notes,
            recorded_at=now,
        )
        self.db.add(in_txn)

        self.db.commit()
        self.db.refresh(in_txn)
        return {
            "brak_out": {"product_id": str(data.input_product_id), "quantity": float(data.input_quantity)},
            "recycled_in": {"product_id": str(data.output_product_id), "quantity": float(data.output_quantity)},
        }

    # ============ SHIFT SCRAP USAGE ============

    def use_scrap_in_shift(self, shift_id: UUID, data: ShiftScrapUsageCreate) -> ShiftScrapUsage:
        """
        Smena davomida atxot skladdan material olish.
        stock_type: 'brak' yoki 'recycled'
        """
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenada material olish mumkin")

        stock_type = data.stock_type if hasattr(data, 'stock_type') and data.stock_type else 'recycled'

        scrap = self.db.query(ScrapStock).filter(
            ScrapStock.finished_product_id == data.finished_product_id,
            ScrapStock.stock_type == stock_type
        ).first()

        if not scrap or scrap.quantity < data.quantity_used:
            avail = scrap.quantity if scrap else 0
            raise BadRequestException(
                detail=f"Yetarli {stock_type} atxot yo'q. Mavjud: {avail}, So'ralgan: {data.quantity_used}"
            )

        # Kamaytirish
        scrap.quantity -= data.quantity_used
        scrap.last_updated = datetime.utcnow()

        txn_type = 'brak_out' if stock_type == 'brak' else 'recycled_out'
        txn = ScrapStockTransaction(
            scrap_stock_id=scrap.id,
            finished_product_id=data.finished_product_id,
            transaction_type=txn_type,
            stock_type=stock_type,
            quantity=data.quantity_used,
            shift_id=shift_id,
            notes=data.notes,
            recorded_at=datetime.utcnow(),
        )
        self.db.add(txn)

        usage = ShiftScrapUsage(
            shift_id=shift_id,
            finished_product_id=data.finished_product_id,
            quantity_used=data.quantity_used,
            recorded_at=datetime.utcnow(),
            notes=data.notes,
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_shift_scrap_usage(self, shift_id: UUID) -> List[ShiftScrapUsage]:
        """Smena atxot foydalanish tarixi"""
        from sqlalchemy.orm import joinedload
        return self.db.query(ShiftScrapUsage).options(
            joinedload(ShiftScrapUsage.finished_product)
        ).filter(ShiftScrapUsage.shift_id == shift_id).all()

    # ============ SHIFT CLOSE (yangilangan) ============

    def close_shift(self, shift_id: UUID, data: ShiftCloseRequest) -> Shift:
        """
        Smenani yopish — bir so'rovda:
        - Tayyor mahsulotlar → finished_product_stock ga qo'shiladi
        - Atxot mahsulotlar → scrap_stock ga qo'shiladi
        - Smena status = completed
        """
        shift = self.get_shift(shift_id)
        if shift.status != 'active':
            raise BadRequestException(detail="Faqat faol smenani yopish mumkin")

        # 1. Tayyor mahsulotlar
        for item in data.outputs:
            if item.quantity_produced <= 0:
                continue
            output = ProductionOutput(
                shift_id=shift_id,
                finished_product_id=item.finished_product_id,
                quantity_produced=item.quantity_produced,
                produced_at=data.end_time,
                notes=item.notes,
            )
            self.db.add(output)
            self._update_finished_stock_add(item.finished_product_id, item.quantity_produced)

        # 2. Atxot mahsulotlar → scrap_stock ga
        for scrap_item in data.scraps:
            if scrap_item.quantity <= 0:
                continue

            # DefectiveProduct yozuvi
            defect = DefectiveProduct(
                shift_id=shift_id,
                finished_product_id=scrap_item.finished_product_id,
                defect_reason_id=scrap_item.defect_reason_id,
                quantity=scrap_item.quantity,
                recorded_at=data.end_time,
                notes=scrap_item.notes,
            )
            self.db.add(defect)

            # Atxot skladga qo'shish
            self._update_scrap_stock_add(
                product_id=scrap_item.finished_product_id,
                quantity=scrap_item.quantity,
                shift_id=shift_id,
                notes=scrap_item.notes,
            )

        # 3. Smena yopish
        shift.status = 'completed'
        shift.end_time = data.end_time
        if data.notes:
            shift.notes = data.notes

        # 4. Handover (ixtiyoriy)
        if data.handover_notes:
            handover = ShiftHandover(
                shift_id=shift_id,
                handover_notes=data.handover_notes,
                handover_time=data.end_time,
            )
            self.db.add(handover)

        self.db.commit()
        self.db.refresh(shift)
        return shift

    def _update_scrap_stock_add(
            self, product_id: UUID, quantity: Decimal,
            stock_type: str = 'brak',
            shift_id: Optional[UUID] = None, notes: Optional[str] = None
    ):
        """Atxot stokka qo'shish yoki yangilash (default: brak)"""
        scrap = self.db.query(ScrapStock).filter(
            ScrapStock.finished_product_id == product_id,
            ScrapStock.stock_type == stock_type
        ).first()

        if not scrap:
            scrap = ScrapStock(
                finished_product_id=product_id,
                stock_type=stock_type,
                quantity=quantity,
                last_updated=datetime.utcnow(),
            )
            self.db.add(scrap)
            self.db.flush()
        else:
            scrap.quantity += quantity
            scrap.last_updated = datetime.utcnow()

        txn_type = 'brak_in' if stock_type == 'brak' else 'recycled_in'
        txn = ScrapStockTransaction(
            scrap_stock_id=scrap.id,
            finished_product_id=product_id,
            transaction_type=txn_type,
            stock_type=stock_type,
            quantity=quantity,
            shift_id=shift_id,
            notes=notes,
            recorded_at=datetime.utcnow(),
        )
        self.db.add(txn)