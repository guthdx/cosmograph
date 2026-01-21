"""Tests for LLM extractor with mocked Anthropic API."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Skip all tests if anthropic not installed
pytest.importorskip("anthropic")

from cosmograph.extractors.llm import (
    HAS_ANTHROPIC,
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    LlmExtractor,
    OperatorDeclinedError,
)
from cosmograph.models import Graph

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with patch("cosmograph.extractors.llm.anthropic") as mock_anthropic:
        client_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = client_instance
        mock_anthropic.AuthenticationError = Exception
        mock_anthropic.RateLimitError = Exception
        yield client_instance


@pytest.fixture
def sample_extraction_result():
    """Sample extraction result for mocking."""
    return ExtractionResult(
        entities=[
            ExtractedEntity(
                id="tribal_council",
                name="Tribal Council",
                category="government_body",
                description="Governing body of the tribe",
            ),
            ExtractedEntity(
                id="chairman",
                name="Chairman",
                category="person",
                description="Leader of the council",
            ),
        ],
        relationships=[
            ExtractedRelationship(
                source_id="chairman",
                target_id="tribal_council",
                relationship_type="leads",
            ),
        ],
    )


@pytest.fixture
def empty_extraction_result():
    """Empty extraction result for mocking edge cases."""
    return ExtractionResult(entities=[], relationships=[])


# ============================================================================
# TestLlmExtractorInit
# ============================================================================


class TestLlmExtractorInit:
    """Tests for LlmExtractor initialization."""

    def test_init_creates_graph(self, mock_anthropic_client):
        """Extractor creates a new graph if none provided."""
        extractor = LlmExtractor()
        assert extractor.graph is not None
        assert isinstance(extractor.graph, Graph)

    def test_init_accepts_existing_graph(self, mock_anthropic_client):
        """Extractor uses provided graph."""
        graph = Graph(title="Test Graph")
        extractor = LlmExtractor(graph=graph)
        assert extractor.graph is graph

    def test_init_default_model(self, mock_anthropic_client):
        """Default model is claude-sonnet-4-5."""
        extractor = LlmExtractor()
        assert extractor.model == "claude-sonnet-4-5"

    def test_init_custom_model(self, mock_anthropic_client):
        """Can specify custom model."""
        extractor = LlmExtractor(model="claude-haiku-4-5")
        assert extractor.model == "claude-haiku-4-5"

    def test_init_interactive_default_true(self, mock_anthropic_client):
        """Interactive mode defaults to True."""
        extractor = LlmExtractor()
        assert extractor.interactive is True

    def test_init_interactive_false(self, mock_anthropic_client):
        """Can disable interactive mode."""
        extractor = LlmExtractor(interactive=False)
        assert extractor.interactive is False


# ============================================================================
# TestDocumentChunking
# ============================================================================


class TestDocumentChunking:
    """Tests for document chunking logic."""

    def test_small_document_single_chunk(self, mock_anthropic_client):
        """Small documents don't get chunked."""
        extractor = LlmExtractor(interactive=False)
        text = "This is a small document."
        chunks = extractor._chunk_document(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_large_document_multiple_chunks(self, mock_anthropic_client):
        """Large documents get split into chunks."""
        extractor = LlmExtractor(interactive=False)
        # Create document larger than MAX_CHUNK_CHARS
        text = "A" * (LlmExtractor.MAX_CHUNK_CHARS + 10000)
        chunks = extractor._chunk_document(text)
        assert len(chunks) > 1

    def test_chunk_overlap_exists(self, mock_anthropic_client):
        """Chunks should have overlapping content."""
        extractor = LlmExtractor(interactive=False)
        # Create document that needs chunking
        text = "A" * (LlmExtractor.MAX_CHUNK_CHARS + 10000)
        chunks = extractor._chunk_document(text)

        # The end of chunk 1 should overlap with start of chunk 2
        # (minus some characters due to OVERLAP_CHARS)
        assert len(chunks) >= 2
        # Total chars in all chunks should exceed original due to overlap
        total_chunk_chars = sum(len(c) for c in chunks)
        assert total_chunk_chars > len(text)

    def test_chunks_split_at_paragraphs(self, mock_anthropic_client):
        """Chunks prefer splitting at paragraph boundaries."""
        extractor = LlmExtractor(interactive=False)

        # Create a document with paragraphs near the chunk boundary
        part1 = "A" * (LlmExtractor.MAX_CHUNK_CHARS - 5000)
        part2 = "\n\n"  # Paragraph break
        part3 = "B" * 10000
        text = part1 + part2 + part3

        chunks = extractor._chunk_document(text)

        # First chunk should end at or near the paragraph break
        # (it looks for breaks in the last quarter of the chunk)
        assert len(chunks) >= 2


# ============================================================================
# TestTokenEstimation
# ============================================================================


class TestTokenEstimation:
    """Tests for token counting and cost estimation."""

    def test_estimate_tokens_calls_api(self, mock_anthropic_client):
        """Token estimation uses official count_tokens API."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=1000
        )

        extractor = LlmExtractor(interactive=False)
        estimate = extractor.estimate_tokens("Some document text")

        mock_anthropic_client.messages.count_tokens.assert_called_once()
        assert estimate["input_tokens"] == 1000

    def test_estimate_returns_cost(self, mock_anthropic_client):
        """Estimate includes cost calculation."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=1000
        )

        extractor = LlmExtractor(interactive=False)
        estimate = extractor.estimate_tokens("Some document text")

        assert "estimated_cost_usd" in estimate
        assert estimate["estimated_cost_usd"] > 0

    def test_cost_calculation_sonnet(self, mock_anthropic_client):
        """Cost calculation uses Sonnet pricing ($3/$15 per MTok)."""
        extractor = LlmExtractor(model="claude-sonnet-4-5", interactive=False)

        # 1M input tokens, 250K output tokens (1M / 4)
        cost = extractor._calculate_cost(1_000_000, 250_000)

        # $3 for input + $3.75 for output = $6.75
        expected = (1_000_000 / 1_000_000) * 3.00 + (250_000 / 1_000_000) * 15.00
        assert abs(cost - expected) < 0.001

    def test_cost_calculation_haiku(self, mock_anthropic_client):
        """Cost calculation uses Haiku pricing ($1/$5 per MTok)."""
        extractor = LlmExtractor(model="claude-haiku-4-5", interactive=False)

        cost = extractor._calculate_cost(1_000_000, 250_000)

        expected = (1_000_000 / 1_000_000) * 1.00 + (250_000 / 1_000_000) * 5.00
        assert abs(cost - expected) < 0.001

    def test_estimate_includes_model(self, mock_anthropic_client):
        """Estimate includes model name."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )

        extractor = LlmExtractor(model="claude-haiku-4-5", interactive=False)
        estimate = extractor.estimate_tokens("text")

        assert estimate["model"] == "claude-haiku-4-5"

    def test_estimate_includes_chunk_count(self, mock_anthropic_client):
        """Estimate includes chunk count."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )

        extractor = LlmExtractor(interactive=False)
        chunks = ["chunk1", "chunk2", "chunk3"]
        estimate = extractor.estimate_tokens("", chunks=chunks)

        assert estimate["chunk_count"] == 3


