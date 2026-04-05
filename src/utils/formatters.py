from typing import Dict, Optional
from datetime import datetime


class MessageFormatter:
    """Форматирование сообщений для разных типов пользователей"""
    
    @staticmethod
    def user_account_message(user_id: int, subscription_info: dict) -> str:
        """Сообщение личного кабинета для обычного пользователя"""
        message = (
            "👤 <b>ЛИЧНЫЙ КАБИНЕТ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Ваш ID:</b> <code>{user_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        if subscription_info['active']:
            expires = subscription_info.get('expires_at')
            days_left = subscription_info.get('days_left', 0)
            
            expires_str = expires.strftime('%d.%m.%Y') if expires else 'неизвестно'
            
            message += (
                f"✅ <b>Подписка активна</b>\n"
                f"<b>До:</b> <code>{expires_str}</code>\n"
                f"<b>Дней осталось:</b> <code>{days_left}</code>\n"
            )
        else:
            message += (
                "❌ <b>Подписка неактивна</b>\n"
                "<b>Дней осталось:</b> <code>0</code>\n"
            )
        
        message += "━━━━━━━━━━━━━━━━━━━━━"
        return message
    
    @staticmethod
    def admin_main_menu() -> str:
        """Главное меню для администратора"""
        message = (
            "👨‍💼 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Добро пожаловать в панель управления SakuraVPN!\n\n"
            "<b>Выберите категорию:</b>"
        )
        return message
    
    @staticmethod
    def user_list_message(users_data: list) -> str:
        """Список пользователей для администратора"""
        message = "👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not users_data:
            message += "Нет пользователей"
            return message
        
        for user in users_data:
            telegram_id = user.get('telegram_id', 'N/A')
            username = user.get('username', 'N/A')
            active = '✅' if user.get('subscription_active') else '❌'
            message += f"{active} ID: <code>{telegram_id}</code> - {username}\n"
        
        return message
    
    @staticmethod
    def admin_stats_message(stats: dict) -> str:
        """Статистика для администратора"""
        message = (
            "📊 <b>СТАТИСТИКА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Всего пользователей:</b> <code>{stats.get('total_users', 0)}</code>\n"
            f"✅ <b>Активных подписок:</b> <code>{stats.get('active_subscriptions', 0)}</code>\n"
            f"📈 <b>Доход (месяц):</b> <code>{stats.get('monthly_revenue', 0)} ₽</code>\n"
            f"💰 <b>Доход (всё время):</b> <code>{stats.get('total_revenue', 0)} ₽</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return message
    
    @staticmethod
    def subscription_purchase_message() -> str:
        """Сообщение выбора тарифа"""
        message = (
            "🎁 <b>ВЫБЕРИТЕ ТАРИФ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <b>1 месяц</b>\n"
            "Цена: <code>99 ₽</code>\n\n"
            "⭐ <b>3 месяца</b>\n"
            "Цена: <code>289 ₽</code>\n"
            "(Экономия: 8 ₽)\n\n"
            "🌟 <b>6 месяцев</b>\n"
            "Цена: <code>579 ₽</code>\n"
            "(Экономия: 15 ₽)\n\n"
            "✨ <b>12 месяцев</b>\n"
            "Цена: <code>999 ₽</code>\n"
            "(Экономия: 189 ₽)\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return message
    
    @staticmethod
    def payment_success_message(key: str) -> str:
        """Сообщение об успешном платеже"""
        message = (
            "✅ <b>ПЛАТЕЖ УСПЕШНО ОБРАБОТАН!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Спасибо за повседневное использование SakuraVPN! 🎉\n\n"
            f"<b>Ваш ключ подписки:</b>\n"
            f"<code>{key}</code>\n\n"
            "Нажмите кнопку ниже для получения конфигурации для вашего устройства.\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return message
    
    @staticmethod
    def help_message() -> str:
        """Сообщение помощи"""
        message = (
            "❓ <b>СПРАВКА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Доступные команды:</b>\n\n"
            "🏠 /start - Главное меню\n"
            "👤 /account - Личный кабинет\n"
            "🔑 /update_keys - Обновить ключи\n"
            "💳 /payment - Оплата подписки\n\n"
            "<b>FAQ:</b>\n\n"
            "❓ <b>Как использовать VPN?</b>\n"
            "Установите приложение для вашей ОС и введите ключ подписки из личного кабинета.\n\n"
            "❓ <b>Я забыл свой ключ</b>\n"
            "Нажмите на кнопку 'Обновить ключи' в приватных сообщениях боту.\n\n"
            "❓ <b>Как вернуть деньги?</b>\n"
            "30 дней гарантии возврата денег!"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return message


class InlineKeyboardBuilder:
    """Построитель inline клавиатур"""
    
    @staticmethod
    def user_account_keyboard():
        """Клавиатура личного кабинета"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("💳 Оформить подписку", callback_data='payment_menu')],
            [
                InlineKeyboardButton("🏠 Кабинет", url='https://example.com/cabinet'),
                InlineKeyboardButton("👥 Реферралы", callback_data='referrals')
            ],
            [InlineKeyboardButton("❓ Помощь", callback_data='help')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def tariff_keyboard():
        """Клавиатура выбора тарифа"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("💫 1 месяц - 99 ₽", callback_data='tariff_1')],
            [InlineKeyboardButton("⭐ 3 месяца - 289 ₽", callback_data='tariff_3')],
            [InlineKeyboardButton("🌟 6 месяцев - 579 ₽", callback_data='tariff_6')],
            [InlineKeyboardButton("✨ 12 месяцев - 999 ₽", callback_data='tariff_12')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_account')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def subscription_link_keyboard(user_id: int):
        """Клавиатура для ссылки подписки"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [
                InlineKeyboardButton("🪟 Windows", url=f'https://example.com/sub/{user_id}/windows'),
                InlineKeyboardButton("🍎 iOS", url=f'https://example.com/sub/{user_id}/ios'),
                InlineKeyboardButton("🤖 Android", url=f'https://example.com/sub/{user_id}/android'),
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_account')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_main_keyboard():
        """Главная клавиатура администратора"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [
                InlineKeyboardButton("👥 Пользователи", callback_data='admin_users'),
                InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')
            ],
            [
                InlineKeyboardButton("🖥 Узлы", callback_data='admin_nodes_list'),
                InlineKeyboardButton("📡 Входы", callback_data='admin_inbounds_list')
            ],
            [
                InlineKeyboardButton("📈 Аналитика", callback_data='admin_analytics'),
                InlineKeyboardButton("⚙️ Настройки", callback_data='admin_settings')
            ],
            [InlineKeyboardButton("🔙 На главную", callback_data='back_home')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_users_keyboard():
        """Клавиатура управления пользователями"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("📝 Список пользователей", callback_data='admin_users_list')],
            [InlineKeyboardButton("➕ Добавить пользователя", callback_data='admin_users_add')],
            [InlineKeyboardButton("🔍 Поиск", callback_data='admin_users_search')],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_nodes_keyboard(page: int = 0):
        """Клавиатура управления узлами"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("📋 Список узлов", callback_data='admin_nodes_list')],
            [InlineKeyboardButton("➕ Добавить узел", callback_data='admin_add_node')],
            [InlineKeyboardButton("📊 Статистика узлов", callback_data='admin_node_stats')],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_inbounds_keyboard():
        """Клавиатура управления inbound'ами"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("📡 Список Inbound'ов", callback_data='admin_inbounds_list')],
            [InlineKeyboardButton("🌐 Хосты", callback_data='admin_hosts_list')],
            [InlineKeyboardButton("➕ Добавить хост", callback_data='admin_add_host')],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_hosts_keyboard():
        """Клавиатура управления хостами"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("📋 Список хостов", callback_data='admin_hosts_list')],
            [InlineKeyboardButton("➕ Добавить хост", callback_data='admin_add_host')],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_inbounds')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_settings_keyboard():
        """Клавиатура настроек"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton("🎁 Настройки подписки", callback_data='settings_subscription')],
            [InlineKeyboardButton("📱 Настройки Telegram", callback_data='settings_telegram')],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_back_keyboard(callback_data: str):
        """Простая клавиатура с кнопкой назад"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data=callback_data)]
        ])
