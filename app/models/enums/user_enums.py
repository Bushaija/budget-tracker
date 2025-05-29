"""User-related enumerations."""

from enum import Enum as PyEnum


class UserRole(str, PyEnum):
    """User roles in the system."""
    ACCOUNTANT = "accountant"
    ADMIN = "admin"
    MANAGER = "manager"


class AuditAction(str, PyEnum):
    """Types of audit actions."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"