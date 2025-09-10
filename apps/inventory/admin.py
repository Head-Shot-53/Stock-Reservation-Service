from django.contrib import admin

from .models import Product, Warehouse, Stock


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