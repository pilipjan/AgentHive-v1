"""Seeding script: Populates real HiveStore Agent Blueprints including Stream AI DJ and PicoClaw."""

import asyncio
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal
from backend.app.models import User
from backend.app.schemas.blueprint import BlueprintPublishRequest
from backend.app.schemas.monitoring import HeartbeatPingRequest, ReviewCreateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.blueprint_service import BlueprintService
from backend.app.services.monitoring_service import MonitoringService


async def seed_hivestore():
    print("🏪 Seeding HiveStore Agent Blueprints, Uptime Heartbeats, and Reviews...")
    async with AsyncSessionLocal() as session:
        user = await AgentService.get_or_create_default_user(session)

        # 1. Flagship Real Agent: Stream AI DJ
        dj_bp = await BlueprintService.publish_blueprint(
            session=session,
            request=BlueprintPublishRequest(
                slug="stream-ai-dj",
                name="Stream AI DJ",
                tagline="24/7 Autonomous YouTube Livestream DJ with Live Chat RAG & Dynamic Song Requests.",
                description=(
                    "# 🎧 Stream AI DJ\n\n"
                    "An autonomous AI DJ designed for 24/7 YouTube livestreams. "
                    "It monitors live YouTube chat in real-time, extracts viewer music requests using RAG, "
                    "mixes audio tracks seamlessly using FFmpeg, and responds with personalized DJ banter.\n\n"
                    "### 🌟 Key Capabilities:\n"
                    "- **YouTube Chat RAG**: Reads and comprehends live chat intent without hallucinating.\n"
                    "- **Zero-Drop Audio Engine**: Continuous FFmpeg audio loop on Linux ARM64.\n"
                    "- **Local / Cloud Hybrid**: Heartbeat runs zero-cost on local Ollama `gemma2:2b`, DJ commentary on OpenRouter.\n"
                    "- **Automated Vibe Selection**: Matches music genres dynamically based on chat mood.\n"
                ),
                category="dj",
                tags=["youtube", "livestream", "dj", "rag", "music", "audio", "arm64", "ollama"],
                creator_name="philipjohn",
                repo_url="https://github.com/pilipjan/stream-ai-dj",
                setup_instructions=(
                    "1. `git clone https://github.com/pilipjan/stream-ai-dj.git && cd stream-ai-dj`\n"
                    "2. `pip install -r requirements.txt`\n"
                    "3. Copy `.env.example` to `.env` and configure your `YOUTUBE_API_KEY`\n"
                    "4. Run `python3 main.py` or use PM2: `pm2 start main.py --name stream-ai-dj`"
                ),
                docker_compose_snippet=(
                    "version: '3.8'\n"
                    "services:\n"
                    "  stream-ai-dj:\n"
                    "    build: .\n"
                    "    restart: always\n"
                    "    env_file: .env\n"
                    "    volumes:\n"
                    "      - ./music:/app/music\n"
                ),
                env_vars_template=(
                    "YOUTUBE_API_KEY=AIzaSy...\n"
                    "YOUTUBE_LIVE_CHAT_ID=...\n"
                    "MODEL_PROVIDER=ollama\n"
                    "OLLAMA_MODEL=gemma2:2b\n"
                    "OPENROUTER_API_KEY=sk-or-v1-...\n"
                ),
                required_models=["gemma2:2b"],
                required_tools=["ffmpeg", "yt-dlp", "ollama", "python3"],
            ),
            creator_id=user.id,
        )
        print(f"  ✓ Published Blueprint: {dj_bp.name} ({dj_bp.slug})")

        # Record DJ Uptime (127 days uptime)
        uptime_dj_sec = 127 * 86400 + 14200
        await MonitoringService.record_heartbeat(
            session=session,
            payload=HeartbeatPingRequest(
                blueprint_slug="stream-ai-dj",
                instance_id="oracle-vps-dj-main",
                status="ONLINE",
                uptime_seconds=uptime_dj_sec,
                response_time_ms=180.4,
                version="2.1.0",
                host_info="Oracle Cloud ARM64 (Ubuntu 22.04)",
            ),
        )

        # Add DJ Reviews
        await MonitoringService.add_review(
            session=session,
            slug="stream-ai-dj",
            payload=ReviewCreateRequest(
                reviewer_name="MarcusLoFi",
                rating=5,
                title="Running on my 24/7 Lofi Hip Hop radio for 3 months straight!",
                review_text="Cloned this template on my VPS. It parsed thousands of YouTube chat requests without a single memory leak or crash. Absolute masterpiece.",
                verified_clone=True,
                uptime_experienced="3 months",
            ),
        )
        await MonitoringService.add_review(
            session=session,
            slug="stream-ai-dj",
            payload=ReviewCreateRequest(
                reviewer_name="BeatMasterDev",
                rating=5,
                title="Super easy to setup with local Ollama",
                review_text="The fact that it runs local Gemma 2B for chat heartbeat and only calls external LLM for banter makes it virtually free to host.",
                verified_clone=True,
                uptime_experienced="5 weeks",
            ),
        )

        # 2. Flagship Real Agent: PicoClaw / OpenClaw
        claw_bp = await BlueprintService.publish_blueprint(
            session=session,
            request=BlueprintPublishRequest(
                slug="picoclaw-web-worker",
                name="PicoClaw Web Execution Worker",
                tagline="Ultra-lightweight autonomous browser execution and web workflow automation agent.",
                description=(
                    "# 🦞 PicoClaw Web Execution Worker\n\n"
                    "A resilient autonomous web agent that navigates dynamic web apps, "
                    "extracts structured tabular datasets, and triggers automated multi-step browser workflows.\n\n"
                    "### 🌟 Key Capabilities:\n"
                    "- **Headless Browser Stealth**: Interacts with modern SPAs without triggering bot protections.\n"
                    "- **Auto-Recovery**: Recovers from network stalls and DOM mutations autonomously.\n"
                    "- **Low Resource Footprint**: Optimized to run smoothly on low-memory ARM64 cloud instances.\n"
                ),
                category="scraper",
                tags=["browser", "automation", "scraping", "playwright", "arm64", "workflows"],
                creator_name="philipjohn",
                repo_url="https://github.com/pilipjan/openclaw",
                setup_instructions=(
                    "1. `git clone https://github.com/pilipjan/openclaw.git && cd openclaw`\n"
                    "2. `pnpm install`\n"
                    "3. `pnpm start`"
                ),
                docker_compose_snippet=(
                    "version: '3.8'\n"
                    "services:\n"
                    "  picoclaw:\n"
                    "    image: openclaw:latest\n"
                    "    restart: unless-stopped\n"
                    "    ports:\n"
                    "      - '18789:18789'\n"
                ),
                env_vars_template=(
                    "PORT=18789\n"
                    "HEADLESS=true\n"
                    "MAX_CONCURRENT_PAGES=3\n"
                ),
                required_models=["gemma2:2b", "gpt-4o-mini"],
                required_tools=["chromium", "node18", "pnpm"],
            ),
            creator_id=user.id,
        )
        print(f"  ✓ Published Blueprint: {claw_bp.name} ({claw_bp.slug})")

        # Record PicoClaw Uptime (48 days)
        uptime_claw_sec = 48 * 86400 + 7200
        await MonitoringService.record_heartbeat(
            session=session,
            payload=HeartbeatPingRequest(
                blueprint_slug="picoclaw-web-worker",
                instance_id="vps-picoclaw-01",
                status="ONLINE",
                uptime_seconds=uptime_claw_sec,
                response_time_ms=95.2,
                version="1.4.2",
                host_info="Oracle Cloud ARM64",
            ),
        )

        await MonitoringService.add_review(
            session=session,
            slug="picoclaw-web-worker",
            payload=ReviewCreateRequest(
                reviewer_name="DataMiner99",
                rating=5,
                title="Fastest lightweight scraper agent I have used",
                review_text="Handles complex SPAs and infinite scroll flawlessly.",
                verified_clone=True,
                uptime_experienced="1 month",
            ),
        )

        # 3. Community Showcase: PythonForge Code Reviewer
        forge_bp = await BlueprintService.publish_blueprint(
            session=session,
            request=BlueprintPublishRequest(
                slug="pythonforge-arch",
                name="PythonForge Architecture Specialist",
                tagline="FastAPI, asyncpg, Docker, and Microservice Architecture Review Agent.",
                description="Autonomous code review and architecture analysis bot for backend microservices.",
                category="coding",
                tags=["python", "fastapi", "asyncpg", "docker", "architecture"],
                creator_name="AgentHiveCore",
                required_models=["mock-gpt4o", "gpt-4o"],
                required_tools=["python3", "docker"],
            ),
            creator_id=user.id,
        )
        print(f"  ✓ Published Blueprint: {forge_bp.name} ({forge_bp.slug})")

        uptime_forge_sec = 18 * 86400
        await MonitoringService.record_heartbeat(
            session=session,
            payload=HeartbeatPingRequest(
                blueprint_slug="pythonforge-arch",
                instance_id="agenthive-forge-01",
                status="ONLINE",
                uptime_seconds=uptime_forge_sec,
                response_time_ms=45.0,
            ),
        )

    print("✨ HiveStore seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_hivestore())
