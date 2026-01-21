"""Pydantic request/response models for Cosmograph API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ExtractionRequest(BaseModel):
    """Request model for extraction jobs."""

    extractor: str = Field(
        default="auto",
        description="Extractor type: auto, legal, text, generic, pdf, llm",
    )
    title: str = Field(
        default="Knowledge Graph",
        description="Title for the generated visualization",
    )
    llm_confirmed: bool = Field(
        default=False,
        description="Whether LLM API usage has been pre-approved (for data sovereignty)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "extractor": "legal",
                    "title": "CRST Legal Framework",
                    "llm_confirmed": False,
                }
            ]
        }
    }


class JobResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(description="Unique job identifier")
    status: JobStatus = Field(description="Current job status")
    progress: int = Field(default=0, description="Number of files processed")
    total: int = Field(default=0, description="Total number of files to process")
    created_at: datetime = Field(description="Job creation timestamp")
    error: str | None = Field(default=None, description="Error message if job failed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "a1b2c3d4",
                    "status": "processing",
                    "progress": 3,
                    "total": 10,
                    "created_at": "2026-01-21T12:00:00Z",
                    "error": None,
                }
            ]
        }
    }


class GraphResponse(BaseModel):
    """Response model for completed graph data."""

    title: str = Field(description="Graph title")
    nodes: list[dict] = Field(description="List of graph nodes")  # type: ignore[type-arg]
    edges: list[dict] = Field(description="List of graph edges")  # type: ignore[type-arg]
    stats: dict = Field(description="Graph statistics")  # type: ignore[type-arg]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Knowledge Graph",
                    "nodes": [{"id": "node1", "label": "Entity 1", "category": "concept"}],
                    "edges": [{"source": "node1", "target": "node2", "label": "relates_to"}],
                    "stats": {"nodes": 1, "edges": 1},
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    detail: str = Field(description="Error description")
    error_code: str | None = Field(default=None, description="Machine-readable error code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "Job not found",
                    "error_code": "JOB_NOT_FOUND",
                }
            ]
        }
    }
