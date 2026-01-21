---
phase: 05-fastapi-backend
plan: 01
subsystem: api
tags: [fastapi, service-layer, extraction, uvicorn, sse-starlette]

# Dependency graph
requires:
  - phase: 04-llm-extractor
    provides: "LlmExtractor with interactive approval gate"
  - phase: 03-pattern-config
    provides: "PatternConfig for generic extractor"
provides:
  - ExtractionService class for framework-agnostic business logic
  - FastAPI and supporting dependencies in [api] optional group
  - [all] convenience group for full development setup
  - Service layer pattern for CLI/API code sharing
affects: [05-02, 05-03, 05-04, 06-react-frontend]

# Tech tracking
tech-stack:
  added: [fastapi>=0.115.0, uvicorn>=0.30.0, python-multipart, sse-starlette, httpx]
  patterns: [service-layer, progress-callback]

key-files:
  created:
    - src/cosmograph/services/__init__.py
    - src/cosmograph/services/extraction.py
    - tests/test_services.py
  modified:
    - pyproject.toml

key-decisions:
  - "Service layer is framework-agnostic (no typer/fastapi imports)"
  - "progress_callback(current, total) signature for progress reporting"
  - "generate_outputs returns dict[str, Path] for flexible output access"

patterns-established:
  - "Service layer: business logic in services/, CLI and API call services"
  - "Progress callback: Callable[[int, int], None] for tracking file processing"

# Metrics
duration: 3min
completed: 2026-01-21
---

# Phase 5 Plan 1: Service Layer + API Dependencies Summary

**ExtractionService class providing framework-agnostic extraction orchestration with FastAPI dependencies in [api] optional group**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-21T22:47:39Z
- **Completed:** 2026-01-21T22:50:50Z
- **Tasks:** 3/3
- **Files modified:** 4

## Accomplishments

- Created ExtractionService with get_extractor(), process_files(), generate_outputs() methods
- Added [api] dependency group with FastAPI 0.115+, uvicorn, python-multipart, sse-starlette, httpx
- Added [all] convenience group combining dev, pdf, llm, api
- Comprehensive test suite with 18 passing tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add FastAPI dependencies** - `935c638` (chore)
2. **Task 2: Create ExtractionService** - `4551ab7` (feat)
3. **Task 3: Add service unit tests** - `39bd05d` (test)

## Files Created/Modified

- `pyproject.toml` - Added [api] and [all] optional dependency groups
- `src/cosmograph/services/__init__.py` - Service module exports
- `src/cosmograph/services/extraction.py` - ExtractionService class with extraction orchestration
- `tests/test_services.py` - 18 unit tests for service functionality

## Decisions Made

1. **Service layer is framework-agnostic** - ExtractionService imports only from core modules (extractors, generators, models, config), never from typer or fastapi. This ensures reusability across CLI and API.

2. **progress_callback signature** - Using `Callable[[int, int], None]` with (current, total) parameters allows both CLI progress bars and API progress streaming.

3. **generate_outputs returns dict** - Returns `dict[str, Path]` mapping output type to path, allowing callers to selectively access outputs without hardcoding file names.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Service layer ready for API integration
- ExtractionService provides the foundation for API routes
- Next plan (05-02) can create API module structure, schemas, and job store

---
*Phase: 05-fastapi-backend*
*Completed: 2026-01-21*
