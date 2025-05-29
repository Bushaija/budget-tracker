"""Models package for the healthcare management system."""

# Import all models to ensure proper relationship resolution
from sqlmodel import SQLModel
from .accounts import Accounts, AccountTypes
from .activities import ActivityExecutions, PlannedActivities
from .audit import ActivityLogs
from .base import BaseEntityModel, CodedEntityModel, TimestampMixin
from .enums import (
    AccountCategory,
    ActivityFacilityType,
    ActivityStatus,
    AuditAction,
    ExecutionStatus,
    FacilityType,
    PlanningStatus,
    PriorityLevel,
    TransactionType,
    UserRole,
)
from .facilities import Facilities
from .finance import BudgetAllocations, FinancialTransactions
from .geographic import Districts, Provinces
from .planning import ActivityCategories, FiscalYears, PlanningSessions, Programs
from .users import Users

# Export all models for easy importing
__all__ = [
    # Base classes
    "BaseEntityModel",
    "CodedEntityModel", 
    "TimestampMixin",
    # Enums
    "AccountCategory",
    "ActivityFacilityType",
    "ActivityStatus",
    "AuditAction",
    "ExecutionStatus",
    "FacilityType",
    "PlanningStatus",
    "PriorityLevel",
    "TransactionType",
    "UserRole",
    # Geographic models
    "Districts",
    "Provinces",
    # Facility models
    "Facilities",
    # User models
    "Users",
    # Account models
    "Accounts",
    "AccountTypes",
    # Planning models
    "ActivityCategories",
    "FiscalYears",
    "PlanningSessions",
    "Programs",
    # Activity models
    "ActivityExecutions",
    "PlannedActivities",
    # Finance models
    "BudgetAllocations",
    "FinancialTransactions",
    # Audit models
    "ActivityLogs",
]