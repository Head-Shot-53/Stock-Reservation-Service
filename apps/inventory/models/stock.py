from django.db import models
from django.db.models import F, Q

from .base import UUIDTimestampedModel
from .product import Product
from .warehouse import Warehouse

class Stock(UUIDTimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stocks')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("product", "warehouse"), name="inventory_stock_product_warehouse_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte = 0), name="inventory_stock_quantity_gte_0"
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__gte=0), name="inventory_stock_reserved_quantity_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(
                    reserved_quantity__lte=F("quantity"),
                ),
                name="inventory_stock_reserved_lte_quantity",
            ),
        ]

    @property 
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity

    def __str__(self) -> str:
        return (
            f"{self.product.sku} @ "
            f"{self.warehouse.code}"
        )