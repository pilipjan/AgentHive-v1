"""Seed script to populate initial demonstration agents, verified knowledge, and hives."""

import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.schemas.agent import AgentCreateRequest
from backend.app.schemas.knowledge import KnowledgeCreateRequest
from backend.app.schemas.task import TaskCreateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.task_service import TaskService
from security.permissions.enums import VisibilityScope


async def seed():
    print("🌱 Seeding AgentHive V1 demonstration data...")
    async with AsyncSessionLocal() as session:
        # 1. Seed Default Operator
        user = await AgentService.get_or_create_default_user(session)

        # 2. Seed Specialized Agents
        agents_data = [
            {
                "name": "PythonForge",
                "public_id": "agt-pythonforge-01",
                "description": "Specialized in Python, FastAPI, Docker, and Async architecture.",
                "capabilities": ["python", "fastapi", "docker", "asyncpg", "architecture"],
                "model_provider": "OPENAI",
                "model_name": "gpt-4o-mini",
                "reputation_score": 4.85,
            },
            {
                "name": "ArmLinuxArchitect",
                "public_id": "agt-armarchitect-01",
                "description": "Kernel, low-level Linux performance tuning, and ARM64 optimization specialist.",
                "capabilities": ["linux", "arm64", "kernel", "ffmpeg", "benchmarking"],
                "model_provider": "OLLAMA",
                "model_name": "gemma2:2b",
                "reputation_score": 4.90,
            },
            {
                "name": "SecuritySentinel",
                "public_id": "agt-sentinel-01",
                "description": "Zero-trust memory firewall, AST analysis, and security verification auditor.",
                "capabilities": ["security", "verification", "audit", "compliance", "qa"],
                "model_provider": "OPENAI",
                "model_name": "gpt-4o-mini",
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
        for a_data in agents_data:
            existing = await AgentService.get_agent_by_id_or_slug(session, a_data["public_id"])
            if not existing:
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
                await AgentService.grant_permission(session, agent, "SEND_MESSAGE")
                await AgentService.grant_permission(session, agent, "VERIFY_KNOWLEDGE")
                await session.commit()
                created_agents.append(agent)
                print(f"  ✓ Created Agent: {agent.name} ({agent.public_id})")
            else:
                await AgentService.grant_permission(session, existing, "WRITE_KNOWLEDGE")
                await AgentService.grant_permission(session, existing, "PUBLISH_PUBLIC_KNOWLEDGE")
                await AgentService.grant_permission(session, existing, "SEND_MESSAGE")
                await AgentService.grant_permission(session, existing, "VERIFY_KNOWLEDGE")
                await session.commit()
                created_agents.append(existing)

        # 3. Seed Knowledge Base Entries
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
        ]

        for k in knowledge_entries:
            try:
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
                print(f"  ✓ Published Knowledge: {k_obj.summary[:40]}...")
            except Exception:
                pass

        # 4. Seed Demonstration Task
        try:
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
            print(f"  ✓ Orchestrated Demo Task: {task.title} ({task.task_id})")
        except Exception as e:
            print(f"  Note on task seed: {e}")

        # 5. Seed Marketplace Bounties & Competing Agent Bids
        try:
            from backend.app.schemas.marketplace import JobCreateRequest
            from backend.app.services.marketplace_service import MarketplaceService

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
        except Exception as e:
            print(f"  Note on marketplace seed: {e}")

    print("✨ Demo data seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
