class RevenueModuleException(Exception):
    """Base exception for revenue module."""
    pass


class ProviderSyncError(RevenueModuleException):
    """Raised when a provider synchronization fails."""
    pass


class DuplicateTransactionError(RevenueModuleException):
    """Raised when duplicate financial records are detected."""
    pass


class InvalidReportFormatError(RevenueModuleException):
    """Raised when provider sales/earnings report fails parsing."""
    pass
