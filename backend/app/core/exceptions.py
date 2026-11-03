class GlobalSearchError(Exception):
    """Base exception for GlobalSearch application."""

    def __init__(self, message: str, code: str = "GLOBAL_SEARCH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ResourceNotFoundError(GlobalSearchError):
    def __init__(self, message: str = "Requested resource was not found"):
        super().__init__(message, "RESOURCE_NOT_FOUND")


class PermissionDeniedError(GlobalSearchError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")


class ValidationError(GlobalSearchError):
    def __init__(self, message: str = "Invalid data"):
        super().__init__(message, "VALIDATION_ERROR")


class ServiceUnavailableError(GlobalSearchError):
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE")
