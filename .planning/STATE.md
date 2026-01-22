# STATE.md

## Current Position

**Milestone**: v0.2.0 - Web Foundation
**Phase**: 07-deployment (7 of 7)
**Plan**: 03 of 3
**Status**: COMPLETE
**Last activity**: 2026-01-22 - Completed 07-03-PLAN.md (v0.2.0 milestone achieved!)

Progress: [██████████] 7/7 phases complete

## Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 01 | complete | 5/5 |
| 02 | complete | 2/2 |
| 03 | complete | 3/3 |
| 04 | complete | 3/3 |
| 05 | complete | 5/5 |
| 06 | complete | 4/4 |
| 07 | complete | 3/3 |

## Decisions Made

- **2026-01-21**: Foundation first approach - solid architecture before features
- **2026-01-21**: LLM costs absorbed as service delivery cost
- **2026-01-21**: Hybrid deployment - local dev, Iyeska HQ infrastructure for production
- **2026-01-21**: Use repr=False on internal tracking fields to keep repr clean (01-02)
- **2026-01-21**: Class-level compiled patterns with _PATTERN naming convention for fixed patterns (01-03)
- **2026-01-21**: Instance-level pattern compilation for configurable extractors (01-03)
- **2026-01-21**: Move pymupdf to [pdf] optional group for future PDF support (01-05)
- **2026-01-21**: Temp file delegation pattern for extractor reuse - write content to temp, delegate to existing extractor (02-01)
- **2026-01-21**: Scanned PDF detection via text length + image presence heuristics (02-01)
- **2026-01-21**: Users must specify -e pdf explicitly; auto extractor remains LegalDocumentExtractor (02-02)
- **2026-01-21**: Use PyMuPDF for test fixtures rather than adding reportlab dependency (02-02)
- **2026-01-21**: Exactly one capture group required in patterns - validates at load time (03-01)
- **2026-01-21**: types-pyyaml added to dev dependencies for mypy compatibility (03-01)
- **2026-01-21**: Pattern metadata stored in _pattern_metadata dict for O(1) lookups (03-02)
- **2026-01-21**: CLI --patterns only affects generic extractor; other extractors ignore it (03-02)
- **2026-01-21**: Dict-based pattern conversion for integration tests until config= parameter available (03-03)
- **2026-01-21**: Use claude-sonnet-4-5 as default model for LLM extraction (04-01)
- **2026-01-21**: 400K char chunks with 2K overlap for document processing (04-01)
- **2026-01-21**: Dynamic retry decorator application to avoid mypy no-redef errors (04-01)
- **2026-01-21**: Export HAS_ANTHROPIC flag for runtime LLM feature detection (04-01)
- **2026-01-21**: Official token counting API over character-based estimation (04-02)
- **2026-01-21**: Interactive mode defaults to True for data sovereignty compliance (04-02)
- **2026-01-21**: OperatorDeclinedError as explicit exception for declined extractions (04-02)
- **2026-01-21**: 16-char document hash for audit trail (never log content) (04-02)
- **2026-01-21**: --no-confirm flag passes interactive=False to LlmExtractor (04-03)
- **2026-01-21**: OperatorDeclinedError exits with code 0 (not an error) (04-03)
- **2026-01-21**: 34 mocked tests with 88% coverage for LLM extractor (04-03)
- **2026-01-21**: Service layer is framework-agnostic (no typer/fastapi imports) (05-01)
- **2026-01-21**: progress_callback(current, total) signature for progress reporting (05-01)
- **2026-01-21**: generate_outputs returns dict[str, Path] for flexible output access (05-01)
- **2026-01-21**: In-memory JobStore with no persistence per REQUIREMENTS.md (05-02)
- **2026-01-21**: 8-char UUID for job IDs (05-02)
- **2026-01-21**: CORS configured for localhost:3000, localhost:5173, cosmograph.localhost (05-02)
- **2026-01-21**: Root path redirects to /docs for developer convenience (05-02)
- **2026-01-21**: LLM extraction requires llm_confirmed=true parameter in API (05-03)
- **2026-01-21**: Stream uploads to disk with shutil.copyfileobj (05-03)
- **2026-01-21**: Store output_dir in Job for download endpoint access (05-03)
- **2026-01-21**: SSE polling interval of 500ms for progress streaming (05-04)
- **2026-01-21**: FileResponse for efficient file downloads (05-04)
- **2026-01-21**: ZIP archive for multi-file CSV download (05-04)
- **2026-01-21**: Job store reset fixture with autouse=True for test isolation (05-05)
- **2026-01-21**: CLI uses ExtractionService.process_files() with progress_callback (05-05)
- **2026-01-21**: Service layer shared by CLI and API for code reuse (05-05)
- **2026-01-22**: ES2022 class syntax (no parameter properties) for Vite erasableSyntaxOnly mode (06-01)
- **2026-01-22**: Type union over enum for JobStatus/ExtractorType - simpler, no runtime overhead (06-01)
- **2026-01-22**: Native HTML5 DnD API over react-dropzone - no external dependency (06-02)
- **2026-01-22**: Type-only imports for verbatimModuleSyntax compliance (06-02)
- **2026-01-22**: Controlled components with callback props for state lifting (06-02)
- **2026-01-22**: Native EventSource for SSE - browser handles reconnection automatically (06-03)
- **2026-01-22**: Derived state pattern - extraction state computed from multiple sources (06-03)
- **2026-01-22**: Sandboxed iframe (allow-scripts) for secure D3.js visualization embedding (06-03)
- **2026-01-22**: ErrorDisplay as reusable component with callback props for retry/dismiss (06-04)
- **2026-01-22**: Traefik config stored in project; symlink to active Traefik instance (06-04)
- **2026-01-22**: host.docker.internal for Docker Traefik to reach host services (06-04)
- **2026-01-22**: Static files only activate if frontend/dist exists (07-02)
- **2026-01-22**: API routes registered before static files for precedence (07-02)
- **2026-01-22**: Catch-all serves index.html for client-side routing (07-02)
- **2026-01-22**: Port 8003 for cosmograph (next available per PORT_REGISTRY.md) (07-01)
- **2026-01-22**: Relative base path './' in Vite for static asset serving (07-01)
- **2026-01-22**: npm ci for clean, reproducible frontend builds (07-01)
- **2026-01-22**: --update-env flag for PM2 restart to pick up env changes (07-01)
- **2026-01-22**: Production domain cosmo.iyeska.net (shortened from cosmograph.iyeska.net) (07-03)
- **2026-01-22**: Repository location ~/projects/cosmograph on Ubuntu server (07-03)

