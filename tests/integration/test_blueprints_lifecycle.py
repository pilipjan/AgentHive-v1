"""Integration tests for HiveStore Blueprint publishing, discovery, and cloning."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_blueprint_publish_browse_and_clone_lifecycle(async_client: AsyncClient):
    """Verify publishing a template, browsing the store, filtering, and cloning."""
    uid = uuid.uuid4().hex[:6]
    slug = f"stream-ai-dj-{uid}"

    # 1. Publish Blueprint to HiveStore
    pub_res = await async_client.post("/api/v1/store/blueprints", json={
        "slug": slug,
        "name": "Stream AI DJ",
        "tagline": "24/7 Autonomous YouTube Livestream DJ with RAG capabilities.",
        "description": "# Stream AI DJ\n\nRuns 24/7 managing chat, requesting tracks, and live mixing.",
        "category": "dj",
        "tags": ["youtube", "livestream", "dj", "rag", "music"],
        "creator_name": "philipjohn",
        "repo_url": "https://github.com/pilipjan/stream-ai-dj",
        "setup_instructions": "1. Clone repo\n2. Set YOUTUBE_API_KEY\n3. Run `python main.py`",
        "docker_compose_snippet": "version: '3.8'\nservices:\n  ai-dj:\n    image: stream-ai-dj\n    restart: always",
        "env_vars_template": "YOUTUBE_API_KEY=your_key\nMODEL_PROVIDER=ollama",
        "required_models": ["gemma2:2b"],
        "required_tools": ["ffmpeg", "yt-dlp", "ollama"],
    })
    assert pub_res.status_code == 201
    bp_data = pub_res.json()
    assert bp_data["slug"] == slug
    assert bp_data["category"] == "dj"
    assert bp_data["clone_count"] == 0

    # 2. Browse Blueprints List
    list_res = await async_client.get("/api/v1/store/blueprints")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(b["slug"] == slug for b in list_data["items"])

    # 3. Filter by Category
    cat_res = await async_client.get("/api/v1/store/blueprints?category=dj")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert len(cat_data["items"]) >= 1
    assert any(b["slug"] == slug for b in cat_data["items"])

    # 4. Search by Name
    search_res = await async_client.get("/api/v1/store/blueprints?q=Stream+AI")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert any(b["slug"] == slug for b in search_data["items"])

    # 5. Get Blueprint Detail
    detail_res = await async_client.get(f"/api/v1/store/blueprints/{slug}")
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Stream AI DJ"
    assert "docker_compose_snippet" in detail_res.json()

    # 6. Clone the Blueprint (get setup package)
    clone_res = await async_client.post(f"/api/v1/store/blueprints/{slug}/clone", json={
        "cloner_name": "AlexStreamer",
        "cloner_note": "Setting this up for my lofi Twitch channel!",
    })
    assert clone_res.status_code == 200
    clone_data = clone_res.json()
    assert clone_data["blueprint_slug"] == slug
    assert clone_data["total_clones"] == 1
    assert "setup_instructions" in clone_data
    assert "docker_compose_snippet" in clone_data

    # 7. Verify Clone Count Updated on Store
    detail_res2 = await async_client.get(f"/api/v1/store/blueprints/{slug}")
    assert detail_res2.status_code == 200
    assert detail_res2.json()["clone_count"] == 1