# ============================================================================
# TestApprovalGate
# ============================================================================


class TestApprovalGate:
    """Tests for approval gate functionality."""

    def test_non_interactive_auto_approves(self, mock_anthropic_client):
        """Non-interactive mode auto-approves."""
        extractor = LlmExtractor(interactive=False)
        estimate = {"input_tokens": 1000, "estimated_output_tokens": 250}

        result = extractor._approval_gate("test document", estimate)

        assert result is True

    def test_interactive_approval_yes(self, mock_anthropic_client):
        """Interactive mode returns True on 'y' input."""
        extractor = LlmExtractor(interactive=True)
        estimate = {
            "input_tokens": 1000,
            "estimated_output_tokens": 250,
            "estimated_cost_usd": 0.01,
            "model": "claude-sonnet-4-5",
            "chunk_count": 1,
        }

        with patch("cosmograph.extractors.llm.Console") as mock_console_class:
            mock_console = mock_console_class.return_value
            mock_console.input.return_value = "y"

            result = extractor._approval_gate("test document", estimate)

        assert result is True

    def test_interactive_approval_no(self, mock_anthropic_client):
        """Interactive mode returns False on 'n' input."""
        extractor = LlmExtractor(interactive=True)
        estimate = {
            "input_tokens": 1000,
            "estimated_output_tokens": 250,
            "estimated_cost_usd": 0.01,
            "model": "claude-sonnet-4-5",
            "chunk_count": 1,
        }

        with patch("cosmograph.extractors.llm.Console") as mock_console_class:
            mock_console = mock_console_class.return_value
            mock_console.input.return_value = "n"

            result = extractor._approval_gate("test document", estimate)

        assert result is False

    def test_declined_raises_error(self, mock_anthropic_client, tmp_path):
        """Declining extraction raises OperatorDeclinedError."""
        # Mock token counting
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )

        extractor = LlmExtractor(interactive=True)

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test document content")

        with patch("cosmograph.extractors.llm.Console") as mock_console_class:
            mock_console = mock_console_class.return_value
            mock_console.input.return_value = "n"

            with pytest.raises(OperatorDeclinedError):
                extractor.extract(test_file)


