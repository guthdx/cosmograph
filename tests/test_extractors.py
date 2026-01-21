"""Unit tests for document extractors."""

import pytest
from pathlib import Path
from cosmograph.extractors import LegalDocumentExtractor, TextExtractor, GenericExtractor
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
