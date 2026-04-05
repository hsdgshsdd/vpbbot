"""
Обработчик ввода для администраторов с ConversationHandler
Управляет состояниями при вводе ID пользователей
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.utils.permissions import check_admin
from src.utils.db_service import UserService
from src.api.marzneshin import api
from datetime import datetime, timedelta
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


async def admin_user_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать подписку для пользователя в Marzneshin"""
    query = update.callback_query
    
    # Парсим Telegram ID из callback_data
    target_user_id = int(query.data.replace('admin_user_create:', ''))
    
    try:
        await query.answer("⏳ Создаем подписку...", show_alert=False)
        
        # 1. Получить список сервисов
        services_data = await api.get_services()
        service_ids = []
        
        if services_data and 'items' in services_data and services_data['items']:
            service_ids = [services_data['items'][0]['id']]
        else:
            raise Exception("Сервисы не найдены на Marzneshin")
        
        # 2. Auto-generate username from Telegram ID (not asking user)
        username = f"user_{target_user_id}"
        
        # 3. Рассчитать параметры подписки (по умолчанию 1 месяц, 100GB)
        expire_date = datetime.utcnow() + timedelta(days=30)
        data_limit = 100 * 1024 * 1024 * 1024  # 100GB
        
        # 4. Создать пользователя в Marzneshin
        logger.info(f"Admin creating user in Marzneshin: {username} (Telegram ID: {target_user_id})")
        created_user = await api.create_user(
            username=username,
            expire_date=expire_date,
            data_limit=data_limit,
            services=service_ids
        )
        
        if not created_user:
            raise Exception("Не удалось создать пользователя в Marzneshin")
        
        # 5. Получить subscription key
        sub_key = created_user.get('key', username)
        
        # 6. Записать в локальную БД
        UserService.update_subscription(
            target_user_id,
            username=username,
            key=sub_key
        )
        
        # 7. Показать подтверждение
        message = (
            f"✅ <b>ПОДПИСКА СОЗДАНА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Telegram ID:</b> <code>{target_user_id}</code>\n"
            f"<b>Логин (Marzneshin):</b> <code>{username}</code>\n"
            f"<b>Ключ подписки:</b> <code>{sub_key[:30]}...</code>\n"
            f"<b>Действует до:</b> {expire_date.strftime('%d.%m.%Y')}\n"
            f"<b>Трафик:</b> 100 GB/месяц\n\n"
            f"✉️ Пользователь получит сообщение с данными для подключения."
        )
        
        buttons = [
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_users')]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )
        
        logger.info(f"✅ User subscription created: {username} for Telegram ID {target_user_id}")
        
    except Exception as e:
        logger.error(f"Error creating user subscription: {e}", exc_info=True)
        
        error_message = (
            f"❌ <b>ОШИБКА ПРИ СОЗДАНИИ ПОДПИСКИ</b>\n\n"
            f"Причина: {str(e)}\n\n"
            f"❕ Попробуйте позже или проверьте Marzneshin."
        )
        
        buttons = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"admin_user_create:{target_user_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data='admin_users')]
        ]
        
        await query.edit_message_text(
            error_message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )

