"""Custom exceptions and handlers for Cosmograph API."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ExtractionError(Exception):
    """Domain exception for extraction failures."""

    def __init__(self, message: str, filename: str | None = None):
        self.message = message
        self.filename = filename
        super().__init__(message)


class JobNotFoundError(Exception):
    """Domain exception for missing jobs."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


async def extraction_error_handler(request: Request, exc: ExtractionError) -> JSONResponse:
    """Handle ExtractionError with 422 status."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message,
            "filename": exc.filename,
            "error_code": "EXTRACTION_FAILED",
        },
    )


async def job_not_found_handler(request: Request, exc: JobNotFoundError) -> JSONResponse:
    """Handle JobNotFoundError with 404 status."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Job not found: {exc.job_id}",
            "error_code": "JOB_NOT_FOUND",
        },
    )
