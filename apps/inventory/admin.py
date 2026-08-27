from django.contrib import admin

from .models import Product, Stock, StockMovement, Warehouse, Reservation


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_active",
    )
    search_fields = (
        "sku",
        "name",
    )
    ordering = (
        "sku",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_active",
    )
    search_fields = (
        "code",
        "name",
        "address",
    )
    ordering = (
        "code",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "warehouse",
        "quantity",
        "reserved_quantity",
        "available_quantity_display",
        "updated_at",
    )
    search_fields = (
        "product__sku",
        "product__name",
        "warehouse__code",
        "warehouse__name",
    )
    list_filter = (
        "warehouse",
        "product__is_active",
        "warehouse__is_active",
    )
    list_select_related = (
        "product",
        "warehouse",
    )
    readonly_fields = (
        "id",
        "quantity",
        "reserved_quantity",
        "available_quantity_display",
        "created_at",
        "updated_at",
    )

    @admin.display(
        description="Available quantity",
    )
    def available_quantity_display(self, obj: Stock) -> int:
        return obj.available_quantity


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_type",
        "stock",
        "quantity",
        "quantity_before",
        "quantity_after",
        "created_at",
    )

    list_filter = (
        "movement_type",
        "created_at",
    )

    search_fields = (
        "stock__product__sku",
        "stock__warehouse__code",
        "external_reference",
    )

    list_select_related = (
        "stock",
        "stock__product",
        "stock__warehouse",
    )

    readonly_fields = (
        "id",
        "stock",
        "movement_type",
        "quantity",
        "quantity_before",
        "quantity_after",
        "reserved_before",
        "reserved_after",
        "external_reference",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "external_reference",
        "product",
        "warehouse",
        "quantity",
        "status",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "status",
        "warehouse",
        "created_at",
    )

    search_fields = (
        "external_reference",
        "idempotency_key",
        "product__sku",
        "warehouse__code",
    )

    list_select_related = (
        "product",
        "warehouse",
    )

    readonly_fields = (
        "id",
        "product",
        "warehouse",
        "quantity",
        "status",
        "external_reference",
        "idempotency_key",
        "expires_at",
        "confirmed_at",
        "cancelled_at",
        "expired_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False