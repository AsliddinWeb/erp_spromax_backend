from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import datetime, date
from decimal import Decimal
from app.utils.datetime_utils import get_today_start, get_month_start
from uuid import UUID
from app.models.sales import Customer, Order, OrderItem, Payment
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        """Telefon bo'yicha mijoz topish"""
        return self.db.query(Customer).filter(
            Customer.phone == phone,
            Customer.is_active == True
        ).first()

    def get_by_inn(self, inn: str) -> Optional[Customer]:
        """INN bo'yicha mijoz topish"""
        return self.db.query(Customer).filter(
            Customer.inn == inn,
            Customer.is_active == True
        ).first()

    def get_all_with_stats(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Barcha mijozlar total_orders va total_spent bilan"""
        from sqlalchemy import outerjoin

        order_stats = (
            self.db.query(
                Order.customer_id,
                func.count(Order.id).label("total_orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
                func.max(Order.created_at).label("last_order_date"),
            )
            .filter(Order.is_active == True)
            .group_by(Order.customer_id)
            .subquery()
        )

        rows = (
            self.db.query(
                Customer,
                func.coalesce(order_stats.c.total_orders, 0).label("total_orders"),
                func.coalesce(order_stats.c.total_spent, 0).label("total_spent"),
                order_stats.c.last_order_date,
            )
            .outerjoin(order_stats, Customer.id == order_stats.c.customer_id)
            .order_by(desc(order_stats.c.total_spent.is_(None)), desc(order_stats.c.total_spent))
            .offset(skip)
            .limit(limit)
            .all()
        )

        customers = []
        for row in rows:
            customer = row[0]
            # dict sifatida qaytaramiz — SQLAlchemy serialize muammosini oldini olish
            customers.append({
                "id": str(customer.id),
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "inn": customer.inn,
                "address": customer.address,
                "contact_person": customer.contact_person,
                "customer_type": customer.customer_type,
                "is_active": customer.is_active,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
                "total_orders": int(row[1] or 0),
                "total_spent": Decimal(str(row[2] or 0)),
            })
        return customers

    def count_all(self) -> int:
        return self.db.query(func.count(Customer.id)).scalar() or 0

    def get_with_statistics(self, customer_id: UUID) -> Optional[dict]:
        """Mijoz statistikasi bilan"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return None

        total_orders = self.db.query(func.count(Order.id)).filter(
            Order.customer_id == customer_id,
            Order.is_active == True
        ).scalar()

        total_spent = self.db.query(func.sum(Order.total_amount)).filter(
            Order.customer_id == customer_id,
            Order.is_active == True
        ).scalar() or Decimal("0")

        return {
            "customer": customer,
            "total_orders": total_orders,
            "total_spent": total_spent
        }


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def get_with_relations(self, order_id: UUID) -> Optional[Order]:
        """Barcha relationship bilan order"""
        return self.db.query(Order).options(
            joinedload(Order.customer),
            joinedload(Order.creator),
            joinedload(Order.order_items).joinedload(OrderItem.finished_product)
        ).filter(
            Order.id == order_id,
            Order.is_active == True
        ).first()

    def get_all_with_relations(
            self,
            skip: int = 0,
            limit: int = 100,
            payment_status: Optional[str] = None,
            delivery_status: Optional[str] = None
    ) -> List[Order]:
        """Barcha orderlar"""
        query = self.db.query(Order).options(
            joinedload(Order.customer),
            joinedload(Order.order_items)
        ).filter(Order.is_active == True)

        if payment_status:
            query = query.filter(Order.payment_status == payment_status)

        if delivery_status:
            query = query.filter(Order.delivery_status == delivery_status)

        return query.order_by(desc(Order.order_date)).offset(skip).limit(limit).all()

    def get_by_customer(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        """Mijoz buyurtmalari"""
        return self.db.query(Order).options(
            joinedload(Order.order_items)
        ).filter(
            Order.customer_id == customer_id,
            Order.is_active == True
        ).order_by(desc(Order.order_date)).offset(skip).limit(limit).all()

    def get_pending_count(self) -> int:
        """Kutilayotgan buyurtmalar soni"""
        return self.db.query(func.count(Order.id)).filter(
            Order.delivery_status == 'pending',
            Order.is_active == True
        ).scalar()

    def get_completed_today(self) -> int:
        """Bugun yetkazilgan buyurtmalar"""
        today_start = get_today_start()

        return self.db.query(func.count(Order.id)).filter(
            Order.delivery_status == 'delivered',
            Order.delivery_date >= today_start,
            Order.is_active == True
        ).scalar()

    def get_total_revenue(self) -> Decimal:
        """Umumiy daromad"""
        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.is_active == True
        ).scalar()
        return result or Decimal("0")

    def get_total_paid(self) -> Decimal:
        """To'langan summa"""
        result = self.db.query(func.sum(Order.paid_amount)).filter(
            Order.is_active == True
        ).scalar()
        return result or Decimal("0")

    def get_revenue_today(self) -> Decimal:
        """Bugungi daromad"""
        today_start = get_today_start()

        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.order_date >= today_start,
            Order.is_active == True
        ).scalar()
        return result or Decimal("0")

    # BUG FIX #8: N+1 muammo — analytics uchun DB da hisoblash
    def get_analytics_by_period(self, start_date: date, end_date: date) -> dict:
        """
        Berilgan davr uchun sotuv tahlilini TO'LIQ DB DA hisoblaydi.
        Python da 10,000 order yuklab filter qilish o'rniga,
        barcha aggregatlar bitta so'rovda DB da bajariladi.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # 1. Asosiy yig'indilar — bitta query
        totals = self.db.query(
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
            func.coalesce(func.sum(Order.paid_amount), 0).label("total_paid"),
        ).filter(
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
            Order.is_active == True
        ).first()

        # 2. Top 10 mijoz — bitta query
        top_customers = self.db.query(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_amount).label("total_amount")
        ).join(
            Order, Customer.id == Order.customer_id
        ).filter(
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
            Order.is_active == True,
            Customer.is_active == True
        ).group_by(
            Customer.id, Customer.name
        ).order_by(
            desc(func.sum(Order.total_amount))
        ).limit(10).all()

        # 3. Top 10 mahsulot — bitta query
        from app.models.production import FinishedProduct
        top_products = self.db.query(
            FinishedProduct.id.label("product_id"),
            FinishedProduct.name.label("product_name"),
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.total_price).label("total_amount")
        ).join(
            OrderItem, FinishedProduct.id == OrderItem.finished_product_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
            Order.is_active == True,
            OrderItem.is_active == True
        ).group_by(
            FinishedProduct.id, FinishedProduct.name
        ).order_by(
            desc(func.sum(OrderItem.total_price))
        ).limit(10).all()

        # 4. Kunlik sotuv — bitta query
        sales_by_day = self.db.query(
            func.date(Order.order_date).label("date"),
            func.sum(Order.total_amount).label("amount")
        ).filter(
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
            Order.is_active == True
        ).group_by(
            func.date(Order.order_date)
        ).order_by(
            func.date(Order.order_date)
        ).all()

        total_revenue = Decimal(str(totals.total_revenue))
        total_paid = Decimal(str(totals.total_paid))
        total_orders = totals.total_orders

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_unpaid": total_revenue - total_paid,
            "average_order_value": total_revenue / total_orders if total_orders > 0 else Decimal("0"),
            "top_customers": [
                {
                    "customer_id": r.customer_id,
                    "customer_name": r.customer_name,
                    "total_orders": r.total_orders,
                    "total_amount": Decimal(str(r.total_amount))
                }
                for r in top_customers
            ],
            "top_products": [
                {
                    "product_id": r.product_id,
                    "product_name": r.product_name,
                    "total_quantity": Decimal(str(r.total_quantity)),
                    "total_amount": Decimal(str(r.total_amount))
                }
                for r in top_products
            ],
            "sales_by_day": [
                {
                    "date": r.date,
                    "amount": Decimal(str(r.amount))
                }
                for r in sales_by_day
            ]
        }


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, db: Session):
        super().__init__(OrderItem, db)

    def get_by_order(self, order_id: UUID) -> List[OrderItem]:
        """Order bo'yicha itemlar"""
        return self.db.query(OrderItem).options(
            joinedload(OrderItem.finished_product)
        ).filter(
            OrderItem.order_id == order_id,
            OrderItem.is_active == True
        ).all()


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_order(self, order_id: UUID) -> List[Payment]:
        """Order bo'yicha to'lovlar"""
        return self.db.query(Payment).options(
            joinedload(Payment.receiver)
        ).filter(
            Payment.order_id == order_id,
            Payment.is_active == True
        ).order_by(Payment.payment_date).all()

    def get_total_for_order(self, order_id: UUID) -> Decimal:
        """Order uchun jami to'lovlar"""
        result = self.db.query(func.sum(Payment.amount)).filter(
            Payment.order_id == order_id,
            Payment.is_active == True
        ).scalar()
        return result or Decimal("0")