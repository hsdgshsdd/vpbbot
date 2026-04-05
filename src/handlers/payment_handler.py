"""
Payment Handler с интеграцией Marzneshin API
Использует простую последовательность callbacks для создания подписки
"""

import logging
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.api.marzneshin import api
from src.utils.db_service import PaymentService, UserService
from src.utils.formatters import MessageFormatter, InlineKeyboardBuilder
from src.config import TARIFFS

logger = logging.getLogger(__name__)


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


async def tariff_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора тарифа → запрос username"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    tariff_key = query.data.replace('tariff_', '')
    
    if tariff_key not in TARIFFS:
        await query.answer("❌ Неизвестный тариф", show_alert=True)
        return
    
    tariff = TARIFFS[tariff_key]
    context.user_data['selected_tariff'] = {
        'key': tariff_key,
        'name': tariff['name'],
        'months': tariff['months'],
        'price': tariff['price']
    }
    context.user_data['expecting_username'] = True
    
    message = (
        "📝 <b>СОЗДАНИЕ ПОДПИСКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Выбран тариф: <b>{tariff['name']}</b>\n"
        f"Стоимость: <code>{tariff['price']} ₽</code>\n\n"
        "Введите имя пользователя для создания подписки:\n"
        "<i>Допустимые: буквы, цифры, подчеркивание (3-32 символа)</i>\n\n"
        "Например: <code>user_123</code>"
    )
    
    await query.edit_message_text(message, parse_mode='HTML')


async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода username и создание пользователя"""
    
    # Проверка что мы ожидаем username
    if not context.user_data.get('expecting_username'):
        return
    
    username = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Валидация username
    if not re.match(r'^[a-zA-Z0-9_]{3,32}$', username):
        await update.message.reply_text(
            "❌ <b>Некорректное имя пользователя!</b>\n\n"
            "Требования:\n"
            "• 3-32 символа\n"
            "• Только буквы, цифры, подчеркивание (_)\n\n"
            "Пример: <code>user_123</code>\n\n"
            "Попробуйте снова:",
            parse_mode='HTML'
        )
        return
    
    context.user_data['expecting_username'] = False
    context.user_data['username'] = username
    
    tariff = context.user_data.get('selected_tariff')
    if not tariff:
        await update.message.reply_text(
            "❌ Ошибка. Пожалуйста, начните с /start",
            parse_mode='HTML'
        )
        return
    
    # Проверить что такого пользователя еще нет в Marzneshin
    try:
        existing_user = await api.get_user(username)
        if existing_user:
            await update.message.reply_text(
                "❌ <b>Пользователь с таким именем уже существует!</b>\n\n"
                "Выберите другое имя:",
                parse_mode='HTML'
            )
            context.user_data['expecting_username'] = True
            return
    except Exception as e:
        # Если ошибка 404 - это нормально (пользователя нет)
        if "404" not in str(e) and "not found" not in str(e).lower():
            logger.error(f"Error checking username: {e}")
    
    # Показать подтверждение
    message = (
        "✅ <b>ПОДТВЕРЖДЕНИЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Имя пользователя:</b> <code>{username}</code>\n"
        f"<b>Тариф:</b> {tariff['name']}\n"
        f"<b>Цена:</b> <code>{tariff['price']} ₽</code>\n"
        f"<b>Срок:</b> {tariff['months']} мес.\n\n"
        "⚠️ <b>Важно:</b> После подтверждения пользователь будет создан\n"
        "и сразу получит доступ к конфигурации."
    )
    
    buttons = [
        [InlineKeyboardButton("✅ Подтвердить и оплатить", callback_data=f'confirm_create_user_{username}')],
        [InlineKeyboardButton("❌ Отмена", callback_data='payment_menu')]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )


async def confirm_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание пользователя в Marzneshin и обработка платежа"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Парсим username из callback_data
    username = query.data.replace('confirm_create_user_', '')
    tariff = context.user_data.get('selected_tariff')
    
    if not username or not tariff:
        await query.answer("❌ Ошибка. Попробуйте заново.", show_alert=True)
        return
    
    try:
        await query.answer("⏳ Создаем подписку...", show_alert=False)
        
        # 1. Получить список сервисов
        services_data = await api.get_services()
        service_ids = []
        
        if services_data and 'items' in services_data and services_data['items']:
            # Используем первый сервис
            service_ids = [services_data['items'][0]['id']]
        else:
            raise Exception("Сервисы не найдены. Обратитесь к администратору.")
        
        # 2. Рассчитать параметры
        expire_date = datetime.utcnow() + timedelta(days=30 * tariff['months'])
        
        # Лимит трафика: 500GB за 12 месяцев, пропорционально
        data_limit_per_month = 500 * 1024 * 1024 * 1024 / 12
        data_limit = int(data_limit_per_month * tariff['months'])
        
        # 3. Создать пользователя в Marzneshin
        user_data = {
            "username": username,
            "expire_strategy": "fixed_date",
            "expire_date": expire_date.isoformat(),
            "data_limit": data_limit,
            "service_ids": service_ids
        }
        
        logger.info(f"Creating user in Marzneshin: {username}")
        created_user = await api.create_user(**user_data)
        
        if not created_user:
            raise Exception("Не удалось создать пользователя в системе")
        
        # 4. Получить subscription key и URL
        sub_key = created_user.get('key', username)
        subscription_url = created_user.get('subscription_url', '')
        
        # 5. Записать в локальную БД (только username и key, остальное из API)
        payment = PaymentService.create_payment(user_id, tariff['price'], tariff['months'])
        PaymentService.complete_payment(payment.id)
        UserService.update_subscription(
            user_id,
            username=username,
            key=sub_key
        )
        
        # 6. Отправить сообщение об успехе
        message = (
            "🎉 <b>ПОДПИСКА УСПЕШНО СОЗДАНА!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Логин:</b> <code>{username}</code>\n"
            f"<b>Ключ подписки:</b> <code>{sub_key}</code>\n"
            f"<b>Действует до:</b> {expire_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Тариф:</b> {tariff['name']}\n\n"
            f"🔗 <b>Ссылка конфигурации:</b>\n"
            f"<code>{subscription_url}</code>\n\n"
            "📲 <b>Как подключиться:</b>\n"
            "1. 📋 Копируешь ссылку в браузер или QR код\n"
            "2. 📱 Открыть в мобильном VPN приложении\n"
            "3. ✅ Подписка автоматически добавится\n\n"
            "⚠️ <b>Сохрани эти данные в безопасном месте!</b>"
        )
        
        buttons = [
            [InlineKeyboardButton("📋 Загрузить конфиг", url=subscription_url)],
            [InlineKeyboardButton("🔑 Мой ключ", callback_data='update_keys')],
            [InlineKeyboardButton("🏠 На главную", callback_data='back_home')]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )
        
        logger.info(f"✅ User created successfully: {username} for Telegram ID {user_id}")
        
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        
        error_message = (
            "❌ <b>ОШИБКА ПРИ СОЗДАНИИ ПОДПИСКИ</b>\n\n"
            f"Причина: {str(e)}\n\n"
            "❕ Попробуйте позже или свяжитесь с поддержкой."
        )
        
        await query.edit_message_text(
            error_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='payment_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='back_home')]
            ]),
            parse_mode='HTML'
        )
