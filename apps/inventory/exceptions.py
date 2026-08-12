class InventoryError(Exception):
    """Base exception for inventory domain errors."""


class InvalidStockQuantityError(InventoryError):
    """Raised when a stock operation has an invalid quantity."""


class InsufficientAvailableStockError(InventoryError):
    """Raised when physical stock cannot be safely decreased."""


class StockNotFoundError(InventoryError):
    """Raised when the requested stock does not exist."""