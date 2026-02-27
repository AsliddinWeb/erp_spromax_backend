from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.exceptions import NotFoundException
from app.database import get_db
from app.schemas.production import (
    # Production Line
    ProductionLineCreate,
    ProductionLineUpdate,
    ProductionLineResponse,
    # Machine
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    # Finished Product
    FinishedProductCreate,
    FinishedProductUpdate,
    FinishedProductResponse,
    # Shift
    ShiftCreate,
    ShiftComplete,
    ShiftResponse,
    ShiftCompleteRequest,

    # Production Record
    ProductionRecordCreate,
    ProductionRecordResponse,
    # Production Output
    ProductionOutputCreate,
    ProductionOutputResponse,
    # Defect
    DefectReasonCreate,
    DefectReasonUpdate,
    DefectReasonResponse,
    DefectiveProductCreate,
    DefectiveProductResponse,
    # Handover
    ShiftHandoverCreate,
    ShiftHandoverResponse,
    # Statistics
    ShiftStatistics,
    ProductionStatistics,
    FinishedProductStockResponse,
    # NEW: Pause, Scrap, Close
    ShiftPauseCreate,
    ShiftPauseResponse,
    ShiftScrapUsageCreate,
    ShiftScrapUsageResponse,
    ScrapStockResponse,
    ScrapStockTransactionResponse,
    ScrapTransferCreate,
    ShiftCloseRequest,
)
from app.services.production_service import ProductionService
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.core.constants import PermissionType

# Machine model
from app.models.production import Machine

router = APIRouter(prefix="/production", tags=["Production"])


# ============ PRODUCTION LINE ENDPOINTS ============

