"""Tests for the ExtractionService class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cosmograph.extractors import (
    GenericExtractor,
    LegalDocumentExtractor,
    PdfExtractor,
    TextExtractor,
)
from cosmograph.models import Graph
from cosmograph.services import ExtractionService


class TestExtractionServiceInit:
    """Tests for ExtractionService initialization."""

    def test_init_without_output_dir(self):
        """Service can be instantiated without output_dir."""
        service = ExtractionService()
        assert service.output_dir is None

    def test_init_with_output_dir(self, tmp_path: Path):
        """Service can be instantiated with output_dir."""
        output_dir = tmp_path / "output"
        service = ExtractionService(output_dir=output_dir)
        assert service.output_dir == output_dir
        assert output_dir.exists()

    def test_init_creates_nested_output_dir(self, tmp_path: Path):
        """Service creates nested output directories."""
        output_dir = tmp_path / "deeply" / "nested" / "output"
        service = ExtractionService(output_dir=output_dir)
        assert service.output_dir == output_dir
        assert output_dir.exists()


class TestGetExtractor:
    """Tests for the get_extractor factory method."""

    @pytest.fixture
    def service(self) -> ExtractionService:
        return ExtractionService()

    @pytest.fixture
    def graph(self) -> Graph:
        return Graph(title="Test Graph")

    def test_get_extractor_legal(self, service: ExtractionService, graph: Graph):
        """Returns LegalDocumentExtractor for 'legal' type."""
        extractor = service.get_extractor("legal", graph)
        assert isinstance(extractor, LegalDocumentExtractor)

    def test_get_extractor_text(self, service: ExtractionService, graph: Graph):
        """Returns TextExtractor for 'text' type."""
        extractor = service.get_extractor("text", graph)
        assert isinstance(extractor, TextExtractor)

    def test_get_extractor_generic(self, service: ExtractionService, graph: Graph):
        """Returns GenericExtractor for 'generic' type."""
        extractor = service.get_extractor("generic", graph)
        assert isinstance(extractor, GenericExtractor)

    def test_get_extractor_pdf(self, service: ExtractionService, graph: Graph):
        """Returns PdfExtractor for 'pdf' type."""
        extractor = service.get_extractor("pdf", graph)
        assert isinstance(extractor, PdfExtractor)

    def test_get_extractor_auto(self, service: ExtractionService, graph: Graph):
        """Returns LegalDocumentExtractor for 'auto' type (default)."""
        extractor = service.get_extractor("auto", graph)
        assert isinstance(extractor, LegalDocumentExtractor)

    def test_get_extractor_unknown_raises_error(
        self, service: ExtractionService, graph: Graph
    ):
        """Raises ValueError for unknown extractor type."""
        with pytest.raises(ValueError, match="Unknown extractor type"):
            service.get_extractor("nonexistent", graph)

    def test_get_extractor_llm_without_anthropic(
        self, service: ExtractionService, graph: Graph
    ):
        """Raises ValueError when anthropic package is not installed."""
        with patch("cosmograph.services.extraction.HAS_ANTHROPIC", False):
            with pytest.raises(ValueError, match="anthropic package"):
                service.get_extractor("llm", graph)

    def test_get_extractor_llm_with_anthropic(
        self, service: ExtractionService, graph: Graph
    ):
        """Returns LlmExtractor when anthropic is available."""
        mock_llm_extractor = MagicMock()
        with (
            patch("cosmograph.services.extraction.HAS_ANTHROPIC", True),
            patch(
                "cosmograph.services.extraction.LlmExtractor",
                return_value=mock_llm_extractor,
            ) as mock_class,
        ):
            extractor = service.get_extractor("llm", graph, interactive=False)
            mock_class.assert_called_once_with(graph, interactive=False)
            assert extractor == mock_llm_extractor


class TestProcessFiles:
    """Tests for the process_files method."""

    @pytest.fixture
    def service(self) -> ExtractionService:
        return ExtractionService()

    def test_process_files_returns_graph(self, service: ExtractionService, tmp_path: Path):
        """process_files returns a Graph with the given title."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("ARTICLE I - TEST\nSection 1. Content.")

        graph = service.process_files(
            files=[test_file],
            extractor_type="legal",
            title="Test Graph",
        )

        assert isinstance(graph, Graph)
        assert graph.title == "Test Graph"

    def test_process_files_with_progress_callback(
        self, service: ExtractionService, tmp_path: Path
    ):
        """Progress callback is called after each file."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"
        for f in [file1, file2, file3]:
            f.write_text("ARTICLE I - CONTENT\nSection 1. Text.")

        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        service.process_files(
            files=[file1, file2, file3],
            extractor_type="legal",
            title="Test",
            progress_callback=progress_callback,
        )

        # Should be called 3 times: (1, 3), (2, 3), (3, 3)
        assert len(callback_calls) == 3
        assert callback_calls[0] == (1, 3)
        assert callback_calls[1] == (2, 3)
        assert callback_calls[2] == (3, 3)

    def test_process_files_without_progress_callback(
        self, service: ExtractionService, tmp_path: Path
    ):
        """process_files works without a progress callback."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("ARTICLE I - TEST")

        # Should not raise
        graph = service.process_files(
            files=[test_file],
            extractor_type="legal",
            title="Test",
            progress_callback=None,
        )
        assert isinstance(graph, Graph)


