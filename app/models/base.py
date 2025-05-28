from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class TimestampMixin(BaseModel):
	"""Mixin for timestamp fields"""
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"onupdate": datetime.utcnow})

class BaseTable(SQLModel, TimestampMixin):
	"""base table class with common fields"""
	id: Optional[int] = Field(default=None, primary_key=True)
	is_active: bool = Field(default=True)

class BaseResponse(BaseModel):
	"""Base table class with common fields"""
	success: bool = True
	message: str = "Operation successful"

class PaginationResponse(BaseModel):
	"""Pagination response"""
	current_page: int
	total_pages: int 
	total_items: int 
	items_per_page: int 
	has_next_page: bool
	has_prev_page: bool