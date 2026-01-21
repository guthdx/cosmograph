"""Command-line interface for Cosmograph."""

from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .config import PatternConfig, load_patterns
from .extractors import HAS_ANTHROPIC, OperatorDeclinedError
from .services import ExtractionService

app = typer.Typer(
    name="cosmograph",
    help="Generate interactive knowledge graph visualizations from documents.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Cosmograph[/bold cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, help="Show version and exit."
    ),
):
    """Cosmograph - Generate interactive knowledge graph visualizations."""
    pass


@app.command()
def generate(
    input_path: Path = typer.Argument(..., help="Input file or directory containing documents"),
    output: Path = typer.Option(
        Path("./output"), "-o", "--output", help="Output directory for generated files"
    ),
    title: str = typer.Option(
        "Knowledge Graph", "-t", "--title", help="Title for the visualization"
    ),
    extractor: str = typer.Option(
        "auto", "-e", "--extractor", help="Extractor type: auto, legal, text, generic, pdf, llm"
    ),
    pattern: str = typer.Option(
        "*.txt", "-p", "--pattern", help="File pattern when input is directory"
    ),
    patterns_file: Annotated[
        Path | None,
        typer.Option(
            "--patterns",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to patterns.yaml configuration file (used with -e generic)",
        ),
    ] = None,
    html_only: bool = typer.Option(False, "--html-only", help="Only generate HTML, skip CSV"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open result in browser"),
    no_confirm: bool = typer.Option(
        False,
        "--no-confirm",
        help="Skip confirmation prompt for LLM extraction (use with caution)",
    ),
):
    """Generate a knowledge graph visualization from documents."""
    console.print("\n[bold cyan]Cosmograph[/bold cyan] - Knowledge Graph Generator\n")

    # Validate input
    if not input_path.exists():
        console.print(f"[red]Error:[/red] Input path does not exist: {input_path}")
        raise typer.Exit(1)

    # Collect input files
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob(pattern))
        if not files:
            console.print(f"[red]Error:[/red] No files matching '{pattern}' in {input_path}")
            raise typer.Exit(1)

    console.print(f"[dim]Found {len(files)} file(s) to process[/dim]\n")

    # Load pattern configuration if provided
    pattern_config: PatternConfig | None = None
    if patterns_file:
        try:
            pattern_config = load_patterns(patterns_file)
            console.print(
                f"[dim]Loaded {len(pattern_config.entity_patterns)} patterns "
                f"from {patterns_file.name}[/dim]"
            )
        except (ValueError, ValidationError, yaml.YAMLError) as e:
            console.print(f"[red]Error:[/red] Invalid patterns file: {e}")
            raise typer.Exit(1)

    # Check LLM extractor availability before starting
    if extractor == "llm" and not HAS_ANTHROPIC:
        console.print("[red]Error:[/red] LLM extractor requires anthropic package.")
        console.print("[dim]Install with: pip install cosmograph[llm][/dim]")
        raise typer.Exit(1)

    # Create service
    service = ExtractionService(output_dir=output)

    # Process files with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(files))

        def update_progress(current: int, total: int) -> None:
            """Update progress bar after each file."""
            # Set the current file being processed (for display)
            if current < len(files):
                progress.update(task, description=f"Processing file {current}/{total}...")
            progress.update(task, completed=current)

        try:
            graph = service.process_files(
                files=files,
                extractor_type=extractor,
                title=title,
                pattern_config=pattern_config,
                progress_callback=update_progress,
                interactive=not no_confirm,
            )
        except OperatorDeclinedError:
            console.print("[yellow]LLM extraction declined by operator[/yellow]")
            raise typer.Exit(0)  # Not an error, just a user decision
        except ValueError as e:
            # Handle extractor errors (e.g., LLM not available)
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Generate outputs using service
    outputs = service.generate_outputs(
        graph=graph,
        output_dir=output,
        title=title,
        html_only=html_only,
    )

    # Report generated files
    if "nodes_csv" in outputs:
        console.print(f"[green]OK[/green] Generated {outputs['nodes_csv'].name}")
    if "edges_csv" in outputs:
        console.print(f"[green]OK[/green] Generated {outputs['edges_csv'].name}")
    console.print(f"[green]OK[/green] Generated {outputs['html'].name}")

    # Print stats
    stats = graph.get_stats()
    _print_stats(stats)

    console.print(f"\n[bold green]Output:[/bold green] {output.absolute()}")

    # Open in browser
    if open_browser:
        import webbrowser

        webbrowser.open(f"file://{outputs['html'].absolute()}")


@app.command()
def stats(
    input_path: Path = typer.Argument(
        ..., help="Path to graph_nodes.csv or directory with CSV files"
    ),
):
    """Show statistics for an existing graph."""
    import csv

    if input_path.is_dir():
        nodes_file = input_path / "graph_nodes.csv"
        edges_file = input_path / "graph_data.csv"
    elif input_path.name == "graph_nodes.csv":
        nodes_file = input_path
        edges_file = input_path.parent / "graph_data.csv"
    else:
        console.print("[red]Error:[/red] Expected graph_nodes.csv or directory")
        raise typer.Exit(1)

    if not nodes_file.exists():
        console.print(f"[red]Error:[/red] Not found: {nodes_file}")
        raise typer.Exit(1)

    # Count nodes by category
    categories = {}
    total_nodes = 0
    with open(nodes_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_nodes += 1
            cat = row.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

    # Count edges
    total_edges = 0
    if edges_file.exists():
        with open(edges_file, encoding="utf-8") as f:
            total_edges = sum(1 for _ in f) - 1  # Subtract header

    stats_data = {"nodes": total_nodes, "edges": total_edges, "categories": categories}
    _print_stats(stats_data)


@app.command()
def serve(
    path: Path = typer.Argument(Path("./output"), help="Path to output directory"),
    port: int = typer.Option(8080, "-p", "--port", help="Port to serve on"),
):
    """Serve the visualization locally."""
    import http.server
    import socketserver

    html_file = path / "index.html"
    if not html_file.exists():
        console.print(f"[red]Error:[/red] No index.html found in {path}")
        raise typer.Exit(1)

    import os

    os.chdir(path)

    console.print(f"\n[bold cyan]Serving[/bold cyan] at http://localhost:{port}")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[dim]Server stopped[/dim]")


def _print_stats(stats: dict):
    """Print graph statistics."""
    table = Table(title="Graph Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Nodes", str(stats["nodes"]))
    table.add_row("Total Edges", str(stats["edges"]))

    console.print(table)

    if stats.get("categories"):
        cat_table = Table(title="Categories", show_header=True, header_style="bold cyan")
        cat_table.add_column("Category", style="dim")
        cat_table.add_column("Count", justify="right")

        for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
            cat_table.add_row(cat, str(count))

        console.print(cat_table)


if __name__ == "__main__":
    app()
