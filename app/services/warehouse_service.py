from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from app.utils.datetime_utils import get_now
from uuid import UUID
from app.models.warehouse import (
    Supplier,
    RawMaterial,
    WarehouseReceipt,
    WarehouseStock,
    MaterialRequest
)
from app.schemas.warehouse import (
    SupplierCreate,
    SupplierUpdate,
    RawMaterialCreate,
    RawMaterialUpdate,
    WarehouseReceiptCreate,
    MaterialRequestCreate,
    MaterialRequestApprove,
    MaterialRequestReject,
    LowStockItem,
    WarehouseStatistics
)
from app.repositories.warehouse_repository import (
    SupplierRepository,
    RawMaterialRepository,
    WarehouseReceiptRepository,
    WarehouseStockRepository,
    MaterialRequestRepository
)
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    InsufficientStockException
)
from app.core.constants import RequestStatus
from app.utils.helpers import generate_batch_number


class WarehouseService:
    def __init__(self, db: Session):
        self.db = db
        self.supplier_repo = SupplierRepository(db)
        self.material_repo = RawMaterialRepository(db)
        self.receipt_repo = WarehouseReceiptRepository(db)
        self.stock_repo = WarehouseStockRepository(db)
        self.request_repo = MaterialRequestRepository(db)

    # ============ SUPPLIER METHODS ============

    def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Yangi supplier yaratish"""
        # Nom bo'yicha tekshirish
        existing = self.supplier_repo.get_by_name(supplier_data.name)
        if existing:
            raise ConflictException(detail=f"'{supplier_data.name}' nomli supplier mavjud")

        # INN bo'yicha tekshirish
        if supplier_data.inn:
            existing_inn = self.supplier_repo.get_by_inn(supplier_data.inn)
            if existing_inn:
                raise ConflictException(detail=f"'{supplier_data.inn}' INN bilan supplier mavjud")

        new_supplier = Supplier(**supplier_data.model_dump())
        return self.supplier_repo.create(new_supplier)

    def get_supplier(self, supplier_id: UUID) -> Supplier:
        """Supplier olish"""
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundException(detail="Supplier topilmadi")
        return supplier

    def get_all_suppliers(self, skip: int = 0, limit: int = 100) -> List[Supplier]:
        """Barcha supplierlar"""
        return self.supplier_repo.get_all(skip=skip, limit=limit)

    def update_supplier(self, supplier_id: UUID, supplier_data: SupplierUpdate) -> Supplier:
        """Supplier yangilash"""
        supplier = self.get_supplier(supplier_id)

        # Nom o'zgargan bo'lsa tekshirish
        if supplier_data.name and supplier_data.name != supplier.name:
            existing = self.supplier_repo.get_by_name(supplier_data.name)
            if existing:
                raise ConflictException(detail=f"'{supplier_data.name}' nomli supplier mavjud")

        update_data = supplier_data.model_dump(exclude_unset=True)
        return self.supplier_repo.update(supplier, update_data)

    def delete_supplier(self, supplier_id: UUID) -> bool:
        """Supplier o'chirish"""
        return self.supplier_repo.delete(supplier_id)

    # ============ RAW MATERIAL METHODS ============

    def create_raw_material(self, material_data: RawMaterialCreate) -> RawMaterial:
        """Yangi xom-ashyo yaratish"""
        # Nom bo'yicha tekshirish
        existing = self.material_repo.get_by_name(material_data.name)
        if existing:
            raise ConflictException(detail=f"'{material_data.name}' nomli xom-ashyo mavjud")

        new_material = RawMaterial(**material_data.model_dump())
        material = self.material_repo.create(new_material)

        # Stock yaratish (boshlang'ich 0)
        stock = WarehouseStock(
            raw_material_id=material.id,
            quantity=Decimal("0"),
            last_updated=get_now()
        )
        self.stock_repo.create(stock)

        return material

    def get_raw_material(self, material_id: UUID) -> RawMaterial:
        """Xom-ashyo olish"""
        material = self.material_repo.get_by_id(material_id)
        if not material:
            raise NotFoundException(detail="Xom-ashyo topilmadi")
        return material

    def get_all_raw_materials(self, skip: int = 0, limit: int = 100) -> List[RawMaterial]:
        """Barcha xom-ashyolar"""
        return self.material_repo.get_all_with_stock(skip=skip, limit=limit)

    def update_raw_material(self, material_id: UUID, material_data: RawMaterialUpdate) -> RawMaterial:
        """Xom-ashyo yangilash"""
        material = self.get_raw_material(material_id)

        # Nom o'zgargan bo'lsa tekshirish
        if material_data.name and material_data.name != material.name:
            existing = self.material_repo.get_by_name(material_data.name)
            if existing:
                raise ConflictException(detail=f"'{material_data.name}' nomli xom-ashyo mavjud")

        update_data = material_data.model_dump(exclude_unset=True)
        return self.material_repo.update(material, update_data)

    def delete_raw_material(self, material_id: UUID) -> bool:
        """Xom-ashyo o'chirish"""
        return self.material_repo.delete(material_id)

    # ============ WAREHOUSE RECEIPT METHODS ============

    def create_receipt(self, receipt_data: WarehouseReceiptCreate, user_id: UUID = None) -> WarehouseReceipt:
        """Xom-ashyo qabul qilish"""
        # Supplier tekshirish
        supplier = self.supplier_repo.get_by_id(receipt_data.supplier_id)
        if not supplier:
            raise NotFoundException(detail="Supplier topilmadi")

        # Xom-ashyo tekshirish
        material = self.material_repo.get_by_id(receipt_data.raw_material_id)
        if not material:
            raise NotFoundException(detail="Xom-ashyo topilmadi")

        # Total price hisoblash
        total_price = receipt_data.quantity * receipt_data.unit_price

        # Batch number generatsiya
        batch_number = generate_batch_number()

        # Receipt yaratish
        new_receipt = WarehouseReceipt(
            supplier_id=receipt_data.supplier_id,
            raw_material_id=receipt_data.raw_material_id,
            quantity=receipt_data.quantity,
            unit_price=receipt_data.unit_price,
            total_price=total_price,
            batch_number=batch_number,
            receipt_date=receipt_data.receipt_date,
            notes=receipt_data.notes
        )
        receipt = self.receipt_repo.create(new_receipt)

        # Stock yangilash
        self._update_stock_add(receipt_data.raw_material_id, receipt_data.quantity)

        # ✅ Moliya — avtomatik tranzaksiya yaratish
        if user_id:
            try:
                from app.services.finance_service import FinanceService
                finance_service = FinanceService(self.db)
                finance_service.create_automatic_transaction(
                    transaction_type="expense",
                    amount=total_price,
                    category_name="Xom-ashyo xarajatlari",
                    description=f"Xom-ashyo qabuli — {supplier.name}",
                    reference_type="warehouse_receipt",
                    reference_id=receipt.id,
                    user_id=user_id
                )
            except Exception:
                pass  # Moliya xatosi asosiy operatsiyani bloklamasin

        return receipt

    def get_receipt(self, receipt_id: UUID) -> WarehouseReceipt:
        """Qabul qilish olish"""
        receipt = self.receipt_repo.get_with_relations(receipt_id)
        if not receipt:
            raise NotFoundException(detail="Qabul qilish topilmadi")
        return receipt

    def get_all_receipts(self, skip: int = 0, limit: int = 100) -> List[WarehouseReceipt]:
        """Barcha qabul qilishlar"""
        return self.receipt_repo.get_all_with_relations(skip=skip, limit=limit)

    def delete_receipt(self, receipt_id: UUID) -> bool:
        """Qabul qilishni o'chirish"""
        receipt = self.receipt_repo.get_by_id(receipt_id)
        if not receipt:
            raise NotFoundException(detail="Qabul qilish topilmadi")
        return self.receipt_repo.delete(receipt_id)

    # ============ STOCK METHODS ============

    def get_stock_by_material(self, material_id: UUID) -> Optional[WarehouseStock]:
        """Xom-ashyo bo'yicha qoldiq"""
        material = self.get_raw_material(material_id)
        stock = self.stock_repo.get_by_material(material_id)
        return stock

    def get_all_stock(self, skip: int = 0, limit: int = 100) -> List[WarehouseStock]:
        """Barcha qoldiqlar"""
        return self.stock_repo.get_all_with_materials(skip=skip, limit=limit)

    def delete_stock(self, stock_id: UUID):
        """Zaxira yozuvini o'chirish (faqat superadmin)"""
        from app.core.exceptions import NotFoundException
        stock = self.db.query(WarehouseStock).filter(WarehouseStock.id == stock_id).first()
        if not stock:
            raise NotFoundException(detail="Zaxira topilmadi")
        self.db.delete(stock)
        self.db.commit()
        return {"message": "O'chirildi"}

    def get_low_stock_items(self) -> List[LowStockItem]:
        """Kam qoldiqlar"""
        items = self.stock_repo.get_low_stock_items()
        return [LowStockItem(**item) for item in items]

    # ============ MATERIAL REQUEST METHODS ============

    def create_material_request(
            self,
            request_data: MaterialRequestCreate,
            user_id: UUID
    ) -> MaterialRequest:
        """Xom-ashyo so'rovi yaratish"""
        # Xom-ashyo tekshirish
        material = self.get_raw_material(request_data.raw_material_id)

        # So'rov yaratish
        new_request = MaterialRequest(
            raw_material_id=request_data.raw_material_id,
            requested_quantity=request_data.requested_quantity,
            request_status=RequestStatus.PENDING.value,
            requested_by=user_id,
            request_date=get_now(),
            notes=request_data.notes
        )

        return self.request_repo.create(new_request)

    def get_material_request(self, request_id: UUID) -> MaterialRequest:
        """So'rov olish"""
        request = self.request_repo.get_with_relations(request_id)
        if not request:
            raise NotFoundException(detail="So'rov topilmadi")
        return request

    def get_all_material_requests(
            self,
            status: Optional[str] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[MaterialRequest]:
        """Barcha so'rovlar"""
        return self.request_repo.get_all_with_relations(
            status=status,
            skip=skip,
            limit=limit
        )

    def approve_material_request(
            self,
            request_id: UUID,
            approve_data: MaterialRequestApprove,
            user_id: UUID
    ) -> MaterialRequest:
        """So'rovni tasdiqlash"""
        # So'rovni olish
        request = self.get_material_request(request_id)

        # Status tekshirish
        if request.request_status != RequestStatus.PENDING.value:
            raise BadRequestException(detail="So'rov allaqachon ko'rib chiqilgan")

        # Stock tekshirish
        stock = self.stock_repo.get_by_material(request.raw_material_id)
        if not stock or stock.quantity < approve_data.approved_quantity:
            raise InsufficientStockException(
                detail=f"Omborda yetarli xom-ashyo yo'q. Mavjud: {stock.quantity if stock else 0}"
            )

        # Tasdiqlanadi
        if approve_data.approved_quantity == request.requested_quantity:
            request.request_status = RequestStatus.APPROVED.value
        elif approve_data.approved_quantity < request.requested_quantity:
            request.request_status = RequestStatus.PARTIALLY_APPROVED.value

        request.approved_quantity = approve_data.approved_quantity
        request.approved_by = user_id
        request.approval_date = get_now()
        if approve_data.notes:
            request.notes = approve_data.notes

        self.db.commit()
        self.db.refresh(request)

        # Stock kamaytirish
        self._update_stock_subtract(request.raw_material_id, approve_data.approved_quantity)

        return request

    def reject_material_request(
            self,
            request_id: UUID,
            reject_data: MaterialRequestReject,
            user_id: UUID
    ) -> MaterialRequest:
        """So'rovni rad etish"""
        # So'rovni olish
        request = self.get_material_request(request_id)

        # Status tekshirish
        if request.request_status != RequestStatus.PENDING.value:
            raise BadRequestException(detail="So'rov allaqachon ko'rib chiqilgan")

        # Rad etish
        request.request_status = RequestStatus.REJECTED.value
        request.approved_by = user_id
        request.approval_date = get_now()
        request.rejection_reason = reject_data.rejection_reason

        self.db.commit()
        self.db.refresh(request)

        return request

    def delete_material_request(self, request_id: UUID) -> bool:
        """Material so'rovini o'chirish"""
        request = self.request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundException(detail="So'rov topilmadi")
        return self.request_repo.delete(request_id)

    def get_my_requests(
            self,
            user_id: UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[MaterialRequest]:
        """Mening so'rovlarim"""
        return self.request_repo.get_by_user(user_id, skip=skip, limit=limit)

    # ============ STATISTICS METHODS ============

    def get_statistics(self) -> WarehouseStatistics:
        """Ombor statistikasi"""
        total_suppliers = self.supplier_repo.count()
        total_raw_materials = self.material_repo.count()
        low_stock_count = len(self.stock_repo.get_low_stock_items())
        pending_requests = self.request_repo.get_pending_count()
        receipts_this_month = self.receipt_repo.get_count_this_month()
        receipts_value_this_month = self.receipt_repo.get_total_value_this_month()
        total_stock_value = self.stock_repo.get_total_stock_value()

        return WarehouseStatistics(
            total_suppliers=total_suppliers,
            total_raw_materials=total_raw_materials,
            total_stock_value=total_stock_value,
            low_stock_items_count=low_stock_count,
            pending_requests_count=pending_requests,
            total_receipts_this_month=receipts_this_month,
            total_receipts_value_this_month=receipts_value_this_month
        )

    # ============ PRIVATE HELPER METHODS ============

    def _update_stock_add(self, material_id: UUID, quantity: Decimal):
        """Stock qo'shish (qabul qilishda)"""
        stock = self.stock_repo.get_by_material(material_id)

        if not stock:
            # Agar stock yo'q bo'lsa yaratish
            stock = WarehouseStock(
                raw_material_id=material_id,
                quantity=quantity,
                last_updated=get_now()
            )
            self.stock_repo.create(stock)
        else:
            # Mavjud stockni yangilash
            stock.quantity += quantity
            stock.last_updated = get_now()
            self.db.commit()

    def _update_stock_subtract(self, material_id: UUID, quantity: Decimal):
        """Stock kamaytirish (so'rov tasdiqlanganda)"""
        stock = self.stock_repo.get_by_material(material_id)

        if not stock or stock.quantity < quantity:
            raise InsufficientStockException(detail="Omborda yetarli xom-ashyo yo'q")

        stock.quantity -= quantity
        stock.last_updated = get_now()
        self.db.commit()

        # Low stock tekshirish va bildirishnoma
        try:
            material = self.material_repo.get_by_id(material_id)
            if material and stock.quantity <= material.minimum_stock:
                from app.services.notification_service import NotificationService
                notif_service = NotificationService(self.db)
                notif_service.notify_low_stock(
                    material_name=material.name,
                    current_qty=float(stock.quantity),
                    min_qty=float(material.minimum_stock),
                    material_id=material_id
                )
        except Exception:
            pass