@router.post("/lines", response_model=ProductionLineResponse, status_code=status.HTTP_201_CREATED)
async def create_production_line(
        line_data: ProductionLineCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Yangi ishlab chiqarish liniyasi yaratish"""
    service = ProductionService(db)
    return service.create_production_line(line_data)


@router.get("/lines", response_model=List[ProductionLineResponse])
async def get_production_lines(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        include_inactive: bool = Query(False),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    service = ProductionService(db)
    return service.get_all_production_lines(skip=skip, limit=limit, include_inactive=include_inactive)


@router.get("/lines/{line_id}", response_model=ProductionLineResponse)
async def get_production_line(
        line_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Bitta liniya ma'lumotlari"""
    service = ProductionService(db)
    return service.get_production_line(line_id)


@router.put("/lines/{line_id}", response_model=ProductionLineResponse)
async def update_production_line(
        line_id: UUID,
        line_data: ProductionLineUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Liniya yangilash"""
    service = ProductionService(db)
    return service.update_production_line(line_id, line_data)


@router.delete("/lines/{line_id}", status_code=status.HTTP_200_OK)
async def delete_production_line(
        line_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Liniya o'chirish"""
    service = ProductionService(db)
    service.delete_production_line(line_id)
    return {"message": "Liniya o'chirildi"}


# ============ MACHINE ENDPOINTS ============

@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
        machine_data: MachineCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Yangi mashina qo'shish"""
    service = ProductionService(db)
    return service.create_machine(machine_data)


@router.get("/machines", response_model=List[MachineResponse])
async def get_machines(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        include_inactive: bool = Query(False),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Barcha mashinalar"""
    service = ProductionService(db)
    return service.get_all_machines(skip=skip, limit=limit, include_inactive=include_inactive)


@router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(
        machine_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Bitta mashina ma'lumotlari"""
    service = ProductionService(db)
    return service.get_machine(machine_id)


# @router.put("/machines/{machine_id}", response_model=MachineResponse)
# async def update_machine(
#     machine_id: UUID,
#     machine_data: MachineUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
# ):
#     """Mashina yangilash"""
#     service = ProductionService(db)
#     return service.update_machine(machine_id, machine_data)

@router.put("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(
        machine_id: UUID,
        machine_data: MachineUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Mashina yangilash"""
    service = ProductionService(db)
    return service.update_machine(machine_id, machine_data)


@router.delete("/machines/{machine_id}", status_code=status.HTTP_200_OK)
async def delete_machine(
        machine_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Mashina o'chirish"""
    service = ProductionService(db)
    service.delete_machine(machine_id)
    return {"message": "Mashina o'chirildi"}


# ============ FINISHED PRODUCT ENDPOINTS ============

@router.post("/finished-products", response_model=FinishedProductResponse, status_code=status.HTTP_201_CREATED)
async def create_finished_product(
        product_data: FinishedProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Yangi tayyor mahsulot qo'shish"""
    service = ProductionService(db)
    return service.create_finished_product(product_data)


@router.get("/finished-products", response_model=List[FinishedProductResponse])
async def get_finished_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Tayyor mahsulotlar katalogi"""
    service = ProductionService(db)
    products = service.get_all_finished_products(skip=skip, limit=limit)

    # Current stock qo'shish
    for product in products:
        if product.finished_product_stock:
            product.current_stock = product.finished_product_stock.quantity_total

    return products


@router.get("/finished-products/{product_id}", response_model=FinishedProductResponse)
async def get_finished_product(
        product_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Bitta tayyor mahsulot"""
    service = ProductionService(db)
    return service.get_finished_product(product_id)


@router.put("/finished-products/{product_id}", response_model=FinishedProductResponse)
async def update_finished_product(
        product_id: UUID,
        product_data: FinishedProductUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Tayyor mahsulot yangilash"""
    service = ProductionService(db)
    return service.update_finished_product(product_id, product_data)


@router.delete("/finished-products/{product_id}", status_code=status.HTTP_200_OK)
async def delete_finished_product(
        product_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Tayyor mahsulot o'chirish"""
    service = ProductionService(db)
    service.delete_finished_product(product_id)
    return {"message": "Mahsulot o'chirildi"}


# ============ SHIFT ENDPOINTS ============

@router.post("/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
        shift_data: ShiftCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Yangi smena boshlash

    Operator smena boshlaganda ishlaydigan mashinalarni belgilaydi.
    """
    service = ProductionService(db)
    return service.create_shift(shift_data, current_user.id)


@router.get("/shifts", response_model=List[ShiftResponse])
async def get_shifts(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Barcha smenalar"""
    service = ProductionService(db)
    return service.get_all_shifts(skip=skip, limit=limit)


@router.get("/shifts/my", response_model=List[ShiftResponse])
async def get_my_shifts(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Mening smenalarim"""
    service = ProductionService(db)
    return service.get_my_shifts(current_user.id, skip=skip, limit=limit)


@router.get("/shifts/{shift_id}", response_model=ShiftResponse)
async def get_shift(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Bitta smena ma'lumotlari"""
    service = ProductionService(db)
    return service.get_shift(shift_id)


@router.put("/shifts/{shift_id}/complete", response_model=ShiftResponse)
async def complete_shift(
        shift_id: UUID,
        body: ShiftCompleteRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Smenani yakunlash

    Smena tugaganda handover (topshirish) ma'lumotlari bilan yakunlanadi.
    """
    service = ProductionService(db)
    return service.complete_shift(shift_id, body.complete_data, body.handover_data)


# ============ PRODUCTION RECORD ENDPOINTS ============

@router.post("/shifts/{shift_id}/records/materials", response_model=ProductionRecordResponse,
             status_code=status.HTTP_201_CREATED)
async def record_material_usage(
        shift_id: UUID,
        record_data: ProductionRecordCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Xom-ashyo ishlatishni yozish

    Operator ishlab chiqarish jarayonida qancha xom-ashyo ishlatganini yozadi.
    """
    service = ProductionService(db)
    return service.record_material_usage(shift_id, record_data)


@router.get("/shifts/{shift_id}/records/materials", response_model=List[ProductionRecordResponse])
async def get_shift_material_usage(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Smena xom-ashyo ishlatish tarixi"""
    service = ProductionService(db)
    return service.get_shift_material_usage(shift_id)


# ============ PRODUCTION OUTPUT ENDPOINTS ============

@router.post("/shifts/{shift_id}/records/output", response_model=ProductionOutputResponse,
             status_code=status.HTTP_201_CREATED)
async def record_production_output(
        shift_id: UUID,
        output_data: ProductionOutputCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Ishlab chiqarishni yozish

    Operator qancha tayyor mahsulot ishlab chiqarganini yozadi.
    """
    service = ProductionService(db)
    return service.record_production_output(shift_id, output_data)


@router.get("/shifts/{shift_id}/records/output", response_model=List[ProductionOutputResponse])
async def get_shift_production_output(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Smena ishlab chiqarish tarixi"""
    service = ProductionService(db)
    return service.get_shift_production_output(shift_id)


# ============ DEFECT ENDPOINTS ============

@router.post("/defect-reasons", response_model=DefectReasonResponse, status_code=status.HTTP_201_CREATED)
async def create_defect_reason(
        reason_data: DefectReasonCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Yangi brak sababi qo'shish"""
    service = ProductionService(db)
    return service.create_defect_reason(reason_data)


@router.get("/defect-reasons", response_model=List[DefectReasonResponse])
async def get_defect_reasons(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Brak sabablari ro'yxati"""
    service = ProductionService(db)
    return service.get_all_defect_reasons(skip=skip, limit=limit)


@router.post("/shifts/{shift_id}/records/defects", response_model=DefectiveProductResponse,
             status_code=status.HTTP_201_CREATED)
async def record_defective_product(
        shift_id: UUID,
        defect_data: DefectiveProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Brak yozish

    Operator yaroqsiz mahsulot (brak) topilganda yozadi.
    """
    service = ProductionService(db)
    return service.record_defective_product(shift_id, defect_data)


@router.get("/shifts/{shift_id}/records/defects", response_model=List[DefectiveProductResponse])
async def get_shift_defects(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Smena braklari"""
    service = ProductionService(db)
    return service.get_shift_defects(shift_id)


# ============ STATISTICS ENDPOINTS ============

@router.get("/shifts/{shift_id}/statistics", response_model=ShiftStatistics)
async def get_shift_statistics(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Smena statistikasi

    Smenaning samaradorligi, brak darajasi va boshqa ko'rsatkichlar.
    """
    service = ProductionService(db)
    return service.get_shift_statistics(shift_id)


@router.get("/statistics", response_model=ProductionStatistics)
async def get_production_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Umumiy ishlab chiqarish statistikasi"""
    service = ProductionService(db)
    return service.get_production_statistics()


# ============ SHIFT PAUSE ENDPOINTS ============

@router.post("/shifts/{shift_id}/pause", response_model=ShiftPauseResponse)
async def pause_shift(
        shift_id: UUID,
        data: ShiftPauseCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Smenani to'xtatish (mashina buzildi, tushlik, boshqa)"""
    service = ProductionService(db)
    return service.pause_shift(shift_id, data)


@router.post("/shifts/{shift_id}/resume", response_model=ShiftPauseResponse)
async def resume_shift(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Smenani davom ettirish"""
    service = ProductionService(db)
    return service.resume_shift(shift_id)


@router.get("/shifts/{shift_id}/pauses", response_model=List[ShiftPauseResponse])
async def get_shift_pauses(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Smena pauzalari ro'yxati"""
    service = ProductionService(db)
    return service.get_shift_pauses(shift_id)


# ============ SHIFT SCRAP USAGE ENDPOINTS ============

@router.post("/shifts/{shift_id}/scrap-usage", response_model=ShiftScrapUsageResponse,
             status_code=status.HTTP_201_CREATED)
async def use_scrap_in_shift(
        shift_id: UUID,
        data: ShiftScrapUsageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """Smena davomida atxot skladdan material olish"""
    service = ProductionService(db)
    return service.use_scrap_in_shift(shift_id, data)


@router.get("/shifts/{shift_id}/scrap-usage", response_model=List[ShiftScrapUsageResponse])
async def get_shift_scrap_usage(
        shift_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Smena atxot foydalanish tarixi"""
    service = ProductionService(db)
    return service.get_shift_scrap_usage(shift_id)


# ============ SHIFT CLOSE (yangilangan) ============

@router.post("/shifts/{shift_id}/close", response_model=ShiftResponse)
async def close_shift(
        shift_id: UUID,
        data: ShiftCloseRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Smenani yopish — bir so'rovda tayyor mahsulot va atxot kiritish.
    - outputs: ishlab chiqarilgan mahsulotlar → tayyor mahsulot skladga
    - scraps: atxot mahsulotlar → atxot mini skladga
    """
    service = ProductionService(db)
    return service.close_shift(shift_id, data)


# ============ FINISHED PRODUCT STOCK ENDPOINTS ============

@router.get("/finished-stock", response_model=List[FinishedProductStockResponse])
async def get_finished_stock(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Tayyor mahsulot ombori — barcha qoldiqlar"""
    service = ProductionService(db)
    return service.get_all_finished_stock()


# ============ SCRAP STOCK ENDPOINTS ============

@router.get("/scrap-stock", response_model=List[ScrapStockResponse])
async def get_scrap_stock(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Atxot mini sklad — barcha qoldiqlar"""
    service = ProductionService(db)
    return service.get_all_scrap_stock()


@router.get("/scrap-stock/transactions", response_model=List[ScrapStockTransactionResponse])
async def get_scrap_transactions(
        product_id: Optional[UUID] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """Atxot sklad harakatlari tarixi"""
    service = ProductionService(db)
    return service.get_scrap_transactions(product_id)


@router.post("/scrap-stock/transfer-to-grinder")
async def transfer_scrap_to_grinder(
        data: ScrapTransferCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_PRODUCTION))
):
    """
    Atxotni tegirmonga o'tkazish.
    Tegirmon atxotni qayta ishlab, uni yana ishlab chiqarishda ishlatish mumkin.
    """
    service = ProductionService(db)
    return service.transfer_scrap_to_grinder(data)