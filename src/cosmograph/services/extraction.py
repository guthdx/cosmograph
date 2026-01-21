"""Framework-agnostic extraction orchestration service."""

from collections.abc import Callable
from pathlib import Path

from ..config import PatternConfig
from ..extractors import (
    HAS_ANTHROPIC,
    BaseExtractor,
    GenericExtractor,
    LegalDocumentExtractor,
    LlmExtractor,
    PdfExtractor,
    TextExtractor,
)
from ..generators import CSVGenerator, HTMLGenerator
from ..models import Graph


class ExtractionService:
    """Framework-agnostic extraction orchestration.

    This service encapsulates the core extraction logic, decoupled from
    CLI/HTTP concerns. Both the CLI and API use this service.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize the extraction service.

        Args:
            output_dir: Optional default output directory for generated files.
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def get_extractor(
        self,
        extractor_type: str,
        graph: Graph,
        config: PatternConfig | None = None,
        interactive: bool = True,
    ) -> BaseExtractor:
        """Get the appropriate extractor based on type.

        Args:
            extractor_type: One of 'auto', 'legal', 'text', 'generic', 'pdf', 'llm'
            graph: The graph to populate
            config: Optional pattern configuration for generic extractor
            interactive: Whether to prompt for confirmation (LLM extractor)

        Returns:
            Configured extractor instance

        Raises:
            ValueError: If extractor_type is 'llm' but anthropic is not installed,
                       or if extractor_type is unknown
        """
        if extractor_type == "legal":
            return LegalDocumentExtractor(graph)
        elif extractor_type == "text":
            return TextExtractor(graph)
        elif extractor_type == "generic":
            if config is not None:
                return GenericExtractor(graph, config=config)
            return GenericExtractor(graph)
        elif extractor_type == "pdf":
            return PdfExtractor(graph)
        elif extractor_type == "llm":
            if not HAS_ANTHROPIC:
                msg = (
                    "LLM extractor requires anthropic package. "
                    "Install with: pip install cosmograph[llm]"
                )
                raise ValueError(msg)
            if LlmExtractor is None:
                raise ValueError("LLM extractor failed to load")
            return LlmExtractor(graph, interactive=interactive)
        elif extractor_type == "auto":
            # Default to legal extractor for auto mode
            return LegalDocumentExtractor(graph)
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")

    def process_files(
        self,
        files: list[Path],
        extractor_type: str,
        title: str,
        pattern_config: PatternConfig | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        interactive: bool = True,
    ) -> Graph:
        """Process files and return a populated graph.

        Args:
            files: List of file paths to process
            extractor_type: Extractor type to use
            title: Title for the graph
            pattern_config: Optional pattern configuration for generic extractor
            progress_callback: Optional callback(current, total) called after each file
            interactive: Whether to prompt for confirmation (LLM extractor)

        Returns:
            Populated Graph instance

        Raises:
            OperatorDeclinedError: If LLM extraction is declined by operator
            ValueError: If extractor is unavailable or unknown
        """
        graph = Graph(title=title)
        extractor = self.get_extractor(
            extractor_type, graph, config=pattern_config, interactive=interactive
        )

        for i, filepath in enumerate(files):
            # OperatorDeclinedError propagates - caller handles
            extractor.extract(filepath)
            if progress_callback:
                progress_callback(i + 1, len(files))

        return graph

    def generate_outputs(
        self,
        graph: Graph,
        output_dir: Path,
        title: str,
        html_only: bool = False,
    ) -> dict[str, Path]:
        """Generate output files from a graph.

        Args:
            graph: The graph to export
            output_dir: Directory for output files
            title: Title for the visualization
            html_only: If True, skip CSV generation

        Returns:
            Dictionary mapping output type to file path:
            - 'html': Path to HTML visualization
            - 'nodes_csv': Path to nodes CSV (if html_only=False)
            - 'edges_csv': Path to edges CSV (if html_only=False)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: dict[str, Path] = {}

        # Generate HTML visualization
        html_gen = HTMLGenerator()
        html_path = html_gen.generate(graph, output_dir / "index.html", title)
        outputs["html"] = html_path

        # Generate CSVs unless html_only
        if not html_only:
            csv_gen = CSVGenerator()
            nodes_path, edges_path = csv_gen.generate(graph, output_dir)
            outputs["nodes_csv"] = nodes_path
            outputs["edges_csv"] = edges_path

        return outputs
