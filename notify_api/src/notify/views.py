import logging
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from redis import Redis
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.viewsets import ViewSet

from .choices import DelayChoices
from .constants import DELAY_MAPPING
from .models import Notification, Recipient
from .openapi_schemas import NOTIFY_201, NOTIFY_400, NOTIFY_500, NOTIFY_EXM, NOTIFY_SETTINGS
from .serializers import NotificationRequestSerializer, NotificationResponseSerializer
from .tasks import send_notification_task

logger = logging.getLogger(__name__)


@extend_schema(tags=[NOTIFY_SETTINGS["name"]])
@extend_schema_view(
    create=extend_schema(
        summary="Создание и отправка уведомления",
        description=(
            "Создание и планирование уведомления для отправки по email и/или Telegram.\n\n"
            "**Поддерживаемые типы получателей:**\n"
            "- Email адреса (user@example.com)\n"
            "- Telegram ID (числовые идентификаторы)\n\n"
            "**Задержки отправки:**\n"
            "- 0: Немедленная отправка\n"
            "- 1: Отправка через 1 час\n"
            "- 2: Отправка через 1 день"
        ),
        request=NotificationRequestSerializer,
        responses={201: NOTIFY_201, 400: NOTIFY_400, 500: NOTIFY_500},
        examples=NOTIFY_EXM,
    )
)
class NotifyViewSet(ViewSet):
    """ViewSet для обработки уведомлений."""

    @transaction.atomic
    def create(self, request: Request) -> Response:
        """Создание и отправка уведомления."""
        serializer = NotificationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation error", "details": serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )
        try:
            validated_data = serializer.validated_data
            recipients_data = validated_data["recipient"]
            delay = validated_data["delay"]
            scheduled_time = self._calculate_scheduled_time(delay)
            notification = Notification.objects.create(
                message=validated_data["message"],
                delay=delay,
                scheduled_for=scheduled_time,
            )
            recipients = []
            for recipient_type, addresses in recipients_data.items():
                for address in addresses:
                    recipients.append(
                        Recipient(
                            notification=notification,
                            address=address,
                            recipient_type=recipient_type,
                        )
                    )
            Recipient.objects.bulk_create(recipients)
            self._schedule_notification_task(notification.id, delay, scheduled_time)
            logger.info(f"Уведомление {notification.id} создано. Получатели: {recipients_data}")
            response_data = {
                "id": notification.id,
                "status": "scheduled",
                "scheduled_for": scheduled_time,
                "recipients_count": sum(len(addrs) for addrs in recipients_data.values()),
            }
            response_serializer = NotificationResponseSerializer(response_data)
            return Response(response_serializer.data, status=HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Ошибка создания уведомления: {e}")
            return Response(
                {"error": "Internal server error"},
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _calculate_scheduled_time(self, delay: int) -> timezone.datetime:
        """Расчет времени отправки через маппинг."""
        time_delta = DELAY_MAPPING.get(delay, timedelta(0))
        return timezone.now() + time_delta

    def _schedule_notification_task(self, notification_id: int, delay: int, scheduled_time: timezone.datetime) -> None:
        """Планирование задачи отправки."""
        if delay == DelayChoices.IMMEDIATE:
            send_notification_task.delay(notification_id)
        else:
            send_notification_task.apply_async(
                args=(notification_id,),
                eta=scheduled_time,
            )


def health_check(request: HttpRequest) -> JsonResponse:
    """Мониторинг состояния сервиса."""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    try:
        redis = Redis.from_url(settings.CELERY_BROKER_URL)
        redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    all_healthy = all(check == "healthy" for check in checks.values())
    if all_healthy:
        return JsonResponse({"status": "healthy", "service": "notify", "checks": checks}, status=200)
    else:
        return JsonResponse({"status": "unhealthy", "service": "notify", "checks": checks}, status=503)
