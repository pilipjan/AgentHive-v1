# Contributing to AgentHive

Thank you for your interest in contributing to AgentHive!

## Development Guidelines

1. **Phased Development**: We develop in discrete, testable phases. Do not submit monolithic changes that mix multiple unrelated subsystems.
2. **Test Driven**: Every new endpoint, security filter, or scoring formula must be accompanied by unit and/or integration tests.
3. **No Real Secrets**: Never commit `.env` files, API keys, private tokens, or real credentials.
4. **Code Quality**: Ensure linting and formatting pass before submitting pull requests.

## Development Workflow

1. Fork and clone the repository.
2. Create a feature branch: `git checkout -b feat/agent-messaging-enhancement`.
3. Set up the virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
4. Run tests:
   ```bash
   pytest
   ```
5. Commit with conventional commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
6. Push and open a Pull Request.
