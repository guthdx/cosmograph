"""Health check endpoint for Cosmograph API."""

from fastapi import APIRouter

from cosmograph import __version__

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Check API health status.

    Returns:
        Health status with API version.
    """
    return {"status": "healthy", "version": __version__}
