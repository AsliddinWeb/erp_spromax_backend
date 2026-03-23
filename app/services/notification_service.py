from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.models.notification import Notification
from app.models.user import User, Role
from app.core.constants import UserRole
from app.core.ws_manager import manager


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_users_by_roles(self, roles: List[str]) -> List[User]:
        """Berilgan rollardagi barcha foydalanuvchilarni olish"""
        return self.db.query(User).join(Role).filter(
            Role.name.in_(roles),
            User.is_active == True
        ).all()

    def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notif_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None
    ) -> Notification:
        """Bitta bildirishnoma yaratish"""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            reference_type=reference_type,
            reference_id=reference_id,
            is_read=False
        )
        self.db.add(notif)
        self.db.flush()
        return notif

    def _notif_to_dict(self, notif: Notification) -> dict:
        return {
            "id": str(notif.id),
            "title": notif.title,
            "message": notif.message,
            "type": notif.type,
            "is_read": False,
            "reference_type": notif.reference_type,
            "reference_id": str(notif.reference_id) if notif.reference_id else None,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }

    def notify_roles(
        self,
        roles: List[str],
        title: str,
        message: str,
        notif_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None
    ):
        """Berilgan rollardagi barcha foydalanuvchilarga bildirishnoma yuborish"""
        users = self._get_users_by_roles(roles)
        created = []
        for user in users:
            notif = self.create_notification(
                user_id=user.id,
                title=title,
                message=message,
                notif_type=notif_type,
                reference_type=reference_type,
                reference_id=reference_id
            )
            created.append((str(user.id), notif))
        self.db.commit()
        for user_id, notif in created:
            manager.push_to_user(user_id, self._notif_to_dict(notif))

    # ============ TRIGGER METODLARI ============

    def notify_low_stock(self, material_name: str, current_qty: float, min_qty: float, material_id: UUID):
        """Kam qoldiq bildirishnomasi"""
        self.notify_roles(
            roles=[UserRole.WAREHOUSE_MANAGER, UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DIRECTOR],
            title="⚠️ Kam qoldiq",
            message=f"{material_name}: {current_qty:.1f} qoldi (minimum: {min_qty:.1f})",
            notif_type="low_stock",
            reference_type="raw_material",
            reference_id=material_id
        )

    def notify_maintenance_request(self, machine_name: str, priority: str, request_id: UUID):
        """Yangi texnik xizmat so'rovi bildirishnomasi"""
        self.notify_roles(
            roles=[UserRole.MAINTENANCE, UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DIRECTOR],
            title="🔧 Yangi texnik xizmat so'rovi",
            message=f"{machine_name} uchun {priority} darajali so'rov yaratildi",
            notif_type="maintenance",
            reference_type="maintenance_request",
            reference_id=request_id
        )

    def notify_new_order(self, customer_name: str, total_amount: float, order_id: UUID):
        """Yangi buyurtma bildirishnomasi"""
        self.notify_roles(
            roles=[UserRole.SALES_MANAGER, UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DIRECTOR],
            title="🛒 Yangi buyurtma",
            message=f"{customer_name} dan {total_amount:,.0f} so'm buyurtma keldi",
            notif_type="order",
            reference_type="order",
            reference_id=order_id
        )

    def notify_leave_request(self, employee_name: str, days_count: int, request_id: UUID):
        """Ta'til so'rovi bildirishnomasi"""
        self.notify_roles(
            roles=[UserRole.HR_MANAGER, UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DIRECTOR],
            title="📅 Yangi ta'til so'rovi",
            message=f"{employee_name} {days_count} kunlik ta'til so'radi",
            notif_type="leave_request",
            reference_type="leave_request",
            reference_id=request_id
        )

    def notify_salary_payment(self, employee_name: str, amount: float, employee_user_id: Optional[UUID], payment_id: UUID):
        """Ish haqi to'lovi bildirishnomasi — xodimning o'ziga"""
        if employee_user_id:
            notif = self.create_notification(
                user_id=employee_user_id,
                title="💰 Ish haqi to'landi",
                message=f"Sizga {amount:,.0f} so'm ish haqi o'tkazildi",
                notif_type="salary",
                reference_type="salary_payment",
                reference_id=payment_id
            )
            self.db.commit()
            manager.push_to_user(str(employee_user_id), self._notif_to_dict(notif))

    # ============ CRUD METODLARI ============

    def get_notifications(
        self,
        user_id: UUID,
        is_read: Optional[bool] = None,
        limit: int = 20
    ):
        """Foydalanuvchi bildirishnomalari"""
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_active == True
        )
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        items = query.order_by(desc(Notification.created_at)).limit(limit).all()
        unread_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_active == True
        ).count()
        return items, unread_count

    def get_unread_count(self, user_id: UUID) -> int:
        """O'qilmagan bildirishnomalar soni"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_active == True
        ).count()

    def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Bitta bildirishnomani o'qildi deb belgilash"""
        notif = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.is_active == True
        ).first()
        if notif:
            notif.is_read = True
            self.db.commit()
            return True
        return False

    def mark_all_read(self, user_id: UUID) -> int:
        """Barcha bildirishnomalarni o'qildi deb belgilash"""
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_active == True
        ).update({"is_read": True})
        self.db.commit()
        return count