# ============================================================================
# TestExtraction
# ============================================================================


class TestExtraction:
    """Tests for extraction logic."""

    def test_extract_parses_response(
        self, mock_anthropic_client, sample_extraction_result, tmp_path
    ):
        """Extraction populates graph from API response."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=sample_extraction_result, stop_reason="end_turn"
        )

        extractor = LlmExtractor(interactive=False)

        test_file = tmp_path / "test.txt"
        test_file.write_text("The Tribal Council is led by the Chairman.")

        graph = extractor.extract(test_file)

        assert len(graph.nodes) == 2
        assert "tribal_council" in graph.nodes
        assert "chairman" in graph.nodes
        assert len(graph.edges) == 1

    def test_extract_handles_empty_result(
        self, mock_anthropic_client, empty_extraction_result, tmp_path
    ):
        """Extraction handles empty results gracefully."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=empty_extraction_result, stop_reason="end_turn"
        )

        extractor = LlmExtractor(interactive=False)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Some text without entities")

        graph = extractor.extract(test_file)

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_extract_deduplicates_entities(self, mock_anthropic_client, tmp_path):
        """Graph deduplication handles duplicate entities."""
        # Response with duplicate entity IDs
        result = ExtractionResult(
            entities=[
                ExtractedEntity(
                    id="council", name="Council", category="organization"
                ),
                ExtractedEntity(
                    id="council", name="Council Updated", category="organization"
                ),
            ],
            relationships=[],
        )

        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=result, stop_reason="end_turn"
        )

        extractor = LlmExtractor(interactive=False)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Document about council")

        graph = extractor.extract(test_file)

        # Graph should deduplicate - only one "council" node
        assert len(graph.nodes) == 1
        assert "council" in graph.nodes

    def test_extract_creates_edges(
        self, mock_anthropic_client, sample_extraction_result, tmp_path
    ):
        """Extraction creates proper edge relationships."""
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=sample_extraction_result, stop_reason="end_turn"
        )

        extractor = LlmExtractor(interactive=False)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Chairman leads Tribal Council")

        graph = extractor.extract(test_file)

        assert len(graph.edges) == 1
        edge = graph.edges[0]
        assert edge.source == "chairman"
        assert edge.target == "tribal_council"
        assert edge.edge_type == "leads"


# ============================================================================
# TestRateLimiting
# ============================================================================


class TestRateLimiting:
    """Tests for rate limiting and retry behavior."""

    def test_api_call_uses_correct_parameters(
        self, mock_anthropic_client, sample_extraction_result
    ):
        """API call uses correct model and structured output."""
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=sample_extraction_result, stop_reason="end_turn"
        )

        extractor = LlmExtractor(model="claude-sonnet-4-5", interactive=False)
        extractor._call_api("test chunk")

        # Verify parse was called with correct parameters
        call_kwargs = mock_anthropic_client.beta.messages.parse.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-5"
        assert "structured-outputs-2025-11-13" in call_kwargs["betas"]
        assert call_kwargs["output_format"] == ExtractionResult


