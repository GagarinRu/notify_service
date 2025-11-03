from drf_spectacular.utils import OpenApiExample, OpenApiResponse

from .serializers import NotificationResponseSerializer

# Настройки сваггера
NOTIFY_SETTINGS = {
    "name": "Уведомления",
    "description": "Микросервис для отправки уведомлений по email и Telegram",
}

# Response схемы
NOTIFY_201 = OpenApiResponse(
    response=NotificationResponseSerializer,
    description="Уведомление успешно создано и запланировано",
    examples=[
        OpenApiExample(
            name="Успешное создание уведомления",
            value={
                "notification_id": 1,
                "status": "scheduled",
                "scheduled_for": "2024-01-15T14:30:00Z",
                "recipients_count": 2,
            },
            response_only=True,
        )
    ],
)

NOTIFY_400 = OpenApiResponse(
    description="Ошибки валидации входных данных",
    examples=[
        OpenApiExample(
            name="Ошибка валидации",
            value={
                "error": "Validation error",
                "details": {
                    "message": ["Это поле обязательно."],
                    "recipient": ["Некорректный формат получателя."],
                },
            },
            response_only=True,
        )
    ],
)

NOTIFY_500 = OpenApiResponse(
    description="Внутренняя ошибка сервера при создании уведомления",
    examples=[
        OpenApiExample(
            name="Внутренняя ошибка",
            value={"error": "Internal server error"},
            response_only=True,
        )
    ],
)

NOTIFY_EXM = [
    OpenApiExample(
        "Пример уведомления",
        value={
            "message": "Ваше бронирование подтверждено",
            "recipient": ["client@example.com", "123456789"],
            "delay": 0,
        },
        request_only=True,
        description="Пример отправки email и Telegram уведомления",
    )
]
