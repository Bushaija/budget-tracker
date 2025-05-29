"""Activity planning and execution models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from ..base import BaseEntityModel
from ..enums import ActivityStatus, ExecutionStatus, PriorityLevel

if TYPE_CHECKING:
    from ..finance.models import FinancialTransactions
    from ..planning.models import ActivityCategories, PlanningSessions
    from ..users.models import Users


class PlannedActivities(BaseEntityModel, table=True):
    """Planned healthcare activities."""
    
    __tablename__ = "planned_activities"
    
    planning_session_id: int = Field(foreign_key="planning_sessions.id")
    activity_category_id: int = Field(foreign_key="activity_categories.id")
    activity_name: str = Field(max_length=255)
    planned_budget: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    description: Optional[str] = Field(default=None)
    planned_start_date: Optional[date] = Field(default=None)
    planned_end_date: Optional[date] = Field(default=None)
    target_beneficiaries: int = Field(default=0)
    success_metrics: Optional[str] = Field(default=None)
    priority_level: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    status: ActivityStatus = Field(default=ActivityStatus.PLANNED)
    
    # Relationships
    activity_category: Optional["ActivityCategories"] = Relationship(back_populates="planned_activities")
    planning_session: Optional["PlanningSessions"] = Relationship(back_populates="planned_activities")
    activity_executions: List["ActivityExecutions"] = Relationship(back_populates="planned_activity")


class ActivityExecutions(BaseEntityModel, table=True):
    """Execution records for planned activities."""
    
    __tablename__ = "activity_executions"
    
    planned_activity_id: int = Field(foreign_key="planned_activities.id")
    executed_by: int = Field(foreign_key="users.id")
    actual_start_date: Optional[date] = Field(default=None)
    actual_end_date: Optional[date] = Field(default=None)
    actual_beneficiaries: int = Field(default=0)
    actual_budget: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    execution_status: ExecutionStatus = Field(default=ExecutionStatus.STARTED)
    completion_percentage: Decimal = Field(default=Decimal("0.00"), max_digits=5, decimal_places=2)
    notes: Optional[str] = Field(default=None)
    challenges_faced: Optional[str] = Field(default=None)
    lessons_learned: Optional[str] = Field(default=None)
    
    # Relationships
    executor: Optional["Users"] = Relationship(back_populates="activity_executions")
    planned_activity: Optional["PlannedActivities"] = Relationship(back_populates="activity_executions")
    financial_transactions: List["FinancialTransactions"] = Relationship(back_populates="activity_execution")