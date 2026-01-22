---
phase: 07-deployment
plan: 01
subsystem: infra
tags: [pm2, vite, cors, deployment, uvicorn]

# Dependency graph
requires:
  - phase: 06-react-frontend
    provides: Frontend build that needs static serving configuration
  - phase: 05-fastapi-backend
    provides: API that needs CORS update for production
provides:
  - PM2 ecosystem configuration for process management
  - Deploy script for automated deployments
  - Vite production build configuration
  - CORS configuration for production domain
affects: [07-02, server-setup, production-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [pm2-ecosystem, deploy-script, static-asset-serving]

key-files:
  created:
    - ecosystem.config.js
    - deploy.sh
  modified:
    - frontend/vite.config.ts
    - src/cosmograph/api/main.py
    - tests/test_api.py

key-decisions:
  - "Port 8003 for cosmograph (next available per PORT_REGISTRY.md)"
  - "Relative base path './' in Vite for static asset serving"
  - "npm ci for clean, reproducible frontend builds"
  - "--update-env flag for PM2 restart to pick up env changes"

patterns-established:
  - "PM2 ecosystem.config.js pattern from wowasi_ya"
  - "Deploy script with git pull, pip install, npm build, pm2 restart"

# Metrics
duration: 15min
completed: 2026-01-22
---

# Phase 7 Plan 1: Deployment Configuration Summary

**PM2 ecosystem and deploy script for Iyeska HQ deployment with Vite relative paths and production CORS**

## Performance

- **Duration:** 15 min
- **Started:** 2026-01-22T17:45:00Z
- **Completed:** 2026-01-22T18:00:05Z
- **Tasks:** 3
- **Files modified:** 5 (including test fix)

## Accomplishments
- Vite configured with `base: './'` for relative asset paths in production
- CORS updated to allow `https://cosmograph.iyeska.net`
- PM2 ecosystem.config.js created with uvicorn on port 8003
- deploy.sh automation script for full deployment workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Vite and CORS configuration for production** - `10c4f83` (chore)
2. **Task 2: Create PM2 ecosystem.config.js** - `5dc387d` (chore)
3. **Task 3: Create deploy.sh automation script** - `56a1653` (chore)
4. **Test fix: Update root endpoint test** - `17521fe` (fix) [deviation]

## Files Created/Modified
- `frontend/vite.config.ts` - Added base, outDir, assetsDir for production builds
- `src/cosmograph/api/main.py` - Added production CORS origin
- `ecosystem.config.js` - PM2 process configuration
- `deploy.sh` - Deployment automation script
- `tests/test_api.py` - Updated test for static file serving behavior

## Decisions Made
- **Port 8003**: Next available port per PORT_REGISTRY.md allocation
- **Relative base path**: `base: './'` required for static file serving
- **npm ci over npm install**: Ensures reproducible builds from lock file
- **--update-env flag**: Required to reload environment variables on restart

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated root endpoint test for static file serving**
- **Found during:** Final verification (pytest run)
- **Issue:** Test expected 307 redirect to /docs, but static.py (added previously) serves frontend when dist exists
- **Fix:** Updated test to expect 200 with HTML content
- **Files modified:** tests/test_api.py
- **Verification:** All 169 tests pass
- **Committed in:** 17521fe

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test fix necessary for correct verification. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Deployment configuration files ready
- Next: Plan 02 - Static file serving integration (if not already complete)
- Server-side setup: Clone repo, create venv, configure Cloudflare Tunnel

---
*Phase: 07-deployment*
*Completed: 2026-01-22*
