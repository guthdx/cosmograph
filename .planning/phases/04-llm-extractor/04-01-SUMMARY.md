---
phase: 04-llm-extractor
plan: 01
subsystem: extractors
tags: [anthropic, claude, llm, pydantic, tenacity, structured-outputs]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: BaseExtractor class and Graph model
provides:
  - LlmExtractor class with Claude API structured outputs
  - Pydantic schemas for entity/relationship extraction
  - Document chunking with paragraph boundary detection
  - Rate limiting with tenacity exponential backoff
affects: [04-02-approval-gate, 04-03-cli-integration]

# Tech tracking
tech-stack:
  added: [anthropic>=0.76.0, tenacity>=8.2.0, python-dotenv>=1.0.0]
  patterns: [optional-dependency-handling, structured-output-parsing, dynamic-decorator-application]

key-files:
  created:
    - src/cosmograph/extractors/llm.py
  modified:
    - pyproject.toml
    - src/cosmograph/extractors/__init__.py

key-decisions:
  - "Use claude-sonnet-4-5 as default model (good balance of quality/cost)"
  - "400K char chunks (~100K tokens) with 2K char overlap for context continuity"
  - "Dynamic retry decorator application to avoid mypy no-redef errors"
  - "Export HAS_ANTHROPIC flag for runtime feature detection"

patterns-established:
  - "Optional dependency pattern: import with try/except, set HAS_X flag, use aliased imports"
  - "Dynamic decorator application at module load time for conditional functionality"
  - "Structured output with Pydantic models for guaranteed schema compliance"

# Metrics
duration: 4min
completed: 2026-01-21
---

# Phase 04 Plan 01: LLM Extractor Core Summary

**LlmExtractor with Claude API structured outputs, Pydantic schemas, chunking, and rate limiting**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-21T22:08:28Z
- **Completed:** 2026-01-21T22:12:34Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created LlmExtractor class inheriting from BaseExtractor with full API integration
- Defined Pydantic schemas (ExtractedEntity, ExtractedRelationship, ExtractionResult) for structured outputs
- Implemented document chunking with paragraph boundary detection and 2K char overlap
- Added rate limiting with tenacity exponential backoff (1-60s, 6 attempts)
- Graceful degradation when anthropic/tenacity packages not installed

## Task Commits

Each task was committed atomically:

1. **Task 1: Update dependencies and create LlmExtractor with Pydantic schemas** - `07bdbc0` (feat)
2. **Task 2: Wire up API calls with structured outputs** - `f955157` (feat)

## Files Created/Modified

- `src/cosmograph/extractors/llm.py` - LlmExtractor with Claude API integration (342 lines)
- `pyproject.toml` - Updated [llm] dependencies to anthropic>=0.76.0, tenacity>=8.2.0, python-dotenv>=1.0.0
- `src/cosmograph/extractors/__init__.py` - Export LlmExtractor and HAS_ANTHROPIC

## Decisions Made

1. **Default model**: claude-sonnet-4-5 - good balance of extraction quality and cost ($3/$15 per MTok)
2. **Chunk size**: 400K chars (~100K tokens) with 2K char overlap - stays well within 200K context window while maximizing context per chunk
3. **Rate limit retry strategy**: Exponential backoff with jitter (1-60s) and 6 max attempts - follows Anthropic best practices
4. **Optional dependency pattern**: Dynamic import with aliased names to avoid mypy redefinition errors
5. **Decorator application**: Apply retry decorator at module load time to wrapped method - cleaner than inline decoration with conditionals

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

1. **Mypy no-redef errors**: Initial try/except import pattern caused "name already defined" errors when tenacity was installed. Resolved by using aliased imports (`_t_retry` etc.) and dynamic decorator application.

2. **Ruff import sorting**: Multiple ruff passes needed to satisfy import ordering rules in try/except blocks. Auto-fixed with `ruff check --fix`.

## User Setup Required

None - no external service configuration required. Users will need to set ANTHROPIC_API_KEY environment variable when using the extractor, but this is handled at runtime with a helpful error message.

## Next Phase Readiness

Ready for plan 04-02 (approval gate):
- LlmExtractor exists and can be instantiated
- Pydantic schemas ready for token counting cost estimation
- Need to add token counting API call and operator approval flow
- Need to add cost estimation display with Rich

---
*Phase: 04-llm-extractor*
*Completed: 2026-01-21*
