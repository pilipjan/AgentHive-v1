#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=================================================="
echo "🐝 AGENTHIVE V1 PLATFORM ORCHESTRATION STARTUP"
echo "=================================================="

# Check PostgreSQL container
if ! docker ps | grep -q agenthive-postgres; then
    echo "📦 Starting isolated PostgreSQL container on port 5433..."
    docker compose -f deployment/docker-compose.yml up -d postgres
    sleep 3
fi

# Run migrations
echo "🔄 Checking database migrations..."
source .venv/bin/activate
export PYTHONPATH=.
alembic -c backend/alembic.ini upgrade head

# Seed demo data if database is empty
echo "🌱 Ensuring baseline demonstration dataset is populated..."
python3 scripts/seed_demo_data.py

echo ""
echo "✅ All subsystems ready!"
echo "   - Backend:  http://127.0.0.1:8000/docs"
echo "   - Frontend: http://127.0.0.1:3001"
echo "   - Postgres: 127.0.0.1:5433 (agenthive)"
echo "=================================================="
