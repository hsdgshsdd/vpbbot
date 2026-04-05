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
    """Список пользователей из Marzneshin API"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    try:
        # Читаем пользователей из API, а не из локальной БД!
        users_data = await api.get_users(page=1, size=10)
        users = users_data.get('items', []) if isinstance(users_data, dict) else []
        
        message = "👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ (из Marzneshin)</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not users:
            message += "Нет пользователей в системе."
        else:
            for user in users:
                username = user.get('username', 'N/A')
                enabled = user.get('enabled', False)
                status = "✅" if enabled else "❌"
                expire_date = user.get('expire_date', 'N/A')
                data_limit = user.get('data_limit', 0)
                used_data = user.get('used_traffic', 0)
                
                # Форматирование data_limit в GB
                data_limit_gb = data_limit / (1024**3) if data_limit else 0
                used_data_gb = used_data / (1024**3) if used_data else 0
                
                message += (
                    f"{status} <b>{username}</b>\n"
                    f"   <b>Трафик:</b> {used_data_gb:.2f}GB / {data_limit_gb:.2f}GB\n"
                    f"   <b>Истекает:</b> {expire_date[:10] if isinstance(expire_date, str) else 'N/A'}\n\n"
                )
    except Exception as e:
        logger.error(f"Error fetching users from API: {e}")
        message = f"❌ <b>Ошибка при загрузке пользователей</b>\n\n{str(e)[:100]}"
    
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
    """Статистика из Marzneshin API"""
    if not await check_admin(update, context):
        return
    
    query = update.callback_query
    
    try:
        # Читаем статистику из API, а не из локальной БД!
        users_stats = await api.get_users_stats()
        
        total_users = users_stats.get('total_users', 0)
        active_users = users_stats.get('active_users', 0)
        expired_users = users_stats.get('expired_users', 0)
        
        # Для дохода остаемся с локальной БД (платежи ведутся локально)
        db = SessionLocal()
        try:
            completed_payments = db.query(Payment).filter(Payment.status == 'completed').all()
            total_revenue = sum(p.amount for p in completed_payments)
            
            month_ago = datetime.utcnow() - timedelta(days=30)
            monthly_revenue = sum(p.amount for p in completed_payments if p.completed_at and p.completed_at > month_ago)
        finally:
            db.close()
        
        stats = {
            'total_users': total_users,
            'active_subscriptions': active_users,
            'expired_users': expired_users,
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        stats = {
            'total_users': 'Ошибка',
            'active_subscriptions': 'Ошибка',
            'expired_users': 'Ошибка',
            'monthly_revenue': 0,
            'total_revenue': 0
        }
    
    message = (
        "📊 <b>СТАТИСТИКА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Всего пользователей:</b> {stats.get('total_users', 0)}\n"
        f"✅ <b>Активных подписок:</b> {stats.get('active_subscriptions', 0)}\n"
        f"❌ <b>Истекших подписок:</b> {stats.get('expired_users', 0)}\n\n"
        f"💰 <b>Заработано за месяц:</b> {stats.get('monthly_revenue', 0)} ₽\n"
        f"💳 <b>Всего заработано:</b> {stats.get('total_revenue', 0)} ₽"
    )
    
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
