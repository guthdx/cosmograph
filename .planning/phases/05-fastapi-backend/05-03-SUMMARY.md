---
phase: 05-fastapi-backend
plan: 03
subsystem: api
tags: [fastapi, file-upload, background-tasks, multipart-form]

# Dependency graph
requires:
  - phase: 05-01
    provides: ExtractionService for framework-agnostic extraction
  - phase: 05-02
    provides: FastAPI app skeleton, JobStore, schemas
provides:
  - POST /api/extract endpoint for file uploads
  - GET /api/extract/{job_id} for status polling
  - Background extraction with progress tracking
  - LLM confirmation gate for data sovereignty
affects: [05-04, 05-05, 06-react-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Background task pattern for sync extractors
    - Stream-to-disk uploads (no memory exhaustion)
    - Form() parameters for multipart compatibility

key-files:
  created:
    - src/cosmograph/api/routes/extract.py
  modified:
    - src/cosmograph/api/main.py

key-decisions:
  - "LLM extraction requires llm_confirmed=true parameter (API equivalent of CLI --no-confirm)"
  - "interactive=False for LLM when confirmed via API (already approved)"
  - "Stream uploads to disk with shutil.copyfileobj (never read entire file into memory)"
  - "Store output_dir in Job for later download endpoint access"

patterns-established:
  - "_job_to_response helper for Job -> JobResponse conversion"
  - "Background task runs sync code, FastAPI handles threading"
  - "Form() not Body() for multipart form data compatibility"

# Metrics
duration: 3min
completed: 2026-01-21
---

# Phase 05 Plan 03: File Upload & Extraction Endpoints Summary

**POST /api/extract and GET /api/extract/{job_id} endpoints with background processing and LLM confirmation gate**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-21T22:54:09Z
- **Completed:** 2026-01-21T22:56:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- File upload endpoint accepting multiple files via multipart form data
- Job status polling endpoint returning progress and completion
- Background extraction using FastAPI BackgroundTasks
- LLM confirmation gate enforcing data sovereignty approval
- Stream-to-disk uploads preventing memory exhaustion on large files

## Task Commits

Each task was committed atomically:

1. **Task 1: Create extraction routes module** - `4bd51e5` (feat)
2. **Task 2: Register extract router and test endpoints** - `e228c77` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `src/cosmograph/api/routes/extract.py` - POST /extract and GET /extract/{id} endpoints with background processing
- `src/cosmograph/api/main.py` - Added extract router import and include

## Decisions Made
- **LLM confirmation as parameter:** API uses `llm_confirmed=true` form field instead of interactive prompt. This is the API equivalent of CLI's `--no-confirm` flag.
- **interactive=False for confirmed LLM:** When llm_confirmed=true, pass interactive=False to LlmExtractor since approval already happened via API.
- **Stream uploads to disk:** Use `shutil.copyfileobj(upload.file, f)` to stream files to temp directory, avoiding memory exhaustion on large PDFs.
- **Output dir in Job:** Store `output_dir` in Job dataclass for later download endpoint to find generated files.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- **graph.to_json() returns dict:** Initially assumed it returned JSON string and used json.loads(), but it returns a dict already. Fixed by removing json.loads() call.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Extraction endpoints complete and tested
- Ready for 05-04: Graph & Download Endpoints (serve results)
- Background processing verified working with progress updates
- All 146 existing tests pass

---
*Phase: 05-fastapi-backend*
*Completed: 2026-01-21*
