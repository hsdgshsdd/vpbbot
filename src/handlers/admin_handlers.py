from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.utils.permissions import check_admin
from src.utils.formatters import MessageFormatter, InlineKeyboardBuilder
from src.utils.db_service import UserService, AdminService
from src.models import SessionLocal, User, Payment
from src.api.marzneshin import api
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    if not await check_admin(update, context):
        return
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            MessageFormatter.admin_main_menu(),
            reply_markup=InlineKeyboardBuilder.admin_main_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            MessageFormatter.admin_main_menu(),
            reply_markup=InlineKeyboardBuilder.admin_main_keyboard(),
            parse_mode='HTML'
        )


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление пользователями"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    await query.edit_message_text(
        "👥 <b>УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardBuilder.admin_users_keyboard(),
        parse_mode='HTML'
    )


async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список пользователей"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    db = SessionLocal()
    try:
        users = db.query(User).limit(10).all()
        
        message = "👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not users:
            message += "Нет пользователей в системе."
        else:
            for user in users:
                status = "✅" if user.subscription_active else "❌"
                message += (
                    f"{status} <b>ID:</b> <code>{user.telegram_id}</code>\n"
                    f"   <b>Юзер:</b> {user.username or 'N/A'}\n"
                    f"   <b>Ключ:</b> {user.subscription_key[:20] + '...' if user.subscription_key else 'N/A'}\n"
                    f"   <b>До:</b> {user.subscription_expires_at.strftime('%d.%m.%Y') if user.subscription_expires_at else 'N/A'}\n\n"
                )
    finally:
        db.close()
    
    buttons = [
        [InlineKeyboardButton("➕ Добавить", callback_data='admin_users_add')],
        [InlineKeyboardButton("🔍 Поиск", callback_data='admin_users_search')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_users')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        active_subs = db.query(User).filter(User.subscription_active == True).count()
        
        # Расчет дохода
        completed_payments = db.query(Payment).filter(Payment.status == 'completed').all()
        total_revenue = sum(p.amount for p in completed_payments)
        
        # Доход за месяц
        month_ago = datetime.utcnow() - timedelta(days=30)
        monthly_revenue = sum(p.amount for p in completed_payments if p.completed_at and p.completed_at > month_ago)
        
        stats = {
            'total_users': total_users,
            'active_subscriptions': active_subs,
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue
        }
        
    finally:
        db.close()
    
    message = MessageFormatter.admin_stats_message(stats)
    
    buttons = [
        [InlineKeyboardButton("📊 Обновить", callback_data='admin_stats')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление сервисами"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    try:
        services = await api.get_services()
        
        message = "🎁 <b>СЕРВИСЫ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not services:
            message += "Нет сервисов"
        else:
            for service in services:
                name = service.get('name', 'N/A')
                service_id = service.get('id', 'N/A')
                user_count = len(service.get('user_ids', []))
                message += f"🎯 <b>{name}</b> (ID: {service_id})\n   Пользователей: {user_count}\n\n"
        
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        message = "❌ Ошибка при загрузке сервисов"
    
    buttons = [
        [InlineKeyboardButton("➕ Добавить сервис", callback_data='admin_services_add')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление входами"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    message = (
        "📥 <b>ВХОДЫ (INBOUNDS)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Управление входами в Marzneshin.\n"
        "Входы настраиваются через административный интерфейс.\n\n"
        "<i>Взаимодействие с входами через API требует предварительной конфигурации.</i>"
    )
    
    buttons = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_inbounds')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    message = (
        "⚙️ <b>НАСТРОЙКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔧 <b>Конфигурация API:</b>\n"
        f"   URL: <code>{api.base_url}</code>\n"
        f"   Статус: {'✅ Подключен' if api.token else '❌ Отключен'}\n\n"
        "📊 <b>Параметры бота:</b>\n"
        "   Язык: Русский\n"
        "   Валюта: RUB\n"
        "   Версия: 1.0.0"
    )
    
    buttons = [
        [InlineKeyboardButton("🔄 Проверить подключение", callback_data='admin_check_api')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логи действий администратора"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    admin_id = update.effective_user.id
    
    actions = AdminService.get_admin_actions(admin_id, limit=10)
    
    message = "📋 <b>ЛОГИ ДЕЙСТВИЙ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not actions:
        message += "Нет логов действий"
    else:
        for action in actions:
            message += (
                f"🔹 <b>{action.action}</b>\n"
                f"   Время: {action.created_at.strftime('%d.%m %H:%M')}\n"
                f"   Деталь: {action.details or 'N/A'}\n\n"
            )
    
    buttons = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_logs')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_main')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def admin_check_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверить подключение к API"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    # Ответ сразу
    await query.answer("🔄 Проверка подключения...", show_alert=False)
    
    try:
        token = await api.get_token()
        if token:
            await query.edit_message_text(
                "✅ <b>ПРОВЕРКА УСПЕШНА</b>\n\n"
                "API Marzneshin подключен и работает корректно.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data='admin_settings')]
                ]),
                parse_mode='HTML'
            )
        else:
            raise Exception("No token received")
    except Exception as e:
        logger.error(f"API check failed: {e}")
        await query.edit_message_text(
            f"❌ <b>ОШИБКА ПОДКЛЮЧЕНИЯ</b>\n\n"
            f"Не удалось подключиться к API:\n<code>{str(e)}</code>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Повторить", callback_data='admin_check_api')],
                [InlineKeyboardButton("◀️ Назад", callback_data='admin_settings')]
            ]),
            parse_mode='HTML'
        )
