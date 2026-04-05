from .database import SessionLocal, User, Payment, AdminAction
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    def get_or_create_user(telegram_id: int, username: str = None, is_admin: bool = False) -> User:
        """Получить или создать пользователя"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id, username=username, is_admin=is_admin)
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        finally:
            db.close()
    
    @staticmethod
    def get_user(telegram_id: int) -> Optional[User]:
        """Получить пользователя"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            db.close()
    
    @staticmethod
    def update_subscription(telegram_id: int, key: str, expires_at: datetime):
        """Обновить информацию о подписке"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.subscription_key = key
                user.subscription_active = True
                user.subscription_expires_at = expires_at
                db.commit()
                return user
        finally:
            db.close()
    
    @staticmethod
    def get_subscription_info(telegram_id: int) -> dict:
        """Получить информацию о подписке"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return {'active': False, 'days_left': 0}
            
            if user.subscription_expires_at:
                days_left = (user.subscription_expires_at - datetime.utcnow()).days
                is_active = days_left > 0
                return {
                    'active': is_active,
                    'days_left': max(0, days_left),
                    'expires_at': user.subscription_expires_at
                }
            return {'active': False, 'days_left': 0}
        finally:
            db.close()


class PaymentService:
    """Сервис для работы с платежами"""
    
    @staticmethod
    def create_payment(telegram_id: int, amount: float, months: int) -> Payment:
        """Создать платеж"""
        db = SessionLocal()
        try:
            payment = Payment(
                telegram_id=telegram_id,
                amount=amount,
                months=months,
                status='pending'
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return payment
        finally:
            db.close()
    
    @staticmethod
    def get_pending_payment(telegram_id: int) -> Optional[Payment]:
        """Получить ожидающий платеж"""
        db = SessionLocal()
        try:
            return db.query(Payment).filter(
                Payment.telegram_id == telegram_id,
                Payment.status == 'pending'
            ).order_by(Payment.created_at.desc()).first()
        finally:
            db.close()
    
    @staticmethod
    def complete_payment(payment_id: int) -> Payment:
        """Завершить платеж"""
        db = SessionLocal()
        try:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if payment:
                payment.status = 'completed'
                payment.completed_at = datetime.utcnow()
                db.commit()
                db.refresh(payment)
            return payment
        finally:
            db.close()


class AdminService:
    """Сервис для административных действий"""
    
    @staticmethod
    def log_action(admin_id: int, action: str, target_user_id: int = None, details: str = None):
        """Залогировать действие администратора"""
        db = SessionLocal()
        try:
            log_entry = AdminAction(
                admin_id=admin_id,
                action=action,
                target_user_id=target_user_id,
                details=details
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def get_admin_actions(admin_id: int, limit: int = 50):
        """Получить действия администратора"""
        db = SessionLocal()
        try:
            return db.query(AdminAction).filter(
                AdminAction.admin_id == admin_id
            ).order_by(AdminAction.created_at.desc()).limit(limit).all()
        finally:
            db.close()
