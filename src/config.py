import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Основная конфигурация приложения"""
    
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    ADMIN_IDS: List[int] = []
    
    # API
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
    API_USERNAME = os.getenv('API_USERNAME', 'admin')
    API_PASSWORD = os.getenv('API_PASSWORD', 'admin')
    
    # Database
    DB_PATH = os.getenv('DB_PATH', 'data/bot.db')
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    def __init__(self):
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            self.ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',')]
    
    @staticmethod
    def get_admin_ids() -> List[int]:
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            return [int(id.strip()) for id in admin_ids_str.split(',')]
        return []

# Глобальная конфигурация
config = Config()

# Тарифы
TARIFFS = {
    '1': {'months': 1, 'price': 99, 'name': '1 месяц'},
    '3': {'months': 3, 'price': 289, 'name': '3 месяца'},
    '6': {'months': 6, 'price': 579, 'name': '6 месяцев'},
    '12': {'months': 12, 'price': 999, 'name': '12 месяцев'},
}

# Текстовые константы
TEXTS = {
    'start': '👋 Добро пожаловать в SakuraVPN!\n\nВыберите опцию:',
    'account': '👤 Личный кабинет',
    'update_keys': '🔑 Обновить ключи',
    'payment': '💳 Оплата',
    'help': '❓ Помощь',
}
