"""Unit tests for HiveStore blueprint data structures and clone tracking."""

import uuid
from backend.app.models.blueprint import AgentBlueprint, BlueprintClone


def test_blueprint_model_instantiation():
    """Verify AgentBlueprint model fields and default values."""
    bp = AgentBlueprint(
        id=uuid.uuid4(),
        slug="test-ai-agent",
        name="Test AI Agent",
        tagline="A test agent template for HiveStore.",
        description="Full markdown guide on running this agent.",
        category="automation",
        tags=["test", "automation", "python"],
        creator_id=uuid.uuid4(),
        creator_name="TestCreator",
        clone_count=0,
        avg_rating=0.0,
        status="PUBLISHED",
    )
    assert bp.slug == "test-ai-agent"
    assert bp.category == "automation"
    assert bp.clone_count == 0
    assert "test" in bp.tags


def test_blueprint_clone_model():
    """Verify BlueprintClone model tracking."""
    bp_id = uuid.uuid4()
    clone = BlueprintClone(
        id=uuid.uuid4(),
        clone_id="clone-abc12345",
        blueprint_id=bp_id,
        cloner_name="BobDev",
        cloner_note="Deploying on my home server",
    )
    assert clone.clone_id == "clone-abc12345"
    assert clone.blueprint_id == bp_id
    assert clone.cloner_name == "BobDev"
