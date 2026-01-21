"""File upload and extraction endpoints for Cosmograph API."""

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from ..deps import Job, JobStore, get_job_store
from ..schemas import JobResponse, JobStatus
from ...services.extraction import ExtractionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _job_to_response(job: Job) -> JobResponse:
    """Convert internal Job to JobResponse schema."""
    return JobResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        total=job.total,
        created_at=job.created_at,
        error=job.error,
    )


@router.post("/extract", response_model=JobResponse)
async def create_extraction(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    extractor: str = Form(default="auto"),
    title: str = Form(default="Knowledge Graph"),
    llm_confirmed: bool = Form(default=False),
) -> JobResponse:
    """Create an extraction job from uploaded files.

    Uploads files, creates a job, and starts background extraction.
    Returns immediately with job_id for polling.

    Args:
        files: Files to process (required)
        extractor: Extractor type: auto, legal, text, generic, pdf, llm
        title: Title for the generated visualization
        llm_confirmed: Required true for LLM extraction (data sovereignty gate)

    Returns:
        JobResponse with job_id and initial status

    Raises:
        HTTPException 400: If no files provided or LLM without confirmation
    """
    # Validate files not empty
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # LLM extraction requires explicit confirmation (data sovereignty)
    if extractor == "llm" and not llm_confirmed:
        raise HTTPException(
            status_code=400,
            detail=(
                "LLM extraction requires llm_confirmed=true. "
                "This sends document content to Claude API. "
                "Please confirm you have authorization for external API calls."
            ),
        )

    # Create temp directory for uploaded files
    temp_dir = Path(tempfile.mkdtemp(prefix="cosmograph_"))
    saved_files: list[Path] = []

    try:
        for upload in files:
            if upload.filename:
                file_path = temp_dir / upload.filename
                # Stream to disk (never read entire file into memory)
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(upload.file, f)
                saved_files.append(file_path)
    except Exception as e:
        # Clean up temp dir on upload failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.exception("Failed to save uploaded files")
        raise HTTPException(status_code=500, detail=f"Failed to save files: {e}") from e

    if not saved_files:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No valid files in upload")

    # Create job
    store = get_job_store()
    job = store.create_job(total=len(saved_files))

    # Store temp_dir in job for later cleanup (download endpoint will need it)
    job.output_dir = temp_dir

    logger.info(
        "Created extraction job %s: %d files, extractor=%s",
        job.id,
        len(saved_files),
        extractor,
    )

    # Start background extraction
    background_tasks.add_task(
        run_extraction,
        job.id,
        saved_files,
        extractor,
        title,
        temp_dir,
        llm_confirmed,
    )

    return _job_to_response(job)


@router.get("/extract/{job_id}", response_model=JobResponse)
async def get_extraction_status(job_id: str) -> JobResponse:
    """Get the status of an extraction job.

    Args:
        job_id: The job identifier returned from POST /api/extract

    Returns:
        Current job status including progress and result

    Raises:
        HTTPException 404: If job_id not found
    """
    store = get_job_store()
    job = store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    return _job_to_response(job)


@router.get("/extract/{job_id}/progress")
async def extraction_progress(job_id: str) -> EventSourceResponse:
    """Stream extraction progress via Server-Sent Events.

    Connects to the progress stream and receives events until the job completes.
    Events: progress (with status/progress/total), complete (with job_id), error.

    Args:
        job_id: The job identifier returned from POST /api/extract

    Returns:
        EventSourceResponse streaming progress updates
    """
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        store = get_job_store()

        while True:
            job = store.get_job(job_id)

            if job is None:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Job not found"}),
                }
                break

            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": job.status.value,
                    "progress": job.progress,
                    "total": job.total,
                }),
            }

            if job.status in (JobStatus.completed, JobStatus.failed):
                # Send final event with result or error
                if job.status == JobStatus.completed:
                    yield {
                        "event": "complete",
                        "data": json.dumps({"job_id": job_id}),
                    }
                else:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": job.error}),
                    }
                break

            await asyncio.sleep(0.5)  # Poll every 500ms

    return EventSourceResponse(event_generator())


def run_extraction(
    job_id: str,
    files: list[Path],
    extractor_type: str,
    title: str,
    temp_dir: Path,
    llm_confirmed: bool,
) -> None:
    """Run extraction in background thread.

    This function runs synchronously (extractors are sync I/O).
    FastAPI BackgroundTasks handles threading.

    Args:
        job_id: Job identifier for status updates
        files: List of file paths to process
        extractor_type: Extractor type to use
        title: Title for the graph
        temp_dir: Temporary directory containing files
        llm_confirmed: Whether LLM usage is pre-approved
    """
    store = get_job_store()

    def progress_callback(current: int, total: int) -> None:
        """Update job progress."""
        store.update_progress(job_id, current)

    try:
        # Create service and process files
        service = ExtractionService(output_dir=temp_dir)

        # For LLM: interactive=False since already confirmed via API
        interactive = not llm_confirmed

        graph = service.process_files(
            files=files,
            extractor_type=extractor_type,
            title=title,
            progress_callback=progress_callback,
            interactive=interactive,
        )

        # Generate outputs
        service.generate_outputs(
            graph=graph,
            output_dir=temp_dir,
            title=title,
        )

        # Store graph data as result
        result = {
            "graph": graph.to_json(),  # Returns dict, not string
            "stats": {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "files_processed": len(files),
            },
            "output_dir": str(temp_dir),
        }

        store.complete_job(job_id, result)
        logger.info(
            "Completed extraction job %s: %d nodes, %d edges",
            job_id,
            len(graph.nodes),
            len(graph.edges),
        )

    except Exception as e:
        logger.exception("Extraction job %s failed", job_id)
        store.fail_job(job_id, str(e))
        # Note: Don't clean temp_dir here - keep for debugging failed jobs
