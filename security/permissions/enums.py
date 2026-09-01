"""Security permission, visibility, sensitivity, and policy enums."""

from enum import Enum


class AgentPermissionEnum(str, Enum):
    """Atomic permission enums for agent actions."""

    READ_PUBLIC_KNOWLEDGE = "READ_PUBLIC_KNOWLEDGE"
    READ_PROJECT_KNOWLEDGE = "READ_PROJECT_KNOWLEDGE"
    WRITE_KNOWLEDGE = "WRITE_KNOWLEDGE"
    VERIFY_KNOWLEDGE = "VERIFY_KNOWLEDGE"
    MESSAGE_AGENTS = "MESSAGE_AGENTS"
    CREATE_TASK = "CREATE_TASK"
    REVIEW_AGENT = "REVIEW_AGENT"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    ACCESS_NETWORK = "ACCESS_NETWORK"
    ACCESS_FILES = "ACCESS_FILES"
    ADMIN_OVERRIDE = "ADMIN_OVERRIDE"


class VisibilityScope(str, Enum):
    """Visibility boundaries for shared knowledge and task artifacts."""

    PRIVATE = "PRIVATE"      # Accessible ONLY by the creator agent/user
    HIVE = "HIVE"            # Accessible ONLY by agents assigned to the same Hive
    PROJECT = "PROJECT"      # Accessible across the same Project/Workspace
    PUBLIC = "PUBLIC"        # Universally queryable across the platform


class SensitivityTier(str, Enum):
    """Data sensitivity classification tiers."""

    PUBLIC = "PUBLIC"              # Free of sensitive/confidential material
    INTERNAL = "INTERNAL"          # General operational data
    CONFIDENTIAL = "CONFIDENTIAL"  # Restricted team data, credentials, PII
    RESTRICTED = "RESTRICTED"      # Strictly protected, requires admin authorization


class PolicyVerdict(str, Enum):
    """Memory Firewall policy verdicts."""

    ALLOWED = "ALLOWED"      # Clean payload, permitted to proceed
    REDACTED = "REDACTED"    # Sanitized payload with sensitive segments replaced
    BLOCKED = "BLOCKED"      # Rejected outright due to security or permission violation
