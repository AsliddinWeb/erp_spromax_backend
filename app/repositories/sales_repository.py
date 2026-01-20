from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import datetime
from decimal import Decimal
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
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
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
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.order_date >= today_start,
            Order.is_active == True
        ).scalar()
        return result or Decimal("0")


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