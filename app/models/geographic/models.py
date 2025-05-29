"""Geographic location models."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from ..base import CodedEntityModel

if TYPE_CHECKING:
    from ..facilities.models import Facilities
    from ..users.models import Users


class Provinces(CodedEntityModel, table=True):
    """Administrative provinces model."""
    
    __tablename__ = "provinces"
    
    name: str = Field(max_length=100, unique=True)
    code: Optional[str] = Field(default=None, max_length=10, unique=True)
    
    # Relationships
    districts: List["Districts"] = Relationship(back_populates="province")
    facilities: List["Facilities"] = Relationship(back_populates="province")
    users: List["Users"] = Relationship(back_populates="province")


class Districts(CodedEntityModel, table=True):
    """Administrative districts model."""
    
    __tablename__ = "districts"
    
    province_id: int = Field(foreign_key="provinces.id")
    name: str = Field(max_length=100)
    code: Optional[str] = Field(default=None, max_length=10)
    
    # Relationships
    province: Optional["Provinces"] = Relationship(back_populates="districts")
    facilities: List["Facilities"] = Relationship(back_populates="district")
    users: List["Users"] = Relationship(back_populates="district")