"""CSV output generator."""

import csv
from pathlib import Path

from ..models import Graph


class CSVGenerator:
    """Generate CSV files from a knowledge graph."""

    def generate(self, graph: Graph, output_dir: Path) -> tuple[Path, Path]:
        """Generate nodes and edges CSV files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        nodes_file = output_dir / "graph_nodes.csv"
        edges_file = output_dir / "graph_data.csv"

        # Write nodes
        with open(nodes_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "label", "category", "description"])
            for node in graph.nodes.values():
                writer.writerow([node.id, node.label, node.category, node.description])

        # Write edges
        with open(edges_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "type"])
            for edge in graph.edges:
                writer.writerow([edge.source, edge.target, edge.edge_type])

        return nodes_file, edges_file
