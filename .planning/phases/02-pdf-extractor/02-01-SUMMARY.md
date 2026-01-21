---
phase: 02-pdf-extractor
plan: 01
subsystem: extractors
tags: [pymupdf, pdf, extractor, text-extraction]

# Dependency graph
requires:
  - phase: 01-foundation-cleanup
    provides: BaseExtractor ABC, LegalDocumentExtractor
provides:
  - PdfExtractor class for PDF document processing
  - Temp file delegation pattern for reusing existing extractors
  - Scanned PDF detection heuristic
affects: [cli-integration, web-api, testing]

# Tech tracking
tech-stack:
  added: []  # pymupdf already in pyproject.toml[pdf]
  patterns:
    - Temp file delegation for extractor reuse
    - TYPE_CHECKING conditional imports for type hints

key-files:
  created:
    - src/cosmograph/extractors/pdf.py
  modified:
    - src/cosmograph/extractors/__init__.py

key-decisions:
  - "Use pymupdf import (not legacy fitz) per research guidance"
  - "Temp file delegation pattern to reuse LegalDocumentExtractor instead of duplicating extraction logic"
  - "Scanned PDF detection via text length + image presence heuristics"

patterns-established:
  - "Extractor delegation: Write extracted content to temp file, delegate to existing extractor"
  - "Use from __future__ import annotations for forward references"

# Metrics
duration: 2min
completed: 2026-01-21
---

# Phase 2 Plan 1: PdfExtractor Class Summary

**PdfExtractor class with PyMuPDF text extraction and LegalDocumentExtractor delegation via temp file pattern**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-21T19:26:21Z
- **Completed:** 2026-01-21T19:28:07Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created PdfExtractor class inheriting from BaseExtractor
- Implemented supports() for .pdf file detection
- Implemented extract() using temp file delegation to LegalDocumentExtractor
- Added _is_likely_scanned() heuristic for detecting image-only PDFs
- Handled encrypted PDFs with clear error messages
- Exported PdfExtractor from extractors module

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PdfExtractor class** - `31c7b0f` (feat)
2. **Task 2: Export PdfExtractor from module** - `812d3a1` (feat)

## Files Created/Modified

- `src/cosmograph/extractors/pdf.py` - PdfExtractor class with extract(), supports(), and _is_likely_scanned() methods
- `src/cosmograph/extractors/__init__.py` - Added PdfExtractor to module exports

## Decisions Made

- **Temp file delegation pattern**: Rather than duplicating entity extraction logic from LegalDocumentExtractor, we write extracted PDF text to a temp file and delegate. This ensures consistent entity extraction behavior across formats and avoids code duplication.
- **Scanned PDF heuristic**: Combined text length check (>100 chars = has text) with per-page image/text ratio check (images present + <50 chars = likely scanned). Simple but effective for common cases.
- **Future annotations import**: Used `from __future__ import annotations` to allow forward references without quotes, satisfying ruff UP037 rule.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Ruff UP037 lint error**: Initial code used quoted type annotations (`"Document | None"`). Fixed by adding `from __future__ import annotations` and removing quotes. This is a minor code style issue, not a deviation.

## User Setup Required

None - no external service configuration required. Note: Users need `pip install "cosmograph[pdf]"` to install the optional pymupdf dependency.

## Next Phase Readiness

- PdfExtractor class complete and exported
- Ready for CLI integration (adding `-e pdf` option)
- Ready for testing in 02-02-PLAN.md
- No blockers for next plan

---
*Phase: 02-pdf-extractor*
*Completed: 2026-01-21*
