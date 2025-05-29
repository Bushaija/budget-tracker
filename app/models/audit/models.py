"""Audit and logging models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, Column, JSON

from ..enums import AuditAction

if TYPE_CHECKING:
    from ..users.models import Users


class ActivityLogs(SQLModel, table=True):
    """Audit trail for system activities."""
    
    __tablename__ = "activity_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    table_name: str = Field(max_length=100)
    record_id: int
    action: AuditAction
    old_values: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    new_values: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["Users"] = Relationship(back_populates="activity_logs")