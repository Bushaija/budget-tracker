"""Healthcare facility models."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from ..base import BaseEntityModel
from ..enums import FacilityType

if TYPE_CHECKING:
    from ..geographic.models import Districts, Provinces
    from ..planning.models import PlanningSessions
    from ..users.models import Users


class Facilities(BaseEntityModel, table=True):
    """Healthcare facilities model."""
    
    __tablename__ = "facilities"
    
    name: str = Field(max_length=255)
    facility_type: FacilityType
    province_id: int = Field(foreign_key="provinces.id")
    district_id: int = Field(foreign_key="districts.id")
    address: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    
    # Relationships
    district: Optional["Districts"] = Relationship(back_populates="facilities")
    province: Optional["Provinces"] = Relationship(back_populates="facilities")
    users: List["Users"] = Relationship(back_populates="facility")
    planning_sessions: List["PlanningSessions"] = Relationship(back_populates="facility")