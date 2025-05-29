"""Planning and program management models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from ..base import BaseEntityModel, CodedEntityModel
from ..enums import ActivityFacilityType, PlanningStatus

if TYPE_CHECKING:
    from ..activities.models import PlannedActivities
    from ..facilities.models import Facilities
    from ..finance.models import BudgetAllocations, FinancialTransactions
    from ..users.models import Users


class FiscalYears(BaseEntityModel, table=True):
    """Fiscal year definitions."""
    
    __tablename__ = "fiscal_years"
    
    name: str = Field(max_length=50, unique=True)
    start_date: date
    end_date: date
    is_current: bool = Field(default=False)
    
    # Relationships
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="fiscal_year")


class Programs(CodedEntityModel, table=True):
    """Program definitions for healthcare activities."""
    
    __tablename__ = "programs"
    
    name: str = Field(max_length=100, unique=True)
    
    # Relationships
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="program")


class ActivityCategories(CodedEntityModel, table=True):
    """Categories for healthcare activities."""
    
    __tablename__ = "activity_categories"
    
    name: str = Field(max_length=100)
    facility_type: ActivityFacilityType = Field(default=ActivityFacilityType.BOTH)
    
    # Relationships
    planned_activities: List["PlannedActivities"] = Relationship(back_populates="activity_category")


class PlanningSessions(BaseEntityModel, table=True):
    """Planning sessions for healthcare programs."""
    
    __tablename__ = "planning_sessions"
    
    facility_id: int = Field(foreign_key="facilities.id")
    program_id: int = Field(foreign_key="programs.id")
    fiscal_year_id: int = Field(foreign_key="fiscal_years.id")
    created_by: int = Field(foreign_key="users.id")
    status: PlanningStatus = Field(default=PlanningStatus.DRAFT)
    total_budget: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    submission_date: Optional[datetime] = Field(default=None)
    approval_date: Optional[datetime] = Field(default=None)
    approved_by: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = Field(default=None)
    
    # Relationships
    creator: Optional["Users"] = Relationship(
        back_populates="created_planning_sessions",
        sa_relationship_kwargs={"foreign_keys": "[PlanningSessions.created_by]"}
    )
    approver: Optional["Users"] = Relationship(
        back_populates="approved_planning_sessions",
        sa_relationship_kwargs={"foreign_keys": "[PlanningSessions.approved_by]"}
    )
    facility: Optional["Facilities"] = Relationship(back_populates="planning_sessions")
    fiscal_year: Optional["FiscalYears"] = Relationship(back_populates="planning_sessions")
    program: Optional["Programs"] = Relationship(back_populates="planning_sessions")
    budget_allocations: List["BudgetAllocations"] = Relationship(back_populates="planning_session")
    planned_activities: List["PlannedActivities"] = Relationship(back_populates="planning_session")
    financial_transactions: List["FinancialTransactions"] = Relationship(back_populates="planning_session")