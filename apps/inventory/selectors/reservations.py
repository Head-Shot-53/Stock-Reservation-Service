import uuid

from django.db.models import QuerySet

from apps.inventory.exceptions import ReservationNotFoundError
from apps.inventory.models import Reservation


def get_reservation(*,reservation_id: uuid.UUID) -> Reservation:
    try:
        return (
            Reservation.objects
            .select_related(
                "product",
                "warehouse",
            )
            .get(id=reservation_id)
        )
    except Reservation.DoesNotExist as exc:
        raise ReservationNotFoundError(
            f"Reservation {reservation_id} does not exist."
        ) from exc

def list_reservations(*,
    status: str | None = None,
    product_id: uuid.UUID | None = None,
    warehouse_id: uuid.UUID | None = None,
    external_reference: str | None = None,
) -> QuerySet[Reservation]:
    queryset = (
        Reservation.objects
        .select_related(
            "product",
            "warehouse",
        )
        .order_by("-created_at")
    )

    if status is not None:
        queryset = queryset.filter(
            status=status,
        )

    if product_id is not None:
        queryset = queryset.filter(
            product_id=product_id,
        )

    if warehouse_id is not None:
        queryset = queryset.filter(
            warehouse_id=warehouse_id,
        )

    if external_reference is not None:
        queryset = queryset.filter(
            external_reference=external_reference,
        )

    return queryset