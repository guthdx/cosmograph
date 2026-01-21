"""LLM-powered entity and relationship extractor using Claude API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from ..models import Graph
from .base import BaseExtractor

# Optional dependency handling for anthropic
HAS_ANTHROPIC = False
anthropic: Any = None
RateLimitError: type[Exception] = Exception

try:
    import anthropic as _anthropic
    from anthropic import RateLimitError as _RateLimitError

    anthropic = _anthropic
    RateLimitError = _RateLimitError
    HAS_ANTHROPIC = True
except ImportError:
    pass

# Optional dependency handling for tenacity
HAS_TENACITY = False
_retry: Any = None
_wait_random_exponential: Any = None
_stop_after_attempt: Any = None
_retry_if_exception_type: Any = None

try:
    from tenacity import (
        retry as _t_retry,
    )
    from tenacity import (
        retry_if_exception_type as _t_retry_if_exception_type,
    )
    from tenacity import (
        stop_after_attempt as _t_stop_after_attempt,
    )
    from tenacity import (
        wait_random_exponential as _t_wait_random_exponential,
    )

    _retry = _t_retry
    _wait_random_exponential = _t_wait_random_exponential
    _stop_after_attempt = _t_stop_after_attempt
    _retry_if_exception_type = _t_retry_if_exception_type
    HAS_TENACITY = True
except ImportError:
    pass


if TYPE_CHECKING:
    from anthropic import Anthropic

logger = logging.getLogger(__name__)


# Pydantic schemas for structured output
class ExtractedEntity(BaseModel):
    """An entity extracted from document text."""

    id: str
    name: str
    category: str
    description: str = ""


class ExtractedRelationship(BaseModel):
    """A relationship between two entities."""

    source_id: str
    target_id: str
    relationship_type: str


class ExtractionResult(BaseModel):
    """Result of entity/relationship extraction from a document chunk."""

    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]


# System prompt for extraction
SYSTEM_PROMPT = """\
You are a knowledge graph extraction expert. \
Extract entities and relationships from the provided document.

For entities, identify:
- People: individuals mentioned by name or role
- Organizations: companies, agencies, departments, committees
- Government bodies: courts, legislatures, executive offices, tribal councils
- Legal concepts: definitions, regulations, rights, obligations, procedures
- Documents: laws, codes, ordinances, contracts, agreements referenced
- Locations: places, jurisdictions, addresses
- Dates: specific dates, time periods, deadlines

For relationships, identify connections like:
- "defines": entity A defines entity B
- "references": entity A references entity B
- "amends": entity A modifies entity B
- "supersedes": entity A replaces entity B
- "establishes": entity A creates entity B
- "governs": entity A has authority over entity B
- "authorizes": entity A grants power to entity B
- "belongs_to": entity A is part of entity B
- "contains": entity A includes entity B
- "reports_to": entity A is subordinate to entity B

Guidelines:
- Be thorough but precise - only extract clearly stated facts
- Use consistent entity IDs (lowercase, underscores for spaces)
- Category values should be lowercase: person, organization, government_body, \
legal_concept, document, location, date
- Relationship types should be lowercase with underscores

