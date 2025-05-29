from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum as PyEnum
from sqlmodel import Field, Relationship, SQLModel


# Enums
class AccountCategory(str, PyEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class ActivityFacilityType(str, PyEnum):
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"
    BOTH = "both"


class FacilityType(str, PyEnum):
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"


class UserRole(str, PyEnum):
    ACCOUNTANT = "accountant"
    ADMIN = "admin"
    MANAGER = "manager"


class AuditAction(str, PyEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class PlanningStatus(str, PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class PriorityLevel(str, PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActivityStatus(str, PyEnum):
    PLANNED = "planned"
    READY_TO_EXECUTE = "ready_to_execute"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, PyEnum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"


class TransactionType(str, PyEnum):
    DEBIT = "debit"
    CREDIT = "credit"


# Models
class AccountTypes(SQLModel, table=True):
    __tablename__ = "account_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    category: AccountCategory
    code: Optional[str] = Field(default=None, max_length=20, unique=True)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    accounts: List["Accounts"] = Relationship(back_populates="account_type")


class ActivityCategories(SQLModel, table=True):
    __tablename__ = "activity_categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    code: Optional[str] = Field(default=None, max_length=20, unique=True)
    description: Optional[str] = Field(default=None)
    facility_type: ActivityFacilityType = Field(default=ActivityFacilityType.BOTH)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    planned_activities: List["PlannedActivities"] = Relationship(back_populates="activity_category")


class FiscalYears(SQLModel, table=True):
    __tablename__ = "fiscal_years"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True)
    start_date: date
    end_date: date
    is_active: bool = Field(default=True)
    is_current: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="fiscal_year")


class Programs(SQLModel, table=True):
    __tablename__ = "programs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    code: Optional[str] = Field(default=None, max_length=20, unique=True)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="program")


class Provinces(SQLModel, table=True):
    __tablename__ = "provinces"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    code: Optional[str] = Field(default=None, max_length=10, unique=True)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    districts: List["Districts"] = Relationship(back_populates="province")
    facilities: List["Facilities"] = Relationship(back_populates="province")
    users: List["Users"] = Relationship(back_populates="province")


class Districts(SQLModel, table=True):
    __tablename__ = "districts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    province_id: int = Field(foreign_key="provinces.id")
    name: str = Field(max_length=100)
    code: Optional[str] = Field(default=None, max_length=10)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    province: Optional["Provinces"] = Relationship(back_populates="districts")
    facilities: List["Facilities"] = Relationship(back_populates="district")
    users: List["Users"] = Relationship(back_populates="district")


class Facilities(SQLModel, table=True):
    __tablename__ = "facilities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    facility_type: FacilityType
    province_id: int = Field(foreign_key="provinces.id")
    district_id: int = Field(foreign_key="districts.id")
    address: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    district: Optional["Districts"] = Relationship(back_populates="facilities")
    province: Optional["Provinces"] = Relationship(back_populates="facilities")
    users: List["Users"] = Relationship(back_populates="facility")
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="facility")


class Users(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    full_name: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True)
    password_hash: str = Field(max_length=255)
    province_id: int = Field(foreign_key="provinces.id")
    district_id: int = Field(foreign_key="districts.id")
    facility_id: int = Field(foreign_key="facilities.id")
    role: UserRole = Field(default=UserRole.ACCOUNTANT)
    is_active: bool = Field(default=True)
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
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


class Accounts(SQLModel, table=True):
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


class ActivityLogs(SQLModel, table=True):
    __tablename__ = "activity_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    table_name: str = Field(max_length=100)
    record_id: int
    action: AuditAction
    old_values: Optional[dict] = Field(default=None)
    new_values: Optional[dict] = Field(default=None)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["Users"] = Relationship(back_populates="activity_logs")


class PlanningSessions(SQLModel, table=True):
    __tablename__ = "planning_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
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


class BudgetAllocations(SQLModel, table=True):
    __tablename__ = "budget_allocations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    planning_session_id: int = Field(foreign_key="planning_sessions.id")
    account_id: int = Field(foreign_key="accounts.id")
    allocated_amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    spent_amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    notes: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    account: Optional["Accounts"] = Relationship(back_populates="budget_allocations")
    planning_session: Optional["PlanningSessions"] = Relationship(back_populates="budget_allocations")
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount from allocated minus spent."""
        return self.allocated_amount - self.spent_amount


class PlannedActivities(SQLModel, table=True):
    __tablename__ = "planned_activities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    activity_category: Optional["ActivityCategories"] = Relationship(back_populates="planned_activities")
    planning_session: Optional["PlanningSessions"] = Relationship(back_populates="planned_activities")
    activity_executions: List["ActivityExecutions"] = Relationship(back_populates="planned_activity")


class ActivityExecutions(SQLModel, table=True):
    __tablename__ = "activity_executions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    executor: Optional["Users"] = Relationship(back_populates="activity_executions")
    planned_activity: Optional["PlannedActivities"] = Relationship(back_populates="activity_executions")
    financial_transactions: List["FinancialTransactions"] = Relationship(back_populates="activity_execution")


class FinancialTransactions(SQLModel, table=True):
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