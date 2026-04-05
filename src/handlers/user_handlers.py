from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.utils.db_service import UserService, PaymentService
from src.utils.formatters import MessageFormatter, InlineKeyboardBuilder
from src.utils.permissions import is_admin
from src.api.marzneshin import api
import logging

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Неизвестный пользователь"
    
    # Создать или получить пользователя в БД
    user = UserService.get_or_create_user(user_id, username)
    
    if await is_admin(user_id):
        # Главное меню для администратора
        await update.message.reply_text(
            MessageFormatter.admin_main_menu(),
            reply_markup=InlineKeyboardBuilder.admin_main_keyboard(),
            parse_mode='HTML'
        )
    else:
        # Главное меню для обычного пользователя
        buttons = [
            [InlineKeyboardButton("👤 Личный кабинет", callback_data='account')],
            [InlineKeyboardButton("🔑 Обновить ключи", callback_data='update_keys')],
            [InlineKeyboardButton("💳 Оплата", callback_data='payment_menu')],
            [InlineKeyboardButton("❓ Помощь", callback_data='help')]
        ]
        
        await update.message.reply_text(
            "👋 <b>Добро пожаловать в SakuraVPN!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите опцию из меню ниже:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )


async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /account или кнопка личного кабинета"""
    user_id = update.effective_user.id
    
    subscription_info = UserService.get_subscription_info(user_id)
    
    message = MessageFormatter.user_account_message(user_id, subscription_info)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardBuilder.user_account_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardBuilder.user_account_keyboard(),
            parse_mode='HTML'
        )


async def update_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /update_keys"""
    user_id = update.effective_user.id
    
    user = UserService.get_user(user_id)
    
    if not user or not user.subscription_key:
        message = (
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Пожалуйста, оформите подписку для получения ключа доступа."
        )
        
        buttons = [
            [InlineKeyboardButton("💳 Оформить подписку", callback_data='payment_menu')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_home')]
        ]
    else:
        message = (
            "🔑 <b>ВАШ КЛЮЧ ПОДПИСКИ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<code>{user.subscription_key}</code>\n\n"
            "⚠️ <b>Сохраните ключ в безопасном месте!</b>\n"
            "Не делитесь этим ключом с другими.\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        
        buttons = [
            [InlineKeyboardButton("📋 Загрузить конфигурацию", callback_data='download_config')],
            [InlineKeyboardButton("🔄 Получить новый ключ", callback_data='regenerate_key')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_home')]
        ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )


async def payment_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню выбора тарифа"""
    
    message = MessageFormatter.subscription_purchase_message()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardBuilder.tariff_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardBuilder.tariff_keyboard(),
            parse_mode='HTML'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    
    message = MessageFormatter.help_message()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data='back_home')]
            ]),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data='back_home')]
            ]),
            parse_mode='HTML'
        )