class TestGenerateOutputs:
    """Tests for the generate_outputs method."""

    @pytest.fixture
    def service(self) -> ExtractionService:
        return ExtractionService()

    @pytest.fixture
    def populated_graph(self) -> Graph:
        """Graph with some nodes and edges."""
        graph = Graph(title="Test Graph")
        graph.add_node("node1", "Node One", "category_a")
        graph.add_node("node2", "Node Two", "category_b")
        graph.add_edge("node1", "node2", "references")
        return graph

    def test_generate_outputs_creates_html(
        self, service: ExtractionService, populated_graph: Graph, tmp_path: Path
    ):
        """generate_outputs creates HTML file."""
        output_dir = tmp_path / "output"
        outputs = service.generate_outputs(
            graph=populated_graph,
            output_dir=output_dir,
            title="Test Visualization",
        )

        assert "html" in outputs
        assert outputs["html"].exists()
        assert outputs["html"].name == "index.html"

    def test_generate_outputs_creates_csv(
        self, service: ExtractionService, populated_graph: Graph, tmp_path: Path
    ):
        """generate_outputs creates CSV files by default."""
        output_dir = tmp_path / "output"
        outputs = service.generate_outputs(
            graph=populated_graph,
            output_dir=output_dir,
            title="Test",
        )

        assert "nodes_csv" in outputs
        assert "edges_csv" in outputs
        assert outputs["nodes_csv"].exists()
        assert outputs["edges_csv"].exists()

    def test_generate_outputs_html_only(
        self, service: ExtractionService, populated_graph: Graph, tmp_path: Path
    ):
        """generate_outputs skips CSV when html_only=True."""
        output_dir = tmp_path / "output"
        outputs = service.generate_outputs(
            graph=populated_graph,
            output_dir=output_dir,
            title="Test",
            html_only=True,
        )

        assert "html" in outputs
        assert "nodes_csv" not in outputs
        assert "edges_csv" not in outputs

    def test_generate_outputs_creates_directory(
        self, service: ExtractionService, populated_graph: Graph, tmp_path: Path
    ):
        """generate_outputs creates output directory if needed."""
        output_dir = tmp_path / "new" / "nested" / "dir"
        outputs = service.generate_outputs(
            graph=populated_graph,
            output_dir=output_dir,
            title="Test",
        )

        assert output_dir.exists()
        assert outputs["html"].parent == output_dir
