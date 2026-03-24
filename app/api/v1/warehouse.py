from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.warehouse import (
    # Supplier
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    # Raw Material
    RawMaterialCreate,
    RawMaterialUpdate,
    RawMaterialResponse,
    # Receipt
    WarehouseReceiptCreate,
    WarehouseReceiptResponse,
    # Stock
    WarehouseStockResponse,
    LowStockItem,
    # Request
    MaterialRequestCreate,
    MaterialRequestApprove,
    MaterialRequestReject,
    MaterialRequestResponse,
    # Statistics
    WarehouseStatistics,
    # Production receipts
    ProductionGoodsReceiptResponse
)
from app.services.warehouse_service import WarehouseService
from app.dependencies import get_current_user, require_permission, require_admin
from app.models.user import User
from app.core.constants import PermissionType

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])


# ============ SUPPLIER ENDPOINTS ============

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
        supplier_data: SupplierCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_WAREHOUSE))
):
    """
    Yangi yetkazib beruvchi qo'shish

    Faqat warehouse_manager va superadmin ruxsat berilgan.
    """
    service = WarehouseService(db)
    return service.create_supplier(supplier_data)


@router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Barcha yetkazib beruvchilar ro'yxati"""
    service = WarehouseService(db)
    return service.get_all_suppliers(skip=skip, limit=limit)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
        supplier_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Bitta yetkazib beruvchi ma'lumotlari"""
    service = WarehouseService(db)
    return service.get_supplier(supplier_id)


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
        supplier_id: UUID,
        supplier_data: SupplierUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_WAREHOUSE))
):
    """Yetkazib beruvchi ma'lumotlarini yangilash"""
    service = WarehouseService(db)
    return service.update_supplier(supplier_id, supplier_data)


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_200_OK)
async def delete_supplier(
        supplier_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Yetkazib beruvchini o'chirish"""
    service = WarehouseService(db)
    service.delete_supplier(supplier_id)
    return {"message": "Yetkazib beruvchi o'chirildi"}


# ============ RAW MATERIAL ENDPOINTS ============

@router.post("/raw-materials", response_model=RawMaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_raw_material(
        material_data: RawMaterialCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_WAREHOUSE))
):
    """Yangi xom-ashyo qo'shish"""
    service = WarehouseService(db)
    return service.create_raw_material(material_data)


@router.get("/raw-materials", response_model=List[RawMaterialResponse])
async def get_raw_materials(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Xom-ashyo katalogi"""
    service = WarehouseService(db)
    materials = service.get_all_raw_materials(skip=skip, limit=limit)

    # Current stock qo'shish
    for material in materials:
        if material.warehouse_stock:
            material.current_stock = material.warehouse_stock.quantity

    return materials


@router.get("/raw-materials/{material_id}", response_model=RawMaterialResponse)
async def get_raw_material(
        material_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Bitta xom-ashyo ma'lumotlari"""
    service = WarehouseService(db)
    return service.get_raw_material(material_id)


@router.put("/raw-materials/{material_id}", response_model=RawMaterialResponse)
async def update_raw_material(
        material_id: UUID,
        material_data: RawMaterialUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_WAREHOUSE))
):
    """Xom-ashyo ma'lumotlarini yangilash"""
    service = WarehouseService(db)
    return service.update_raw_material(material_id, material_data)


@router.delete("/raw-materials/{material_id}", status_code=status.HTTP_200_OK)
async def delete_raw_material(
        material_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Xom-ashyoni o'chirish"""
    service = WarehouseService(db)
    service.delete_raw_material(material_id)
    return {"message": "Xom-ashyo o'chirildi"}


# ============ RECEIPT ENDPOINTS ============

@router.post("/receipts", response_model=WarehouseReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
        receipt_data: WarehouseReceiptCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_WAREHOUSE))
):
    """
    Xom-ashyo qabul qilish

    Yetkazib beruvchidan xom-ashyo qabul qilib, omborga kiritish.
    """
    service = WarehouseService(db)
    return service.create_receipt(receipt_data, current_user.id)


