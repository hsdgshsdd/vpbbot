"""Расширенные админ хэндлеры для управления узлами, inbound'ами и статистикой"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import List
from src.utils.formatters import MessageFormatter, InlineKeyboardBuilder
from src.utils.db_service import AdminService
from src.api.marzneshin import api
import logging

logger = logging.getLogger(__name__)

formatter = MessageFormatter()
kb_builder = InlineKeyboardBuilder()

# ============ NODE MANAGEMENT ============

async def admin_nodes_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех узлов"""
    try:
        nodes_data = await api.get_nodes()
        nodes = nodes_data.get('items', [])
        
        if not nodes:
            await update.callback_query.answer("Нет узлов", show_alert=True)
            return
        
        text = "🖥 <b>Список узлов:</b>\n\n"
        
        for node in nodes[:10]:  # Show first 10 nodes
            status_emoji = "✅" if node.get('status') == 'connected' else "⚠️"
            text += f"{status_emoji} <b>{node['name']}</b>\n"
            text += f"  IP: {node['address']}\n"
            text += f"  Статус: {node.get('status', 'unknown')}\n\n"
        
        keyboard = kb_builder.admin_nodes_keyboard(page=context.user_data.get('node_page', 0))
        
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_nodes_list: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_add_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление нового узла"""
    context.user_data['add_node_step'] = 'name'
    
    await update.callback_query.edit_message_text(
        "📍 <b>Добавление нового узла</b>\n\n"
        "Введите название узла:",
        parse_mode='HTML'
    )

async def admin_node_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика по узлу"""
    try:
        nodes_data = await api.get_nodes()
        nodes = nodes_data.get('items', [])
        
        if not nodes:
            await update.callback_query.answer("Нет узлов", show_alert=True)
            return
        
        # Show first node stats as example
        node = nodes[0]
        node_id = node.get('id')
        
        usage_data = await api.get_node_usage(node_id)
        stats_data = await api.get_nodes_stats()
        
        text = f"📊 <b>Статистика узла: {node['name']}</b>\n\n"
        text += f"Адрес: {node['address']}\n"
        text += f"Статус: {node.get('status', 'unknown')}\n"
        
        if stats_data:
            text += f"Активных пользователей: {stats_data.get('total', 0)}\n"
        
        keyboard = kb_builder.admin_back_keyboard("admin_main")
        
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_node_stats: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)


# ============ INBOUND MANAGEMENT ============

async def admin_inbounds_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех inbound'ов"""
    try:
        inbounds_data = await api.get_inbounds()
        inbounds = inbounds_data.get('items', [])
        
        if not inbounds:
            await update.callback_query.answer("Нет inbound'ов", show_alert=True)
            return
        
        text = "📡 <b>Список Inbound'ов:</b>\n\n"
        
        for inbound in inbounds[:10]:
            text += f"<b>{inbound['tag']}</b>\n"
            text += f"  Протокол: {inbound.get('protocol', 'N/A')}\n"
            text += f"  Результат: {inbound.get('multiplex', 'No')}\n\n"
        
        keyboard = kb_builder.admin_inbounds_keyboard()
        
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_inbounds_list: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_add_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление нового хоста"""
    context.user_data['add_host_step'] = 'remark'
    
    await update.callback_query.edit_message_text(
        "🌐 <b>Добавление нового хоста</b>\n\n"
        "Введите описание хоста (remark):",
        parse_mode='HTML'
    )

async def admin_hosts_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех хостов"""
    try:
        hosts_data = await api.get_hosts()
        hosts = hosts_data.get('items', [])
        
        if not hosts:
            await update.callback_query.answer("Нет хостов", show_alert=True)
            return
        
        text = "🌐 <b>Список хостов:</b>\n\n"
        
        for host in hosts[:10]:
            text += f"<b>{host['remark']}</b>\n"
            text += f"  Адрес: {host['address']}\n"
            text += f"  SNI: {host.get('sni', 'N/A')}\n\n"
        
        keyboard = kb_builder.admin_hosts_keyboard()
        
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_hosts_list: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)


# ============ USER MANAGEMENT (ADVANCED) ============

