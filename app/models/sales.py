from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User
from app.models.production import FinishedProduct


class Customer(BaseModel):
    """Mijozlar jadvali"""
    __tablename__ = "customers"
    
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    inn = Column(String(9), nullable=True)  # STIR
    customer_type = Column(String(20), nullable=False, default='regular')  # regular, wholesale, vip
    
    # Relationships
    orders = relationship("Order", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.name}>"


class Order(BaseModel):
    """Buyurtmalar jadvali"""
    __tablename__ = "orders"
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_status = Column(String(20), nullable=False, default='unpaid')  # unpaid, partial, paid
    delivery_status = Column(String(20), nullable=False, default='pending')  # pending, processing, shipped, delivered, cancelled
    delivery_address = Column(Text, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign Keys
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    creator = relationship("User", foreign_keys=[created_by])
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    
    def __repr__(self):
        return f"<Order {self.id}>"


class OrderItem(BaseModel):
    """Buyurtma pozitsiyalari jadvali"""
    __tablename__ = "order_items"
    
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    finished_product_id = Column(UUID(as_uuid=True), ForeignKey('finished_products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    finished_product = relationship("FinishedProduct")
    
    def __repr__(self):
        return f"<OrderItem {self.id}>"


class Payment(BaseModel):
    """To'lovlar jadvali"""
    __tablename__ = "payments"
    
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, card, transfer, etc.
    transaction_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign Keys
    received_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    receiver = relationship("User", foreign_keys=[received_by])
    
    def __repr__(self):
        return f"<Payment {self.id}>"