from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from app.utils.datetime_utils import get_now
from uuid import UUID
from app.models.sales import Customer, Order, OrderItem, Payment
from app.schemas.sales import (
    CustomerCreate,
    CustomerUpdate,
    OrderCreate,
    OrderUpdate,
    PaymentCreate,
    SalesStatistics,
    CustomerStatistics
)
from app.repositories.sales_repository import (
    CustomerRepository,
    OrderRepository,
    OrderItemRepository,
    PaymentRepository
)
from app.repositories.production_repository import FinishedProductStockRepository
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    InsufficientStockException
)


class SalesService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.finished_stock_repo = FinishedProductStockRepository(db)

    # ============ CUSTOMER METHODS ============

    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Yangi mijoz yaratish"""
        # Telefon bo'yicha tekshirish
        existing = self.customer_repo.get_by_phone(customer_data.phone)
        if existing:
            raise ConflictException(detail=f"'{customer_data.phone}' telefon raqami bilan mijoz mavjud")

        # INN bo'yicha tekshirish
        if customer_data.inn:
            existing_inn = self.customer_repo.get_by_inn(customer_data.inn)
            if existing_inn:
                raise ConflictException(detail=f"'{customer_data.inn}' INN bilan mijoz mavjud")

        new_customer = Customer(**customer_data.model_dump())
        return self.customer_repo.create(new_customer)

    def get_customer(self, customer_id: UUID) -> Customer:
        """Mijoz olish"""
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundException(detail="Mijoz topilmadi")
        return customer

    def get_all_customers(self, skip: int = 0, limit: int = 100):
        """Barcha mijozlar — total_orders va total_spent bilan"""
        try:
            customers = self.customer_repo.get_all_with_stats(skip=skip, limit=limit)
            total = self.customer_repo.count_all()
        except Exception:
            # Fallback: oddiy ro'yxat
            customers_orm = self.customer_repo.get_all(skip=skip, limit=limit)
            customers = [
                {
                    "id": str(c.id), "name": c.name, "phone": c.phone,
                    "email": c.email, "inn": c.inn, "address": c.address,
                    "contact_person": c.contact_person, "customer_type": c.customer_type,
                    "is_active": c.is_active, "created_at": c.created_at,
                    "updated_at": c.updated_at, "total_orders": 0, "total_spent": 0,
                }
                for c in customers_orm
            ]
            total = self.customer_repo.count()
        return {"customers": customers, "total": total}

    def update_customer(self, customer_id: UUID, customer_data: CustomerUpdate) -> Customer:
        """Mijoz yangilash"""
        customer = self.get_customer(customer_id)

        # Telefon o'zgargan bo'lsa tekshirish
        if customer_data.phone and customer_data.phone != customer.phone:
            existing = self.customer_repo.get_by_phone(customer_data.phone)
            if existing:
                raise ConflictException(detail=f"'{customer_data.phone}' telefon raqami bilan mijoz mavjud")

        update_data = customer_data.model_dump(exclude_unset=True)
        return self.customer_repo.update(customer, update_data)

    def delete_customer(self, customer_id: UUID) -> bool:
        """Mijoz o'chirish"""
        return self.customer_repo.delete(customer_id)

    def get_customer_statistics(self, customer_id: UUID) -> CustomerStatistics:
        """Mijoz statistikasi"""
        stats = self.customer_repo.get_with_statistics(customer_id)
        if not stats:
            raise NotFoundException(detail="Mijoz topilmadi")

        customer = stats["customer"]

        # To'langan va to'lanmagan summa
        orders = self.order_repo.get_by_customer(customer_id, skip=0, limit=1000)
        total_paid = sum(order.paid_amount for order in orders)
        total_unpaid = stats["total_spent"] - total_paid

        # Oxirgi buyurtma sanasi
        last_order_date = None
        if orders:
            last_order_date = orders[0].order_date

        return CustomerStatistics(
            customer_id=customer.id,
            customer_name=customer.name,
            total_orders=stats["total_orders"],
            total_spent=stats["total_spent"],
            total_paid=total_paid,
            total_unpaid=total_unpaid,
            last_order_date=last_order_date
        )

    # ============ ORDER METHODS ============

    def create_order(self, order_data: OrderCreate, user_id: UUID) -> Order:
        """Yangi buyurtma yaratish"""
        # Mijoz tekshirish
        customer = self.get_customer(order_data.customer_id)

        # ✅ Avval stock tekshirish (order yaratishdan oldin)
        for item_data in order_data.items:
            stock = self.finished_stock_repo.get_by_product(item_data.finished_product_id)
            if not stock or stock.quantity_available < item_data.quantity:
                raise InsufficientStockException(
                    detail=f"Mahsulot omborda yetarli emas. Mavjud: {stock.quantity_available if stock else 0}"
                )

        # Total amount hisoblash
        total_amount = Decimal("0")
        for item in order_data.items:
            item_total = item.quantity * item.unit_price
            total_amount += item_total

        # Order yaratish
        new_order = Order(
            customer_id=order_data.customer_id,
            order_date=order_data.order_date,
            total_amount=total_amount,
            paid_amount=Decimal("0"),
            payment_status='unpaid',
            delivery_status='pending',
            delivery_address=order_data.delivery_address,
            delivery_date=order_data.delivery_date,
            notes=order_data.notes,
            created_by=user_id
        )
        order = self.order_repo.create(new_order)

        # Order items yaratish va stock rezerv qilish
        for item_data in order_data.items:
            item_total = item_data.quantity * item_data.unit_price
            order_item = OrderItem(
                order_id=order.id,
                finished_product_id=item_data.finished_product_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=item_total
            )
            self.order_item_repo.create(order_item)
            self._reserve_stock(item_data.finished_product_id, item_data.quantity)

        self.db.commit()
        self.db.refresh(order)

        # Bildirishnoma yuborish
        try:
            from app.services.notification_service import NotificationService
            notif_service = NotificationService(self.db)
            notif_service.notify_new_order(
                customer_name=customer.name,
                total_amount=float(total_amount),
                order_id=order.id
            )
        except Exception:
            pass

        return order

    def get_order(self, order_id: UUID) -> Order:
        """Buyurtma olish"""
        order = self.order_repo.get_with_relations(order_id)
        if not order:
            raise NotFoundException(detail="Buyurtma topilmadi")
        return order

    def get_all_orders(
            self,
            skip: int = 0,
            limit: int = 100,
            payment_status: Optional[str] = None,
            delivery_status: Optional[str] = None
    ) -> List[Order]:
        """Barcha buyurtmalar"""
        return self.order_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            payment_status=payment_status,
            delivery_status=delivery_status
        )

    def get_customer_orders(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        """Mijoz buyurtmalari"""
        return self.order_repo.get_by_customer(customer_id, skip=skip, limit=limit)

    def update_order(self, order_id: UUID, order_data: OrderUpdate) -> Order:
        """Buyurtma yangilash"""
        order = self.get_order(order_id)

        # Delivery status o'zgarsa
        if order_data.delivery_status and order_data.delivery_status != order.delivery_status:
            if order_data.delivery_status == 'delivered':
                # Stockdan rezervni olib, realga aylantirish
                self._fulfill_order(order_id)
            elif order_data.delivery_status == 'cancelled':
                # Rezervni bekor qilish
                self._cancel_order_reservation(order_id)

        update_data = order_data.model_dump(exclude_unset=True)
        return self.order_repo.update(order, update_data)

    def delete_order(self, order_id: UUID) -> bool:
        """Buyurtma bekor qilish"""
        order = self.get_order(order_id)

        # Stockdan rezervni qaytarish
        self._cancel_order_reservation(order_id)

        return self.order_repo.delete(order_id)

    # ============ PAYMENT METHODS ============

    def create_payment(self, payment_data: PaymentCreate, user_id: UUID) -> Payment:
        """To'lov qo'shish"""
        # Order tekshirish
        order = self.get_order(payment_data.order_id)

        # To'lov summasi orderdan oshmasligini tekshirish
        remaining = order.total_amount - order.paid_amount
        if payment_data.amount > remaining:
            raise BadRequestException(
                detail=f"To'lov summasi qolgan qarzdan oshib ketmoqda. Qolgan: {remaining}"
            )

        # Auto transaction_id generatsiya
        if not payment_data.transaction_id:
            last = self.db.query(Payment).filter(
                Payment.transaction_id.like('SPX-%')
            ).order_by(Payment.transaction_id.desc()).first()
            if last and last.transaction_id:
                try:
                    last_num = int(last.transaction_id.split('-')[1])
                    next_num = last_num + 1
                except (IndexError, ValueError):
                    next_num = 1
            else:
                next_num = 1
            auto_txn_id = f"SPX-{next_num:010d}"
        else:
            auto_txn_id = payment_data.transaction_id

        # Payment yaratish
        new_payment = Payment(
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            payment_date=payment_data.payment_date,
            payment_method=payment_data.payment_method,
            transaction_id=auto_txn_id,
            notes=payment_data.notes,
            received_by=user_id
        )
        payment = self.payment_repo.create(new_payment)

        # Order paid_amount yangilash
        order.paid_amount += payment_data.amount

        # Payment status yangilash
        if order.paid_amount >= order.total_amount:
            order.payment_status = 'paid'
        elif order.paid_amount > 0:
            order.payment_status = 'partial'

        self.db.commit()

        # ✅ Moliya — avtomatik tranzaksiya yaratish
        try:
            from app.services.finance_service import FinanceService
            finance_service = FinanceService(self.db)
            finance_service.create_automatic_transaction(
                transaction_type="income",
                amount=payment_data.amount,
                category_name="Sotuv daromadi",
                description=f"Sotuv to'lovi — Order #{payment.order_id}",
                reference_type="sales_payment",
                reference_id=payment.id,
                user_id=user_id
            )
        except Exception:
            pass  # Moliya xatosi asosiy to'lovni bloklamasin

        return payment

    def get_order_payments(self, order_id: UUID) -> List[Payment]:
        """Buyurtma to'lovlari"""
        return self.payment_repo.get_by_order(order_id)

    def delete_payment(self, payment_id: UUID) -> bool:
        """To'lovni o'chirish"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(detail="To'lov topilmadi")
        return self.payment_repo.delete(payment_id)

    # ============ STATISTICS METHODS ============

    def get_sales_statistics(self) -> SalesStatistics:
        """Sotuv statistikasi"""
        total_customers = self.customer_repo.count()
        total_orders = self.order_repo.count()
        total_revenue = self.order_repo.get_total_revenue()
        total_paid = self.order_repo.get_total_paid()
        total_unpaid = total_revenue - total_paid
        pending_orders = self.order_repo.get_pending_count()
        completed_today = self.order_repo.get_completed_today()
        revenue_today = self.order_repo.get_revenue_today()

        return SalesStatistics(
            total_customers=total_customers,
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_paid=total_paid,
            total_unpaid=total_unpaid,
            pending_orders=pending_orders,
            completed_orders_today=completed_today,
            revenue_today=revenue_today,
            top_customers=[],  # TODO: Implement
            top_products=[]  # TODO: Implement
        )

    # ============ PRIVATE HELPER METHODS ============

    def _reserve_stock(self, product_id: UUID, quantity: Decimal):
        """Mahsulot rezerv qilish"""
        stock = self.finished_stock_repo.get_by_product(product_id)

        if not stock or stock.quantity_available < quantity:
            raise InsufficientStockException(detail="Mahsulot yetarli emas")

        stock.quantity_available -= quantity
        stock.quantity_reserved += quantity
        stock.last_updated = get_now()
        self.db.commit()

    def _fulfill_order(self, order_id: UUID):
        """Buyurtmani yetkazish (rezervdan realga)"""
        items = self.order_item_repo.get_by_order(order_id)

        for item in items:
            stock = self.finished_stock_repo.get_by_product(item.finished_product_id)

            if stock:
                # Rezervdan total'ga o'tkazish
                stock.quantity_reserved -= item.quantity
                stock.quantity_total -= item.quantity
                stock.last_updated = get_now()

        self.db.commit()

    def _cancel_order_reservation(self, order_id: UUID):
        """Buyurtma rezervini bekor qilish"""
        items = self.order_item_repo.get_by_order(order_id)

        for item in items:
            stock = self.finished_stock_repo.get_by_product(item.finished_product_id)

            if stock:
                # Rezervni qaytarish
                stock.quantity_reserved -= item.quantity
                stock.quantity_available += item.quantity
                stock.last_updated = get_now()

        self.db.commit()