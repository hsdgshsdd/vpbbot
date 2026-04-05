"""
Администраторские команды (текстовые команды для админ-функций)
Повторяют функционал кнопок админки
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.utils.permissions import check_admin
from src.utils.db_service import UserService
from src.api.marzneshin import api
import logging

logger = logging.getLogger(__name__)


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /adduser TELEGRAM_ID - добавить пользователя
    Пример: /adduser 6392184784
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    # Проверяем аргументы
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❓ <b>ИСПОЛЬЗОВАНИЕ:</b> /adduser TELEGRAM_ID\n\n"
            "Пример: <code>/adduser 6392184784</code>",
            parse_mode='HTML'
        )
        return
    
    # Валидируем ID
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Telegram ID должен быть числом\n"
            "Пример: <code>/adduser 6392184784</code>",
            parse_mode='HTML'
        )
        return
    
    # Проверяем, существует ли уже пользователь
    target_user = UserService.get_user(target_user_id)
    
    if target_user:
        message = (
            f"⚠️ <b>ПОЛЬЗОВАТЕЛЬ УЖЕ СУЩЕСТВУЕТ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Telegram ID:</b> <code>{target_user.telegram_id}</code>\n"
            f"<b>Логин:</b> {target_user.username or 'N/A'}\n"
            f"<b>Ключ:</b> {target_user.subscription_key[:20] + '...' if target_user.subscription_key else 'Нет'}"
        )
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        # Создаём нового пользователя
        new_user = UserService.create_user(target_user_id, f"user_{target_user_id}")
        message = (
            f"✅ <b>ПОЛЬЗОВАТЕЛЬ ДОБАВЛЕН</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Telegram ID:</b> <code>{new_user.telegram_id}</code>\n"
            f"<b>Логин:</b> {new_user.username}\n"
            f"<b>Создан:</b> {new_user.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await update.message.reply_text(message, parse_mode='HTML')


async def cmd_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /userinfo TELEGRAM_ID - информация о пользователе
    Пример: /userinfo 6392184784
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❓ <b>ИСПОЛЬЗОВАНИЕ:</b> /userinfo TELEGRAM_ID\n\n"
            "Пример: <code>/userinfo 6392184784</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом", parse_mode='HTML')
        return
    
    # Получаём информацию из локальной БД
    user = UserService.get_user(target_user_id)
    
    if not user:
        await update.message.reply_text(
            f"❌ Пользователь с ID <code>{target_user_id}</code> не найден",
            parse_mode='HTML'
        )
        return
    
    # Если есть username, пытаемся получить информацию из API
    api_info = ""
    if user.username:
        try:
            api_user = await api.get_user(user.username)
            enabled = api_user.get('enabled', False)
            expire_date = api_user.get('expire_date', 'N/A')
            data_limit = api_user.get('data_limit', 0)
            used_traffic = api_user.get('used_traffic', 0)
            
            data_limit_gb = data_limit / (1024**3) if data_limit else 0
            used_traffic_gb = used_traffic / (1024**3) if used_traffic else 0
            
            api_info = (
                f"\n<b>📊 Данные из Marzneshin API:</b>\n"
                f"   <b>Статус:</b> {'✅ Активна' if enabled else '❌ Отключена'}\n"
                f"   <b>Истекает:</b> {expire_date[:10] if isinstance(expire_date, str) else 'N/A'}\n"
                f"   <b>Трафик:</b> {used_traffic_gb:.2f}GB / {data_limit_gb:.2f}GB"
            )
        except Exception as e:
            logger.error(f"Error getting user from API: {e}")
            api_info = f"\n⚠️ <i>API недоступен: {str(e)[:50]}</i>"
    
    message = (
        f"👤 <b>ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Telegram ID:</b> <code>{user.telegram_id}</code>\n"
        f"<b>Логин (Marzneshin):</b> {user.username or 'N/A'}\n"
        f"<b>Ключ подписки:</b> {user.subscription_key[:30] + '...' if user.subscription_key else 'Нет'}\n"
        f"<b>Администратор:</b> {'✅ Да' if user.is_admin else '❌ Нет'}\n"
        f"<b>Создан:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}"
        f"{api_info}"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /listusers [страница] - список пользователей
    Пример: /listusers или /listusers 1
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    page = 1
    if context.args and context.args[0].isdigit():
        page = int(context.args[0])
    
    try:
        users_data = await api.get_users(page=page, size=10)
        users = users_data.get('items', [])
        
        message = f"👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ (стр. {page})</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not users:
            message += "Нет пользователей на этой странице"
        else:
            for user in users:
                username = user.get('username', 'N/A')
                enabled = user.get('enabled', False)
                status = "✅" if enabled else "❌"
                expire_date = user.get('expire_date', 'N/A')
                
                message += f"{status} <b>{username}</b> (до {expire_date[:10] if isinstance(expire_date, str) else 'N/A'})\n"
        
        # Добавляем информацию о навигации
        total = users_data.get('total', 0)
        total_pages = (total + 9) // 10
        message += f"\n<i>Всего: {total} чел. | Страница {page}/{total_pages}</i>"
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        message = f"❌ Ошибка при загрузке пользователей: {str(e)[:100]}"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cmd_listservices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /listservices - список всех сервисов
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        services_data = await api.get_services()
        services = services_data.get('items', [])
        
        message = "🎁 <b>СПИСОК СЕРВИСОВ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not services:
            message += "Нет сервисов"
        else:
            for service in services:
                name = service.get('name', 'N/A')
                service_id = service.get('id', 'N/A')
                user_count = len(service.get('user_ids', []))
                message += f"🎯 <b>{name}</b> (ID: {service_id})\n   Пользователей: {user_count}\n\n"
        
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        message = f"❌ Ошибка: {str(e)[:100]}"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cmd_listnodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /listnodes - список всех узлов
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        nodes_data = await api.get_nodes()
        nodes = nodes_data.get('items', [])
        
        message = "🖥 <b>СПИСОК УЗЛОВ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not nodes:
            message += "Нет узлов"
        else:
            for node in nodes:
                name = node.get('name', 'N/A')
                address = node.get('address', 'N/A')
                status = node.get('status', 'unknown')
                status_emoji = "✅" if status == 'connected' else "⚠️"
                message += f"{status_emoji} <b>{name}</b>\n   Адрес: {address}\n   Статус: {status}\n\n"
        
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        message = f"❌ Ошибка: {str(e)[:100]}"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /stats - статистика системы
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        users_stats = await api.get_users_stats()
        nodes_stats = await api.get_nodes_stats()
        
        message = "📊 <b>СТАТИСТИКА СИСТЕМЫ</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += f"👥 <b>Пользователи:</b>\n"
        message += f"   Всего: {users_stats.get('total_users', 0)}\n"
        message += f"   Активных: {users_stats.get('active_users', 0)}\n"
        message += f"   Истекших: {users_stats.get('expired_users', 0)}\n\n"
        
        message += f"🖥 <b>Узлы:</b>\n"
        message += f"   Всего: {nodes_stats.get('total_nodes', 0)}\n"
        message += f"   Подключено: {nodes_stats.get('connected_nodes', 0)}\n\n"
        
        message += f"<i>Обновлено: {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}</i>"
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        message = f"❌ Ошибка: {str(e)[:100]}"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cmd_adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /adminhelp - справка по администраторским командам
    """
    if not await check_admin(update, context):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    message = (
        "🛠 <b>АДМИНИСТРАТОРСКИЕ КОМАНДЫ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "<b>👥 Управление пользователями:</b>\n"
        "   /adduser TELEGRAM_ID - добавить пользователя\n"
        "   /userinfo TELEGRAM_ID - информация о пользователе\n"
        "   /listusers [стр] - список пользователей\n\n"
        
        "<b>🎁 Управление сервисами:</b>\n"
        "   /listservices - список сервисов\n\n"
        
        "<b>🖥 Управление узлами:</b>\n"
        "   /listnodes - список узлов\n\n"
        
        "<b>📊 Статистика и аналитика:</b>\n"
        "   /stats - общая статистика\n"
        "   /adminhelp - эта справка\n\n"
        
        "<i>Примеры:</i>\n"
        "   <code>/adduser 6392184784</code>\n"
        "   <code>/userinfo 6392184784</code>\n"
        "   <code>/listusers 1</code>"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')
