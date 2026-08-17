from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import Reservation
from apps.inventory.services import ReservationService


DEFAULT_EXPIRATION_BATCH_SIZE = 100


@shared_task
def expire_stale_reservations(batch_size: int = DEFAULT_EXPIRATION_BATCH_SIZE) -> int:
    if batch_size <= 0:
        return 0

    processed = 0

    for _ in range(batch_size):
        with transaction.atomic():
            reservation_id = (
                Reservation.objects
                .select_for_update(
                    skip_locked=True,
                    of=("self",),
                )
                .filter(
                    status=Reservation.Status.ACTIVE,
                    expires_at__lte=timezone.now(),
                )
                .order_by(
                    "expires_at",
                    "created_at",
                )
                .values_list(
                    "id",
                    flat=True,
                )
                .first()
            )

            if reservation_id is None:
                break

            ReservationService.expire_reservation(
                reservation_id=reservation_id,
            )

            processed += 1

    return processed