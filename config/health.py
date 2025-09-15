import logging

from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from redis import Redis


logger = logging.getLogger(__name__)


def _database_is_ready() -> bool:
    connection = connections["default"]

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        row = cursor.fetchone()

    return row == (1,)


def _redis_is_ready() -> bool:
    client = Redis.from_url(
        settings.CELERY_BROKER_URL,
        socket_connect_timeout=1,
        socket_timeout=1,
    )

    return bool(client.ping())


def health_view(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "stock-reservation-service",
        }
    )


def readiness_view(request):
    checks = {
        "database": False,
        "redis": False,
    }

    try:
        checks["database"] = _database_is_ready()
    except Exception:
        logger.warning(
            "Database readiness check failed.",
            exc_info=True,
        )

    try:
        checks["redis"] = _redis_is_ready()
    except Exception:
        logger.warning(
            "Redis readiness check failed.",
            exc_info=True,
        )

    is_ready = all(checks.values())

    return JsonResponse(
        {
            "status": (
                "ready"
                if is_ready
                else "not_ready"
            ),
            "checks": checks,
        },
        status=(
            200
            if is_ready
            else 503
        ),
    )