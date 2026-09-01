"""Security unit tests for PermissionAuthorizer."""

from security.permissions.enums import AgentPermissionEnum, VisibilityScope
from security.permissions.authorizer import PermissionAuthorizer


def test_permission_normalization_and_check():
    perms = ["READ_PUBLIC_KNOWLEDGE", "MESSAGE_AGENTS"]
    assert PermissionAuthorizer.has_permission(perms, AgentPermissionEnum.READ_PUBLIC_KNOWLEDGE)
    assert not PermissionAuthorizer.has_permission(perms, AgentPermissionEnum.WRITE_KNOWLEDGE)


def test_admin_override():
    perms = ["ADMIN_OVERRIDE"]
    assert PermissionAuthorizer.has_permission(perms, AgentPermissionEnum.WRITE_KNOWLEDGE)
    assert PermissionAuthorizer.can_read_knowledge(perms, VisibilityScope.PRIVATE, is_owner=False)
    assert PermissionAuthorizer.can_verify_knowledge(perms, reputation_score=1.0)


def test_knowledge_visibility_rules():
    # Public knowledge with READ_PUBLIC_KNOWLEDGE
    assert PermissionAuthorizer.can_read_knowledge(
        ["READ_PUBLIC_KNOWLEDGE"], VisibilityScope.PUBLIC
    )
    assert not PermissionAuthorizer.can_read_knowledge(
        [], VisibilityScope.PUBLIC
    )

    # Hive knowledge requires same hive and READ_PROJECT_KNOWLEDGE
    assert PermissionAuthorizer.can_read_knowledge(
        ["READ_PROJECT_KNOWLEDGE"], VisibilityScope.HIVE, is_hive_member=True
    )
    assert not PermissionAuthorizer.can_read_knowledge(
        ["READ_PROJECT_KNOWLEDGE"], VisibilityScope.HIVE, is_hive_member=False
    )

    # Private knowledge accessible ONLY by owner
    assert PermissionAuthorizer.can_read_knowledge(
        ["READ_PUBLIC_KNOWLEDGE", "READ_PROJECT_KNOWLEDGE"], VisibilityScope.PRIVATE, is_owner=False
    ) is False
    assert PermissionAuthorizer.can_read_knowledge(
        [], VisibilityScope.PRIVATE, is_owner=True
    ) is True


def test_verification_reputation_threshold():
    perms = ["VERIFY_KNOWLEDGE"]
    # Score 3.8 >= 3.5 -> Authorized
    assert PermissionAuthorizer.can_verify_knowledge(perms, reputation_score=3.8) is True
    # Score 3.2 < 3.5 -> Unauthorized
    assert PermissionAuthorizer.can_verify_knowledge(perms, reputation_score=3.2) is False
