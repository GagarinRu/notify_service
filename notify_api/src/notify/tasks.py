import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from redis import Redis

from .choices import StatusChoices, StatusDeliveryChoices
from .models import DeliveryLog, Notification
from .services import NotificationService

logger = logging.getLogger(__name__)

redis_client = Redis.from_url(settings.CELERY_BROKER_URL)


def acquire_lock(lock_key: str) -> bool:
    """Установка блокировки для задачи."""
    if not redis_client:
        return True
    result = redis_client.set(
        lock_key,
        "processing",
        ex=settings.EMAIL_TASK_LOCK_TIMEOUT,
        nx=True,
    )
    return bool(result)


def release_lock(lock_key: str) -> None:
    """Снятие блокировки задачи."""
    if redis_client:
        redis_client.delete(lock_key)


@contextmanager
def task_lock(lock_key: str, timeout: int | None = None) -> Generator[bool, None, None]:
    """
    Context manager для работы с блокировками задач.
    """
    if timeout is None:
        timeout = settings.EMAIL_TASK_LOCK_TIMEOUT
    is_locked = acquire_lock(lock_key)
    try:
        yield is_locked
    finally:
        if is_locked:
            release_lock(lock_key)


@shared_task(
    bind=True,
    queue="notify",
    autoretry_for=(Exception,),
    retry_backoff=settings.EMAIL_TASK_RETRY_DELAY,
    max_retries=settings.EMAIL_TASK_MAX_RETRIES,
)
def send_email_task(self: Any, subject: str, message: str, to_email: str | list[str]) -> bool:
    """Задача для отправки email."""
    if not isinstance(to_email, list):
        to_email = [to_email]
    lock_key = f"email_lock:{subject}:{hash(frozenset(to_email))}"
    with task_lock(lock_key) as is_locked:
        if not is_locked:
            logger.info(f"Email задача пропущена (блокировка): {to_email}")
            return False
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=to_email,
            )
            email.send(fail_silently=False)
            logger.info(f"Email отправлен: {subject} -> {to_email}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки email {subject} -> {to_email}: {e}")
            raise self.retry(exc=e) from e


@shared_task(
    bind=True,
    queue="notify",
    autoretry_for=(Exception,),
    retry_backoff=settings.EMAIL_TASK_RETRY_DELAY,
    max_retries=settings.EMAIL_TASK_MAX_RETRIES,
)
def send_telegram_task(self: Any, message: str, chat_ids: list[str]) -> bool:
    """Задача для отправки Telegram сообщений."""
    from telebot import TeleBot
    from telebot.apihelper import ApiException

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.error("Telegram bot token не настроен")
        return False
    lock_key = f"telegram_lock:{hash(message)}:{hash(frozenset(chat_ids))}"
    with task_lock(lock_key) as is_locked:
        if not is_locked:
            logger.info(f"Telegram задача пропущена (блокировка): {chat_ids}")
            return False
        try:
            bot = TeleBot(bot_token)
            success_count = 0
            for chat_id in chat_ids:
                try:
                    bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
                    success_count += 1
                    logger.info(f"Telegram отправлено: {chat_id}")
                except ApiException as e:
                    error_description = str(e)
                    logger.error(f"Telegram ошибка для {chat_id}: {error_description}")
                except Exception as e:
                    logger.error(f"Ошибка отправки Telegram для {chat_id}: {e}")
            return success_count > 0
        except Exception as e:
            logger.error(f"Общая ошибка отправки telegram: {e}")
            raise self.retry(exc=e) from e


@shared_task(
    bind=True,
    queue="notify",
    autoretry_for=(Exception,),
    retry_backoff=settings.EMAIL_TASK_RETRY_DELAY,
    retry_backoff_max=settings.EMAIL_TASK_STATE_TIMEOUT,
    max_retries=settings.EMAIL_TASK_MAX_RETRIES,
)
def send_notification_task(self: Any, notification_id: int) -> bool:
    """Основная задача для отправки уведомления."""
    lock_key = f"notification_lock:{notification_id}"
    with task_lock(lock_key) as is_locked:
        if not is_locked:
            logger.info(f"Уведомление {notification_id} пропущено (блокировка)")
            return False

        try:
            notification = Notification.objects.get(id=notification_id)
            notification_service = NotificationService()

            recipients_data = {}
            for recipient in notification.recipients.all():
                if recipient.recipient_type not in recipients_data:
                    recipients_data[recipient.recipient_type] = []
                recipients_data[recipient.recipient_type].append(recipient.address)

            results = notification_service.send_notification(
                notification.message,
                recipients_data,
            )
            for recipient in notification.recipients.all():
                success = results.get(recipient.recipient_type, False)
                DeliveryLog.objects.create(
                    recipient=recipient,
                    status=StatusDeliveryChoices.SUCCESS if success else StatusDeliveryChoices.FAILED,
                    error_message="" if success else f"Ошибка отправки через {recipient.recipient_type}",
                )
            all_success = all(results.values())
            notification.status = StatusChoices.COMPLETED if all_success else StatusChoices.FAILED
            notification.save()
            logger.info(f"Уведомление {notification_id} обработано. Успех: {all_success}")
            return all_success
        except Notification.DoesNotExist:
            logger.error(f"Уведомление {notification_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления {notification_id}: {e}")
            raise self.retry(exc=e) from e
