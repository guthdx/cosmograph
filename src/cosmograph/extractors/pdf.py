"""PDF document extractor using PyMuPDF."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pymupdf

from ..models import Graph
from .base import BaseExtractor
from .legal import LegalDocumentExtractor

if TYPE_CHECKING:
    from pymupdf import Document


class PdfExtractor(BaseExtractor):
    """Extract entities from PDF documents via LegalDocumentExtractor delegation."""

    def supports(self, filepath: Path) -> bool:
        """Check if this extractor supports the given file type."""
        return filepath.suffix.lower() == ".pdf"

    def extract(self, filepath: Path) -> Graph:
        """Extract entities from a PDF document via LegalDocumentExtractor.

        Opens the PDF, extracts text from all pages in reading order,
        writes to a temp file, and delegates entity extraction to
        LegalDocumentExtractor.

        Args:
            filepath: Path to the PDF file.

        Returns:
            Graph containing extracted entities and relationships.

        Raises:
            ValueError: If PDF is password-protected or appears to be scanned.
        """
        doc: Document | None = None
        try:
            doc = pymupdf.open(filepath)

            # Check for encrypted PDF
            if doc.needs_pass:
                raise ValueError(f"PDF is password-protected: {filepath.name}")

            # Extract text from all pages with reading order preserved
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text(sort=True))
            full_text = "\n".join(text_parts)

            # Check for scanned PDF (no extractable text)
            if self._is_likely_scanned(doc, full_text):
                raise ValueError(
                    f"PDF appears to be scanned (no extractable text): {filepath.name}"
                )

            # Delegate to LegalDocumentExtractor via temp file
            # LegalDocumentExtractor.extract() expects a filepath, not raw text
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix=filepath.stem + "_",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(full_text)
                tmp_path = Path(tmp.name)

            try:
                # Use same graph instance for continuity
                legal_extractor = LegalDocumentExtractor(self.graph)
                return legal_extractor.extract(tmp_path)
            finally:
                # Clean up temp file
                tmp_path.unlink(missing_ok=True)

        finally:
            if doc:
                doc.close()

    def _is_likely_scanned(self, doc: Document, text: str) -> bool:
        """Detect if PDF is likely a scanned document (image-only).

        Uses heuristics based on:
        - Amount of extractable text
        - Presence of large images with minimal text per page

        Args:
            doc: The PyMuPDF Document object.
            text: The full extracted text from all pages.

        Returns:
            True if the PDF appears to be scanned (no extractable text).
        """
        # If we have substantial text, it's not scanned
        if len(text.strip()) > 100:
            return False

        # Check for pages with images but minimal text
        for page in doc:
            # Get image count on page
            images = page.get_images()
            page_text = page.get_text().strip()
            # Full-page image with < 50 chars suggests scanned
            if images and len(page_text) < 50:
                return True

        # Very little text overall suggests scanned
        return len(text.strip()) < 20
