# Shadow AI Architecture

Shadow AI is organized as a desktop shell plus a local service backend.

## Layers

- **Electron host**: owns the native window lifecycle and secure IPC preload bridge.
- **React renderer**: TypeScript UI built with Tailwind CSS and Framer Motion.
- **FastAPI backend**: local API boundary for agents, plugins, persistence, logging, and future AI integrations.
- **SQLite persistence**: lightweight local database accessed through SQLAlchemy async sessions.
- **Plugin system**: manifest-first extension contract under `app/plugins` for future runtime loading.
- **Agent system**: abstract `Agent` base class under `app/agents` for future specialized workers.

## Production Principles

- Context isolation is enabled in Electron.
- Runtime settings are environment-driven through Pydantic settings.
- Logs are emitted as structured JSON.
- Errors are surfaced through centralized FastAPI exception handlers.
- Build scripts separate development, validation, packaging, and Docker workflows.

## Shadow Core

Shadow Core is the central backend brain. It receives commands at `/api/v1/core/commands`, detects a preliminary intent, persists conversation messages, creates a task with a generated ID, emits task logs, creates an agent request, tracks the task lifecycle, and returns a response pipeline for future execution services.
