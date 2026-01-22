# PROJECT.md

## Overview

**Name**: Cosmograph
**Tagline**: Turn documents into interactive knowledge graphs for tribal and enterprise clients
**Stage**: v0.1.0 → v0.2.0 (CLI → Web Service)
**Primary User**: Iyeska document services team, then client self-service

## Vision

Cosmograph transforms unstructured documents (legal codes, policies, contracts, project docs) into explorable knowledge graphs. Clients upload documents, the system extracts entities and relationships using pattern matching + LLM intelligence, and delivers interactive D3.js visualizations.

**Why this matters for Iyeska clients:**
- Tribal codes and ordinances become navigable maps
- Policy documents reveal hidden dependencies
- Contract relationships become visible at a glance
- Project documentation connects across silos

## Current State (v0.1.0)

Working CLI tool with:
- Legal document extractor (CRST codes successfully processed)
- Plain text/markdown extractor
- Generic pattern-based extractor
- Self-contained HTML visualization (D3.js force graph)
- CSV export for external analysis

**Missing:**
- No PDF support (legal docs often come as PDFs)
- No LLM extraction (limited to regex patterns)
- No custom pattern configuration
- No web interface
- No job persistence

## Product Principles

1. **Document Sovereignty** - Client documents never leave Iyeska infrastructure unless explicitly approved
2. **Progressive Extraction** - Pattern matching first, LLM for what patterns miss (cost control)
3. **Self-Contained Output** - Generated visualizations work offline, no external dependencies
4. **Operator-First UX** - Built for Iyeska team to serve clients, not direct client self-service (initially)

## Success Criteria

### v0.2.0 Milestone: "Web Foundation"

**Goal**: Iyeska team can process client documents through a web interface on Iyeska HQ infrastructure

**Acceptance Criteria:**
- [ ] Upload PDF/TXT/MD files through web UI
- [ ] Select extraction method (pattern, LLM, hybrid)
- [ ] View/download generated knowledge graph
- [ ] Process a real client document set end-to-end
- [ ] Running on Iyeska HQ Ubuntu server (192.168.11.20)

**What's NOT in v0.2.0:**
- Client self-service (operator tool only)
- User accounts/auth (internal use)
- Job persistence beyond session
- Multi-tenant isolation

## Technical Alignment (Iyeska Stack)

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend | FastAPI | Wrap existing extractors as API |
| Frontend | React + TypeScript + Vite | Simple upload/preview UI |
| Database | PostgreSQL | Job queue, results cache (v0.3+) |
| LLM | Claude API (Anthropic) | Smart extraction, your cost center |
| Deployment | PM2 on Ubuntu 192.168.11.20 | Behind Traefik proxy |
| DNS | cosmo.iyeska.net | Cloudflare |

## Data Sovereignty Compliance

- **Local Processing**: All extraction runs on Iyeska HQ infrastructure
- **LLM Gate**: Explicit operator approval before sending any content to Claude API
- **No External Fetch**: Generated HTML embeds all data (no CDN calls in output)
- **Audit Trail**: Log what was processed, when, extraction method used

## Architecture Evolution

```
v0.1 (current)                v0.2 (target)                 v0.3+ (future)
┌─────────────┐              ┌─────────────┐               ┌─────────────┐
│   CLI       │              │  React UI   │               │  React UI   │
│  cosmograph │              │  (upload)   │               │  + Auth0    │
└──────┬──────┘              └──────┬──────┘               └──────┬──────┘
       │                            │                             │
       │                     ┌──────┴──────┐               ┌──────┴──────┐
       │                     │  FastAPI    │               │  FastAPI    │
       │                     │  /extract   │               │  + Workers  │
       │                     │  /status    │               │  + Queue    │
       │                     └──────┬──────┘               └──────┬──────┘
       │                            │                             │
┌──────┴──────┐              ┌──────┴──────┐               ┌──────┴──────┐
│ Extractors  │              │ Extractors  │               │ Extractors  │
│ Pattern     │              │ + PDF       │               │ + Workers   │
│ Only        │              │ + LLM       │               │ + PostgreSQL│
└─────────────┘              └─────────────┘               └─────────────┘
```

## Milestones

### v0.2.0 - Web Foundation (Current Focus)
Transform CLI into web-accessible service for internal use

### v0.3.0 - Production Ready
- PostgreSQL job persistence
- Background workers for large docs
- Basic usage tracking

### v0.4.0 - Client Self-Service
- Auth0 integration
- Multi-tenant isolation
- Client upload portal

### v1.0.0 - Full Product
- SaaS-ready
- Billing integration
- API access for integrations

## File Structure (Target v0.2.0)

```
cosmograph/
├── src/cosmograph/
│   ├── cli.py              # Keep CLI for power users
│   ├── api/                # NEW: FastAPI application
│   │   ├── main.py         # FastAPI app, routes
│   │   └── schemas.py      # Pydantic request/response
│   ├── extractors/         # Existing + PDF + LLM
│   │   ├── base.py
│   │   ├── legal.py
│   │   ├── text.py
│   │   ├── generic.py
│   │   ├── pdf.py          # NEW: pymupdf-based
│   │   └── llm.py          # NEW: Claude API
│   ├── config/             # NEW: Pattern configuration
│   │   └── patterns.yaml   # Custom extraction rules
│   ├── generators/
│   ├── models.py
│   └── templates/          # Jinja2 templates (move inline HTML)
├── frontend/               # NEW: React app
│   ├── src/
│   └── package.json
├── tests/                  # Add real tests
├── .planning/              # GSD planning files
├── pyproject.toml
└── CLAUDE.md
```

## Context & References

- **Main Iyeska CLAUDE.md**: `~/terminal_projects/claude_code/CLAUDE.md`
- **Infrastructure**: Ubuntu server 192.168.11.20, Traefik proxy
- **Similar Project**: `document-intelligence-pipeline` (PDF processing patterns)
- **Codebase Analysis**: `.planning/codebase/*.md`

---

*Created: 2026-01-21 | Status: Planning v0.2.0*
