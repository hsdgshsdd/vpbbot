@echo off
REM Скрипт быстрого старта SakuraVPN Bot (Windows)

cls
echo 🚀 SakuraVPN Telegram Bot - Быстрый старт
echo ==========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен. Пожалуйста установите Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python найден: 
python --version
echo.

REM Создание виртуального окружения
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
    echo ✅ Окружение создано
) else (
    echo ✅ Виртуальное окружение уже существует
)

echo.

REM Активация окружения
echo 🔧 Активация окружения...
call venv\Scripts\activate.bat

echo.

REM Установка зависимостей
echo 📥 Установка зависимостей...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo ✅ Зависимости установлены
echo.

REM Проверка .env файла
if not exist ".env" (
    echo ⚙️ Создание .env из примера...
    copy .env.example .env
    echo ❌ Пожалуйста отредактируйте .env файл со своими параметрами
    echo    1. Откройте .env файл в блокноте
    echo    2. Заполните BOT_TOKEN, ADMIN_IDS и параметры API
    echo    3. Сохраните файл
    echo    4. Запустите скрипт снова
    pause
    exit /b 1
)

echo ✅ .env файл найден
echo.

REM Инициализация базы данных
echo 📊 Инициализация базы данных...
if not exist "data" mkdir data
echo ✅ База данных готова
echo.

REM Запуск бота
echo 🤖 Запуск бота...
echo ==========================================
echo.
python main.py

pause
