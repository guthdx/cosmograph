# STATE.md

## Current Position

**Milestone**: v0.2.0 - Web Foundation
**Phase**: 03-pattern-configuration (3 of 7)
**Plan**: 01 of ?
**Status**: In progress
**Last activity**: 2026-01-21 - Completed 03-01-PLAN.md

Progress: [██░░░░░░░░] 2/7 phases complete

## Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 01 | ✓ complete | 5/5 |
| 02 | ✓ complete | 2/2 |
| 03 | in progress | 1/? |
| 04 | pending | 0/? |
| 05 | pending | 0/? |
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

## Blockers

None

## Context

Project evolving from CLI tool (v0.1.0) to web service (v0.2.0) for Iyeska client document processing services.

## Session Continuity

Last session: 2026-01-21T21:43:20Z
Stopped at: Completed 03-01-PLAN.md
Resume file: None
