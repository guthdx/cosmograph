# Phase 5: FastAPI Backend - Research

**Researched:** 2026-01-21
**Domain:** FastAPI web API, file uploads, background processing
**Confidence:** HIGH

## Summary

Phase 5 wraps existing Cosmograph extractors in a FastAPI web API. The research confirms FastAPI 0.115+ (Iyeska standard) provides all needed capabilities: async file uploads with `UploadFile`, built-in `BackgroundTasks` for extraction processing, Server-Sent Events (SSE) for progress updates, and comprehensive error handling via `HTTPException` and custom handlers.

The key architectural insight is **service layer extraction**: business logic must be factored out of `cli.py` into reusable services that both CLI and API can call. This follows the standard layered architecture pattern where the service layer is framework-agnostic.

**Primary recommendation:** Use FastAPI's built-in `BackgroundTasks` with in-memory job state (dict) for this single-operator tool. SSE for progress is simpler than WebSocket for unidirectional server-to-client updates. Extract core extraction logic into a service module that both CLI and API import.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.115+ | Web framework | Iyeska standard, async-first, automatic OpenAPI |
| uvicorn | 0.30+ | ASGI server | Standard FastAPI server, production-ready |
| python-multipart | 0.0.9+ | File uploads | Required for `UploadFile` form data parsing |
| pydantic | 2.x | Request/response schemas | Already in use, FastAPI integration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sse-starlette | 2.0+ | Server-Sent Events | Progress streaming to frontend |
| httpx | 0.27+ | Async HTTP client | Testing with TestClient |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SSE | WebSocket | WebSocket is bidirectional but more complex; SSE simpler for progress |
| BackgroundTasks | Celery | Celery needed for multi-worker/multi-server; overkill for single-operator |
| In-memory state | Redis | Redis survives restarts but adds complexity; out of scope per REQUIREMENTS |

**Installation:**
```bash
pip install "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0" "python-multipart>=0.0.9" "sse-starlette>=2.0.0"
```

## Architecture Patterns

### Recommended Project Structure
```
src/cosmograph/
├── api/                    # NEW: API layer
│   ├── __init__.py
│   ├── main.py            # FastAPI app, lifespan, middleware
│   ├── routes/            # Route modules by concern
│   │   ├── __init__.py
│   │   ├── extract.py     # POST /api/extract, GET /api/extract/{id}
│   │   ├── graph.py       # GET /api/graph/{id}, GET /api/download/{id}
│   │   └── health.py      # GET /health
│   ├── schemas.py         # Pydantic request/response models
│   ├── deps.py            # FastAPI dependencies
│   └── exceptions.py      # Custom exceptions and handlers
├── services/              # NEW: Business logic layer (framework-agnostic)
│   ├── __init__.py
│   └── extraction.py      # Core extraction orchestration
├── cli.py                 # Thin wrapper calling services
├── extractors/            # Unchanged
├── generators/            # Unchanged
└── models.py              # Unchanged
```

### Pattern 1: Service Layer for Code Sharing
**What:** Extract business logic from CLI into framework-agnostic service classes
**When to use:** When both CLI and API need the same functionality
**Example:**
```python
# Source: https://medium.com/@abhinav.dobhal/building-production-ready-fastapi-applications-with-service-layer-architecture-in-2025-f3af8a6ac563
# src/cosmograph/services/extraction.py

from pathlib import Path
from ..extractors import get_extractor
from ..generators import HTMLGenerator, CSVGenerator
from ..models import Graph

class ExtractionService:
    """Framework-agnostic extraction orchestration."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_files(
        self,
        files: list[Path],
        extractor_type: str,
        title: str,
        pattern_config: dict | None = None,
        progress_callback: callable | None = None,
    ) -> Graph:
        """Process files and return graph. Calls progress_callback(current, total) if provided."""
        graph = Graph(title=title)
        extractor = get_extractor(extractor_type, graph, pattern_config)

        for i, filepath in enumerate(files):
            extractor.extract(filepath)
            if progress_callback:
                progress_callback(i + 1, len(files))

        return graph

    def generate_outputs(self, graph: Graph, title: str) -> dict[str, Path]:
        """Generate HTML and CSV outputs, return paths."""
        html_gen = HTMLGenerator()
        csv_gen = CSVGenerator()

        html_path = html_gen.generate(graph, self.output_dir / "index.html", title)
        nodes_path, edges_path = csv_gen.generate(graph, self.output_dir)

        return {
            "html": html_path,
            "nodes_csv": nodes_path,
            "edges_csv": edges_path,
        }
```

### Pattern 2: In-Memory Job Store
**What:** Simple dict-based job state for tracking extraction progress
**When to use:** Single-operator tools without persistence requirements
**Example:**
```python
# Source: https://github.com/fastapi/fastapi/discussions/8523
# src/cosmograph/api/deps.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Job:
    id: str
    status: JobStatus
    created_at: datetime
    progress: int = 0
    total: int = 0
    result: Any = None
    error: str | None = None

class JobStore:
    """In-memory job storage. Single-process only."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def create_job(self, total: int = 0) -> Job:
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            total=total,
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int):
        if job := self._jobs.get(job_id):
            job.progress = progress
            job.status = JobStatus.PROCESSING

# Global instance - fine for single-worker deployment
job_store = JobStore()
```

