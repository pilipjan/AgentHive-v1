"""Permission Authorization Engine for enforcing least-privilege access."""

from typing import List, Set, Union
from security.permissions.enums import AgentPermissionEnum, VisibilityScope


class PermissionAuthorizer:
    """Evaluates agent permissions against actions, visibility tiers, and operational rules."""

    MIN_REPUTATION_FOR_VERIFICATION = 3.50

    @classmethod
    def normalize_permissions(cls, permissions: Union[List[str], Set[str]]) -> Set[str]:
        """Normalize permissions to set of strings."""
        return {p.value if isinstance(p, AgentPermissionEnum) else str(p) for p in permissions}

    @classmethod
    def has_permission(cls, agent_permissions: Union[List[str], Set[str]], required_perm: AgentPermissionEnum) -> bool:
        """Check if an agent holds an explicit permission or admin override."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms:
            return True
        return required_perm.value in perms

    @classmethod
    def can_read_knowledge(
        cls,
        agent_permissions: Union[List[str], Set[str]],
        visibility: Union[VisibilityScope, str],
        is_owner: bool = False,
        is_hive_member: bool = False,
    ) -> bool:
        """Evaluate if an agent can read a knowledge entry given its visibility tier."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms or is_owner:
            return True

        vis = VisibilityScope(visibility) if isinstance(visibility, str) else visibility

        if vis == VisibilityScope.PUBLIC:
            return AgentPermissionEnum.READ_PUBLIC_KNOWLEDGE.value in perms
        elif vis == VisibilityScope.HIVE:
            return is_hive_member and AgentPermissionEnum.READ_PROJECT_KNOWLEDGE.value in perms
        elif vis == VisibilityScope.PROJECT:
            return AgentPermissionEnum.READ_PROJECT_KNOWLEDGE.value in perms
        elif vis == VisibilityScope.PRIVATE:
            return is_owner  # PRIVATE is never accessible by non-owners

        return False

    @classmethod
    def can_write_knowledge(
        cls,
        agent_permissions: Union[List[str], Set[str]],
        visibility: Union[VisibilityScope, str],
    ) -> bool:
        """Evaluate if an agent can publish knowledge to the target visibility tier."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms:
            return True

        if AgentPermissionEnum.WRITE_KNOWLEDGE.value not in perms:
            return False

        vis = VisibilityScope(visibility) if isinstance(visibility, str) else visibility
        # Publishing to PUBLIC requires explicit public permission as well
        if vis == VisibilityScope.PUBLIC:
            return AgentPermissionEnum.READ_PUBLIC_KNOWLEDGE.value in perms
        return True

    @classmethod
    def can_verify_knowledge(
        cls,
        agent_permissions: Union[List[str], Set[str]],
        reputation_score: float,
    ) -> bool:
        """Evaluate if an agent is authorized to submit peer verification verdicts."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms:
            return True

        if AgentPermissionEnum.VERIFY_KNOWLEDGE.value not in perms:
            return False

        return reputation_score >= cls.MIN_REPUTATION_FOR_VERIFICATION

    @classmethod
    def can_message_agents(
        cls,
        agent_permissions: Union[List[str], Set[str]],
        is_same_hive: bool = True,
    ) -> bool:
        """Evaluate if an agent is permitted to send a collaborative message."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms:
            return True

        if AgentPermissionEnum.MESSAGE_AGENTS.value not in perms:
            return False

        return is_same_hive

    @classmethod
    def can_execute_tool(
        cls,
        agent_permissions: Union[List[str], Set[str]],
        tool_name: str,
    ) -> bool:
        """Evaluate if an agent can execute a named tool."""
        perms = cls.normalize_permissions(agent_permissions)
        if AgentPermissionEnum.ADMIN_OVERRIDE.value in perms:
            return True

        return AgentPermissionEnum.EXECUTE_TOOL.value in perms
