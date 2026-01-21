"""Command-line interface for Cosmograph."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .extractors import GenericExtractor, LegalDocumentExtractor, PdfExtractor, TextExtractor
from .generators import CSVGenerator, HTMLGenerator
from .models import Graph

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
    title: str = typer.Option("Knowledge Graph", "-t", "--title", help="Title for the visualization"),
    extractor: str = typer.Option(
        "auto", "-e", "--extractor", help="Extractor type: auto, legal, text, generic, pdf"
    ),
    pattern: str = typer.Option("*.txt", "-p", "--pattern", help="File pattern when input is directory"),
    html_only: bool = typer.Option(False, "--html-only", help="Only generate HTML, skip CSV"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open result in browser"),
):
    """Generate a knowledge graph visualization from documents."""
    console.print(f"\n[bold cyan]Cosmograph[/bold cyan] - Knowledge Graph Generator\n")

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

    # Initialize graph
    graph = Graph(title=title)

    # Select extractor
    extractor_instance = _get_extractor(extractor, graph)

    # Process files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(files))

        for filepath in files:
            progress.update(task, description=f"Processing {filepath.name}...")
            try:
                extractor_instance.extract(filepath)
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to process {filepath.name}: {e}")
            progress.advance(task)

    # Generate outputs
    output.mkdir(parents=True, exist_ok=True)

    if not html_only:
        csv_gen = CSVGenerator()
        nodes_file, edges_file = csv_gen.generate(graph, output)
        console.print(f"[green]✓[/green] Generated {nodes_file.name}")
        console.print(f"[green]✓[/green] Generated {edges_file.name}")

    html_gen = HTMLGenerator()
    html_file = html_gen.generate(graph, output / "index.html", title)
    console.print(f"[green]✓[/green] Generated {html_file.name}")

    # Print stats
    stats = graph.get_stats()
    _print_stats(stats)

    console.print(f"\n[bold green]Output:[/bold green] {output.absolute()}")

    # Open in browser
    if open_browser:
        import webbrowser

        webbrowser.open(f"file://{html_file.absolute()}")


@app.command()
def stats(
    input_path: Path = typer.Argument(..., help="Path to graph_nodes.csv or directory with CSV files"),
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
    with open(nodes_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_nodes += 1
            cat = row.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

    # Count edges
    total_edges = 0
    if edges_file.exists():
        with open(edges_file, "r", encoding="utf-8") as f:
            total_edges = sum(1 for _ in f) - 1  # Subtract header

    stats = {"nodes": total_nodes, "edges": total_edges, "categories": categories}
    _print_stats(stats)


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


def _get_extractor(extractor_type: str, graph: Graph):
    """Get the appropriate extractor based on type."""
    if extractor_type == "legal":
        return LegalDocumentExtractor(graph)
    elif extractor_type == "text":
        return TextExtractor(graph)
    elif extractor_type == "generic":
        return GenericExtractor(graph)
    elif extractor_type == "pdf":
        return PdfExtractor(graph)
    else:  # auto
        return LegalDocumentExtractor(graph)  # Default to legal for now


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
