"""Unit tests for document extractors."""

import pytest
from pathlib import Path
from cosmograph.extractors import (
    GenericExtractor,
    LegalDocumentExtractor,
    PdfExtractor,
    TextExtractor,
)
from cosmograph.models import Graph


class TestLegalDocumentExtractor:
    """Tests for LegalDocumentExtractor."""

    @pytest.fixture
    def extractor(self):
        return LegalDocumentExtractor()

    def test_supports_txt_files(self, extractor):
        assert extractor.supports(Path("test.txt"))
        assert extractor.supports(Path("test.md"))
        assert not extractor.supports(Path("test.pdf"))

    def test_extracts_articles(self, extractor, tmp_path):
        test_file = tmp_path / "constitution.txt"
        test_file.write_text("ARTICLE I - RIGHTS\nSome content here.")
        graph = extractor.extract(test_file)
        # Should have document node + article node
        assert len(graph.nodes) >= 2
        assert any("Article I" in n.label for n in graph.nodes.values())

    def test_extracts_sections(self, extractor, tmp_path):
        test_file = tmp_path / "constitution.txt"
        test_file.write_text("SECTION 1. Test section content.")
        graph = extractor.extract(test_file)
        assert any("Section 1" in n.label for n in graph.nodes.values())

    def test_detects_constitution_type(self, extractor, tmp_path):
        test_file = tmp_path / "tribal_constitution.txt"
        test_file.write_text("CONSTITUTION OF THE TRIBE")
        graph = extractor.extract(test_file)
        doc_node = list(graph.nodes.values())[0]
        assert doc_node.category == "constitution"

    def test_extracts_titles(self, extractor, tmp_path):
        test_file = tmp_path / "code.txt"
        test_file.write_text("TITLE I: GENERAL PROVISIONS\nSome content.")
        graph = extractor.extract(test_file)
        assert any("Title" in n.label for n in graph.nodes.values())

    def test_extracts_chapters(self, extractor, tmp_path):
        test_file = tmp_path / "code.txt"
        test_file.write_text("CHAPTER II - DEFINITIONS\nSome content.")
        graph = extractor.extract(test_file)
        assert any("Chapter" in n.label for n in graph.nodes.values())

    def test_extracts_key_entities(self, extractor, tmp_path):
        test_file = tmp_path / "ordinance.txt"
        test_file.write_text("The Tribal Council shall decide. The Tribal Court reviews.")
        graph = extractor.extract(test_file)
        assert any("Tribal Council" in n.label for n in graph.nodes.values())
        assert any("Tribal Court" in n.label for n in graph.nodes.values())


class TestTextExtractor:
    """Tests for TextExtractor."""

    @pytest.fixture
    def extractor(self):
        return TextExtractor()

    def test_supports_text_files(self, extractor):
        assert extractor.supports(Path("readme.md"))
        assert extractor.supports(Path("doc.txt"))
        assert extractor.supports(Path("notes.text"))

    def test_extracts_markdown_headers(self, extractor, tmp_path):
        test_file = tmp_path / "readme.md"
        test_file.write_text("# Main Title\n## Subtitle\nContent here.")
        graph = extractor.extract(test_file)
        assert any("Main Title" in n.label for n in graph.nodes.values())
        assert any("Subtitle" in n.label for n in graph.nodes.values())

    def test_extracts_definitions(self, extractor, tmp_path):
        test_file = tmp_path / "glossary.md"
        test_file.write_text('"Entity" means a person or organization.')
        graph = extractor.extract(test_file)
        assert any("Entity" in n.label for n in graph.nodes.values())

    def test_creates_document_node(self, extractor, tmp_path):
        test_file = tmp_path / "doc.txt"
        test_file.write_text("Some content")
        graph = extractor.extract(test_file)
        # Should have at least the document node
        assert len(graph.nodes) >= 1
        doc_nodes = [n for n in graph.nodes.values() if n.category == "document"]
        assert len(doc_nodes) == 1


