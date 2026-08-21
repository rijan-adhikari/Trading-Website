"""
Standard error envelope used across the whole API:

    { "success": false, "error": { "code": "...", "message": "..." } }

Raise `APIError` from anywhere in a service/route and the global exception
handler in main.py turns it into this shape with the right HTTP status.
Never let a raw exception/stack trace reach the client.
"""
from fastapi import status


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__("NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


class UnauthorizedError(APIError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__("UNAUTHORIZED", message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(APIError):
    def __init__(self, message: str = "You do not have access to this resource"):
        super().__init__("FORBIDDEN", message, status.HTTP_403_FORBIDDEN)


class ConflictError(APIError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__("CONFLICT", message, status.HTTP_409_CONFLICT)


class ValidationAPIError(APIError):
    def __init__(self, message: str = "Invalid input"):
        super().__init__("VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class InsufficientFundsError(APIError):
    def __init__(self, message: str = "You do not have enough virtual cash to complete this order."):
        super().__init__("INSUFFICIENT_FUNDS", message, status.HTTP_400_BAD_REQUEST)


class InsufficientSharesError(APIError):
    def __init__(self, message: str = "You do not own enough shares to complete this order."):
        super().__init__("INSUFFICIENT_SHARES", message, status.HTTP_400_BAD_REQUEST)


class MarketClosedError(APIError):
    def __init__(self, message: str = "The market is currently closed."):
        super().__init__("MARKET_CLOSED", message, status.HTTP_400_BAD_REQUEST)
