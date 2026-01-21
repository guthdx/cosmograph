"""Graph retrieval and download endpoints for Cosmograph API."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..deps import get_job_store
from ..schemas import GraphResponse, JobStatus

router = APIRouter(prefix="/api")


@router.get("/graph/{job_id}", response_model=GraphResponse)
async def get_graph(job_id: str) -> GraphResponse:
    """Get the extracted graph data as JSON.

    Args:
        job_id: The job identifier returned from POST /api/extract

    Returns:
        Graph data including nodes, edges, and stats

    Raises:
        HTTPException 404: If job_id not found
        HTTPException 400: If extraction not yet complete
    """
    store = get_job_store()
    job = store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    if job.status != JobStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction not complete. Status: {job.status.value}",
        )

    if job.result is None:
        raise HTTPException(
            status_code=500,
            detail="Job completed but no result available",
        )

    graph_data = job.result.get("graph", {})

    return GraphResponse(
        title=graph_data.get("title", "Knowledge Graph"),
        nodes=graph_data.get("nodes", []),
        edges=graph_data.get("edges", []),
        stats=job.result.get("stats", {}),
    )


@router.get("/download/{job_id}")
async def download_html(job_id: str) -> FileResponse:
    """Download the generated HTML visualization.

    Args:
        job_id: The job identifier returned from POST /api/extract

    Returns:
        HTML file as download

    Raises:
        HTTPException 404: If job_id not found or output file missing
        HTTPException 400: If extraction not yet complete
    """
    store = get_job_store()
    job = store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    if job.status != JobStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction not complete. Status: {job.status.value}",
        )

    if job.output_dir is None:
        raise HTTPException(
            status_code=500,
            detail="Job completed but output directory not available",
        )

    html_path = job.output_dir / "index.html"

    if not html_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Output file not found",
        )

    return FileResponse(
        path=html_path,
        media_type="text/html",
        filename=f"{job_id}_graph.html",
    )


@router.get("/download/{job_id}/csv")
async def download_csv(job_id: str) -> FileResponse:
    """Download CSV exports as a ZIP archive.

    Args:
        job_id: The job identifier returned from POST /api/extract

    Returns:
        ZIP file containing graph_nodes.csv and graph_data.csv

    Raises:
        HTTPException 404: If job_id not found or CSV files missing
        HTTPException 400: If extraction not yet complete
    """
    store = get_job_store()
    job = store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    if job.status != JobStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction not complete. Status: {job.status.value}",
        )

    if job.output_dir is None:
        raise HTTPException(
            status_code=500,
            detail="Job completed but output directory not available",
        )

    # CSVGenerator uses graph_nodes.csv and graph_data.csv filenames
    nodes_csv = job.output_dir / "graph_nodes.csv"
    edges_csv = job.output_dir / "graph_data.csv"

    if not nodes_csv.exists() or not edges_csv.exists():
        raise HTTPException(
            status_code=404,
            detail="CSV files not found",
        )

    # Create temp directory for zip
    temp_dir = Path(tempfile.mkdtemp(prefix="cosmograph_zip_"))
    csv_dir = temp_dir / "csv_export"
    csv_dir.mkdir()

    # Copy CSV files to temp directory with user-friendly names
    shutil.copy(nodes_csv, csv_dir / "nodes.csv")
    shutil.copy(edges_csv, csv_dir / "edges.csv")

    # Create zip archive
    zip_path = shutil.make_archive(
        str(temp_dir / f"{job_id}_csv"),
        "zip",
        csv_dir,
    )

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{job_id}_csv.zip",
    )
