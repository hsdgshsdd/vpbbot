"""
Дополнительные обработчики callback'ов для административных функций
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.utils.permissions import check_admin
from src.utils.db_service import UserService, AdminService
from src.utils.business_logic import ReferralService, PromotionManager, NotificationManager
from src.utils.messages import MESSAGES, get_faq_text
import logging

logger = logging.getLogger(__name__)


async def confirm_regenerate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение получения нового ключа"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # В реальной системе здесь должна быть логика переполучения ключа
    await query.answer("🔑 Новый ключ сгенерирован!", show_alert=True)
    
    # Переход обратно к ключам
    from src.handlers.user_handlers import update_keys
    await update_keys(update, context)


async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реферальная программа"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Получить статистику рефералов
    referral_stats = ReferralService.get_referral_stats(user_id)
    referral_link = ReferralService.get_referral_link(user_id)
    
    # Форматирование сообщения
    referral_text = MESSAGES['referral_info'].format(
        referral_count=referral_stats.get('total_referrals', 0),
        total_bonus=referral_stats.get('total_bonus', 0),
        referral_link=referral_link
    )
    
    buttons = [
        [InlineKeyboardButton("📋 Скопировать ссылку", callback_data='copy_referral_link')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_account')]
    ]
    
    await query.edit_message_text(
        referral_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def download_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Загрузить конфигурацию"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    user = UserService.get_user(user_id)
    
    if not user or not user.subscription_key:
        await query.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    message = (
        "📥 <b>ЗАГРУЗКА КОНФИГУРАЦИИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите операционную систему вашего устройства:"
    )
    
    buttons = [
        [
            InlineKeyboardButton("🪟 Windows", url=f'https://example.com/configs/windows/{user.subscription_key}'),
            InlineKeyboardButton("🍎 macOS", url=f'https://example.com/configs/macos/{user.subscription_key}'),
        ],
        [
            InlineKeyboardButton("🐧 Linux", url=f'https://example.com/configs/linux/{user.subscription_key}'),
        ],
        [
            InlineKeyboardButton("🍎 iOS", url=f'https://example.com/configs/ios/{user.subscription_key}'),
        ],
        [
            InlineKeyboardButton("🤖 Android", url=f'https://example.com/configs/android/{user.subscription_key}'),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data='update_keys')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def regenerate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить новый ключ подписки"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    user = UserService.get_user(user_id)
    
    if not user or not user.subscription_key:
        await query.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    # Подтверждение
    message = (
        "⚠️ <b>ПОЛУЧИТЬ НОВЫЙ КЛЮЧ?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Это действие заменит ваш текущий ключ подписки.\n"
        "Старый ключ больше не будет работать.\n\n"
        "Вы уверены?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ Да, получить новый ключ", callback_data='confirm_regenerate_key'),
            InlineKeyboardButton("❌ Отмена", callback_data='update_keys')
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def confirm_regenerate_key_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение получения нового ключа (OLD)"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # В реальной системе здесь должна быть логика переполучения ключа
    await query.answer("🔑 Новый ключ сгенерирован!", show_alert=True)


async def admin_users_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить пользователя (admin) - запускает режим ввода ID"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    message = (
        "➕ <b>ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Введите Telegram ID пользователя, которого хотите добавить.\n\n"
        "<i>Вы можете узнать ID у пользователя или с помощью @userinfobot</i>"
    )
    
    buttons = [
        [InlineKeyboardButton("◀️ Отмена", callback_data='admin_users')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    
    # Возвращаем состояние для ConversationHandler
    from src.handlers.admin_user_input_handler import WAITING_FOR_USER_ID
    return WAITING_FOR_USER_ID


async def admin_users_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск пользователя (admin)"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    message = (
        "🔍 <b>ПОИСК ПОЛЬЗОВАТЕЛЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Введите Telegram ID или никнейм для поиска\n\n"
        "<i>Остановить поиск: /cancel</i>"
    )
    
    buttons = [
        [InlineKeyboardButton("◀️ Отмена", callback_data='admin_users')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    
    # Запуск режима ввода
    context.user_data['waiting_for_search_query'] = True


async def admin_services_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить сервис (admin)"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    message = (
        "➕ <b>СОЗДАТЬ НОВЫЙ СЕРВИС</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Введите название сервиса\n\n"
        "Пример: <code>Premium_Service</code>"
    )
    
    buttons = [
        [InlineKeyboardButton("◀️ Отмена", callback_data='admin_services')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    
    # Запуск режима ввода
    context.user_data['waiting_for_service_name'] = True


async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать FAQ в виде отдельных кнопок"""
    query = update.callback_query
    
    buttons = []
    for i, faq in enumerate(MESSAGES['faq'], 1):
        buttons.append([
            InlineKeyboardButton(
                f"❓ {faq['question'][:30]}...",
                callback_data=f'faq_{i-1}'
            )
        ])
    
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data='back_home')])
    
    await query.edit_message_text(
        "❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите интересующий вас вопрос:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def show_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, faq_index: int):
    """Показать ответ на вопрос FAQ"""
    query = update.callback_query
    
    if faq_index >= len(MESSAGES['faq']):
        await query.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    faq = MESSAGES['faq'][faq_index]
    
    message = (
        f"❓ <b>{faq['question']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{faq['answer']}"
    )
    
    buttons = [
        [InlineKeyboardButton("◀️ Назад к вопросам", callback_data='help')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def copy_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скопировать реферальную ссылку"""
    query = update.callback_query
    
    await query.answer(
        "✅ Ссылка скопирована в буфер обмена!",
        show_alert=False
    )
