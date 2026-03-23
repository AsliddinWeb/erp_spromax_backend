from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
from app.utils.datetime_utils import get_today_start, get_month_start
from uuid import UUID
from app.models.warehouse import (
    Supplier,
    RawMaterial,
    WarehouseReceipt,
    WarehouseStock,
    MaterialRequest
)
from app.repositories.base import BaseRepository
from app.core.constants import RequestStatus


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, db: Session):
        super().__init__(Supplier, db)

    def get_by_name(self, name: str) -> Optional[Supplier]:
        """Nom bo'yicha supplier topish"""
        return self.db.query(Supplier).filter(
            Supplier.name == name,
            Supplier.is_active == True
        ).first()

    def get_by_inn(self, inn: str) -> Optional[Supplier]:
        """INN bo'yicha supplier topish"""
        return self.db.query(Supplier).filter(
            Supplier.inn == inn,
            Supplier.is_active == True
        ).first()


class RawMaterialRepository(BaseRepository[RawMaterial]):
    def __init__(self, db: Session):
        super().__init__(RawMaterial, db)

    def get_by_name(self, name: str) -> Optional[RawMaterial]:
        """Nom bo'yicha xom-ashyo topish"""
        return self.db.query(RawMaterial).filter(
            RawMaterial.name == name,
            RawMaterial.is_active == True
        ).first()

    def get_with_stock(self, material_id: UUID) -> Optional[RawMaterial]:
        """Stock bilan xom-ashyo olish"""
        return self.db.query(RawMaterial).options(
            joinedload(RawMaterial.warehouse_stock)
        ).filter(
            RawMaterial.id == material_id,
            RawMaterial.is_active == True
        ).first()

    def get_all_with_stock(self, skip: int = 0, limit: int = 100) -> List[RawMaterial]:
        """Barcha xom-ashyolarni stock bilan olish"""
        return self.db.query(RawMaterial).options(
            joinedload(RawMaterial.warehouse_stock)
        ).filter(
            RawMaterial.is_active == True
        ).offset(skip).limit(limit).all()


class WarehouseReceiptRepository(BaseRepository[WarehouseReceipt]):
    def __init__(self, db: Session):
        super().__init__(WarehouseReceipt, db)

    def get_with_relations(self, receipt_id: UUID) -> Optional[WarehouseReceipt]:
        """Relationships bilan qabul qilish"""
        return self.db.query(WarehouseReceipt).options(
            joinedload(WarehouseReceipt.supplier),
            joinedload(WarehouseReceipt.raw_material)
        ).filter(
            WarehouseReceipt.id == receipt_id,
            WarehouseReceipt.is_active == True
        ).first()

    def get_all_with_relations(self, skip: int = 0, limit: int = 100) -> List[WarehouseReceipt]:
        """Barcha qabul qilishlar"""
        return self.db.query(WarehouseReceipt).options(
            joinedload(WarehouseReceipt.supplier),
            joinedload(WarehouseReceipt.raw_material)
        ).filter(
            WarehouseReceipt.is_active == True
        ).order_by(WarehouseReceipt.receipt_date.desc()).offset(skip).limit(limit).all()

    def get_by_batch_number(self, batch_number: str) -> Optional[WarehouseReceipt]:
        """Partiya raqami bo'yicha"""
        return self.db.query(WarehouseReceipt).filter(
            WarehouseReceipt.batch_number == batch_number,
            WarehouseReceipt.is_active == True
        ).first()

    def get_total_value_this_month(self) -> Decimal:
        """Ushbu oydagi umumiy qabul qiymati"""
        start_of_month = get_month_start()

        result = self.db.query(
            func.sum(WarehouseReceipt.total_price)
        ).filter(
            WarehouseReceipt.receipt_date >= start_of_month,
            WarehouseReceipt.is_active == True
        ).scalar()

        return result or Decimal("0")

    def get_count_this_month(self) -> int:
        """Ushbu oydagi qabul qilishlar soni"""
        start_of_month = get_month_start()

        return self.db.query(func.count(WarehouseReceipt.id)).filter(
            WarehouseReceipt.receipt_date >= start_of_month,
            WarehouseReceipt.is_active == True
        ).scalar()


