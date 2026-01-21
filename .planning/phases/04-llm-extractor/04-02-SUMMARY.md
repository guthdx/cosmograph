---
phase: 04-llm-extractor
plan: 02
subsystem: extractors
tags: [anthropic, token-counting, cost-estimation, data-sovereignty, rich, approval-gate]

# Dependency graph
requires:
  - phase: 04-01
    provides: LlmExtractor core with Claude API integration
provides:
  - Token estimation using official count_tokens API
  - Cost calculation with model-specific pricing
  - Interactive approval gate for data sovereignty
  - OperatorDeclinedError exception
affects: [04-03, cli-integration, api-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Token counting before API calls for cost transparency"
    - "Approval gate pattern for external API calls"
    - "Document hash for audit logging (never content)"

key-files:
  created: []
  modified:
    - src/cosmograph/extractors/llm.py

key-decisions:
  - "Official token counting API (free call) over character-based estimation"
  - "Interactive mode default True for data sovereignty compliance"
  - "OperatorDeclinedError as explicit exception vs silent return"
  - "Document hash (16 chars) for audit trail, never content"

patterns-established:
  - "Approval gate: estimate_tokens() -> _approval_gate() -> proceed or raise"
  - "Rich table display for cost transparency"

# Metrics
duration: 2min
completed: 2026-01-21
---

# Phase 04 Plan 02: Approval Gate Summary

**Token estimation with official API, Rich cost display, and approval gate for data sovereignty compliance**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-21T22:14:02Z
- **Completed:** 2026-01-21T22:16:12Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Token counting using official Anthropic API (free, accurate counts)
- Cost estimation with model-specific pricing (Sonnet, Haiku, Opus)
- Rich table display showing document hash, tokens, cost, model
- Interactive approval gate requiring explicit 'y' to proceed
- Non-interactive mode for batch/automated processing
- Audit logging with document hash (never content)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add token counting and cost estimation** - `9d42dcc` (feat)
2. **Task 2: Add approval gate with Rich display** - `6767e8b` (feat)

## Files Created/Modified

- `src/cosmograph/extractors/llm.py` - Added _PRICING constants, estimate_tokens(), _calculate_cost(), _approval_gate(), OperatorDeclinedError, interactive parameter

## Decisions Made

1. **Official token counting API over character estimation** - The Anthropic SDK provides `client.messages.count_tokens()` which is free and accurate. Character-based estimation (1 token ~ 4 chars) is inaccurate for non-English text and special characters.

2. **Interactive mode defaults to True** - Data sovereignty is a core requirement. Defaulting to interactive ensures operators always see cost estimates unless explicitly running in batch mode.

3. **OperatorDeclinedError as explicit exception** - Rather than silently returning an empty graph, we raise a clear exception so CLI/API layers can handle the decline appropriately (e.g., display message, return specific status code).

4. **16-character document hash for audit** - SHA256 truncated to 16 chars provides sufficient uniqueness for audit logs while remaining human-readable. Full content is never logged.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. (ANTHROPIC_API_KEY was already required by 04-01.)

## Next Phase Readiness

- Approval gate ready for CLI integration in 04-03
- Token estimation can be exposed as standalone command
- Non-interactive mode ready for batch processing

---
*Phase: 04-llm-extractor*
*Completed: 2026-01-21*
