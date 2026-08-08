# Shadow AI

Production-ready project architecture for a desktop AI operating system built with Electron, React, TypeScript, FastAPI, SQLite, Tailwind CSS, and Framer Motion.

> This repository intentionally contains architecture and boilerplate only. Product features are not implemented yet.

## Folder Structure

```text
.
├── apps/desktop              # Electron + React TypeScript desktop app
│   └── src
│       ├── main              # Electron main process
│       ├── preload           # Secure IPC bridge
│       └── renderer          # React application
├── services/backend          # FastAPI local backend service
│   ├── app
│   │   ├── agents            # Future agent abstractions and implementations
│   │   ├── api/routes        # HTTP route modules
│   │   ├── core              # Config, logging, and errors
│   │   ├── db                # SQLite/SQLAlchemy setup
│   │   ├── models            # Database models
│   │   ├── plugins           # Plugin manifests and loaders
│   │   ├── schemas           # Pydantic API schemas
│   │   └── services          # Domain services
│   └── tests                 # Backend tests
├── config                    # Shared future configuration assets
├── docs                      # Architecture and installation documentation
└── scripts                   # Bootstrap and build scripts
```

## Installation Guide

### Prerequisites

- Node.js 20+
- npm 10+
- Python 3.12+
- Docker Desktop, optional for backend container workflows

### Local Setup

```bash
./scripts/bootstrap.sh
```

Or manually:

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r services/backend/requirements.txt
cp .env.example .env
```

### Development

Run desktop and backend together:

```bash
npm run dev
```

Run only the backend:

```bash
npm run backend:dev
```

Run only the desktop shell:

```bash
npm run desktop:dev
```

### Validation

```bash
npm run lint
npm run typecheck
npm run backend:test
```

### Production Build

```bash
npm run build
npm run desktop:package
```

### Docker Backend

```bash
docker compose build
docker compose up
```

## Environment Configuration

Copy `.env.example` to `.env` and override values as needed:

- `SHADOW_AI_ENVIRONMENT`
- `SHADOW_AI_LOG_LEVEL`
- `SHADOW_AI_DATABASE_URL`
- `SHADOW_AI_PLUGIN_DIRECTORY`

## Architecture Notes

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the layered design, agent boundary, plugin contract, persistence approach, and production principles.

## Shadow Core API

Shadow Core is the central AI brain exposed by the FastAPI backend.

- `POST /api/v1/core/commands` receives a user command, creates a conversation record, assigns a task ID, detects intent, creates an agent request, stores logs, and returns the response pipeline.
- `GET /api/v1/core/tasks/{task_id}` returns the persisted task, generated agent requests, and task logs.
