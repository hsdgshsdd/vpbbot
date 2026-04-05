"""
Обработчик ввода для администраторов с ConversationHandler
Управляет состояниями при вводе ID пользователей
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.utils.permissions import check_admin
from src.utils.db_service import UserService
import logging

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_USER_ID = 1


async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для администраторов (ConversationHandler)"""
    
    user_id_input = update.message.text.strip()
    
    # Валидируем, что это число
    try:
        target_user_id = int(user_id_input)
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Telegram ID должен быть числом.\n\n"
            "Попробуйте ещё раз или введите /cancel для отмены.",
            parse_mode='HTML'
        )
        return WAITING_FOR_USER_ID
    
    # Проверяем, существует ли пользователь
    target_user = UserService.get_user(target_user_id)
    
    if target_user:
        # Показываем информацию о пользователе
        message = (
            f"👤 <b>ПОЛЬЗОВАТЕЛЬ НАЙДЕН</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Telegram ID:</b> <code>{target_user.telegram_id}</code>\n"
            f"<b>Логин (Marzneshin):</b> {target_user.username or 'N/A'}\n"
            f"<b>Ключ подписки:</b> {target_user.subscription_key[:20] + '...' if target_user.subscription_key else 'Нет'}\n\n"
            f"<i>Администратор:</i> {'✅ Да' if target_user.is_admin else '❌ Нет'}"
        )
        
        buttons = [
            [InlineKeyboardButton("✏️ Изменить", callback_data=f"admin_user_edit:{target_user_id}")],
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f"admin_user_delete:{target_user_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_users')]
        ]
    else:
        # Пользователь не найден - предлагаем создать
        message = (
            f"❓ <b>ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Пользователь с ID <code>{target_user_id}</code> не зарегистрирован в системе.\n\n"
            f"Желаете добавить этого пользователя?"
        )
        
        buttons = [
            [InlineKeyboardButton("➕ Добавить", callback_data=f"admin_user_create:{target_user_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_users')]
        ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    
    # Возвращаем ConversationHandler.END чтобы выйти из состояния
    return ConversationHandler.END


async def cancel_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена ввода"""
    if update.message:
        await update.message.reply_text(
            "❌ Отменено. Используйте /admin для открытия админ-панели.",
            parse_mode='HTML'
        )
    elif update.callback_query:
        await update.callback_query.answer("Вернулись в меню", show_alert=False)
    
    return ConversationHandler.END

