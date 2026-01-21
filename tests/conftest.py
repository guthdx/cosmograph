"""Shared pytest fixtures for cosmograph tests."""

from pathlib import Path

import pytest
import yaml

from cosmograph.models import Edge, Graph, Node


@pytest.fixture
def empty_graph() -> Graph:
    """Fresh Graph instance for each test."""
    return Graph()


@pytest.fixture
def graph_with_nodes() -> Graph:
    """Graph with 3 sample nodes of category 'test'."""
    graph = Graph()
    graph.add_node("node1", "Node One", "test", "First test node")
    graph.add_node("node2", "Node Two", "test", "Second test node")
    graph.add_node("node3", "Node Three", "test", "Third test node")
    return graph


@pytest.fixture
def sample_node() -> Node:
    """Single Node instance for unit tests."""
    return Node(
        id="sample_node",
        label="Sample Node",
        category="test",
        description="A sample node for testing",
        source_file="test.txt",
    )


@pytest.fixture
def sample_edge() -> Edge:
    """Single Edge instance for unit tests."""
    return Edge(
        source="source_node",
        target="target_node",
        edge_type="references",
    )


@pytest.fixture
def create_test_pdf(tmp_path):
    """Factory fixture to create test PDFs with PyMuPDF."""

    def _create(filename: str, content: str, pages: int = 1) -> Path:
        import pymupdf

        filepath = tmp_path / filename
        doc = pymupdf.open()
        for i in range(pages):
            page = doc.new_page()
            # Insert text at top of page
            page.insert_text(
                (72, 72), content if i == 0 else f"Page {i + 1}\n{content}", fontsize=12
            )
        doc.save(str(filepath))
        doc.close()
        return filepath

    return _create


@pytest.fixture
def create_encrypted_pdf(tmp_path):
    """Create an encrypted PDF for testing."""

    def _create(filename: str = "encrypted.pdf") -> Path:
        import pymupdf

        filepath = tmp_path / filename
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Secret content", fontsize=12)
        # Encrypt with user password
        doc.save(str(filepath), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret")
        doc.close()
        return filepath

    return _create


@pytest.fixture
def create_image_only_pdf(tmp_path):
    """Create a PDF with only an image (simulates scanned document)."""

    def _create(filename: str = "scanned.pdf") -> Path:
        import pymupdf

        filepath = tmp_path / filename
        doc = pymupdf.open()
        page = doc.new_page()
        # Create a simple colored rectangle as an image covering the page
        rect = page.rect
        page.draw_rect(rect, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9))
        doc.save(str(filepath))
        doc.close()
        return filepath

    return _create


@pytest.fixture
def create_multipage_ordered_pdf(tmp_path):
    """Create a multi-page PDF with distinct content per page for order verification."""

    def _create(filename: str = "ordered.pdf") -> Path:
        import pymupdf

        filepath = tmp_path / filename
        doc = pymupdf.open()
        # Page 1: Title I content
        page1 = doc.new_page()
        page1.insert_text(
            (72, 72), "TITLE I: FIRST SECTION\nContent from page one.", fontsize=12
        )
        # Page 2: Title II content
        page2 = doc.new_page()
        page2.insert_text(
            (72, 72), "TITLE II: SECOND SECTION\nContent from page two.", fontsize=12
        )
        # Page 3: Title III content
        page3 = doc.new_page()
        page3.insert_text(
            (72, 72), "TITLE III: THIRD SECTION\nContent from page three.", fontsize=12
        )
        doc.save(str(filepath))
        doc.close()
        return filepath

    return _create


@pytest.fixture
def create_pattern_file(tmp_path):
    """Factory fixture to create pattern YAML files for testing."""

    def _create(filename: str, config: dict) -> Path:
        filepath = tmp_path / filename
        with open(filepath, "w") as f:
            yaml.dump(config, f)
        return filepath

    return _create


@pytest.fixture
def valid_pattern_config():
    """Return a valid pattern configuration dict."""
    return {
        "version": "1.0",
        "name": "test-patterns",
        "description": "Test patterns",
        "min_occurrences": 1,
        "entity_patterns": [
            {
                "name": "email",
                "pattern": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                "category": "email",
                "description": "Email addresses",
                "min_length": 5,
            },
            {
                "name": "phone",
                "pattern": r"(\d{3}-\d{3}-\d{4})",
                "category": "phone",
                "description": "US phone numbers",
            },
        ],
        "relationship_triggers": [
            {
                "name": "mentions",
                "source_categories": ["document"],
                "target_categories": ["email", "phone"],
                "proximity": 0,
            }
        ],
    }
