#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🚀 Starting AgentHive FastAPI Backend on port 8000..."
source .venv/bin/activate
export PYTHONPATH=.

# Run database migrations first
echo "🔄 Running Alembic database migrations..."
alembic -c backend/alembic.ini upgrade head

# Start Uvicorn server
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info
