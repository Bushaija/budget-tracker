"""Financial management models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from ..base import BaseEntityModel
from ..enums import TransactionType

if TYPE_CHECKING:
    from ..accounts.models import Accounts
    from ..activities.models import ActivityExecutions
    from ..planning.models import PlanningSessions
    from ..users.models import Users


class BudgetAllocations(BaseEntityModel, table=True):
    """Budget allocations for planning sessions."""
    
    __tablename__ = "budget_allocations"
    
    planning_session_id: int = Field(foreign_key="planning_sessions.id")
    account_id: int = Field(foreign_key="accounts.id")
    allocated_amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    spent_amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    notes: Optional[str] = Field(default=None)
    
    # Relationships
    account: Optional["Accounts"] = Relationship(back_populates="budget_allocations")
    planning_session: Optional["PlanningSessions"] = Relationship(back_populates="budget_allocations")
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount from allocated minus spent."""
        return self.allocated_amount - self.spent_amount


class FinancialTransactions(SQLModel, table=True):
    """Financial transaction records."""
    
    __tablename__ = "financial_transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    transaction_type: TransactionType
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    transaction_date: date
    created_by: int = Field(foreign_key="users.id")
    planning_session_id: Optional[int] = Field(default=None, foreign_key="planning_sessions.id")
    activity_execution_id: Optional[int] = Field(default=None, foreign_key="activity_executions.id")
    description: Optional[str] = Field(default=None)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    account: Optional["Accounts"] = Relationship(back_populates="financial_transactions")
    activity_execution: Optional["ActivityExecutions"] = Relationship(back_populates="financial_transactions")
    creator: Optional["Users"] = Relationship(back_populates="financial_transactions")
    planning_session: Optional["PlanningSessions"] = Relationship(back_populates="financial_transactions")