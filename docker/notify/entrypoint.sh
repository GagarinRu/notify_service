#!/usr/bin/env bash
set -e

# === Функция: ожидание доступности PostgreSQL ===
wait_for_postgres() {
    echo "Ожидание готовности базы данных PostgreSQL..."
    python << END
import time
import asyncpg
import asyncio
import os

dsn = os.environ.get("POSTGRES_DSN")
if not dsn:
    raise RuntimeError("POSTGRES_DSN не задан")

async def wait_for_db():
    while True:
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            print("PostgreSQL доступна.")
            break
        except Exception as e:
            print(f"PostgreSQL недоступна: {e}. Жду...")
            time.sleep(2)

asyncio.run(wait_for_db())
END
}

# === Определяем тип сервиса по переменной окружения ===
SERVICE_TYPE=${SERVICE_TYPE:-app}

case "$SERVICE_TYPE" in
  app|celery_worker|celery_beat|migration)
    wait_for_postgres
    ;;
  flower)
    echo "Запуск Flower (проверка PostgreSQL пропущена)"
    ;;
  *)
    echo "Неизвестный тип сервиса: $SERVICE_TYPE" >&2
    exit 1
    ;;
esac

# === Выполняем действия в зависимости от типа сервиса ===
case "$SERVICE_TYPE" in
  app)
    echo "Старт Gunicorn"
    exec gunicorn config.wsgi:application \
        --bind "${GUNICORN_HOST}:${GUNICORN_PORT}" \
        --workers 3 \
        --timeout 120 \
        --preload
    ;;
  celery_worker)
    echo "Запуск Celery Worker"
    exec celery -A config worker --loglevel=info --concurrency=1 --max-tasks-per-child=1
    ;;
  celery_beat)
    echo "Запуск Celery Beat"
    exec celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;
  flower)
    echo "Запуск Flower"
    exec celery -A config flower --port=${CELERY_FLOWER_PORT} --broker=${CELERY_BROKER_URL}
    ;;
  migration)
    echo "Создание миграций..."
    python3 manage.py makemigrations --noinput
    echo "Выполнение миграций"
    python3 manage.py migrate --noinput
    echo "Миграции выполнены успешно"
    ;;
esac