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

### Phase 3: Pattern Configuration

**Goal**: Custom extraction rules without code changes

**Rationale**: Different document types need different patterns. Code changes for each client is unsustainable.

**Tasks**:
1. Define YAML schema for pattern configuration
2. Create `PatternConfig` loader with validation
3. Modify `GenericExtractor` to accept dynamic patterns
4. Create default patterns.yaml with current hardcoded patterns
5. Add CLI option `--patterns path/to/patterns.yaml`
6. Document pattern authoring in CLAUDE.md
7. Add tests for pattern loading and validation

**Success Criteria**:
- [ ] Custom patterns.yaml loads at runtime
- [ ] Invalid YAML produces helpful error message
- [ ] Default patterns produce same results as current code
- [ ] Pattern documentation complete

**Requirements Satisfied**: FR-3 (Custom Pattern Configuration)

---

### Phase 4: LLM Extractor

**Goal**: Claude-powered entity and relationship extraction

**Rationale**: Regex patterns miss semantic relationships. LLM can understand context.

**Tasks**:
1. Create `LlmExtractor` class inheriting `BaseExtractor`
2. Implement document chunking for context window management
3. Design extraction prompt (entities, relationships, structure)
4. Implement token estimation before processing
5. Add approval gate with estimated cost display
6. Implement response parsing into Graph nodes/edges
7. Add CLI option `-e llm` with confirmation prompt
8. Add rate limiting (requests per minute)
9. Create hybrid mode: patterns first, LLM for gaps
10. Add tests with mocked API responses

**Success Criteria**:
- [ ] LLM extraction produces valid graph
- [ ] Token estimate shown before processing
- [ ] Confirmation required before API call
- [ ] Hybrid mode works: patterns → LLM enrichment
- [ ] Tests pass without real API calls

**Requirements Satisfied**: FR-2 (LLM-Powered Extraction)

**Data Sovereignty Compliance**:
- [ ] Explicit operator confirmation before any API call
- [ ] Log extraction events (document hash, not content)

---

### Phase 5: FastAPI Backend

**Goal**: HTTP API for web interface

**Rationale**: Web UI needs endpoints to call. Keep CLI working.

**Tasks**:
1. Create `src/cosmograph/api/main.py` with FastAPI app
2. Implement file upload endpoint `POST /api/extract`
3. Implement extraction options (method, patterns file)
4. Return graph JSON and download URLs
5. Add progress endpoint (polling or SSE)
6. Implement error responses with helpful messages
7. Add CORS for local development
8. Add health check endpoint `GET /health`
9. Keep CLI working (refactor to share code, not duplicate)
10. Add API tests

**Endpoints**:
```
POST /api/extract         - Upload files, start extraction
GET  /api/extract/{id}    - Get extraction status/results
GET  /api/graph/{id}      - Get graph JSON
GET  /api/download/{id}   - Download HTML visualization
GET  /health              - Health check
```

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
