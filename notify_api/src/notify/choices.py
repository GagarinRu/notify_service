from django.db import models


class DelayChoices(models.IntegerChoices):
    """Выбор времени уведомления."""

    IMMEDIATE = 0, "Немедленно"
    ONE_HOUR = 1, "Через 1 час"
    ONE_DAY = 2, "Через 1 день"


class StatusChoices(models.TextChoices):
    """Выбор статуса уведомления."""

    PENDING = "pending", "Ожидает отправки"
    PROCESSING = "processing", "В процессе отправки"
    COMPLETED = "completed", "Завершено"
    FAILED = "failed", "Ошибка"


class RecipientTypeChoices(models.TextChoices):
    """Выбор способа уведомления."""

    EMAIL = "email", "Email"
    TELEGRAM = "telegram", "Telegram"


class StatusDeliveryChoices(models.TextChoices):
    """Выбор статуса отправки уведомления."""

    SUCCESS = "success", "Успешно"
    FAILED = "failed", "Ошибка"
