from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик callback'ов"""
    from src.handlers.user_handlers import (
        account, update_keys, payment_menu, help_command, tariff_selected, confirm_payment, start
    )
    from src.handlers.admin_handlers import (
        admin_start, admin_users, admin_users_list, admin_stats,
        admin_services, admin_inbounds, admin_settings, admin_logs, admin_check_api
    )
    from src.handlers.admin_extended_handlers import (
        # Node Management
        admin_nodes_list,
        admin_add_node,
        admin_node_stats,
        # Inbound Management
        admin_inbounds_list,
        admin_add_host,
        admin_hosts_list,
        # User Management
        admin_user_actions,
        admin_user_stats,
        admin_disable_user,
        admin_enable_user,
        admin_reset_user_data,
        admin_revoke_subscription,
        admin_delete_user_confirm,
        admin_confirm_delete_user,
        # System
        admin_settings as admin_settings_extended,
        admin_analytics,
    )
    from src.handlers.extended_handlers import (
        referrals, download_config, regenerate_key, admin_users_add,
        admin_users_search, admin_services_add, show_faq, show_faq_answer
    )
    
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Пользовательские команды
    if callback_data == 'account':
        await account(update, context)
    elif callback_data == 'update_keys':
        await update_keys(update, context)
    elif callback_data == 'payment_menu':
        await payment_menu(update, context)
    elif callback_data == 'help':
        await help_command(update, context)
    elif callback_data.startswith('tariff_'):
        await tariff_selected(update, context)
    elif callback_data.startswith('confirm_payment_'):
        await confirm_payment(update, context)
    elif callback_data == 'referrals':
        await referrals(update, context)
    elif callback_data == 'download_config':
        await download_config(update, context)
    elif callback_data == 'regenerate_key':
        await regenerate_key(update, context)
    elif callback_data == 'confirm_regenerate_key':
        await regenerate_key(update, context)  # Немного хака для совместимости
    
    # ============ Node Management Callbacks ============
    elif callback_data == 'admin_nodes_list':
        await admin_nodes_list(update, context)
    elif callback_data == 'admin_add_node':
        await admin_add_node(update, context)
    elif callback_data == 'admin_node_stats':
        await admin_node_stats(update, context)
    
    # ============ Inbound Management Callbacks ============
    elif callback_data == 'admin_inbounds_list':
        await admin_inbounds_list(update, context)
    elif callback_data == 'admin_hosts_list':
        await admin_hosts_list(update, context)
    elif callback_data == 'admin_add_host':
        await admin_add_host(update, context)
    
    # ============ Advanced User Management Callbacks ============
    elif callback_data == 'user_actions':
        await admin_user_actions(update, context)
    elif callback_data.startswith('user_stats:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_user_stats(update, context)
    elif callback_data.startswith('disable_user:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_disable_user(update, context)
    elif callback_data.startswith('enable_user:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_enable_user(update, context)
    elif callback_data.startswith('reset_user:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_reset_user_data(update, context)
    elif callback_data.startswith('revoke_sub:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_revoke_subscription(update, context)
    elif callback_data.startswith('delete_user:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_delete_user_confirm(update, context)
    elif callback_data.startswith('confirm_delete:'):
        context.user_data['selected_username'] = callback_data.split(':')[1]
        await admin_confirm_delete_user(update, context)
    
    # ============ System Management Callbacks ============
    elif callback_data == 'admin_settings':
        await admin_settings_extended(update, context)
    elif callback_data in ['admin_analytics', 'analytics_today', 'analytics_week', 'analytics_month', 'analytics_year']:
        await admin_analytics(update, context)
    
    # Старые админ команды
    elif callback_data == 'admin_main':
        await admin_start(update, context)
    elif callback_data == 'admin_users':
        await admin_users(update, context)
    elif callback_data == 'admin_users_list':
        await admin_users_list(update, context)
    elif callback_data == 'admin_users_add':
        await admin_users_add(update, context)
    elif callback_data == 'admin_users_search':
        await admin_users_search(update, context)
    elif callback_data == 'admin_stats':
        await admin_stats(update, context)
    elif callback_data == 'admin_services':
        await admin_services(update, context)
    elif callback_data == 'admin_services_add':
        await admin_services_add(update, context)
    elif callback_data == 'admin_inbounds':
        await admin_inbounds(update, context)
    elif callback_data == 'admin_logs':
        await admin_logs(update, context)
    elif callback_data == 'admin_check_api':
        await admin_check_api(update, context)
    
    # FAQ обработчики
    elif callback_data == 'faq_menu':
        await show_faq(update, context)
    elif callback_data.startswith('faq_'):
        faq_index = int(callback_data.split('_')[1])
        await show_faq_answer(update, context, faq_index)
    
    # Утилиты
    elif callback_data == 'copy_referral_link':
        from src.handlers.extended_handlers import copy_referral_link
        await copy_referral_link(update, context)
    
    # Кнопки навигации
    elif callback_data == 'back_home':
        await start(update, context)
    elif callback_data == 'back_account':
        await account(update, context)
