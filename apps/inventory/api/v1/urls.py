from django.urls import path

from .views import (
    AvailabilityView,
    ReservationCancelView,
    ReservationConfirmView,
    ReservationCreateView,
    ReservationDetailView,
)


app_name = "inventory-api-v1"


urlpatterns = [
    path(
        "availability/",
        AvailabilityView.as_view(),
        name="availability",
    ),
    path(
        "reservations/",
        ReservationCreateView.as_view(),
        name="reservation-create",
    ),
    path(
        "reservations/<uuid:reservation_id>/",
        ReservationDetailView.as_view(),
        name="reservation-detail",
    ),
    path(
        "reservations/<uuid:reservation_id>/confirm/",
        ReservationConfirmView.as_view(),
        name="reservation-confirm",
    ),
    path(
        "reservations/<uuid:reservation_id>/cancel/",
        ReservationCancelView.as_view(),
        name="reservation-cancel",
    ),
]