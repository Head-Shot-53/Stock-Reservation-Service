from django.contrib import admin

from .models import Product, Warehouse


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