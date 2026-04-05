#!/bin/bash
# Скрипт быстрого старта SakuraVPN Bot

echo "🚀 SakuraVPN Telegram Bot - Быстрый старт"
echo "=========================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Пожалуйста установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"
echo ""

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    echo "✅ Окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

echo ""

# Активация окружения
echo "🔧 Активация окружения..."
source venv/bin/activate

echo ""

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✅ Зависимости установлены"
echo ""

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚙️ Создание .env из примера..."
    cp .env.example .env
    echo "❌ Пожалуйста отредактируйте .env файл со своими параметрами"
    echo "   1. Откройте .env файл"
    echo "   2. Заполните BOT_TOKEN, ADMIN_IDS и параметры API"
    echo "   3. Сохраните файл"
    echo "   4. Запустите скрипт снова"
    exit 1
fi

echo "✅ .env файл найден"
echo ""

# Инициализация базы данных
echo "📊 Инициализация базы данных..."
mkdir -p data
echo "✅ База данных готова"
echo ""

# Запуск бота
echo "🤖 Запуск бота..."
echo "=========================================="
echo ""
python3 main.py
