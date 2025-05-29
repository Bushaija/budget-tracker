"""Base model classes and common functionality."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Boolean
from sqlalchemy import text, Column


class TimestampMixin(SQLModel):
    """Mixin to add timestamp fields to models."""
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class BaseEntityModel(TimestampMixin):
    """Base model for entities with common fields."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(
        default=True,
        sa_column_kwargs={'server_default': text('true')}
    )


class CodedEntityModel(BaseEntityModel):
    """Base model for entities with name and code."""
    
    name: str = Field(max_length=100)
    code: Optional[str] = Field(default=None, max_length=20, unique=True)
    description: Optional[str] = Field(default=None)