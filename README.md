# Микросервис уведомлений (Notify Service)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)
![Django REST Framework](https://img.shields.io/badge/DRF-3.16-red?logo=django)
![Celery](https://img.shields.io/badge/Celery-5.5-green?logo=celery)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-orange?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7.0-red?logo=redis)
![Docker](https://img.shields.io/badge/Docker-24.0-blue?logo=docker)
![Nginx](https://img.shields.io/badge/Nginx-1.25-green?logo=nginx)

## 📚 Описание

Микросервис для асинхронной отправки уведомлений по email и Telegram. Сервис предоставляет REST API для создания уведомлений с поддержкой отложенной отправки и детальным логированием доставки.

## 🧩 Основные функции

- **📧 Email уведомления** - отправка через SMTP сервер
- **📱 Telegram уведомления** - отправка через Telegram Bot API
- **⏰ Отложенная отправка** - поддержка задержек отправки (немедленно, через 1 час, через 1 день)
- **📊 Мониторинг доставки** - детальное логирование статусов отправки
- **🚀 Асинхронная обработка** - использование Celery для фоновой обработки задач
- **🔒 Безопасность** - блокировки для предотвращения дублирования отправки
- **📈 Health checks** - мониторинг состояния сервиса

## 🛠 Технологический стек

- **Django 5.2** - веб-фреймворк
- **Django REST Framework** - REST API
- **Celery** - асинхронная обработка задач
- **PostgreSQL** - основное хранилище данных
- **Redis** - брокер сообщений для Celery и кэширование
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy и статические файлы
- **Gunicorn** - WSGI сервер
- **Telegram Bot API** - отправка сообщений в Telegram

## 🏗 Архитектура

### Модели данных
- **Notification** - основная модель уведомления
- **Recipient** - получатели уведомления
- **DeliveryLog** - логи доставки сообщений

### Сервисы
- **NotificationService** - фасад для отправки уведомлений
- **EmailSender** - сервис отправки email
- **TelegramSender** - сервис отправки Telegram сообщений

### Celery задачи
- `send_notification_task` - основная задача отправки
- `send_email_task` - задача отправки email
- `send_telegram_task` - задача отправки Telegram

## 📋 API Endpoints

### Создание уведомления
```http
POST /api/notify/
```

### Тело запроса:

```json
{
  "message": "Текст уведомления",
  "recipient": ["user@example.com", "123456789"],
  "delay": 0
}
```

**Параметры:**

- `message` (string, 1-1024 символов) - текст сообщения
- `recipient` (array) - список получателей (email или числовой Telegram ID)
- `delay` (integer) - задержка отправки:
  - `0` - немедленно
  - `1` - через 1 час
  - `2` - через 1 день

### Health check
```http
GET /health/
```

## 🔧 Установка и запуск

### Требования

- Docker и Docker Compose
- Python 3.12 (для разработки)

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd notify-service
```

### 2. Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните необходимые переменные:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=notify
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=notify_service.db
POSTGRES_PORT=5432

# Email
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@yandex.ru
EMAIL_HOST_PASSWORD=your-password

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### 3. Запуск сервисов

```bash
# Запуск всех сервисов
docker-compose --profile app --profile first up --build

# Или выборочный запуск
docker-compose --profile app up --build      # Django + Nginx
docker-compose --profile worker up --build   # Celery worker + beat
docker-compose --profile migration up --build # Миграции БД
docker-compose --profile monitoring up # Flower
```

## 🚀 Использование

### Пример создания уведомления

```bash
curl -X POST http://localhost:8000/api/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Ваше бронирование подтверждено",
    "recipient": ["user@example.com", "123456789"],
    "delay": 0
  }'
```

### Получение статуса здоровья сервиса

```bash
curl http://localhost:8000/health/
```

## 🔒 Безопасность

- Валидация получателей (email и числовые Telegram ID)

- Блокировки для предотвращения дублирования отправки

- Ограничение длины сообщений

- Поддержка SSL/TLS для email

## 📈 Производительность

- Асинхронная обработка через Celery

- Connection pooling для БД

- Кэширование через Redis

- Поддержка горизонтального масштабирования

## 🤝 Разработка

### Установка для разработки

```bash
cd notify_api
poetry install
poetry shell
```

### Создание миграций

``bash
python manage.py makemigrations
```

### Запуск в режиме разработки

```bash
python manage.py runserver
```

### 👥 Авторы

- Евгений Кудряшов - [GitHub](https://github.com/GagarinRu/)