async def admin_user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню действий с пользователем"""
    query = update.callback_query
    
    if 'selected_username' not in context.user_data:
        await query.answer("Пользователь не выбран", show_alert=True)
        return
    
    username = context.user_data['selected_username']
    
    text = f"👤 <b>Действия с пользователем: {username}</b>\n\n" \
           f"Выберите действие:"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Статистика", callback_data=f"user_stats:{username}"),
            InlineKeyboardButton("🔄 Сбросить трафик", callback_data=f"reset_user:{username}")
        ],
        [
            InlineKeyboardButton("⏸ Отключить", callback_data=f"disable_user:{username}"),
            InlineKeyboardButton("▶️ Включить", callback_data=f"enable_user:{username}")
        ],
        [
            InlineKeyboardButton("🚫 Отозвать подписку", callback_data=f"revoke_sub:{username}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"delete_user:{username}")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def admin_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика пользователя"""
    try:
        query = update.callback_query
        username = context.user_data.get('selected_username')
        
        if not username:
            await query.answer("Пользователь не выбран", show_alert=True)
            return
        
        user_data = await api.get_user(username)
        usage_data = await api.get_user_usage(username)
        
        text = f"📊 <b>Статистика пользователя: {username}</b>\n\n"
        text += f"Активен: {'✅' if user_data.get('enabled') else '❌'}\n"
        text += f"Дата истечения: {user_data.get('expire_date', 'N/A')}\n"
        
        if usage_data:
            total_usage = usage_data.get('total', 0)
            text += f"Использовано: {total_usage / (1024**3):.2f} GB\n"
        
        if user_data.get('data_limit'):
            limit = user_data.get('data_limit')
            text += f"Лимит: {limit / (1024**3):.2f} GB\n"
        
        keyboard = kb_builder.admin_back_keyboard("user_actions")
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_user_stats: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_disable_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отключить пользователя"""
    try:
        query = update.callback_query
        username = query.data.split(':')[1]
        
        await api.disable_user(username)
        
        # Log action
        AdminService.log_action(context.user_data.get('user_id'), "disable_user", username)
        
        await query.answer(f"✅ Пользователь {username} отключен", show_alert=True)
        context.user_data['selected_username'] = username
        await admin_user_actions(update, context)
        
    except Exception as e:
        logger.error(f"Error in admin_disable_user: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_enable_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить пользователя"""
    try:
        query = update.callback_query
        username = query.data.split(':')[1]
        
        await api.enable_user(username)
        
        # Log action
        AdminService.log_action(context.user_data.get('user_id'), "enable_user", username)
        
        await query.answer(f"✅ Пользователь {username} включен", show_alert=True)
        context.user_data['selected_username'] = username
        await admin_user_actions(update, context)
        
    except Exception as e:
        logger.error(f"Error in admin_enable_user: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_reset_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить трафик пользователя"""
    try:
        query = update.callback_query
        username = query.data.split(':')[1]
        
        await api.reset_user_data(username)
        
        # Log action
        AdminService.log_action(context.user_data.get('user_id'), "reset_data", username)
        
        await query.answer(f"✅ Трафик пользователя {username} сброшен", show_alert=True)
        context.user_data['selected_username'] = username
        await admin_user_actions(update, context)
        
    except Exception as e:
        logger.error(f"Error in admin_reset_user_data: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_revoke_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отозвать подписку пользователя"""
    try:
        query = update.callback_query
        username = query.data.split(':')[1]
        
        await api.revoke_user_subscription(username)
        
        # Log action
        AdminService.log_action(context.user_data.get('user_id'), "revoke_subscription", username)
        
        await query.answer(f"✅ Подписка пользователя {username} отозвана", show_alert=True)
        context.user_data['selected_username'] = username
        await admin_user_actions(update, context)
        
    except Exception as e:
        logger.error(f"Error in admin_revoke_subscription: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def admin_delete_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления пользователя"""
    query = update.callback_query
    username = query.data.split(':')[1]
    
    context.user_data['delete_user_confirm'] = username
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete:{username}"),
            InlineKeyboardButton("❌ Отмена", callback_data="user_actions")
        ]
    ])
    
    await query.edit_message_text(
        f"⚠️ <b>Вы уверены?</b>\n\n"
        f"Удалить пользователя <b>{username}</b>?\n"
        f"Это действие не может быть отменено!",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def admin_confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Окончательное удаление пользователя"""
    try:
        query = update.callback_query
        username = query.data.split(':')[1]
        
        await api.delete_user(username)
        
        # Log action
        AdminService.log_action(context.user_data.get('user_id'), "delete_user", username)
        
        await query.answer(f"✅ Пользователь {username} удален", show_alert=True)
        await admin_users(update, context)
        
    except Exception as e:
        logger.error(f"Error in admin_confirm_delete_user: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)


# ============ SYSTEM SETTINGS ============

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Системные настройки"""
    try:
        query = update.callback_query
        
        # Get settings
        sub_settings = await api.get_subscription_settings()
        telegram_settings = await api.get_telegram_settings()
        
        text = "⚙️ <b>Системные настройки</b>\n\n"
        text += "<b>Подписка:</b>\n"
        
        if sub_settings:
            text += f"  Формат: {sub_settings.get('format', 'N/A')}\n"
            text += f"  Включить хостов: {sub_settings.get('include_hosts', 'N/A')}\n"
        
        if telegram_settings:
            text += f"\n<b>Telegram:</b>\n"
            text += f"  API ID: {'✅' if telegram_settings.get('api_id') else '❌'}\n"
            text += f"  API Hash: {'✅' if telegram_settings.get('api_hash') else '❌'}\n"
        
        keyboard = kb_builder.admin_settings_keyboard()
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_settings: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)


# ============ DASHBOARD / ANALYTICS ============

async def admin_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Аналитика и статистика"""
    try:
        query = update.callback_query
        
        # Get statistics
        users_stats = await api.get_users_stats()
        nodes_stats = await api.get_nodes_stats()
        traffic_stats = await api.get_traffic_stats()
        
        text = "📈 <b>Аналитика и статистика</b>\n\n"
        
        if users_stats:
            text += f"👥 Всего пользователей: {users_stats.get('total_users', 0)}\n"
            text += f"   Активных: {users_stats.get('active_users', 0)}\n"
            text += f"   Истекших: {users_stats.get('expired_users', 0)}\n\n"
        
        if nodes_stats:
            text += f"🖥 Всего узлов: {nodes_stats.get('total_nodes', 0)}\n"
            text += f"   Подключено: {nodes_stats.get('connected_nodes', 0)}\n\n"
        
        text += "📊 Выберите период для подробного анализа:"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Сегодня", callback_data="analytics_today"),
                InlineKeyboardButton("Неделя", callback_data="analytics_week")
            ],
            [
                InlineKeyboardButton("Месяц", callback_data="analytics_month"),
                InlineKeyboardButton("Год", callback_data="analytics_year")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_main")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in admin_analytics: {e}")
        await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

# Stub for backward compatibility
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для совместимости"""
    await admin_user_actions(update, context)
