from rest_framework import serializers

from apps.inventory.models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(
        read_only=True,
    )
    warehouse_id = serializers.UUIDField(
        read_only=True,
    )

    class Meta:
        model = Reservation
        fields = (
            "id",
            "external_reference",
            "product_id",
            "warehouse_id",
            "quantity",
            "status",
            "expires_at",
            "confirmed_at",
            "cancelled_at",
            "expired_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CreateReservationSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()

    quantity = serializers.IntegerField(
        min_value=1,
    )

    external_reference = serializers.CharField(
        max_length=255,
    )

    ttl_seconds = serializers.IntegerField(
        required=False,
        default=15 * 60,
        min_value=60,
        max_value=24 * 60 * 60,
    )


class AvailabilityQuerySerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()


class AvailabilitySerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    reserved_quantity = serializers.IntegerField()
    available_quantity = serializers.IntegerField()