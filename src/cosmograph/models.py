"""Data models for graph nodes and edges."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """A node in the knowledge graph."""

    id: str
    label: str
    category: str
    description: str = ""
    source_file: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label[:60],  # Truncate for display
            "category": self.category,
            "description": self.description[:150] if self.description else "",
        }


@dataclass
class Edge:
    """An edge (relationship) between two nodes."""

    source: str
    target: str
    edge_type: str
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
        }


@dataclass
class Graph:
    """A knowledge graph containing nodes and edges."""

    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    title: str = "Knowledge Graph"
    description: str = ""

    def add_node(
        self,
        node_id: str,
        label: str,
        category: str,
        description: str = "",
        source_file: str = "",
    ) -> str:
        """Add a node, returning its cleaned ID."""
        clean_id = self._clean_id(node_id)
        if clean_id not in self.nodes:
            self.nodes[clean_id] = Node(
                id=clean_id,
                label=label,
                category=category,
                description=description,
                source_file=source_file,
            )
        return clean_id

    def add_edge(self, source: str, target: str, edge_type: str) -> bool:
        """Add an edge if both nodes exist and edge is unique."""
        source_id = self._clean_id(source)
        target_id = self._clean_id(target)

        # Skip self-loops
        if source_id == target_id:
            return False

        # Check for duplicates
        for edge in self.edges:
            if edge.source == source_id and edge.target == target_id and edge.edge_type == edge_type:
                return False

        self.edges.append(Edge(source_id, target_id, edge_type))
        return True

    def _clean_id(self, text: str) -> str:
        """Clean text to create valid node ID."""
        import re

        cleaned = re.sub(r"[^\w\s\-]", "", str(text))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:100]

    def get_stats(self) -> dict:
        """Get graph statistics."""
        categories = {}
        for node in self.nodes.values():
            categories[node.category] = categories.get(node.category, 0) + 1

        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "categories": categories,
        }

    def to_json(self) -> dict:
        """Export graph as JSON-serializable dict."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "title": self.title,
            "stats": self.get_stats(),
        }