### Pattern 3: File Upload with Temp Files
**What:** Save UploadFile to temp directory, pass to extractors
**When to use:** When extractors expect file paths (our case)
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
# src/cosmograph/api/routes/extract.py

import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks

router = APIRouter(prefix="/api")

@router.post("/extract")
async def create_extraction(
    files: list[UploadFile],
    background_tasks: BackgroundTasks,
    extractor: str = "auto",
    title: str = "Knowledge Graph",
):
    # Create temp directory for this job
    temp_dir = Path(tempfile.mkdtemp(prefix="cosmograph_"))
    saved_files = []

    for upload in files:
        file_path = temp_dir / upload.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        saved_files.append(file_path)

    # Create job and start background processing
    job = job_store.create_job(total=len(saved_files))
    background_tasks.add_task(
        run_extraction, job.id, saved_files, extractor, title, temp_dir
    )

    return {"job_id": job.id, "status": job.status}
```

### Pattern 4: SSE for Progress Updates
**What:** Server-Sent Events stream for real-time progress
**When to use:** Long-running operations, unidirectional server-to-client updates
**Example:**
```python
# Source: https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154
# src/cosmograph/api/routes/extract.py

import asyncio
from sse_starlette.sse import EventSourceResponse

@router.get("/extract/{job_id}/progress")
async def extraction_progress(job_id: str):
    async def event_generator():
        while True:
            job = job_store.get_job(job_id)
            if not job:
                yield {"event": "error", "data": "Job not found"}
                break

            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": job.status,
                    "progress": job.progress,
                    "total": job.total,
                })
            }

            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
```

### Anti-Patterns to Avoid
- **Mixing HTTP concerns in service layer:** Services should never import FastAPI; raise domain exceptions, let API layer convert to HTTPException
- **Blocking the event loop:** Don't call sync extractors directly in async endpoints; use BackgroundTasks or run_in_executor
- **Storing files in memory:** Always stream large uploads to disk with shutil.copyfileobj
- **Wildcard CORS with credentials:** `allow_origins=["*"]` with `allow_credentials=True` is invalid

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File upload parsing | Manual multipart | `UploadFile` + python-multipart | Edge cases in multipart parsing |
| CORS handling | Manual headers | CORSMiddleware | Preflight requests, OPTIONS handling |
| Request validation | Manual checks | Pydantic models | Automatic 422 errors with details |
| Progress streaming | Custom chunked response | sse-starlette | Proper SSE event formatting |
| API documentation | Swagger/OpenAPI manual | FastAPI auto-docs | Generated from type hints |

**Key insight:** FastAPI's batteries-included approach means most common web API patterns have built-in or well-integrated solutions. The focus should be on wiring existing extractors correctly, not reinventing HTTP handling.

## Common Pitfalls

### Pitfall 1: Blocking the Event Loop
**What goes wrong:** Calling synchronous extractors directly in async endpoints blocks all concurrent requests
**Why it happens:** Extractors use sync I/O (file reading, regex processing)
**How to avoid:** Use BackgroundTasks for extraction processing; endpoint returns job_id immediately
**Warning signs:** API becomes unresponsive during large file processing

### Pitfall 2: Lost Job State on Restart
**What goes wrong:** In-memory job store loses all state when server restarts
**Why it happens:** No persistence layer
**How to avoid:** Acceptable per REQUIREMENTS.md ("Results exist only during session"). Document this limitation clearly.
**Warning signs:** Users confused about missing results after restart

### Pitfall 3: File Upload Memory Exhaustion
**What goes wrong:** Large PDFs exhaust server memory
**Why it happens:** Reading entire file into memory instead of streaming
**How to avoid:** Use `shutil.copyfileobj(upload.file, dest)` to stream to disk; never `await upload.read()` for large files
**Warning signs:** MemoryError during multi-file uploads

### Pitfall 4: CORS Misconfiguration
**What goes wrong:** Frontend can't reach API during development
**Why it happens:** Missing localhost origins or incorrect port
**How to avoid:** Explicitly list `http://localhost:3000`, `http://localhost:5173` (Vite default), and `http://cosmograph.localhost`
**Warning signs:** Browser console shows CORS errors

### Pitfall 5: LLM Extractor in API Without Approval Gate
**What goes wrong:** API calls Claude without operator confirmation
**Why it happens:** Approval gate is interactive (console prompt); can't work in HTTP context
**How to avoid:** For API, LLM extraction must be pre-approved (client sends confirmation flag) or disabled
**Warning signs:** Unexpected API costs, data sovereignty violation

## Code Examples

Verified patterns from official sources:

