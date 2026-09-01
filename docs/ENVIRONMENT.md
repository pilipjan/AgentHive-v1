# AgentHive V1 — Environment Discovery Report

**Generated Date:** 2026-09-01  
**Target Environment:** Oracle Cloud VPS (Always-Free ARM Ampere Instance)  
**Hostname:** `n8n-server`

---

## 1. System & Architecture Overview

| Parameter | Specification / Discovered Value |
| :--- | :--- |
| **Operating System** | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| **Kernel** | Linux 6.8.0-1057-oracle (`aarch64`) |
| **Architecture** | `aarch64` (ARM64 - ARM Neoverse-N1) |
| **vCPUs / Cores** | 4 OCPUs / 4 Cores, 4 Threads (1 thread/core) |
| **Total Memory (RAM)** | 23 GiB (Oracle Cloud A1 Flex ARM allocation) |
| **Available Memory** | ~19.0 GiB available (3.5 GiB used, 18 GiB cache/buffers) |
| **Swap Space** | 0 B (No swap partition configured) |
| **Total Disk Storage** | 194 GiB root filesystem (`/dev/sda1`) |
| **Used Disk Space** | 127 GiB (66% used) |
| **Available Disk Space** | 67 GiB free |

---

## 2. Installed Software & Runtimes

| Software / Runtime | Discovered Version | Status & Notes |
| :--- | :--- | :--- |
| **Docker Engine** | `29.1.3` (build 29.1.3-0ubuntu3~22.04.2) | Active, running systemd service |
| **Docker Compose** | `2.40.3` (`v2.40.3+ds1-0ubuntu1~22.04.1`) | Available for containerized orchestration |
| **Python** | `Python 3.10.12` | System runtime available; `python3-venv` available |
| **pip** | `22.0.2` | Available (`python3 -m pip`) |
| **Node.js** | `v22.22.2` | Active |
| **npm** | `10.9.7` | Active |
| **pnpm** | `10.32.1` | Active |
| **Git** | `2.34.1` | Installed and active |
| **PostgreSQL (Host)** | None directly on host OS | Running containerized PostgreSQL 15 for n8n |
| **Web Server / Reverse Proxy**| Nginx `1.18.0` (Ubuntu) | Active systemd service, bound to port 80 |
| **Tunnel / Edge Routing** | Cloudflared (`cloudflared.service`) | Active tunnel (`philipjohnn8nautomation.online`) |
| **Local LLM Engine** | Ollama (`ollama.service`) | Active on `localhost:11434` with local models: `gemma2:9b`, `gemma2:2b`, `llama3.1:8b`, `mistral-nemo:latest`, etc. |

---

## 3. Existing Projects & Background Services

The VPS hosts several existing projects that must remain completely untouched:

1. **`portfolio`**: Node.js web server running on port `8080`.
2. **`clark-bpo-careers`**: Node.js/TypeScript backend running on port `3000`, proxied via Nginx.
3. **`n8n-n8n-1` & `n8n-postgres-1`**: Docker Compose deployment for n8n automation on port `5678` with internal PostgreSQL 15 on port `5432` (container network).
4. **`openclaw` & `openclaw-gateway`**: Gateway running on port `18789`.
5. **`picoclaw`**: Systemd automation agent service.
6. **`stream`**: Daily automated livestream scheduler python process (`run_daily_stream.py`).
7. **`ollama`**: Local inference daemon serving models on port `11434`.
8. **`cloudflared`**: Cloudflare Tunnel mapping subdomains (`vps-health`, `philipjohnn8nautomation.online`, `n8n`, `openclaw`, `clawmetry`, `agri-inventory`, `invoice`) to respective local ports.

---

## 4. Port Allocations & Availability

### Currently Occupied Ports
- **`22` / TCP**: OpenSSH daemon
- **`53` / TCP/UDP**: systemd-resolved (DNS)
- **`80` / TCP**: Nginx reverse proxy
- **`3000` / TCP**: `clark-bpo-careers` application
- **`5678` / TCP**: n8n container
- **`8080` / TCP**: Portfolio service
- **`11434` / TCP**: Ollama local inference API
- **`18789` / TCP**: OpenClaw gateway
- **`41915` / TCP**: Local listening service

### Allocated Ports for AgentHive (Conflict-Free)
- **AgentHive Backend (FastAPI)**: **`8000`** (or `8090` fallback)
- **AgentHive Frontend (Next.js)**: **`3001`** (or `3030` fallback, avoiding port `3000`)
- **AgentHive PostgreSQL (Dedicated DB)**: **`5433`** (or internal Docker network only, ensuring no collision with host or existing containers)

---

## 5. Network & Firewall Configuration

- **UFW Firewall**: Active.
  - Allowed ingress: SSH (22), Nginx (80, 443 via Cloudflare IP ranges), n8n (5678), OpenClaw (18789), Node (3000).
- **Oracle Cloud Security Lists**: Standard egress allowed; ingress restricted to configured security rules.
- **AgentHive Access Strategy**:
  - For local development & testing: Bind to `127.0.0.1` / `0.0.0.0` on dedicated ports (`8000` for backend, `3001` for frontend).
  - For remote browser access: Can be exposed cleanly via Nginx reverse proxy location block (e.g., `/agenthive`) or a dedicated Cloudflare Tunnel ingress route (e.g., `agenthive.philipjohnn8nautomation.online`), requiring zero modifications to existing project tunnels.

---

## 6. Isolation & Directory Strategy

To guarantee that AgentHive does not interfere with or overwrite any existing projects:
- **Development Directory**: `/home/ubuntu/agenthive/` (Isolated Python virtual environment `.venv/`, isolated Node `node_modules/`, independent Git repository).
- **Production Staging Directory**: `/opt/agenthive/` (Owned by `ubuntu:ubuntu`).
- **Data Persistence**: Dedicated Docker volume or directory `/home/ubuntu/agenthive/data/postgres` completely separate from `/home/ubuntu/n8n/`.
- **Environment Isolation**: Dedicated `.env` file within the AgentHive repository with strict `.gitignore` rules.
