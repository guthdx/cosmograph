"""Base extractor interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..models import Graph


class BaseExtractor(ABC):
    """Base class for document extractors."""

    def __init__(self, graph: Optional[Graph] = None):
        self.graph = graph or Graph()

    @abstractmethod
    def extract(self, filepath: Path) -> Graph:
        """Extract entities and relationships from a document."""
        pass

    @abstractmethod
    def supports(self, filepath: Path) -> bool:
        """Check if this extractor supports the given file type."""
        pass

    def read_text(self, filepath: Path) -> str:
        """Read text content from a file."""
        return filepath.read_text(encoding="utf-8", errors="ignore")
