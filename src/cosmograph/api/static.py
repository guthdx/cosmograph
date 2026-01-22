"""Static file serving for production deployment."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def setup_static_files(app: FastAPI) -> None:
    """Configure static file serving for frontend.

    Only activates if frontend/dist exists (production build present).
    API routes are registered first, so they take precedence.
    """
    # Calculate path relative to this module
    module_dir = Path(__file__).parent
    frontend_dist = module_dir.parent.parent.parent / "frontend" / "dist"

    if not frontend_dist.exists():
        return  # No frontend build, skip static serving

    frontend_dist = frontend_dist.resolve()
    assets_dir = frontend_dist / "assets"
    index_html = frontend_dist / "index.html"

    # Mount assets directory for JS/CSS files
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="static_assets",
        )

    @app.get("/", include_in_schema=False)
    async def serve_root() -> FileResponse:
        """Serve frontend index.html at root."""
        return FileResponse(str(index_html))

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str) -> FileResponse:
        """Catch-all for SPA routing - serves index.html for non-file paths."""
        # Check if it's a real file in dist
        file_path = frontend_dist / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for SPA routing
        return FileResponse(str(index_html))
