"""FastAPI application for Cosmograph API."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from cosmograph import __version__

from .exceptions import (
    ExtractionError,
    JobNotFoundError,
    extraction_error_handler,
    job_not_found_handler,
)
from .routes import extract, graph, health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    logger.info("Starting Cosmograph API v%s", __version__)
    yield
    logger.info("Shutting down Cosmograph API")


app = FastAPI(
    title="Cosmograph API",
    description="Document-to-knowledge-graph extraction service",
    version=__version__,
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

# Register exception handlers
app.add_exception_handler(ExtractionError, extraction_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(JobNotFoundError, job_not_found_handler)  # type: ignore[arg-type]

# Include routers
app.include_router(health.router)
app.include_router(extract.router)
app.include_router(graph.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")