class WarehouseStockRepository(BaseRepository[WarehouseStock]):
    def __init__(self, db: Session):
        super().__init__(WarehouseStock, db)

    def get_by_material(self, material_id: UUID) -> Optional[WarehouseStock]:
        """Xom-ashyo bo'yicha qoldiq"""
        return self.db.query(WarehouseStock).filter(
            WarehouseStock.raw_material_id == material_id,
            WarehouseStock.is_active == True
        ).first()

    def get_all_with_materials(self, skip: int = 0, limit: int = 100) -> List[WarehouseStock]:
        """Barcha qoldiqlar xom-ashyo bilan"""
        return self.db.query(WarehouseStock).options(
            joinedload(WarehouseStock.raw_material)
        ).filter(
            WarehouseStock.is_active == True
        ).offset(skip).limit(limit).all()

    def get_low_stock_items(self) -> List[dict]:
        """Kam qoldiqlar ro'yxati"""
        results = self.db.query(
            RawMaterial,
            WarehouseStock
        ).join(
            WarehouseStock,
            RawMaterial.id == WarehouseStock.raw_material_id
        ).filter(
            WarehouseStock.quantity < RawMaterial.minimum_stock,
            RawMaterial.is_active == True,
            WarehouseStock.is_active == True
        ).all()

        low_stock_items = []
        for material, stock in results:
            low_stock_items.append({
                'raw_material_id': material.id,
                'raw_material_name': material.name,
                'current_stock': stock.quantity,
                'minimum_stock': material.minimum_stock,
                'difference': material.minimum_stock - stock.quantity,
                'unit': material.unit
            })

        return low_stock_items

    def get_total_stock_value(self) -> Decimal:
        """Umumiy qoldiq qiymati.

        Har bir xom-ashyo uchun oxirgi qabul narxi (unit_price) olinadi,
        keyin joriy qoldiq (quantity) ga ko'paytiriladi va yig'indisi hisoblanadi.

        Formula: SUM(stock.quantity * last_receipt.unit_price)
        """
        # 1-qadam: har bir raw_material uchun oxirgi receipt sanasini topamiz
        last_receipt_subquery = (
            self.db.query(
                WarehouseReceipt.raw_material_id,
                func.max(WarehouseReceipt.receipt_date).label("last_date")
            )
            .filter(WarehouseReceipt.is_active == True)
            .group_by(WarehouseReceipt.raw_material_id)
            .subquery()
        )

        # 2-qadam: o'sha sanaga mos unit_price ni olamiz
        last_price_subquery = (
            self.db.query(
                WarehouseReceipt.raw_material_id,
                WarehouseReceipt.unit_price.label("last_unit_price")
            )
            .join(
                last_receipt_subquery,
                and_(
                    WarehouseReceipt.raw_material_id == last_receipt_subquery.c.raw_material_id,
                    WarehouseReceipt.receipt_date == last_receipt_subquery.c.last_date
                )
            )
            .filter(WarehouseReceipt.is_active == True)
            .subquery()
        )

        # 3-qadam: stock.quantity * last_unit_price ni yig'amiz
        result = (
            self.db.query(
                func.sum(WarehouseStock.quantity * last_price_subquery.c.last_unit_price)
            )
            .join(
                last_price_subquery,
                WarehouseStock.raw_material_id == last_price_subquery.c.raw_material_id
            )
            .filter(WarehouseStock.is_active == True)
            .scalar()
        )

        return result or Decimal("0")


class MaterialRequestRepository(BaseRepository[MaterialRequest]):
    def __init__(self, db: Session):
        super().__init__(MaterialRequest, db)

    def get_with_relations(self, request_id: UUID) -> Optional[MaterialRequest]:
        """Relationships bilan so'rov"""
        return self.db.query(MaterialRequest).options(
            joinedload(MaterialRequest.raw_material),
            joinedload(MaterialRequest.requester),
            joinedload(MaterialRequest.approver)
        ).filter(
            MaterialRequest.id == request_id,
            MaterialRequest.is_active == True
        ).first()

    def get_all_with_relations(
            self,
            status: Optional[str] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[MaterialRequest]:
        """Barcha so'rovlar"""
        query = self.db.query(MaterialRequest).options(
            joinedload(MaterialRequest.raw_material),
            joinedload(MaterialRequest.requester),
            joinedload(MaterialRequest.approver)
        ).filter(MaterialRequest.is_active == True)

        if status:
            query = query.filter(MaterialRequest.request_status == status)

        return query.order_by(
            MaterialRequest.request_date.desc()
        ).offset(skip).limit(limit).all()

    def get_pending_count(self) -> int:
        """Kutilayotgan so'rovlar soni"""
        return self.db.query(func.count(MaterialRequest.id)).filter(
            MaterialRequest.request_status == RequestStatus.PENDING.value,
            MaterialRequest.is_active == True
        ).scalar()

    def get_by_user(
            self,
            user_id: UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[MaterialRequest]:
        """Foydalanuvchi so'rovlari"""
        return self.db.query(MaterialRequest).options(
            joinedload(MaterialRequest.raw_material)
        ).filter(
            MaterialRequest.requested_by == user_id,
            MaterialRequest.is_active == True
        ).order_by(
            MaterialRequest.request_date.desc()
        ).offset(skip).limit(limit).all()