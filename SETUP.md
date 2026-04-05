# Инструкция по установке и настройке SakuraVPN Telegram Bot

## Быстрый старт

### 1️⃣ Подготовка
Убедитесь, что у вас установлены:
- Python 3.8 или выше
- pip (обычно идет с Python)

### 2️⃣ Копирование конфигурации
```bash
cp .env.example .env
```

### 3️⃣ Редактирование .env файла

Откройте файл `.env` и заполните следующие параметры:

```env
# 🤖 Telegram Bot Token
BOT_TOKEN=your_bot_token_here
```
Как получить:
1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/botfather)
3. Отправьте `/newbot`
4. Следуйте инструкциям
5. Скопируйте полученный токен

```env
# 👨‍💼 ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321
```
Как получить ваш ID:
1. Отправьте боту [@userinfobot](https://t.me/userinfobot) любое сообщение
2. Он вернет ваш ID
3. Для нескольких администраторов разделите запятыми

```env
# 🖥️ Marzneshin API конфигурация
API_BASE_URL=http://localhost:8000
API_USERNAME=admin
API_PASSWORD=admin
```
Здесь укажите данные вашего Marzneshin сервера

### 4️⃣ Установка зависимостей
```bash
pip install -r requirements.txt
```

### 5️⃣ Запуск бота

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
bash run.sh
```

**Или прямо через Python:**
```bash
python main.py
```

## Верификация установки

1. Откройте Telegram
2. Найдите вашего бота по имени
3. Отправьте команду `/start`
4. Должно появиться главное меню

Если администратор, должно отобразиться меню администратора.
Если обычный пользователь, должно отобразиться меню пользователя.

## Интеграция платежной системы

В текущей версии используются заглушки платежей. Для реальной интеграции:

### Вариант 1: Yandex.Kassa
```bash
pip install yookassa
```

### Вариант 2: Stripe
```bash
pip install stripe
```

### Вариант 3: LiqPay
```bash
pip install liqpay
```

После установки отредактируйте `src/handlers/user_handlers.py` функцию `confirm_payment()`.

## Интеграция конфигураций

Для отправки конфигураций пользователям (Windows, iOS, Android), обновите ссылки в `src/utils/formatters.py`:

```python
# Замените примеры ссылок на реальные
InlineKeyboardButton("🪟 Windows", url='https://your-domain.com/configs/windows'),
InlineKeyboardButton("🍎 iOS", url='https://your-domain.com/configs/ios'),
InlineKeyboardButton("🤖 Android", url='https://your-domain.com/configs/android'),
```

## Часто задаваемые вопросы

### Вопрос: Как добавить нового администратора?
**Ответ:** Отредактируйте `.env` файл и добавьте ID в `ADMIN_IDS`:
```env
ADMIN_IDS=123456789,987654321,555666777
```
Затем перезагрузите бота.

### Вопрос: Как изменить тарифы?
**Ответ:** Отредактируйте `src/config.py`, секция `TARIFFS`:
```python
TARIFFS = {
    '1': {'months': 1, 'price': 99, 'name': '1 месяц'},
    # ...
}
```

### Вопрос: Где хранятся данные?
**Ответ:** В `data/bot.db` (SQLite база данных).

### Вопрос: Как просмотреть логи?
**Ответ:** Логи выводятся в консоль при запуске бота. 
Для сохранения в файл, отредактируйте `main.py`:
```python
logging.basicConfig(
    filename='bot.log',
    format='...',
    level=logging.INFO
)
```

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|---------|--------|
| BOT_TOKEN | Токен Telegram бота | `123456:ABC-DEF...` |
| ADMIN_IDS | ID администраторов | `123456,789012` |
| API_BASE_URL | URL Marzneshin API | `http://localhost:8000` |
| API_USERNAME | Логин для API | `admin` |
| API_PASSWORD | Пароль для API | `password123` |
| DB_PATH | Путь к БД | `data/bot.db` |
| DEBUG | Режим отладки | `True` или `False` |

## Структура данных

### Таблица users
- **telegram_id** - ID пользователя в Telegram
- **username** - никнейм в Telegram
- **is_admin** - администратор ли пользователь
- **subscription_key** - ключ подписки
- **subscription_active** - активна ли подписка
- **subscription_expires_at** - дата истечения подписки

### Таблица payments
- **telegram_id** - кто совершил платеж
- **amount** - сумма платежа
- **months** - количество месяцев подписки
- **status** - статус платежа (pending, completed, cancelled)
- **created_at** - дата создания платежа
- **completed_at** - дата завершения платежа

## Docker (опционально)

Для запуска в Docker создайте файл `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Затем:
```bash
docker build -t sakuravpn-bot .
docker run -d --env-file .env sakuravpn-bot
```

## Поддержка и помощь

Если у вас возникли проблемы:
1. Проверьте наличие всех зависимостей: `pip list | grep telegram`
2. Проверьте внешний IP доступ
3. Проверьте правильность token'ов в .env
4. Посмотрите логи запуска
5. Создайте issue на GitHub

---

**Готово! Ваш бот установлен и запущен! 🎉**
