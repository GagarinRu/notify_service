from rest_framework.serializers import CharField, DateTimeField, IntegerField, ListField, Serializer

from .constants import MAX_LENGTH_ADDRESS, MAX_LENGTH_MESSAGE, MAX_VALUE_DELAY, MIN_LENGTH_MESSAGE, MIN_VALUE_DELAY
from .validators import RecipientValidator


class NotificationRequestSerializer(Serializer):
    """Сериализатор для входящих уведомлений."""

    message = CharField(
        max_length=MAX_LENGTH_MESSAGE,
        min_length=MIN_LENGTH_MESSAGE,
        trim_whitespace=True,
    )
    recipient = ListField(
        child=CharField(max_length=MAX_LENGTH_ADDRESS),
        allow_empty=False,
    )
    delay = IntegerField(min_value=MIN_VALUE_DELAY, max_value=MAX_VALUE_DELAY)

    def validate_recipient(self, value: list[str] | str) -> dict[str, list[str]]:
        """Валидация получателей"""
        if isinstance(value, str):
            value = [value]
        return RecipientValidator.validate_recipients(value)


class NotificationResponseSerializer(Serializer):
    """Сериализатор для исходящих ответов."""

    notification_id = IntegerField(source="id", help_text="ID созданного уведомления")
    status = CharField(help_text="Статус уведомления")
    scheduled_for = DateTimeField(help_text="Запланированное время отправки")
    recipients_count = IntegerField(help_text="Количество получателей")