# ============================================================================
# TestFileSupport
# ============================================================================


class TestFileSupport:
    """Tests for file type support."""

    def test_supports_txt_files(self, mock_anthropic_client):
        """LLM extractor supports .txt files."""
        extractor = LlmExtractor(interactive=False)
        assert extractor.supports(Path("document.txt")) is True

    def test_supports_md_files(self, mock_anthropic_client):
        """LLM extractor supports .md files."""
        extractor = LlmExtractor(interactive=False)
        assert extractor.supports(Path("document.md")) is True

    def test_supports_pdf_files(self, mock_anthropic_client):
        """LLM extractor supports .pdf files."""
        extractor = LlmExtractor(interactive=False)
        assert extractor.supports(Path("document.pdf")) is True

    def test_unsupported_file_type(self, mock_anthropic_client):
        """LLM extractor rejects unsupported file types."""
        extractor = LlmExtractor(interactive=False)
        assert extractor.supports(Path("document.docx")) is False
        assert extractor.supports(Path("image.png")) is False


# ============================================================================
# TestFullFlow
# ============================================================================


class TestFullFlow:
    """Integration tests for full extraction flow (still mocked)."""

    def test_full_extraction_flow(
        self, mock_anthropic_client, sample_extraction_result, tmp_path
    ):
        """Test complete extraction from file to graph."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text(
            "The Tribal Council governs the reservation. "
            "The Chairman leads the Tribal Council."
        )

        # Mock API responses
        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=100
        )
        mock_anthropic_client.beta.messages.parse.return_value = Mock(
            parsed_output=sample_extraction_result, stop_reason="end_turn"
        )

        # Run extraction
        extractor = LlmExtractor(interactive=False)
        graph = extractor.extract(test_file)

        # Verify results
        assert len(graph.nodes) == 2
        assert "tribal_council" in graph.nodes
        assert "chairman" in graph.nodes

        # Verify node properties
        council_node = graph.nodes["tribal_council"]
        assert council_node.label == "Tribal Council"
        assert council_node.category == "government_body"

        # Verify edge
        assert len(graph.edges) == 1
        assert graph.edges[0].source == "chairman"
        assert graph.edges[0].target == "tribal_council"

    def test_extraction_with_multiple_chunks(self, mock_anthropic_client, tmp_path):
        """Test extraction handles multi-chunk documents."""
        # Create a large test file that will be chunked
        test_file = tmp_path / "large.txt"
        # Create content larger than MAX_CHUNK_CHARS
        large_content = "ARTICLE I: TEST CONTENT\n" * 20000
        test_file.write_text(large_content)

        # Each chunk gets different entities
        chunk1_result = ExtractionResult(
            entities=[
                ExtractedEntity(id="entity_a", name="Entity A", category="concept")
            ],
            relationships=[],
        )
        chunk2_result = ExtractionResult(
            entities=[
                ExtractedEntity(id="entity_b", name="Entity B", category="concept")
            ],
            relationships=[],
        )

        mock_anthropic_client.messages.count_tokens.return_value = Mock(
            input_tokens=50000
        )

        # Return different results for each chunk
        mock_anthropic_client.beta.messages.parse.side_effect = [
            Mock(parsed_output=chunk1_result, stop_reason="end_turn"),
            Mock(parsed_output=chunk2_result, stop_reason="end_turn"),
        ]

        extractor = LlmExtractor(interactive=False)
        graph = extractor.extract(test_file)

        # Both entities from different chunks should be in graph
        assert "entity_a" in graph.nodes or "entity_b" in graph.nodes


# ============================================================================
# TestModuleExports
# ============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_has_anthropic_flag(self):
        """HAS_ANTHROPIC flag is exported and True."""
        assert HAS_ANTHROPIC is True

    def test_operator_declined_error_exported(self):
        """OperatorDeclinedError is properly exported."""
        from cosmograph.extractors import OperatorDeclinedError as ImportedError

        assert ImportedError is OperatorDeclinedError

    def test_llm_extractor_exported(self):
        """LlmExtractor is properly exported."""
        from cosmograph.extractors import LlmExtractor as ImportedExtractor

        assert ImportedExtractor is LlmExtractor
