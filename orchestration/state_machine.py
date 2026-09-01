"""Task state machine and valid transition rules."""

from enum import Enum
from typing import Dict, Set


class TaskState(str, Enum):
    """Lifecycle states of a Task."""

    CREATED = "CREATED"
    DISCOVERY = "DISCOVERY"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStateMachine:
    """Validates and enforces deterministic task state transitions."""

    VALID_TRANSITIONS: Dict[TaskState, Set[TaskState]] = {
        TaskState.CREATED: {TaskState.DISCOVERY, TaskState.CANCELLED, TaskState.FAILED},
        TaskState.DISCOVERY: {TaskState.ASSIGNED, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.ASSIGNED: {TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.RUNNING: {TaskState.REVIEW, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.REVIEW: {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.COMPLETED: set(),  # Terminal
        TaskState.FAILED: set(),     # Terminal
        TaskState.CANCELLED: set(),  # Terminal
    }

    @classmethod
    def is_valid_transition(cls, current: TaskState, next_state: TaskState) -> bool:
        """Check if transitioning from current to next_state is valid."""
        return next_state in cls.VALID_TRANSITIONS.get(current, set())
