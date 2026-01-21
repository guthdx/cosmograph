# STATE.md

## Current Position

**Milestone**: v0.2.0 - Web Foundation
**Phase**: 05-fastapi-backend (5 of 7)
**Plan**: 01 of 4
**Status**: In progress
**Last activity**: 2026-01-21 - Completed 05-01-PLAN.md (Service Layer + API Dependencies)

Progress: [████░░░░░░] 4/7 phases complete

## Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 01 | complete | 5/5 |
| 02 | complete | 2/2 |
| 03 | complete | 3/3 |
| 04 | complete | 3/3 |
| 05 | in progress | 1/4 |
| 06 | pending | 0/? |
| 07 | pending | 0/? |

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

## Blockers

None

## Context

Project evolving from CLI tool (v0.1.0) to web service (v0.2.0) for Iyeska client document processing services.

Phase 5 (FastAPI Backend) started. First plan complete:
- ExtractionService class for framework-agnostic business logic
- FastAPI dependencies in [api] optional group
- [all] convenience group for full dev setup
- 18 service tests passing

Next: 05-02 - API Module Structure & Schemas

## Session Continuity

Last session: 2026-01-21T22:50:50Z
Stopped at: Completed 05-01-PLAN.md
Resume file: None
