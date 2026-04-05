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
    """Команда /account или кнопка личного кабинета - показывает данные из API"""
    user_id = update.effective_user.id
    
    # Сначала получаем username из локальной БД
    user = UserService.get_user(user_id)
    
    if not user or not user.username:
        # Если нет пользователя в БД, показываем приглашение купить подписку
        message = (
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Пожалуйста, оформите подписку для получения доступа."
        )
        
        buttons = [
            [InlineKeyboardButton("💳 Оформить подписку", callback_data='payment_menu')],
            [InlineKeyboardButton("🏠 На главную", callback_data='back_home')]
        ]
        
        reply_markup = InlineKeyboardMarkup(buttons)
    else:
        # Получаем информацию о подписке из API
        try:
            api_user = await api.get_user(user.username)
            
            # Форматируем информацию из API
            enabled = api_user.get('enabled', False)
            expire_date = api_user.get('expire_date', 'N/A')
            data_limit = api_user.get('data_limit', 0)
            used_traffic = api_user.get('used_traffic', 0)
            
            # Конвертируем в GB
            data_limit_gb = data_limit / (1024**3) if data_limit else 0
            used_traffic_gb = used_traffic / (1024**3) if used_traffic else 0
            
            status = "✅ Активна" if enabled else "❌ Отключена"
            
            message = (
                "👤 <b>МОЙ ЛИЧНЫЙ КАБИНЕТ</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Статус:</b> {status}\n"
                f"<b>Логин:</b> <code>{user.username}</code>\n"
                f"<b>Ключ подписки:</b> <code>{user.subscription_key[:20]}...</code>\n\n"
                f"📊 <b>Трафик:</b>\n"
                f"   Использовано: {used_traffic_gb:.2f} GB\n"
                f"   Лимит: {data_limit_gb:.2f} GB\n"
                f"   Осталось: {max(0, data_limit_gb - used_traffic_gb):.2f} GB\n\n"
                f"📅 <b>Действует до:</b> {expire_date[:10] if isinstance(expire_date, str) else 'N/A'}\n\n"
                f"<i>Данные обновлены из Marzneshin панели</i>"
            )
            
            buttons = [
                [InlineKeyboardButton("🔑 Мой ключ", callback_data='update_keys')],
                [InlineKeyboardButton("💳 Продлить подписку", callback_data='payment_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='back_home')]
            ]
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            # Если API недоступен, используем локальную БД как fallback
            logger.error(f"Error fetching user from API: {e}")
            
            subscription_info = UserService.get_subscription_info(user_id)
            message = (
                f"👤 <b>МОЙ ЛИЧНЫЙ КАБИНЕТ</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Логин:</b> <code>{user.username}</code>\n"
                f"<b>Ключ подписки:</b> <code>{user.subscription_key[:20] if user.subscription_key else 'N/A'}...</code>\n\n"
                f"<b>Статус подписки:</b> {'✅ Активна' if subscription_info.get('active') else '❌ Истекла'}\n"
                f"<b>Осталось дней:</b> {subscription_info.get('days_left', 0)}\n\n"
                "<i>⚠️ Данные загружены из кэша (API недоступен)</i>"
            )
            
            buttons = [
                [InlineKeyboardButton("🔑 Мой ключ", callback_data='update_keys')],
                [InlineKeyboardButton("💳 Продлить подписку", callback_data='payment_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='back_home')]
            ]
            
            reply_markup = InlineKeyboardMarkup(buttons)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
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
