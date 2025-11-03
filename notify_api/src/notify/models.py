from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models

from .choices import DelayChoices, RecipientTypeChoices, StatusChoices, StatusDeliveryChoices
from .constants import MAX_LENGTH_ADDRESS, MAX_LENGTH_MESSAGE, MIN_LENGTH_MESSAGE


class Notification(models.Model):
    """Модель для хранения уведомлений."""

    message = models.TextField(
        validators=[MinLengthValidator(MIN_LENGTH_MESSAGE), MaxLengthValidator(MAX_LENGTH_MESSAGE)],
        verbose_name="Текст сообщения",
        help_text="Текст сообщения",
    )
    status = models.CharField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="Статус",
        help_text="Статус отправки",
    )
    delay = models.IntegerField(
        choices=DelayChoices.choices,
        default=DelayChoices.IMMEDIATE,
        verbose_name="Задержка отправки",
        help_text="Задержка отправки",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Запланировано на",
    )

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["scheduled_for", "status"]),
        ]

    def __str__(self) -> str:
        return f"Уведомление #{self.id} - {self.status}"


class Recipient(models.Model):
    """Модель получателей уведомления."""

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Уведомление",
    )
    address = models.CharField(
        max_length=MAX_LENGTH_ADDRESS,
        verbose_name="Адрес получателя",
    )
    recipient_type = models.CharField(
        choices=RecipientTypeChoices.choices,
        verbose_name="Тип получателя",
        help_text="Тип получателя",
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        indexes = [
            models.Index(fields=["recipient_type", "address"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_type}: {self.address}"


class DeliveryLog(models.Model):
    """Модель логирования отправки уведомлений."""

    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.CASCADE,
        related_name="delivery_logs",
        verbose_name="Получатель",
        help_text="Получатель",
    )
    status = models.CharField(
        choices=StatusDeliveryChoices.choices,
        verbose_name="Статус отправки",
        help_text="Статус отправки",
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Сообщение об ошибке",
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время отправки",
    )

    class Meta:
        verbose_name = "Лог доставки"
        verbose_name_plural = "Логи доставки"
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return f"Лог #{self.id} - {self.status}"
