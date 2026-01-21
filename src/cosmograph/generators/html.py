"""HTML visualization generator."""

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader

from ..models import Graph


class HTMLGenerator:
    """Generate interactive HTML visualization from a knowledge graph."""

    # Category colors for visualization
    CATEGORY_COLORS = {
        "document": "#e91e63",
        "article": "#9c27b0",
        "title": "#673ab7",
        "chapter": "#3f51b5",
        "section": "#2196f3",
        "ordinance": "#00bcd4",
        "authority": "#ff9800",
        "right": "#4caf50",
        "offense": "#f44336",
        "penalty": "#ff5722",
        "procedure": "#795548",
        "definition": "#607d8b",
        "place": "#8bc34a",
        "entity": "#ffc107",
        "concept": "#9e9e9e",
        "constitution": "#e91e63",
        "code": "#9c27b0",
        "proper_noun": "#4caf50",
        "acronym": "#ff9800",
        "quoted_term": "#2196f3",
        "section_ref": "#673ab7",
    }

    def __init__(self) -> None:
        """Initialize HTMLGenerator with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("cosmograph", "templates"),
            autoescape=False,  # We control escaping with |safe filter
        )

    def generate(self, graph: Graph, output_path: Path, title: str | None = None) -> Path:
        """Generate an interactive HTML visualization."""
        title = title or graph.title

        nodes_json = json.dumps([n.to_dict() for n in graph.nodes.values()])
        edges_json = json.dumps([e.to_dict() for e in graph.edges])
        colors_json = json.dumps(self.CATEGORY_COLORS)
        stats = graph.get_stats()

        html = self._generate_html(title, nodes_json, edges_json, colors_json, stats)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _generate_html(
        self, title: str, nodes_json: str, edges_json: str, colors_json: str, stats: dict[str, int]
    ) -> str:
        """Render HTML visualization using Jinja2 template."""
        template = self.env.get_template("graph.html.j2")
        return template.render(
            title=title,
            nodes_json=nodes_json,
            edges_json=edges_json,
            colors_json=colors_json,
            stats=stats,
        )
