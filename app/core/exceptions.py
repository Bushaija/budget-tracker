"""
Custom exception classes for the application.
"""
from typing import Any, Dict, Optional


class CustomException(Exception):
    """
    Base exception class for the application.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CustomException):
    """
    Exception raised for validation errors.
    """
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 422, details)


class NotFoundError(CustomException):
    """
    Exception raised when a requested resource is not found.
    """
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 404, details)


class PermissionError(CustomException):
    """
    Exception raised when user doesn't have permission.
    """
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 403, details)


class AuthenticationError(CustomException):
    """
    Exception raised for authentication errors.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 401, details)


class DuplicateError(CustomException):
    """
    Exception raised when trying to create a duplicate resource.
    """
    def __init__(
        self,
        message: str = "Resource already exists",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 409, details)


class BusinessLogicError(CustomException):
    """
    Exception raised for business logic violations.
    """
    def __init__(
        self,
        message: str = "Business logic error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 400, details)