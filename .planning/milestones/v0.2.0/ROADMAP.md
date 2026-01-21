# ROADMAP.md - v0.2.0 Web Foundation

## Milestone Goal

Transform Cosmograph from CLI tool to web-accessible service for Iyeska team to process client documents.

## Phase Overview

| Phase | Name | Dependencies | Description |
|-------|------|--------------|-------------|
| 1 | Foundation Cleanup | None | Tests, fix tech debt, prepare for extension |
| 2 | PDF Extractor | Phase 1 | Add PDF document support using pymupdf |
| 3 | Pattern Configuration | Phase 1 | YAML-based custom extraction rules |
| 4 | LLM Extractor | Phase 1 | Claude API integration with approval gate |
| 5 | FastAPI Backend | Phases 1-4 | Web API wrapping extractors |
| 6 | React Frontend | Phase 5 | Upload UI, results display |
| 7 | Deployment | Phase 6 | PM2, Traefik, DNS setup |

## Detailed Phases

---

### Phase 1: Foundation Cleanup ✓

**Status**: Complete (2026-01-21)
**Goal**: Solid base for extending the codebase

**Plans:** 5/5 complete

Plans:
- [x] 01-01-PLAN.md — Add unit tests for core models (Graph, Node, Edge)
- [x] 01-02-PLAN.md — Fix models.py (re import, edge deduplication)
- [x] 01-03-PLAN.md — Pre-compile regex patterns in extractors
- [x] 01-04-PLAN.md — Extract HTML to Jinja2 template
- [x] 01-05-PLAN.md — Clean up dependencies, add extractor/CLI tests

**Results:**
- 66 tests, 90% coverage (100% on models.py)
- HTML template at `templates/graph.html.j2`
- CLI verified working

**Requirements Satisfied**: NFR-4 (Maintainability)

---

### Phase 2: PDF Extractor ✓

**Status**: Complete (2026-01-21)
**Goal**: Process PDF documents without pre-conversion

**Plans:** 2/2 complete

Plans:
- [x] 02-01-PLAN.md — Create PdfExtractor class with temp file delegation
- [x] 02-02-PLAN.md — CLI integration and tests

**Results:**
- PdfExtractor class (114 lines) with encrypted/scanned detection
- CLI `-e pdf` option working
- 7 PDF tests, 73 total tests passing
- FR-1 requirements all satisfied

**Requirements Satisfied**: FR-1 (PDF Document Support)

---

### Phase 3: Pattern Configuration ✓

**Status**: Complete (2026-01-21)
**Goal**: Custom extraction rules without code changes

**Plans:** 3/3 complete

Plans:
- [x] 03-01-PLAN.md — Create PatternConfig Pydantic models and default patterns.yaml
- [x] 03-02-PLAN.md — Update GenericExtractor and CLI --patterns option
- [x] 03-03-PLAN.md — Add tests for pattern configuration

**Results:**
- PatternConfig Pydantic models with regex validation (exactly 1 capture group)
- CLI `--patterns` option for custom YAML files
- 21 pattern tests, 94 total tests passing
- 100% coverage on config module

**Requirements Satisfied**: FR-3 (Custom Pattern Configuration)

---

### Phase 4: LLM Extractor ✓

**Status**: Complete (2026-01-21)
**Goal**: Claude-powered entity and relationship extraction

**Plans:** 3/3 complete

Plans:
- [x] 04-01-PLAN.md — Create LlmExtractor with structured outputs and chunking
- [x] 04-02-PLAN.md — Add token estimation and approval gate
- [x] 04-03-PLAN.md — CLI integration and mocked tests

**Results:**
- LlmExtractor class (492 lines) with Pydantic structured outputs
- Token estimation via official count_tokens API (free, accurate)
- Operator approval gate with Rich table display
- Document hash logging for audit (never content)
- CLI `-e llm` with `--no-confirm` flag
- 34 mocked tests, 128 total tests passing

**Success Criteria**:
- [x] LLM extraction produces valid graph
- [x] Token estimate shown before processing
- [x] Confirmation required before API call
- [x] Tests pass without real API calls

**Requirements Satisfied**: FR-2 (LLM-Powered Extraction)

**Data Sovereignty Compliance**:
- [x] Explicit operator confirmation before any API call
- [x] Log extraction events (document hash, not content)

---

### Phase 5: FastAPI Backend

**Status**: Planned (2026-01-21)
**Goal**: HTTP API for web interface

**Plans:** 5 plans