@router.get("/receipts", response_model=List[WarehouseReceiptResponse])
async def get_receipts(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Qabul qilishlar tarixi"""
    service = WarehouseService(db)
    return service.get_all_receipts(skip=skip, limit=limit)


@router.get("/receipts/{receipt_id}", response_model=WarehouseReceiptResponse)
async def get_receipt(
        receipt_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Bitta qabul qilish ma'lumotlari"""
    service = WarehouseService(db)
    return service.get_receipt(receipt_id)


@router.delete("/receipts/{receipt_id}", status_code=status.HTTP_200_OK)
async def delete_receipt(
        receipt_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Qabul qilishni o'chirish (faqat admin)"""
    service = WarehouseService(db)
    service.delete_receipt(receipt_id)
    return {"message": "Qabul qilish o'chirildi"}


# ============ STOCK ENDPOINTS ============

@router.get("/stock", response_model=List[WarehouseStockResponse])
async def get_stock(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Ombor qoldiqlari"""
    service = WarehouseService(db)
    return service.get_all_stock(skip=skip, limit=limit)


@router.get("/stock/{material_id}", response_model=WarehouseStockResponse)
async def get_stock_by_material(
        material_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Bitta xom-ashyo qoldig'i"""
    service = WarehouseService(db)
    return service.get_stock_by_material(material_id)


@router.get("/low-stock", response_model=List[LowStockItem])
async def get_low_stock(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Kam qoldiqlar ro'yxati"""
    service = WarehouseService(db)
    return service.get_low_stock_items()


# ============ MATERIAL REQUEST ENDPOINTS ============

@router.post("/requests", response_model=MaterialRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_material_request(
        request_data: MaterialRequestCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Xom-ashyo so'rovi yuborish

    Operator ishlab chiqarish uchun xom-ashyo so'raydi.
    """
    service = WarehouseService(db)
    return service.create_material_request(request_data, current_user.id)


@router.get("/requests", response_model=List[MaterialRequestResponse])
async def get_material_requests(
        status: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Xom-ashyo so'rovlari ro'yxati"""
    service = WarehouseService(db)
    return service.get_all_material_requests(status=status, skip=skip, limit=limit)


@router.get("/requests/my", response_model=List[MaterialRequestResponse])
async def get_my_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Mening so'rovlarim"""
    service = WarehouseService(db)
    return service.get_my_requests(current_user.id, skip=skip, limit=limit)


@router.get("/requests/{request_id}", response_model=MaterialRequestResponse)
async def get_material_request(
        request_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Bitta so'rov ma'lumotlari"""
    service = WarehouseService(db)
    return service.get_material_request(request_id)


@router.delete("/requests/{request_id}", status_code=status.HTTP_200_OK)
async def delete_material_request(
        request_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """Material so'rovini o'chirish (faqat admin)"""
    service = WarehouseService(db)
    service.delete_material_request(request_id)
    return {"message": "So'rov o'chirildi"}


@router.put("/requests/{request_id}/approve", response_model=MaterialRequestResponse)
async def approve_request(
        request_id: UUID,
        approve_data: MaterialRequestApprove,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.APPROVE_MATERIAL_REQUEST))
):
    """
    So'rovni tasdiqlash

    Faqat warehouse_manager tasdiqlashi mumkin.
    """
    service = WarehouseService(db)
    return service.approve_material_request(request_id, approve_data, current_user.id)


@router.put("/requests/{request_id}/reject", response_model=MaterialRequestResponse)
async def reject_request(
        request_id: UUID,
        reject_data: MaterialRequestReject,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.APPROVE_MATERIAL_REQUEST))
):
    """
    So'rovni rad etish

    Faqat warehouse_manager rad etishi mumkin.
    """
    service = WarehouseService(db)
    return service.reject_material_request(request_id, reject_data, current_user.id)


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=WarehouseStatistics)
async def get_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Ombor statistikasi"""
    service = WarehouseService(db)
    return service.get_statistics()


# ============ PRODUCTION GOODS RECEIPTS ============

@router.get("/production-receipts")
async def get_production_receipts(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        page: int = Query(1, ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """Ishlab chiqarishdan kelgan tayyor mahsulotlar qabuli"""
    from sqlalchemy import desc
    from app.models.warehouse import ProductionGoodsReceipt
    from app.models.production import FinishedProduct, Shift

    actual_skip = (page - 1) * limit if page > 1 else skip
    rows = (
        db.query(ProductionGoodsReceipt)
        .filter(ProductionGoodsReceipt.is_active == True)
        .order_by(desc(ProductionGoodsReceipt.received_at))
        .offset(actual_skip).limit(limit).all()
    )
    total = db.query(ProductionGoodsReceipt).filter(ProductionGoodsReceipt.is_active == True).count()

    result = []
    for r in rows:
        product = db.query(FinishedProduct).filter(FinishedProduct.id == r.finished_product_id).first()
        result.append({
            "id": str(r.id),
            "finished_product_id": str(r.finished_product_id),
            "shift_id": str(r.shift_id) if r.shift_id else None,
            "quantity": float(r.quantity),
            "status": r.status,
            "received_at": r.received_at,
            "notes": r.notes,
            "finished_product": {"id": str(product.id), "name": product.name, "unit": product.unit} if product else None,
        })

    return {"items": result, "total": total, "page": page, "limit": limit}