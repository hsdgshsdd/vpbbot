from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_chat:
        try:
            await update.effective_chat.send_message(
                "⚠️ Произошла ошибка.\n\n"
                "Пожалуйста, попробуйте позже или напишите поддержке."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
