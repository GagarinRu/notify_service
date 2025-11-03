import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationSender(ABC):
    """Абстрактный базовый класс для отправки уведомлений."""

    @abstractmethod
    def send(self, message: str, recipients: list[str]) -> bool:
        pass


class EmailSender(NotificationSender):
    """Сервис отправки email уведомлений через Celery задачу."""

    def send(self, message: str, recipients: list[str]) -> bool:
        from .tasks import send_email_task

        try:
            send_email_task.delay(
                subject="Уведомление",
                message=message,
                to_email=recipients,
            )
            logger.info(f"Email задача поставлена в очередь для: {recipients}")
            return True
        except Exception as e:
            logger.error(f"Ошибка постановки email задачи: {e}")
            return False


class TelegramSender(NotificationSender):
    """Сервис отправки telegram уведомлений через TeleBot."""

    def send(self, message: str, recipients: list[str]) -> bool:
        from .tasks import send_telegram_task

        if not recipients:
            logger.warning("Список получателей Telegram пуст")
            return True
        try:
            send_telegram_task.delay(
                message=message,
                chat_ids=recipients,
            )
            logger.info(f"Telegram задача поставлена в очередь для: {recipients}")
            return True
        except Exception as e:
            logger.error(f"Ошибка постановки Telegram задачи: {e}")
            return False


class NotificationService:
    """Фасад для отправки уведомлений через различные каналы."""

    def __init__(self) -> None:
        self.senders = {
            "email": EmailSender(),
            "telegram": TelegramSender(),
        }

    def send_notification(self, message: str, recipients_data: dict) -> dict:
        """Отправка уведомлений по всем каналам."""
        results = {}
        for recipient_type, recipients in recipients_data.items():
            if recipients and recipient_type in self.senders:
                sender = self.senders[recipient_type]
                results[recipient_type] = sender.send(message, recipients)
            elif recipients:
                logger.warning(f"Неизвестный тип получателя: {recipient_type}")
        return results
