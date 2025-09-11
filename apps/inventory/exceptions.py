class InventoryError(Exception):
    """Base exception for inventory domain errors."""


class InvalidStockQuantityError(InventoryError):
    """Raised when a stock operation has an invalid quantity."""


class InsufficientAvailableStockError(InventoryError):
    """Raised when physical stock cannot be safely decreased."""


class StockNotFoundError(InventoryError):
    """Raised when the requested stock does not exist."""

class InvalidReservationQuantityError(InventoryError):
    """Raised when reservation quantity is invalid."""


class InvalidReservationTTLError(InventoryError):
    """Raised when reservation TTL is invalid."""


class ProductInactiveError(InventoryError):
    """Raised when attempting to reserve an inactive product."""


class WarehouseInactiveError(InventoryError):
    """Raised when attempting to reserve stock in an inactive warehouse."""


class IdempotencyConflictError(InventoryError):
    """Raised when an idempotency key is reused with different data."""