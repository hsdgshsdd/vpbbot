#!/usr/bin/env python3
"""
SakuraVPN Telegram Bot
Полнофункциональный бот для управления VPN подписками
"""

import logging
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from telegram.error import TelegramError

from src.config import config
from src.models import init_db
from src.handlers.user_handlers import (
    start, account, update_keys, payment_menu, help_command
)
from src.handlers.admin_handlers import admin_start
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
    admin_settings,
    admin_analytics,
)
from src.handlers.callback_handler import callback_handler
from src.utils.error_handler import error_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not config.DEBUG else logging.DEBUG
)

logger = logging.getLogger(__name__)


def main():
    """Основная функция запуска бота"""
    
    # Проверка конфигурации
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле")
        sys.exit(1)
    
    logger.info("🚀 Запуск SakuraVPN Telegram Bot...")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    # Инициализация базы данных
    logger.info("📊 Инициализация базы данных...")
    init_db()
    logger.info("✅ База данных готова")
    
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Добавление обработчиков команд
    logger.info("🔧 Регистрация обработчиков...")
    
    # Команды для всех пользователей
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("account", account))
    application.add_handler(CommandHandler("update_keys", update_keys))
    application.add_handler(CommandHandler("payment", payment_menu))
    application.add_handler(CommandHandler("help", help_command))
    
    # Команды только для администраторов
    application.add_handler(CommandHandler("admin", admin_start))
    
    # ============ Node Management Handlers ============
    application.add_handler(CallbackQueryHandler(
        admin_nodes_list, pattern='^admin_nodes_list$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_add_node, pattern='^admin_add_node$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_node_stats, pattern='^admin_node_stats$'
    ))
    
    # ============ Inbound Management Handlers ============
    application.add_handler(CallbackQueryHandler(
        admin_inbounds_list, pattern='^admin_inbounds_list$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_hosts_list, pattern='^admin_hosts_list$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_add_host, pattern='^admin_add_host$'
    ))
    
    # ============ Advanced User Management Handlers ============
    application.add_handler(CallbackQueryHandler(
        admin_user_actions, pattern='^user_actions$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_user_stats, pattern='^user_stats:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_disable_user, pattern='^disable_user:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_enable_user, pattern='^enable_user:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_reset_user_data, pattern='^reset_user:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_revoke_subscription, pattern='^revoke_sub:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_delete_user_confirm, pattern='^delete_user:'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_confirm_delete_user, pattern='^confirm_delete:'
    ))
    
    # ============ System Management Handlers ============
    application.add_handler(CallbackQueryHandler(
        admin_settings, pattern='^admin_settings$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_analytics, pattern='^admin_analytics$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_analytics, pattern='^analytics_(today|week|month|year)$'
    ))
    
    # Обработчик callback'ов (универсальный, для всех остальных)
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("✅ Обработчики зарегистрированы")
    
    # Запуск бота
    logger.info("🤖 Бот запущен и слушает обновления...")
    logger.info(f"📋 Администраторы: {config.get_admin_ids()}")
    
    try:
        application.run_polling(allowed_updates=None)
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except TelegramError as e:
        logger.error(f"❌ Ошибка Telegram: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