Plans:
- [ ] 05-01-PLAN.md — Add FastAPI dependencies and create ExtractionService
- [ ] 05-02-PLAN.md — Create FastAPI app skeleton with health endpoint
- [ ] 05-03-PLAN.md — Implement extraction endpoints (upload, job status)
- [ ] 05-04-PLAN.md — Implement graph retrieval, download, and SSE progress
- [ ] 05-05-PLAN.md — Add API tests and refactor CLI to use service layer

**Endpoints**:
```
POST /api/extract         - Upload files, start extraction
GET  /api/extract/{id}    - Get extraction status/results
GET  /api/extract/{id}/progress - SSE progress stream
GET  /api/graph/{id}      - Get graph JSON
GET  /api/download/{id}   - Download HTML visualization
GET  /health              - Health check
```

**Wave Structure**:
- Wave 1: Plans 01, 02 (parallel - deps + service, app skeleton)
- Wave 2: Plan 03 (extraction routes)
- Wave 3: Plan 04 (graph routes + SSE)
- Wave 4: Plan 05 (tests + CLI refactor)

**Success Criteria**:
- [ ] Can upload file via curl and get graph JSON
- [ ] Progress updates available during processing
- [ ] Error responses are helpful
- [ ] CLI still works exactly as before
- [ ] Health check returns {"status": "healthy"}

**Requirements Satisfied**: FR-4 (Web Interface - backend)

---

### Phase 6: React Frontend

**Goal**: Browser UI for document processing

**Rationale**: Operators need visual interface, not just CLI.

**Tasks**:
1. Initialize Vite + React + TypeScript in `frontend/`
2. Create upload component (drag & drop + file picker)
3. Create extraction options form (method, patterns)
4. Implement progress display during extraction
5. Create graph preview component (embed D3.js or iframe)
6. Add download buttons (HTML, CSV)
7. Add error display for failures
8. Style with minimal, functional CSS (not over-designed)
9. Add Traefik config for `cosmograph.localhost`

**Success Criteria**:
- [ ] Can upload file through browser
- [ ] Progress shown during processing
- [ ] Graph displays in browser after completion
- [ ] Download links work for HTML and CSV
- [ ] Accessible at `http://cosmograph.localhost`

**Requirements Satisfied**: FR-4 (Web Interface - frontend)

---

### Phase 7: Deployment

**Goal**: Running on Iyeska HQ infrastructure

**Rationale**: Tool needs to be accessible from any Iyeska machine.

**Tasks**:
1. Create PM2 ecosystem.config.js for backend
2. Build frontend for production
3. Configure Traefik route on Ubuntu server
4. Set up DNS for cosmograph.iyeska.net (Cloudflare)
5. Test deployment end-to-end
6. Document deployment in CLAUDE.md
7. Process real client document set as validation

**Success Criteria**:
- [ ] Accessible at https://cosmograph.iyeska.net
- [ ] PM2 shows healthy process
- [ ] Real client document processed successfully
- [ ] Deployment documented

**Requirements Satisfied**: All functional requirements validated

---

## Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├──> Phase 2 (PDF)
    │
    ├──> Phase 3 (Patterns)
    │
    └──> Phase 4 (LLM)
              │
              v
         Phase 5 (API)
              │
              v
         Phase 6 (Frontend)
              │
              v
         Phase 7 (Deployment)
```

Phases 2, 3, 4 can run in parallel after Phase 1.

---

## Risk Mitigation

**Phase 4 (LLM) Risk**: API costs, rate limits
- Mitigation: Start with small test docs, mock API in tests
- Fallback: Pattern-only mode is always functional

**Phase 6 (Frontend) Risk**: Scope creep on UI
- Mitigation: Minimal viable UI, no fancy features
- Fallback: CLI with curl scripts if UI stalls

**Phase 7 (Deployment) Risk**: Infrastructure issues
- Mitigation: Local dev validates everything first
- Fallback: Run on Mac Mini if Ubuntu has issues

---

## Checkpoint: v0.2.0 Complete

After Phase 7, verify:

1. [ ] Upload PDF → Get knowledge graph (web UI)
2. [ ] LLM extraction with approval gate works
3. [ ] Custom patterns loaded from YAML
4. [ ] CLI still works as before
5. [ ] Deployed to cosmograph.iyeska.net
6. [ ] One real client document processed

---

*Roadmap created: 2026-01-21*
*Phase 1 planned: 2026-01-21*
*Phase 3 planned: 2026-01-21*
*Phase 4 planned: 2026-01-21*
*Phase 5 planned: 2026-01-21*
