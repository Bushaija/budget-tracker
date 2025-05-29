"""User management models."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from ..base import BaseEntityModel
from ..enums import UserRole

if TYPE_CHECKING:
    from ..activities.models import ActivityExecutions
    from ..audit.models import ActivityLogs
    from ..facilities.models import Facilities
    from ..finance.models import FinancialTransactions
    from ..geographic.models import Districts, Provinces
    from ..planning.models import PlanningSessions


class Users(BaseEntityModel, table=True):
    """System users model."""
    
    __tablename__ = "users"
    
    full_name: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True)
    password_hash: str = Field(max_length=255)
    province_id: int = Field(foreign_key="provinces.id")
    district_id: int = Field(foreign_key="districts.id")
    facility_id: int = Field(foreign_key="facilities.id")
    
    role: UserRole = Field(default=UserRole.ACCOUNTANT)
    
    # Relationships
    district: Optional["Districts"] = Relationship(back_populates="users")
    facility: Optional["Facilities"] = Relationship(back_populates="users")
    province: Optional["Provinces"] = Relationship(back_populates="users")
    activity_logs: List["ActivityLogs"] = Relationship(back_populates="user")
    created_planning_sessions: List["PlanningSessions"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[PlanningSessions.created_by]"}
    )
    approved_planning_sessions: List["PlanningSessions"] = Relationship(
        back_populates="approver",
        sa_relationship_kwargs={"foreign_keys": "[PlanningSessions.approved_by]"}
    )
    activity_executions: List["ActivityExecutions"] = Relationship(back_populates="executor")
    financial_transactions: List["FinancialTransactions"] = Relationship(back_populates="creator")