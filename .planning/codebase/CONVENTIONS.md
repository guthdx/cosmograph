# Coding Conventions

**Analysis Date:** 2026-01-21

## Naming Patterns

**Files:**
- Lowercase with underscores: `legal.py`, `base.py`, `csv.py`
- Module names match class concepts: `models.py` contains `Node`, `Edge`, `Graph`
- `__init__.py` files provide clean re-exports

**Functions:**
- snake_case for all functions: `add_node()`, `get_stats()`, `read_text()`
- Private methods prefixed with underscore: `_clean_id()`, `_extract_headers()`, `_determine_document_type()`
- CLI commands use bare names: `generate`, `stats`, `serve`

**Variables:**
- snake_case: `source_name`, `doc_id`, `entity_counts`
- Loop variables are descriptive: `filepath`, `node`, `edge`, `match`
- Short names acceptable in tight scopes: `f`, `n`, `e`, `q`

**Types/Classes:**
- PascalCase: `Graph`, `Node`, `Edge`, `BaseExtractor`, `HTMLGenerator`
- Extractor classes end with `Extractor`: `TextExtractor`, `LegalDocumentExtractor`, `GenericExtractor`
- Generator classes end with `Generator`: `HTMLGenerator`, `CSVGenerator`

**Constants:**
- UPPER_SNAKE_CASE: `KEY_ENTITIES`, `CATEGORY_COLORS`, `DEFAULT_PATTERNS`, `PATTERNS`
- Defined as class attributes, not module-level

## Code Style

**Formatting:**
- Tool: Ruff
- Line length: 100 characters (configured in `pyproject.toml`)
- Target version: Python 3.11+

**Linting:**
- Tool: Ruff
- Rules enabled: E (errors), F (pyflakes), I (isort), N (pep8-naming), W (warnings), UP (pyupgrade)
- Type checking: mypy with strict mode

**Configuration Location:**
- All tool config in `pyproject.toml` (no separate config files)

## Import Organization

**Order:**
1. Standard library imports: `csv`, `json`, `re`, `webbrowser`, `http.server`
2. Third-party imports: `typer`, `rich`, `pydantic`
3. Local imports: `from ..models import Graph`, `from .base import BaseExtractor`

**Style:**
- Separate groups with blank lines
- Use relative imports within package: `from .base import BaseExtractor`
- Use `from x import y` style, not `import x`

**Example from `cli.py`:**
```python
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .extractors import GenericExtractor, LegalDocumentExtractor, TextExtractor
from .generators import CSVGenerator, HTMLGenerator
from .models import Graph
```

**Path Aliases:**
- None configured; use relative imports

## Error Handling

**Patterns:**
- CLI uses `typer.Exit(1)` for user-facing errors with `[red]Error:[/red]` formatting
- Warnings use `[yellow]Warning:[/yellow]` prefix
- Broad `Exception` catch for file processing with warning output (non-fatal)

**Example:**
```python
if not input_path.exists():
    console.print(f"[red]Error:[/red] Input path does not exist: {input_path}")
    raise typer.Exit(1)

try:
    extractor_instance.extract(filepath)
except Exception as e:
    console.print(f"[yellow]Warning:[/yellow] Failed to process {filepath.name}: {e}")
```

**File reading:**
- Use `errors="ignore"` for encoding issues: `filepath.read_text(encoding="utf-8", errors="ignore")`

## Logging

**Framework:** Rich console for CLI output

**Patterns:**
- Use `rich.console.Console()` for all output
- Color/style via Rich markup: `[bold cyan]`, `[red]Error:[/red]`, `[green]`
- Progress bars via `rich.progress.Progress` with spinner and text columns
- Tables via `rich.table.Table` for statistics

**No traditional logging** - this is a CLI tool that outputs to terminal only

## Comments

**When to Comment:**
- Docstrings on all public classes and methods
- Brief inline comments for regex patterns explaining what they match
- No redundant comments on obvious code

**Docstring Style:**
- Triple-quoted strings immediately after class/method definition
- Single line for simple methods: `"""Clean text to create valid node ID."""`
- Multi-line for complex methods with parameters not documented

**Example:**
```python
class Node:
    """A node in the knowledge graph."""

def add_node(
    self,
    node_id: str,
    label: str,
    category: str,
    description: str = "",
    source_file: str = "",
) -> str:
    """Add a node, returning its cleaned ID."""
```

## Function Design

**Size:** Functions are focused, typically 10-30 lines. Longer functions (like `_generate_html`) are acceptable for template generation.

**Parameters:**
- Use type hints for all parameters
- Default values for optional parameters: `description: str = ""`
- Use `Optional[T]` for nullable types
- CLI parameters use Typer's `Option()` and `Argument()` decorators

**Return Values:**
- Always type-hinted: `-> str`, `-> Graph`, `-> bool`, `-> dict`
- Return early on validation failures
- Return meaningful values (node IDs, success booleans, file paths)

**Example:**
```python
def add_edge(self, source: str, target: str, edge_type: str) -> bool:
    """Add an edge if both nodes exist and edge is unique."""
    source_id = self._clean_id(source)
    target_id = self._clean_id(target)

    # Skip self-loops
    if source_id == target_id:
        return False

    # Check for duplicates
    for edge in self.edges:
        if edge.source == source_id and edge.target == target_id and edge.edge_type == edge_type:
            return False

    self.edges.append(Edge(source_id, target_id, edge_type))
    return True
```

## Module Design

**Exports:**
- Use `__all__` in `__init__.py` files to define public API
- Re-export classes from submodules at package level

**Example from `extractors/__init__.py`:**
```python
from .base import BaseExtractor
from .text import TextExtractor
from .legal import LegalDocumentExtractor
from .generic import GenericExtractor

__all__ = ["BaseExtractor", "TextExtractor", "LegalDocumentExtractor", "GenericExtractor"]
```

**Barrel Files:**
- Each subpackage (`extractors/`, `generators/`) has an `__init__.py` that re-exports
- Main package `__init__.py` only defines `__version__`

## Data Classes

**Pattern:** Use `@dataclass` from `dataclasses` module (not Pydantic for core models)

**Fields:**
- Required fields first, optional fields with defaults after
- Use `field(default_factory=dict)` for mutable defaults
- Implement `to_dict()` for JSON serialization

**Example:**
```python
@dataclass
class Node:
    """A node in the knowledge graph."""

    id: str
    label: str
    category: str
    description: str = ""
    source_file: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label[:60],
            "category": self.category,
            "description": self.description[:150] if self.description else "",
        }
```

## Inheritance Pattern

**Abstract Base Classes:**
- Use `ABC` from `abc` module
- Mark abstract methods with `@abstractmethod`
- Provide concrete helper methods in base class

**Example:**
```python
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
```

## Regex Patterns

**Storage:** Define as class constants in dict format with descriptive keys

**Example:**
```python
PATTERNS = {
    "header": r"^#{1,6}\s+(.+)$",  # Markdown headers
    "definition": r'"([A-Za-z\s]+)"\s+(?:means|shall mean|is defined as)\s+([^.]+)',
    "reference": r"(?:see|refer to|pursuant to)\s+([A-Za-z\s\d\-]+)",
}
```

## CLI Design

**Framework:** Typer with Rich integration

**Patterns:**
- Main `app = typer.Typer()` with help text
- Commands decorated with `@app.command()`
- Private helper functions prefixed with underscore: `_get_extractor()`, `_print_stats()`
- Exit with `typer.Exit(code)` for clean termination

---

*Convention analysis: 2026-01-21*
