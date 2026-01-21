"""Job store and FastAPI dependencies for Cosmograph API."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schemas import JobStatus


@dataclass
class Job:
    """Represents an extraction job."""

    id: str
    status: JobStatus
    created_at: datetime
    progress: int = 0
    total: int = 0
    result: dict[str, Any] | None = field(default=None, repr=False)
    error: str | None = None
    output_dir: Path | None = field(default=None, repr=False)


class JobStore:
    """In-memory job storage. Single-process only.

    Note: Per REQUIREMENTS.md, no persistence needed - "Results exist only during session"
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create_job(self, total: int = 0) -> Job:
        """Create a new job with generated 8-char UUID."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            status=JobStatus.pending,
            created_at=datetime.now(UTC),
            total=total,
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID, or None if not found."""
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int) -> None:
        """Update job progress and set status to processing."""
        if job := self._jobs.get(job_id):
            job.progress = progress
            job.status = JobStatus.processing

    def complete_job(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark job as completed with result."""
        if job := self._jobs.get(job_id):
            job.status = JobStatus.completed
            job.result = result

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        if job := self._jobs.get(job_id):
            job.status = JobStatus.failed
            job.error = error


# Global instance - fine for single-worker deployment
job_store = JobStore()


def get_job_store() -> JobStore:
    """FastAPI dependency for job store injection."""
    return job_store
