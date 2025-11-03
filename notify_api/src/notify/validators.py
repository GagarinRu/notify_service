from django.core.exceptions import ValidationError

from .constants import EMAIL_REGEX, TELEGRAM_ID_REGEX


class RecipientValidator:
    """Валидатор для проверки получателей."""

    @classmethod
    def validate_recipient(cls, recipient: str) -> str:
        """Валидация одного получателя."""
        if not isinstance(recipient, str):
            raise ValidationError("Получатель должен быть строкой")
        recipient = recipient.strip()
        if EMAIL_REGEX.match(recipient):
            return "email"
        elif TELEGRAM_ID_REGEX.match(recipient):
            return "telegram"
        else:
            raise ValidationError(
                f"Некорректный формат получателя: {recipient}. Должен быть email или числовой Telegram ID"
            )

    @classmethod
    def validate_recipients(cls, recipients: str | list) -> dict[str, list[str]]:
        """Валидация одного или нескольких получателей."""
        if isinstance(recipients, str):
            recipients = [recipients]
        if not recipients:
            raise ValidationError("Список получателей не может быть пустым")
        if not isinstance(recipients, list):
            raise ValidationError("Получатели должны быть строкой или списком строк")
        validated_data: dict[str, list[str]] = {"email": [], "telegram": []}
        for recipient in recipients:
            recipient_type = cls.validate_recipient(recipient)
            validated_data[recipient_type].append(recipient)
        if not validated_data["email"] and not validated_data["telegram"]:
            raise ValidationError("Не указано ни одного валидного получателя")
        return validated_data
