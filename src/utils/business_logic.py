"""
Дополнительные утилиты для работы с бизнес-логикой
"""

from datetime import datetime, timedelta
from src.models import SessionLocal, User
from src.api.marzneshin import api
import logging

logger = logging.getLogger(__name__)


class ReferralService:
    """Сервис реферальной программы"""
    
    REFERRAL_BONUS = 50  # бонус в рублях за реферала
    
    @staticmethod
    def get_referral_link(user_id: int) -> str:
        """Получить реферальную ссылку"""
        # Здесь должна быть реальная реферальная система
        return f"https://t.me/your_bot?start=ref_{user_id}"
    
    @staticmethod
    def get_referral_stats(user_id: int) -> dict:
        """Получить статистику по рефералам"""
        db = SessionLocal()
        try:
            # Здесь должна быть реальная система подсчета рефералов
            return {
                'total_referrals': 0,
                'active_referrals': 0,
                'total_bonus': 0
            }
        finally:
            db.close()


class SubscriptionManager:
    """Менеджер подписок"""
    
    @staticmethod
    async def create_subscription(user_id: int, months: int) -> dict:
        """Создать подписку для пользователя"""
        username = f"user_{user_id}"
        expire_date = datetime.utcnow() + timedelta(days=30 * months)
        
        try:
            # Получить или создать сервис
            services = await api.get_services()
            service_ids = [s.get('id') for s in services] if services else []
            
            if not service_ids:
                service = await api.create_service(f"Default_Service", [])
                service_ids = [service.get('id')]
            
            # Создать пользователя в API
            user_data = await api.create_user(username, expire_date=expire_date, services=service_ids)
            
            return {
                'success': True,
                'username': user_data.get('username'),
                'key': user_data.get('username'),
                'expires_at': expire_date
            }
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    async def renew_subscription(user_id: int, months: int) -> dict:
        """Продлить подписку"""
        user = SessionLocal().query(User).filter(User.telegram_id == user_id).first()
        
        if not user or not user.subscription_key:
            return {'success': False, 'error': 'No active subscription'}
        
        try:
            new_expire_date = datetime.utcnow() + timedelta(days=30 * months)
            
            # Обновить пользователя в API
            await api.modify_user(user.subscription_key, expire_date=new_expire_date)
            
            return {
                'success': True,
                'expires_at': new_expire_date
            }
        except Exception as e:
            logger.error(f"Error renewing subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def check_expiring_subscriptions():
        """Проверить подписки, заканчивающиеся в ближайшее время"""
        db = SessionLocal()
        try:
            # Поиск подписок, заканчивающихся в течение 7 дней
            seven_days_later = datetime.utcnow() + timedelta(days=7)
            
            users = db.query(User).filter(
                User.subscription_active == True,
                User.subscription_expires_at <= seven_days_later,
                User.subscription_expires_at > datetime.utcnow()
            ).all()
            
            return users
        finally:
            db.close()


class PromotionManager:
    """Менеджер промоций и скидок"""
    
    PROMO_CODES = {
        'WELCOME10': {'discount': 0.10, 'max_uses': 100, 'uses': 0},
        'HOLIDAY20': {'discount': 0.20, 'max_uses': 50, 'uses': 0},
        'NEWYEAR50': {'discount': 0.50, 'max_uses': 10, 'uses': 0},
    }
    
    @staticmethod
    def apply_promo_code(code: str, price: float) -> dict:
        """Применить промо-код к цене"""
        if code not in PromotionManager.PROMO_CODES:
            return {'success': False, 'error': 'Invalid promo code'}
        
        promo = PromotionManager.PROMO_CODES[code]
        
        if promo['uses'] >= promo['max_uses']:
            return {'success': False, 'error': 'Promo code has reached maximum uses'}
        
        discount = price * promo['discount']
        final_price = price - discount
        
        return {
            'success': True,
            'original_price': price,
            'discount': discount,
            'final_price': final_price
        }
    
    @staticmethod
    def get_active_promotions() -> list:
        """Получить активные промоции"""
        return [
            {
                'title': 'Добро пожаловать!',
                'description': 'Скидка 10% на первую подписку',
                'code': 'WELCOME10'
            },
            {
                'title': 'Новогодняя акция',
                'description': 'Скидка 50% на любую подписку',
                'code': 'NEWYEAR50'
            }
        ]


class NotificationManager:
    """Менеджер уведомлений"""
    
    @staticmethod
    def get_notification_text(event_type: str, data: dict) -> str:
        """Получить текст уведомления по типу события"""
        notifications = {
            'subscription_expiring_soon': (
                "⏰ <b>НАПОМИНАНИЕ</b>\n\n"
                f"Ваша подписка истекает через {data.get('days_left', 0)} дней!\n"
                "Не пропустите и продлите подписку прямо сейчас."
            ),
            'subscription_expired': (
                "❌ <b>ПОДПИСКА ИСТЕКЛА</b>\n\n"
                "Ваша подписка больше не активна.\n"
                "Продлите подписку для продолжения использования VPN."
            ),
            'new_promotion': (
                f"🎉 <b>НОВАЯ АКЦИЯ!</b>\n\n"
                f"{data.get('title', '')}\n"
                f"{data.get('description', '')}"
            ),
            'payment_received': (
                "✅ <b>ПЛАТЕЖ ПОЛУЧЕН</b>\n\n"
                f"Спасибо за платеж! Ваша подписка активирована на {data.get('months', 0)} месяцев."
            )
        }
        
        return notifications.get(event_type, "Новое уведомление")
