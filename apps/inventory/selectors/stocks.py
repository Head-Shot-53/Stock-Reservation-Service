import uuid

from apps.inventory.exceptions import StockNotFoundError
from apps.inventory.models import Stock


def get_stock(*,product_id: uuid.UUID,warehouse_id: uuid.UUID,) -> Stock:
    try:
        return (
            Stock.objects
            .select_related(
                "product",
                "warehouse",
            )
            .get(
                product_id=product_id,
                warehouse_id=warehouse_id,
            )
        )
    except Stock.DoesNotExist as exc:
        raise StockNotFoundError(
            "Stock for the requested product "
            "and warehouse does not exist."
        ) from exc