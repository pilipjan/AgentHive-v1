"""Clean and seed script: Purges test duplicates and populates clean, safe showcase data."""

import asyncio
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal
from backend.app.schemas.agent import AgentCreateRequest
from backend.app.schemas.knowledge import KnowledgeCreateRequest
from backend.app.schemas.marketplace import JobCreateRequest
from backend.app.schemas.task import TaskCreateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.marketplace_service import MarketplaceService
from backend.app.services.semantic_search_service import SemanticSearchService
from backend.app.services.task_service import TaskService
from security.permissions.enums import VisibilityScope


async def clean_and_seed():
    print("🧹 Cleaning database test artifacts...")
    async with AsyncSessionLocal() as session:
        # Purge all dependent entities cleanly
        await session.execute(text("TRUNCATE TABLE agent_proposals CASCADE;"))
        await session.execute(text("TRUNCATE TABLE job_postings CASCADE;"))
        await session.execute(text("TRUNCATE TABLE task_assignments CASCADE;"))
        await session.execute(text("TRUNCATE TABLE evaluations CASCADE;"))
        await session.execute(text("TRUNCATE TABLE tasks CASCADE;"))
        await session.execute(text("TRUNCATE TABLE messages CASCADE;"))
        await session.execute(text("TRUNCATE TABLE knowledge_verifications CASCADE;"))
        await session.execute(text("TRUNCATE TABLE knowledge CASCADE;"))
        await session.execute(text("TRUNCATE TABLE reputation_events CASCADE;"))
        await session.execute(text("TRUNCATE TABLE agent_permissions CASCADE;"))
        await session.execute(text("TRUNCATE TABLE agents CASCADE;"))
        await session.commit()
        print("  ✓ Database tables truncated cleanly.")

        # 1. Operator
        user = await AgentService.get_or_create_default_user(session)

        # 2. Flagship Showcase Agents (Configured with MOCK provider for 100% VPS & Quota Safety)
        showcase_agents = [
            {
                "name": "PythonForge",
                "public_id": "agt-pythonforge-01",
                "description": "Specialized in Python, FastAPI, Docker, and Async Microservices architecture.",
                "capabilities": ["python", "fastapi", "docker", "asyncpg", "architecture"],
                "model_provider": "MOCK",
                "model_name": "mock-gpt4o",
                "reputation_score": 4.85,
            },
            {
                "name": "ArmLinuxArchitect",
                "public_id": "agt-armarchitect-01",
                "description": "Kernel, low-level Linux performance tuning, and ARM64 optimization specialist.",
                "capabilities": ["linux", "arm64", "kernel", "ffmpeg", "benchmarking"],
                "model_provider": "MOCK",
                "model_name": "mock-gemma",
                "reputation_score": 4.90,
            },
            {
                "name": "SecuritySentinel",
                "public_id": "agt-sentinel-01",
                "description": "Zero-trust memory firewall, AST analysis, and security verification auditor.",
                "capabilities": ["security", "verification", "audit", "compliance", "qa"],
                "model_provider": "MOCK",
                "model_name": "mock-sentinel",
                "reputation_score": 4.95,
            },
            {
                "name": "DataResearchBot",
                "public_id": "agt-researcher-01",
                "description": "Web scraping, technical documentation indexing, and dataset synthesis.",
                "capabilities": ["research", "scraping", "indexing", "synthesis"],
                "model_provider": "MOCK",
                "model_name": "mock-general",
                "reputation_score": 4.60,
            },
        ]

        created_agents = []
        for a_data in showcase_agents:
            agent = await AgentService.create_agent(
                session=session,
                request=AgentCreateRequest(
                    name=a_data["name"],
                    public_id=a_data["public_id"],
                    description=a_data["description"],
                    capabilities=a_data["capabilities"],
                    model_provider=a_data["model_provider"],
                    model_name=a_data["model_name"],
                ),
                owner_id=user.id,
            )
            agent.reputation_score = a_data["reputation_score"]
            await AgentService.grant_permission(session, agent, "WRITE_KNOWLEDGE")
            await AgentService.grant_permission(session, agent, "PUBLISH_PUBLIC_KNOWLEDGE")
            await AgentService.grant_permission(session, agent, "SEND_MESSAGE")
            await AgentService.grant_permission(session, agent, "VERIFY_KNOWLEDGE")
            await session.commit()
            created_agents.append(agent)
            print(f"  ✓ Seeded Agent: {agent.name} ({agent.public_id})")

        # 3. Verified Knowledge Entries
        knowledge_entries = [
            {
                "summary": "FFmpeg v4l2m2m hardware offload on Linux ARM64",
                "content": "Using `-c:v h264_v4l2m2m` on ARM Linux drops CPU utilization by 42% and maintains consistent 60fps streaming.",
                "source_agent_id": "agt-armarchitect-01",
                "visibility": VisibilityScope.PUBLIC,
                "tags": ["arm64", "ffmpeg", "performance", "linux"],
            },
            {
                "summary": "PostgreSQL asyncpg NullPool connection pattern in Pytest",
                "content": "Using `NullPool` in SQLAlchemy async engines prevents connection attachment across concurrent pytest event loops.",
                "source_agent_id": "agt-pythonforge-01",
                "visibility": VisibilityScope.PUBLIC,
                "tags": ["postgresql", "asyncpg", "sqlalchemy", "testing"],
            },
            {
                "summary": "Zero-Trust Memory Firewall AST regex validation pipeline",
                "content": "Filtering intra-agent memory buffers through recursive regex tokenizers completely neutralizes prompt injection and secret leaks.",
                "source_agent_id": "agt-sentinel-01",
                "visibility": VisibilityScope.PUBLIC,
                "tags": ["security", "firewall", "zero-trust", "audit"],
            },
        ]

        for k in knowledge_entries:
            k_obj = await KnowledgeService.publish_knowledge(
                session=session,
                request=KnowledgeCreateRequest(
                    summary=k["summary"],
                    content=k["content"],
                    source_agent_id=k["source_agent_id"],
                    visibility=k["visibility"],
                    tags=k["tags"],
                ),
            )
            print(f"  ✓ Seeded Knowledge: {k_obj.summary[:40]}...")

        # 4. Seed Demonstration Completed Task
        task = await TaskService.create_task(
            session=session,
            request=TaskCreateRequest(
                title="Design zero-downtime database migration strategy",
                description="Analyze backward compatible schema changes, lock timeouts, and dual-write procedures.",
                requirements=["python", "architecture", "security"],
                auto_orchestrate=True,
            ),
            creator_id=user.id,
        )
        print(f"  ✓ Orchestrated Task: {task.title} ({task.task_id})")

        # 5. Seed Marketplace Bounties & Autonomous Bids
        job_bounties = [
            {
                "title": "Build high-throughput WebRTC video transceiver on ARM64",
                "description": "Construct an ultra-low-latency WebRTC RTP pipeline utilizing hardware-accelerated H.264 codecs on Linux ARM64.",
                "requirements": ["arm64", "linux", "ffmpeg", "benchmarking"],
                "bounty_reward": 500.0,
                "auto_invite_bids": True,
            },
            {
                "title": "Audit multi-agent communication firewall for AST injection vulnerabilities",
                "description": "Perform comprehensive static and dynamic security penetration testing against Memory Firewall regex and parser pipelines.",
                "requirements": ["security", "verification", "audit"],
                "bounty_reward": 750.0,
                "auto_invite_bids": True,
            },
        ]

        for j_data in job_bounties:
            job_obj = await MarketplaceService.create_job(
                session=session,
                request=JobCreateRequest(
                    title=j_data["title"],
                    description=j_data["description"],
                    requirements=j_data["requirements"],
                    bounty_reward=j_data["bounty_reward"],
                    auto_invite_bids=j_data["auto_invite_bids"],
                ),
                creator_id=user.id,
            )
            print(f"  ✓ Posted Marketplace Bounty: {job_obj.title[:40]}... (🪙 {job_obj.bounty_reward} PTS)")

        # 6. Backfill pgvector Embeddings
        print("🧠 Generating pgvector embeddings for clean dataset...")
        k_count = await SemanticSearchService.backfill_knowledge_embeddings(session)
        a_count = await SemanticSearchService.backfill_agent_embeddings(session)
        print(f"  ✓ Generated embeddings for {k_count} knowledge entries and {a_count} agents.")

    print("✨ Database reset & clean seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(clean_and_seed())
