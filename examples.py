# Example usage of SakuraVPN Telegram Bot

from telegram import Update
from telegram.ext import ContextTypes
from src.utils.business_logic import SubscriptionManager, ReferralService, PromotionManager
from src.utils.db_service import UserService


# Пример 1: Создание подписки
async def example_create_subscription():
    """Создать подписку для пользователя"""
    user_id = 123456789
    months = 3
    
    result = await SubscriptionManager.create_subscription(user_id, months)
    
    if result['success']:
        print(f"✅ Подписка создана!")
        print(f"   Ключ: {result['key']}")
        print(f"   Действительна до: {result['expires_at']}")
    else:
        print(f"❌ Ошибка: {result['error']}")


# Пример 2: Получение реферальной ссылки
def example_referral_link():
    """Получить реферальную ссылку"""
    user_id = 123456789
    link = ReferralService.get_referral_link(user_id)
    print(f"Реферальная ссылка: {link}")


# Пример 3: Применение промо-кода
def example_promo_code():
    """Применить промо-код"""
    code = 'WELCOME10'
    original_price = 99
    
    result = PromotionManager.apply_promo_code(code, original_price)
    
    if result['success']:
        print(f"✅ Промо-код применен!")
        print(f"   Оригинальная цена: {result['original_price']} ₽")
        print(f"   Скидка: {result['discount']} ₽")
        print(f"   Итоговая цена: {result['final_price']} ₽")
    else:
        print(f"❌ Ошибка: {result['error']}")


# Пример 4: Получение информации о подписке
def example_subscription_info():
    """Получить информацию о подписке"""
    user_id = 123456789
    info = UserService.get_subscription_info(user_id)
    
    print(f"Статус подписки:")
    print(f"   Активна: {info['active']}")
    print(f"   Дней осталось: {info['days_left']}")
    if 'expires_at' in info:
        print(f"   До: {info['expires_at'].strftime('%d.%m.%Y')}")


# Пример 5: Проверка заканчивающихся подписок
def example_check_expiring():
    """Проверить подписки, заканчивающиеся в ближайшее время"""
    users = SubscriptionManager.check_expiring_subscriptions()
    
    print(f"Найдено подписок к продлению: {len(users)}")
    
    for user in users:
        days_left = (user.subscription_expires_at - datetime.utcnow()).days
        print(f"   User {user.telegram_id}: {days_left} дней")


# Для запуска примеров раскомментируйте нужную функцию и запустите:
# python -c "from examples import example_promo_code; example_promo_code()"

if __name__ == "__main__":
    # example_referral_link()
    # example_promo_code()
    # example_subscription_info()
    # example_check_expiring()
    pass
