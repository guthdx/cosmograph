"""Text file extractor."""

import re
from pathlib import Path

from ..models import Graph
from .base import BaseExtractor


class TextExtractor(BaseExtractor):
    """Extract entities from plain text files."""

    # Common patterns for entity extraction
    PATTERNS = {
        "header": r"^#{1,6}\s+(.+)$",  # Markdown headers
        "definition": r'"([A-Za-z\s]+)"\s+(?:means|shall mean|is defined as)\s+([^.]+)',
        "reference": r"(?:see|refer to|pursuant to)\s+([A-Za-z\s\d\-]+)",
    }

    def supports(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in {".txt", ".md", ".text"}

    def extract(self, filepath: Path) -> Graph:
        """Extract entities from a text file."""
        text = self.read_text(filepath)
        source_name = filepath.stem

        # Add document as root node
        doc_id = self.graph.add_node(
            source_name, source_name, "document", f"Source: {filepath.name}", filepath.name
        )

        # Extract headers as sections
        self._extract_headers(text, doc_id, filepath.name)

        # Extract definitions
        self._extract_definitions(text, doc_id, filepath.name)

        return self.graph

    def _extract_headers(self, text: str, doc_id: str, source: str) -> None:
        """Extract markdown-style headers."""
        for match in re.finditer(self.PATTERNS["header"], text, re.MULTILINE):
            header_text = match.group(1).strip()
            if len(header_text) > 3:
                header_id = self.graph.add_node(
                    header_text, header_text, "section", header_text[:100], source
                )
                self.graph.add_edge(doc_id, header_id, "contains")

    def _extract_definitions(self, text: str, doc_id: str, source: str) -> None:
        """Extract term definitions."""
        for match in re.finditer(self.PATTERNS["definition"], text):
            term = match.group(1).strip().title()
            definition = match.group(2).strip()[:100]
            if 2 < len(term) < 40:
                term_id = self.graph.add_node(term, term, "definition", definition, source)
                self.graph.add_edge(doc_id, term_id, "defines")
