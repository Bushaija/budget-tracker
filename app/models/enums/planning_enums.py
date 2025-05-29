"""Planning and activity-related enumerations."""

from enum import Enum as PyEnum


class PlanningStatus(str, PyEnum):
    """Status of planning sessions."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class PriorityLevel(str, PyEnum):
    """Priority levels for activities."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActivityStatus(str, PyEnum):
    """Status of planned activities."""
    PLANNED = "planned"
    READY_TO_EXECUTE = "ready_to_execute"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, PyEnum):
    """Status of activity execution."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"