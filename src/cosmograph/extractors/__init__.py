"""Document extractors for building knowledge graphs."""

from .base import BaseExtractor
from .generic import GenericExtractor
from .legal import LegalDocumentExtractor
from .pdf import PdfExtractor
from .text import TextExtractor

# Conditional import for LLM extractor (requires anthropic package)
try:
    from .llm import HAS_ANTHROPIC, LlmExtractor, OperatorDeclinedError
except ImportError:
    HAS_ANTHROPIC = False
    LlmExtractor = None  # type: ignore[assignment, misc]
    OperatorDeclinedError = Exception  # type: ignore[assignment, misc]

__all__ = [
    "BaseExtractor",
    "GenericExtractor",
    "HAS_ANTHROPIC",
    "LegalDocumentExtractor",
    "LlmExtractor",
    "OperatorDeclinedError",
    "PdfExtractor",
    "TextExtractor",
]
