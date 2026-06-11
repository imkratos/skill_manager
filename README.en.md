<div align="center">
     <h1>Skill Manager</h1>
     <h3>AI Skill Engineering Platform</h3>
     <p>A platform for engineering, debugging, governing, and publishing enterprise AI skills.</p>
     <p>
          <b>FastAPI</b> + <b>Vue3</b> + <b>TypeScript</b> + <b>Workflow</b> + <b>Agent Runtime</b>
     </p>

English | [简体中文](./README.md)

</div>

## Overview

Skill Manager is not just a Prompt management dashboard. It is designed as an **AI Skill Engineering Platform** for building production-ready Agent capabilities.

In real enterprise scenarios, a reusable and governable Skill is more than a single prompt. It usually includes prompts, workflows, tool permissions, model configuration, input/output schemas, test cases, versions, logs, and release metadata.

The goal of this project is to manage these pieces as one engineering unit, so teams can manage AI Skills the same way they manage code, APIs, and microservices.

## Why This Project

Many AI Agent projects are still in a "wild prompt" stage:

| Current State | Problem |
| ---- | ---- |
| Prompts are copied everywhere | Hard to version, reuse, and audit |
| MCP / tools are connected freely | Permission boundaries are unclear |
| Workflows are scattered across projects | Hard to standardize and debug |
| Agent debugging relies on chat history | Missing trace, logs, and evaluation |
| Domain knowledge is fragmented | Hard to turn into reusable capability |

Skill Manager focuses on one core question:

> How do we manage the full lifecycle of an AI Skill, instead of only calling an LLM?

## What Is A Skill

A future-ready Skill should contain:

```text
Skill
├── Prompt
├── Workflow
├── Tool / MCP permissions
├── Memory
├── Model configuration
├── Input/output schemas
├── DSL
├── Test cases
├── Evaluation results
├── Version history
├── Agent strategy
└── Release metadata
```

In this sense, a Skill can be treated as a **microservice for the AI era**. It needs to be designed, debugged, tested, released, observed, reused, and governed.

## Product Direction

The long-term product direction includes four major parts:

| Module | Description | Status |
| ---- | ---- | ---- |
| Skill IDE | Editing and debugging prompts, workflows, DSL, and schemas | Planned |
| Skill Runtime | Execution, sandboxing, permissions, token usage, logs, and monitoring | In progress |
| Skill Registry | Skill upload, versioning, tagging, search, and installation, similar to npm | Planned |
| Skill Marketplace | Sharing, distribution, and commercialization of domain Skills | Planned |

## Current Foundation

This project is currently built on top of FastApiAdmin and already provides several enterprise admin foundations:

| Capability | Description |
| ---- | ---- |
| Users and permissions | Users, roles, menus, button permissions, and basic RBAC |
| Multi-tenant foundation | Tenant management, data isolation, and admin capabilities |
| Workflow foundation | Workflow definitions, node types, publishing, and execution entry |
| AI assistant foundation | Agent-based chat entry and conversation memory |
| Logs and monitoring | Operation logs, online users, server monitoring, and cache monitoring |
| Developer tools | Code generator, API docs, file management, and admin infrastructure |

These capabilities provide the base for building Skill IDE, Skill Runtime, Skill Registry, and enterprise permission governance.

## Initial Focus

Skill Manager focuses first on **enterprise document Skills**, rather than a generic Agent platform.

Typical scenarios include:

- Official documents, audit reports, contract review, and compliance documents
- Bid documents, PPT generation, Word reports, and structured document generation
- Domain knowledge for forestry, government affairs, auditing, and other vertical industries
- DSL-to-Word / PPT / spreadsheet rendering workflows
- Unified governance for enterprise prompts, workflows, and tool permissions

## Roadmap

Phase 1: Skill IDE

- Prompt editing and template management
- Visual workflow orchestration
- DSL debugging and rendering preview
- Input/output schema management
- Local debugging experience similar to Postman

Phase 2: Skill Runtime

- Skill execution entry
- Tool / MCP permission control
- Token usage, logs, and exception tracing
- Workflow Trace, Tool Trace, and Memory Trace

Phase 3: Skill Registry

- Skill upload, installation, and version management
- Tags, categories, and search
- Team-level sharing and reuse

Phase 4: Skill Marketplace

- Domain Skill publishing
- Enterprise Skill delivery
- Authorization and commercial distribution

> Note: The roadmap describes the product direction. It does not mean all capabilities are already implemented. The current repository is still in the stage of integrating enterprise admin foundations with Skill engineering capabilities.

## Quick Start

```bash
# 1. Configure environments
cp backend/env/.env.dev.example backend/env/.env.dev
cp frontend/web/.env.development.example frontend/web/.env.development

# 2. Start backend
cd backend
uv sync
uv run main.py run --env=dev

# 3. Start frontend
cd ../frontend/web
pnpm install
pnpm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Default accounts depend on your seed data or local environment configuration.

## Requirements

| Type | Requirement |
| ---- | ---- |
| Python | 3.10+, 3.12 recommended |
| Node.js | 20+ |
| Package managers | uv, pnpm |
| Database | MySQL 8.0+ or PostgreSQL 14+ |
| Cache | Redis 6.x / 7.x |

## Project Structure

```text
skill_manager/
├── backend/              # FastAPI backend
├── frontend/
│   └── web/              # Vue3 + TypeScript frontend
├── docker/               # Docker deployment configuration
├── scripts/              # Utility scripts
├── README.md             # Chinese README
└── README.en.md          # English README
```

## Tech Stack

- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic, Redis, APScheduler, Agno, Prefect
- Frontend: Vue3, TypeScript, Vite, Element Plus, Pinia, Vue Flow, CodeMirror
- Engineering: uv, pnpm, Docker, Ruff, ESLint, Vitest

## Vision

Stable AI applications will not rely on a single Agent alone. They will rely on testable, reusable, and governable Skills.

Skill Manager aims to turn scattered enterprise prompts, workflows, tool permissions, domain rules, and document templates into continuously evolving AI capability assets, eventually forming a Skill Operating System for enterprise document scenarios.
