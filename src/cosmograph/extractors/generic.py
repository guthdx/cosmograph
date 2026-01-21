"""Generic extractor that uses pattern matching for any document type."""

import re
from pathlib import Path
from typing import Optional

from ..models import Graph
from .base import BaseExtractor


class GenericExtractor(BaseExtractor):
    """Generic entity extractor using configurable patterns."""

    # Default extraction patterns
    DEFAULT_PATTERNS = {
        "proper_noun": r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
        "acronym": r"\b([A-Z]{2,6})\b",
        "quoted_term": r'"([^"]+)"',
        "section_ref": r"(?:Section|§)\s*(\d+(?:\.\d+)*)",
    }

    def __init__(
        self,
        graph: Optional[Graph] = None,
        patterns: Optional[dict[str, str]] = None,
        min_occurrences: int = 2,
    ):
        super().__init__(graph)
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.min_occurrences = min_occurrences

    def supports(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in {".txt", ".md", ".text"}

    def extract(self, filepath: Path) -> Graph:
        """Extract entities using pattern matching."""
        text = self.read_text(filepath)
        source_name = filepath.stem

        # Add document node
        doc_id = self.graph.add_node(
            source_name, source_name, "document", f"Source: {filepath.name}", filepath.name
        )

        # Count occurrences for each pattern
        entity_counts: dict[str, dict[str, int]] = {}

        for category, pattern in self.patterns.items():
            entity_counts[category] = {}
            for match in re.finditer(pattern, text):
                entity = match.group(1).strip()
                if len(entity) > 2:
                    entity_counts[category][entity] = entity_counts[category].get(entity, 0) + 1

        # Add entities that meet minimum occurrence threshold
        for category, entities in entity_counts.items():
            for entity, count in entities.items():
                if count >= self.min_occurrences:
                    entity_id = self.graph.add_node(
                        entity, entity, category, f"Occurs {count} times", filepath.name
                    )
                    self.graph.add_edge(doc_id, entity_id, "mentions")

        return self.graph
