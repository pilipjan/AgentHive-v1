#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR/frontend"

echo "✨ Starting AgentHive Next.js Web Dashboard on port 3001..."
exec pnpm start