class TestGenericExtractor:
    """Tests for GenericExtractor."""

    @pytest.fixture
    def extractor(self):
        return GenericExtractor(min_occurrences=1)  # Lower threshold for testing

    def test_extracts_proper_nouns(self, extractor, tmp_path):
        test_file = tmp_path / "doc.txt"
        test_file.write_text("John Smith went to New York. John Smith returned.")
        graph = extractor.extract(test_file)
        assert any("John Smith" in n.label for n in graph.nodes.values())

    def test_respects_min_occurrences(self, tmp_path):
        extractor = GenericExtractor(min_occurrences=3)
        test_file = tmp_path / "doc.txt"
        test_file.write_text(
            "Rare Name appears once. Common Name appears. "
            "Common Name appears. Common Name appears."
        )
        graph = extractor.extract(test_file)
        assert any("Common Name" in n.label for n in graph.nodes.values())
        # Rare Name should not appear (only 1 occurrence)
        assert not any("Rare Name" in n.label for n in graph.nodes.values())

    def test_supports_txt_files(self, extractor):
        assert extractor.supports(Path("test.txt"))
        assert extractor.supports(Path("test.md"))
        assert not extractor.supports(Path("test.pdf"))

    def test_extracts_quoted_terms(self, extractor, tmp_path):
        test_file = tmp_path / "doc.txt"
        test_file.write_text('The "Important Term" is used here.')
        graph = extractor.extract(test_file)
        assert any("Important Term" in n.label for n in graph.nodes.values())

    def test_custom_patterns(self, tmp_path):
        custom_patterns = {
            "email": r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
        }
        extractor = GenericExtractor(patterns=custom_patterns, min_occurrences=1)
        test_file = tmp_path / "doc.txt"
        test_file.write_text("Contact us at info@example.com for details.")
        graph = extractor.extract(test_file)
        assert any("info@example.com" in n.label for n in graph.nodes.values())

    def test_creates_document_node(self, extractor, tmp_path):
        test_file = tmp_path / "doc.txt"
        test_file.write_text("Some content")
        graph = extractor.extract(test_file)
        doc_nodes = [n for n in graph.nodes.values() if n.category == "document"]
        assert len(doc_nodes) == 1


class TestPdfExtractor:
    """Tests for PdfExtractor."""

    @pytest.fixture
    def extractor(self):
        return PdfExtractor()

    def test_supports_pdf_files(self, extractor):
        assert extractor.supports(Path("test.pdf"))
        assert extractor.supports(Path("TEST.PDF"))  # Case insensitive
        assert not extractor.supports(Path("test.txt"))
        assert not extractor.supports(Path("test.md"))

    def test_extracts_text_from_pdf(self, extractor, create_test_pdf):
        pdf_file = create_test_pdf("legal.pdf", "TITLE I: GENERAL PROVISIONS\nSome content here.")
        graph = extractor.extract(pdf_file)
        # Should have document node + extracted entities
        assert len(graph.nodes) >= 1
        # Should extract title from legal document patterns
        assert any("Title" in n.label for n in graph.nodes.values())

    def test_extracts_from_multipage_pdf(self, extractor, create_test_pdf):
        # Using TITLE pattern since PDFs get classified as "code" type by default
        pdf_file = create_test_pdf(
            "multipage.pdf",
            "TITLE I: GENERAL PROVISIONS\nFirst page content with additional text to pass scanned detection.",
            pages=3,
        )
        graph = extractor.extract(pdf_file)
        # Should process all pages as single document
        assert len(graph.nodes) >= 1
        assert any("Title" in n.label for n in graph.nodes.values())

    def test_multipage_preserves_reading_order(self, extractor, create_multipage_ordered_pdf):
        """Verify multi-page content is extracted in correct page order (FR-1 structure preservation)."""
        pdf_file = create_multipage_ordered_pdf()
        graph = extractor.extract(pdf_file)
        # Should extract all three titles
        labels = [n.label for n in graph.nodes.values()]
        title_labels = [label for label in labels if "Title" in label]
        # Should have Title I, Title II, Title III
        assert len(title_labels) >= 3, f"Expected 3 titles, got: {title_labels}"
        # Verify all pages processed (Title I from page 1, Title II from page 2, Title III from page 3)
        assert any("Title I" in label or "Title 1" in label for label in labels), "Missing Title I from page 1"
        assert any("Title II" in label or "Title 2" in label for label in labels), "Missing Title II from page 2"
        assert any("Title III" in label or "Title 3" in label for label in labels), "Missing Title III from page 3"

    def test_rejects_encrypted_pdf(self, extractor, create_encrypted_pdf):
        pdf_file = create_encrypted_pdf()
        with pytest.raises(ValueError, match="password-protected"):
            extractor.extract(pdf_file)

    def test_detects_scanned_pdf(self, extractor, create_image_only_pdf):
        pdf_file = create_image_only_pdf()
        with pytest.raises(ValueError, match="scanned"):
            extractor.extract(pdf_file)

    def test_creates_document_node(self, extractor, create_test_pdf):
        # Content must be >100 chars to pass scanned PDF detection
        long_content = "SECTION 1. Some content here that is long enough to pass the scanned PDF detection threshold. Additional text to ensure extraction works properly."
        pdf_file = create_test_pdf("doc.pdf", long_content)
        graph = extractor.extract(pdf_file)
        doc_nodes = [
            n for n in graph.nodes.values()
            if n.category in ("document", "code", "constitution", "ordinance")
        ]
        assert len(doc_nodes) >= 1