### FastAPI App with Lifespan Events
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
# src/cosmograph/api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize job store, clean old temp files
    print("Starting Cosmograph API")
    yield
    # Shutdown: cleanup
    print("Shutting down Cosmograph API")

app = FastAPI(
    title="Cosmograph API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://cosmograph.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Health Check Endpoint
```python
# Source: https://www.index.dev/blog/how-to-implement-health-check-in-python
# src/cosmograph/api/routes/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Pydantic Response Models
```python
# Source: https://fastapi.tiangolo.com/tutorial/response-model/
# src/cosmograph/api/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class ExtractionRequest(BaseModel):
    extractor: str = Field(default="auto", description="Extractor type: auto, legal, text, generic, pdf, llm")
    title: str = Field(default="Knowledge Graph", description="Title for visualization")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"extractor": "legal", "title": "CRST Legal Framework"}
            ]
        }
    }

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = 0
    total: int = 0
    created_at: datetime

class GraphResponse(BaseModel):
    title: str
    nodes: list[dict]
    edges: list[dict]
    stats: dict

class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
```

### Custom Exception Handler
```python
# Source: https://fastapi.tiangolo.com/tutorial/handling-errors/
# src/cosmograph/api/exceptions.py

from fastapi import Request
from fastapi.responses import JSONResponse

class ExtractionError(Exception):
    """Domain exception for extraction failures."""
    def __init__(self, message: str, filename: str | None = None):
        self.message = message
        self.filename = filename

async def extraction_error_handler(request: Request, exc: ExtractionError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message,
            "filename": exc.filename,
            "error_code": "EXTRACTION_FAILED",
        }
    )

# Register in main.py:
# app.add_exception_handler(ExtractionError, extraction_error_handler)
```

### TestClient Test Pattern
```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
# tests/test_api.py

import io
from fastapi.testclient import TestClient
from cosmograph.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_upload_file():
    # Create test file content
    content = b"ARTICLE I - TEST\nSECTION 1. Content."
    files = {"files": ("test.txt", io.BytesIO(content), "text/plain")}
    data = {"extractor": "legal", "title": "Test Graph"}

    response = client.post("/api/extract", files=files, data=data)
    assert response.status_code == 200
    assert "job_id" in response.json()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `startup`/`shutdown` events | `lifespan` context manager | FastAPI 0.93+ | Cleaner resource management |
| `@app.on_event("startup")` | `asynccontextmanager` lifespan | 2023 | Deprecated warning in newer versions |
| Pydantic v1 `Config` class | `model_config` dict | Pydantic 2.0 | Must use new syntax |
| `example` in Field | `examples` (list) | OpenAPI 3.1 | Single example deprecated |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")` - use lifespan instead
- `response_model_exclude` / `response_model_include` - create separate models instead
- Starlette TestClient direct import - use FastAPI's re-export

## Open Questions

Things that couldn't be fully resolved:

1. **LLM Extractor in API Context**
   - What we know: Approval gate uses interactive console prompt
   - What's unclear: How to handle approval in HTTP context
   - Recommendation: Add `confirmed: bool = False` to request; if extractor=llm and confirmed=false, return cost estimate; require confirmed=true for actual extraction

2. **Temp File Cleanup Timing**
   - What we know: Must clean temp files after job completes
   - What's unclear: How long to retain for download endpoint access
   - Recommendation: Clean on next request or after configurable TTL (e.g., 30 minutes)

3. **Multiple Worker Deployment**
   - What we know: In-memory state doesn't work with multiple workers
   - What's unclear: Whether Phase 7 deployment will use multiple workers
   - Recommendation: Design for single worker (uvicorn --workers 1); document limitation

## Sources

### Primary (HIGH confidence)
- [FastAPI Official Docs - Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) - UploadFile API
- [FastAPI Official Docs - Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) - BackgroundTasks patterns
- [FastAPI Official Docs - Testing](https://fastapi.tiangolo.com/tutorial/testing/) - TestClient usage
- [FastAPI Official Docs - CORS](https://fastapi.tiangolo.com/tutorial/cors/) - CORSMiddleware configuration
- [FastAPI Official Docs - Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) - HTTPException patterns

### Secondary (MEDIUM confidence)
- [Better Stack - FastAPI Error Handling](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/) - Custom exception patterns
- [sse-starlette PyPI](https://pypi.org/project/fastapi-sse/) - SSE implementation
- [FastAPI Best Practices GitHub](https://github.com/zhanymkanov/fastapi-best-practices) - Project structure patterns
- [Medium - Service Layer Architecture](https://medium.com/@abhinav.dobhal/building-production-ready-fastapi-applications-with-service-layer-architecture-in-2025-f3af8a6ac563) - CLI/API code sharing

### Tertiary (LOW confidence)
- [GitHub Discussion #8523](https://github.com/fastapi/fastapi/discussions/8523) - In-memory state patterns (community, needs validation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official FastAPI documentation verified
- Architecture: HIGH - Well-documented patterns, matches Iyeska conventions
- Pitfalls: MEDIUM - Some derived from community sources

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - FastAPI stable, patterns well-established)
