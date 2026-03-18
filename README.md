# Human Responsibility Computing Engine (HRCE)

> **Agentic AI-Powered Responsibility Management Platform**

HRCE is a full-stack platform that uses AI agents (LangChain + LangGraph) to intelligently decompose events into responsibilities, model dependencies, assess risk, and orchestrate notifications — helping humans manage complex obligations.

---

## 🏗️ Architecture

```
hrce-platform/
├── backend/           # FastAPI — Core API & responsibility engine
├── agent-service/     # LangChain/LangGraph — AI agent orchestration
├── web-app/           # React/Next.js — Dashboard UI
├── workers/           # Celery — Background task workers
├── vector-db/         # pgvector config & scripts
├── graph-db/          # PostgreSQL graph + init SQL
├── docs/              # Project documentation
└── .github/workflows/ # CI/CD pipelines
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.11 |
| AI Agents | LangChain + LangGraph |
| Database | PostgreSQL + pgvector |
| Cache / Queue | Redis + Celery |
| Object Storage | MinIO |
| Frontend | React + Next.js + Tailwind + ShadCN |
| Real-time | WebSockets + Socket.IO |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## 🚀 Quickstart

### Prerequisites
- Docker Desktop
- Git

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd hrce-platform
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Start all services
```bash
docker compose up -d
```

### 4. Verify services are running
```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 5. Access services

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Agent Service | http://localhost:8001 |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 🧑‍💻 Developer Commands

```bash
make up          # Start all services
make down        # Stop all services
make logs        # Follow logs
make test        # Run tests
make lint        # Lint backend code
make migrate     # Run DB migrations
make build       # Rebuild Docker images
```

---

## 📋 Development Stages

| Stage | Description | Status |
|---|---|---|
| 0 | Environment & Foundational Setup | ✅ Complete |
| 1 | Core Backend Scaffolding | ✅ Complete |
| 2 | Database Schema & Storage Layer | ✅ Complete |
| 3 | Event & Responsibility Engine | ✅ Complete |
| 4 | Document & Context System | ✅ Complete |
| 5 | Agentic AI Layer | ✅ Complete |
| 6 | Risk & Preparation Intelligence | ✅ Complete |
| 7 | Notification Orchestration | ✅ Complete |
| 8 | Real-Time Communication | ✅ Complete |
| 9 | Web Full-Stack UI | ✅ Complete |
| 10 | Agent Execution Triggers | ✅ Complete |
| 11 | Security & Auth | ✅ Complete |
| 12 | Containerization & Local Orchestration | ✅ Complete |

---

## 🔐 Environment Variables

See [`.env.example`](.env.example) for all required environment variables.

**Required keys to fill in:**
- `GROQ_API_KEY` — Your Groq API key (for RAG/Agents)
- `OPENAI_API_KEY` — Your OpenAI API key (optional/fallback)
- `LANGCHAIN_API_KEY` — Your LangSmith API key (for tracing)
- `APP_SECRET_KEY` — Random secret for the app
- `JWT_SECRET_KEY` — Random secret for JWT auth
