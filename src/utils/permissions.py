from telegram import Update
from telegram.ext import ContextTypes
from src.utils.db_service import UserService
from config import config


async def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return user_id in config.get_admin_ids()


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверить права администратора"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text(
            "❌ У вас нет доступа к этой команде.\n"
            "Это команда только для администраторов."
        )
        return False
    return True
