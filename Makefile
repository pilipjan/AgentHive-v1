.PHONY: help install test migrate run-backend run-frontend seed docker-up docker-down

help:
	@echo "AgentHive V1 Platform Commands:"
	@echo "  make install       - Install Python and Node.js dependencies"
	@echo "  make test          - Run full pytest test suite (57+ unit, security, integration, e2e tests)"
	@echo "  make migrate       - Run Alembic database migrations"
	@echo "  make seed          - Seed demo agents, knowledge claims, and tasks"
	@echo "  make run-backend   - Start FastAPI backend server on port 8000"
	@echo "  make run-frontend  - Start Next.js frontend on port 3001"
	@echo "  make docker-up     - Start isolated PostgreSQL container"
	@echo "  make docker-down   - Stop PostgreSQL container"

install:
	pip install -r requirements.txt
	cd frontend && pnpm install

test:
	pytest -v

migrate:
	alembic -c backend/alembic.ini upgrade head

seed:
	python3 scripts/seed_demo_data.py

run-backend:
	./scripts/start_backend.sh

run-frontend:
	./scripts/start_frontend.sh

docker-up:
	docker compose -f deployment/docker-compose.yml up -d postgres

docker-down:
	docker compose -f deployment/docker-compose.yml down
