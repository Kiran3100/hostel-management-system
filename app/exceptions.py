"""Custom exception classes."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """Authorization failed (insufficient permissions)."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict] = None):
        super().__init__(message, status_code=404, details=details)


class ConflictError(AppException):
    """Resource conflict (duplicate, etc.)."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Dict] = None):
        super().__init__(message, status_code=409, details=details)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation error", details: Optional[Dict] = None):
        super().__init__(message, status_code=422, details=details)


class SubscriptionLimitError(AppException):
    """Subscription limit exceeded."""

    def __init__(
        self, message: str = "Subscription limit exceeded", details: Optional[Dict] = None
    ):
        super().__init__(message, status_code=402, details=details)


class PaymentError(AppException):
    """Payment processing error."""

    def __init__(self, message: str = "Payment failed", details: Optional[Dict] = None):
        super().__init__(message, status_code=402, details=details)


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict] = None):
        super().__init__(message, status_code=429, details=details)