"""Generic extractor that uses pattern matching for any document type."""

import re
from pathlib import Path

from ..config import PatternConfig
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
        graph: Graph | None = None,
        patterns: dict[str, str] | None = None,
        config: PatternConfig | None = None,
        min_occurrences: int = 2,
    ):
        super().__init__(graph)

        # Handle configuration sources in priority order
        if config is not None:
            # Build patterns dict from PatternConfig
            pattern_strings = {ep.name: ep.pattern for ep in config.entity_patterns}
            self.min_occurrences = config.min_occurrences
            # Store metadata for category and min_length lookup
            self._pattern_metadata = {ep.name: ep for ep in config.entity_patterns}
        elif patterns is not None:
            pattern_strings = patterns
            self.min_occurrences = min_occurrences
            self._pattern_metadata = {}
        else:
            pattern_strings = self.DEFAULT_PATTERNS
            self.min_occurrences = min_occurrences
            self._pattern_metadata = {}

        # Compile patterns once at init
        self._compiled_patterns = {
            name: re.compile(pattern) for name, pattern in pattern_strings.items()
        }

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

        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            # Get min_length from metadata if available, else default to 2
            if pattern_name in self._pattern_metadata:
                min_length = self._pattern_metadata[pattern_name].min_length
            else:
                min_length = 2

            entity_counts[pattern_name] = {}
            for match in compiled_pattern.finditer(text):
                entity = match.group(1).strip()
                if len(entity) >= min_length:
                    entity_counts[pattern_name][entity] = (
                        entity_counts[pattern_name].get(entity, 0) + 1
                    )

        # Add entities that meet minimum occurrence threshold
        for pattern_name, entities in entity_counts.items():
            # Get category from metadata if available, else use pattern name
            if pattern_name in self._pattern_metadata:
                category = self._pattern_metadata[pattern_name].category
            else:
                category = pattern_name

            for entity, count in entities.items():
                if count >= self.min_occurrences:
                    entity_id = self.graph.add_node(
                        entity, entity, category, f"Occurs {count} times", filepath.name
                    )
                    self.graph.add_edge(doc_id, entity_id, "mentions")

        return self.graph
