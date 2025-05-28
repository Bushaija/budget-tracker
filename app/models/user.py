from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from app.models.base import BaseTable
from app.utils.enums import UserRole

class User(BaseTable, table=True):
    __tablename__ = "users"
    
    full_name: str = Field(max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.ACCOUNTANT)
    
    # Location relationships
    province_id: int = Field(foreign_key="provinces.id")
    district_id: int = Field(foreign_key="districts.id")
    hospital_id: int = Field(foreign_key="facilities.id")
    
    # Relationships
    province: Optional["Province"] = Relationship(back_populates="users")
    district: Optional["District"] = Relationship(back_populates="users")
    hospital: Optional["Facility"] = Relationship(back_populates="users")
    
    # Created items
    planning_sessions: List["PlanningSession"] = Relationship(back_populates="created_by_user")
    activity_executions: List["ActivityExecution"] = Relationship(back_populates="executed_by_user")

    def __repr__(self):
    	return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    
class UserLogin(SQLModel):
    """User login tracking"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    login_time: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(max_length=45)
    user_agent: Optional[str] = Field(max_length=500)
    success: bool = Field(default=True, index=True)

