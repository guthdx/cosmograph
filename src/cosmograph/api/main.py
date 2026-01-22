"""FastAPI application for Cosmograph API."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cosmograph import __version__

from .exceptions import (
    ExtractionError,
    JobNotFoundError,
    extraction_error_handler,
    job_not_found_handler,
)
from .routes import extract, graph, health
from .static import setup_static_files

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

# CORS for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://cosmograph.localhost",
        "https://cosmograph.iyeska.net",
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

# Setup static file serving (must be after routers for API precedence)
setup_static_files(app)
