"""Chart of accounts models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from ..enums import AccountCategory

if TYPE_CHECKING:
    from ..finance.models import BudgetAllocations, FinancialTransactions


class AccountTypes(SQLModel, table=True):
    """Account type definitions for chart of accounts."""
    
    __tablename__ = "account_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    category: AccountCategory
    code: Optional[str] = Field(default=None, max_length=20, unique=True)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    accounts: List["Accounts"] = Relationship(back_populates="account_type")


class Accounts(SQLModel, table=True):
    """Chart of accounts model."""
    
    __tablename__ = "accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_type_id: int = Field(foreign_key="account_types.id")
    name: str = Field(max_length=255)
    code: str = Field(max_length=50, unique=True)
    description: Optional[str] = Field(default=None)
    parent_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    account_type: Optional["AccountTypes"] = Relationship(back_populates="accounts")
    parent_account: Optional["Accounts"] = Relationship(
        back_populates="child_accounts",
        sa_relationship_kwargs={"remote_side": "[Accounts.id]"}
    )
    child_accounts: List["Accounts"] = Relationship(back_populates="parent_account")
    budget_allocations: List["BudgetAllocations"] = Relationship(back_populates="account")
    financial_transactions: List["FinancialTransactions"] = Relationship(back_populates="account")