Output all extracted entities and relationships in the structured format."""


def _make_retry_decorator() -> Any:
    """Create retry decorator if tenacity is available, otherwise return identity."""
    if HAS_TENACITY and _retry is not None:
        return _retry(
            wait=_wait_random_exponential(min=1, max=60),
            stop=_stop_after_attempt(6),
            retry=_retry_if_exception_type((RateLimitError,)),
        )
    else:
        # Identity decorator when tenacity not installed
        def identity(func: Any) -> Any:
            return func
        return identity


class LlmExtractor(BaseExtractor):
    """Extract entities and relationships using Claude API with structured outputs."""

    # Chunking parameters: ~400K chars = ~100K tokens
    MAX_CHUNK_CHARS = 400_000
    OVERLAP_CHARS = 2_000  # ~500 tokens overlap

    # Pricing per million tokens (as of 2026-01)
    _PRICING: dict[str, dict[str, float]] = {
        "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
        "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
        "claude-opus-4-5": {"input": 5.00, "output": 25.00},
    }

    def __init__(
        self,
        graph: Graph | None = None,
        model: str = "claude-sonnet-4-5",
    ) -> None:
        """Initialize the LLM extractor.

        Args:
            graph: Optional existing graph to add to
            model: Claude model to use for extraction

        Raises:
            ImportError: If anthropic package not installed
            ValueError: If ANTHROPIC_API_KEY not set
        """
        super().__init__(graph)
        self.model = model
        self.client: Anthropic | None = None

        if not HAS_ANTHROPIC:
            raise ImportError(
                "anthropic package required for LLM extraction. "
                "Install with: pip install cosmograph[llm]"
            )

        if anthropic is None:
            raise ImportError("anthropic module failed to load")

        # Create client - uses ANTHROPIC_API_KEY env var
        try:
            self.client = anthropic.Anthropic()
        except anthropic.AuthenticationError as e:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set or invalid. "
                "Set it with: export ANTHROPIC_API_KEY=your-key"
            ) from e

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost in USD.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (actual or estimated)

        Returns:
            Estimated cost in USD
        """
        prices = self._PRICING.get(self.model, self._PRICING["claude-sonnet-4-5"])
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        return input_cost + output_cost

    def estimate_tokens(
        self, text: str, chunks: list[str] | None = None
    ) -> dict[str, Any]:
        """Count tokens and estimate cost before extraction.

        Uses the official token counting API (free call) for accurate counts.

        Args:
            text: Full document text (used for single-document estimation)
            chunks: Optional pre-computed chunks (for chunked document estimation)

        Returns:
            Dict with:
                - input_tokens: int (from API)
                - estimated_output_tokens: int (conservative estimate)
                - estimated_cost_usd: float
                - model: str
                - chunk_count: int
        """
        if self.client is None:
            raise RuntimeError("Anthropic client not initialized")

        # Use chunks if provided, otherwise use full text
        if chunks is None:
            chunks = [text]

        total_input_tokens = 0

        for chunk in chunks:
            # Count tokens using official API (free call)
            count_response = self.client.messages.count_tokens(
                model=self.model,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": chunk}],
            )
            total_input_tokens += count_response.input_tokens

        # Conservative output estimate: extraction typically <25% of input, capped at 4096/chunk
        max_output_per_chunk = 4096
        estimated_output = min(
            total_input_tokens // 4, max_output_per_chunk * len(chunks)
        )

        # Calculate estimated cost
        estimated_cost = self._calculate_cost(total_input_tokens, estimated_output)

        return {
            "input_tokens": total_input_tokens,
            "estimated_output_tokens": estimated_output,
            "estimated_cost_usd": estimated_cost,
            "model": self.model,
            "chunk_count": len(chunks),
        }

    def supports(self, filepath: Path) -> bool:
        """Check if this extractor supports the given file type.

        LLM extractor can process text files (.txt, .md) and PDFs.
        """
        return filepath.suffix.lower() in {".txt", ".md", ".pdf"}

    def extract(self, filepath: Path) -> Graph:
        """Extract entities and relationships from a document.

        Args:
            filepath: Path to document file

        Returns:
            Graph with extracted nodes and edges
        """
        text = self.read_text(filepath)
        source_file = filepath.name

        # Chunk document if necessary
        chunks = self._chunk_document(text)
        logger.info(f"Processing {filepath.name} in {len(chunks)} chunk(s)")

        # Extract from each chunk and merge results
        for i, chunk in enumerate(chunks, 1):
            logger.debug(f"Processing chunk {i}/{len(chunks)}")
            try:
                result = self._extract_chunk(chunk)
                self._parse_result(result, source_file)
            except Exception as e:
                logger.warning(f"Extraction failed for chunk {i}: {e}")
                # Continue with remaining chunks

        return self.graph

    def _chunk_document(self, text: str) -> list[str]:
        """Split document into chunks for processing.

        Uses paragraph boundaries when possible for cleaner splits.
        Includes overlap between chunks for context continuity.

        Args:
            text: Full document text

        Returns:
            List of text chunks
        """
        if len(text) <= self.MAX_CHUNK_CHARS:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.MAX_CHUNK_CHARS

            # Find paragraph boundary for cleaner split
            if end < len(text):
                # Look for paragraph break in last quarter of chunk
                boundary = text.rfind("\n\n", start + (self.MAX_CHUNK_CHARS // 2), end)
                if boundary > start:
                    end = boundary

            chunks.append(text[start:end])

            # Move start with overlap for context continuity
            start = end - self.OVERLAP_CHARS
            if start < 0:
                start = 0

        return chunks

    def _extract_chunk(self, chunk: str) -> ExtractionResult:
        """Extract entities and relationships from a text chunk.

        Args:
            chunk: Text chunk to process

        Returns:
            ExtractionResult with entities and relationships
        """
        response = self._call_api(chunk)

        # Handle potential refusals
        if hasattr(response, "stop_reason") and response.stop_reason == "refusal":
            logger.warning("Claude declined extraction request")
            return ExtractionResult(entities=[], relationships=[])

        # Return parsed output
        if hasattr(response, "parsed_output") and response.parsed_output is not None:
            result = response.parsed_output
            if isinstance(result, ExtractionResult):
                return result

        # Fallback: empty result if parsing failed
        logger.warning("No parsed output in response")
        return ExtractionResult(entities=[], relationships=[])

    def _call_api(self, chunk: str) -> Any:
        """Call Claude API with rate limiting and retries.

        Args:
            chunk: Text to extract from

        Returns:
            API response with parsed output
        """
        if self.client is None:
            raise RuntimeError("Anthropic client not initialized")

        return self._call_api_inner(chunk)

    def _call_api_inner(self, chunk: str) -> Any:
        """Inner API call method that gets wrapped with retry decorator."""
        if self.client is None:
            raise RuntimeError("Anthropic client not initialized")

        response = self.client.beta.messages.parse(
            model=self.model,
            betas=["structured-outputs-2025-11-13"],
            max_tokens=4096,
            output_format=ExtractionResult,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": chunk}],
        )

        return response

    def _parse_result(self, result: ExtractionResult, source_file: str) -> None:
        """Convert extraction result to graph nodes and edges.

        Args:
            result: Extraction result with entities and relationships
            source_file: Source file name for metadata
        """
        # Add nodes for each entity
        for entity in result.entities:
            self.graph.add_node(
                node_id=entity.id,
                label=entity.name,
                category=entity.category,
                description=entity.description,
                source_file=source_file,
            )

        # Add edges for each relationship
        for rel in result.relationships:
            self.graph.add_edge(
                source=rel.source_id,
                target=rel.target_id,
                edge_type=rel.relationship_type,
            )


# Apply retry decorator to the inner method if tenacity is available
LlmExtractor._call_api_inner = _make_retry_decorator()(  # type: ignore[method-assign]
    LlmExtractor._call_api_inner
)