## Blockers

None

## Context

**v0.2.0 MILESTONE COMPLETE!**

Cosmograph has evolved from CLI tool (v0.1.0) to full web service (v0.2.0) for Iyeska client document processing.

**Production URL:** https://cosmo.iyeska.net

**All phases complete:**
- Phase 01: Foundation Cleanup - 66 tests, 90% coverage
- Phase 02: PDF Extractor - PdfExtractor with encrypted/scanned detection
- Phase 03: Pattern Configuration - YAML-based custom extraction rules
- Phase 04: LLM Extractor - Claude API with approval gate
- Phase 05: FastAPI Backend - 6 API endpoints, SSE progress streaming
- Phase 06: React Frontend - Full extraction workflow UI
- Phase 07: Deployment - PM2 on Ubuntu, Cloudflare Tunnel HTTPS

**Capabilities delivered:**
- Web UI for document upload and extraction
- PDF, pattern-based, and LLM extraction methods
- Real-time progress streaming (SSE)
- Interactive D3.js graph visualization
- HTML and CSV downloads
- CLI remains functional for power users
- Data sovereignty compliance (LLM approval gate)

Total tests: 169 passing

## Session Continuity

Last session: 2026-01-22T18:21:00Z
Stopped at: v0.2.0 MILESTONE COMPLETE
Resume file: None
