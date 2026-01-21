# Phase 1: Foundation Cleanup - Research

**Researched:** 2026-01-21
**Domain:** Python testing, template extraction, regex optimization, data structures
**Confidence:** HIGH

## Summary

This research covers the technical decisions needed to implement Phase 1: Foundation Cleanup. The phase addresses technical debt in the Cosmograph codebase by adding tests, moving inline HTML to Jinja2 templates, fixing import locations, pre-compiling regex patterns, and improving edge deduplication performance.

The codebase is already well-structured with clear separation of concerns (extractors, generators, models). The refactoring tasks are straightforward because the existing patterns are correct - they just need optimization or extraction.

**Primary recommendation:** Implement changes incrementally, keeping CLI functional at each step. Start with tests for models.py, then fix the easy issues (import location, regex compilation), then tackle the larger refactor (Jinja2 template extraction).

## Standard Stack

The established tools already in use or declared as dependencies.

### Core (Already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 | Test framework | Standard Python testing, already configured in pyproject.toml |
| pytest-cov | >=4.0.0 | Coverage reporting | Standard pytest coverage plugin, already declared |
| jinja2 | >=3.1.0 | Template engine | Already declared as dependency but unused |
| ruff | >=0.1.0 | Linting/formatting | Already configured, handles import ordering |
| mypy | >=1.0.0 | Type checking | Already configured with strict mode |

### Supporting (For This Phase)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typer.testing.CliRunner | bundled | CLI testing | End-to-end command testing |
| unittest.mock | stdlib | Mocking | File system, browser operations |
| pathlib.Path | stdlib | File operations | Already used throughout codebase |

### Dependencies to Remove

| Library | Reason | Action |
|---------|--------|--------|
| pydantic>=2.0.0 | Unused - models use dataclasses | Remove from dependencies |
| pymupdf>=1.23.0 | Unused - PDF support not implemented | Move to optional `[pdf]` group or remove |

**Installation:** No new dependencies needed. All required packages already declared.

## Architecture Patterns

### Recommended Test Structure

```
tests/
├── __init__.py              # Exists (empty docstring only)
├── conftest.py              # NEW: Shared fixtures
├── fixtures/                # NEW: Sample test documents
│   ├── sample_constitution.txt
│   ├── sample_ordinance.txt
│   └── sample_code.txt
├── test_models.py           # NEW: Graph, Node, Edge tests
├── test_extractors.py       # NEW: Extractor tests
├── test_generators.py       # NEW: Generator tests
└── test_cli.py              # NEW: CLI command tests
```

### Pattern 1: Pytest Fixtures for Graph Testing

**What:** Use function-scoped fixtures for fresh graph instances, shared fixtures in conftest.py
**When to use:** All model and extractor tests
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/how-to/fixtures.html
import pytest
from cosmograph.models import Graph

@pytest.fixture
def empty_graph():
    """Fresh empty graph for each test."""
    return Graph(title="Test Graph")

@pytest.fixture
def graph_with_nodes():
    """Graph with sample nodes for edge testing."""
    graph = Graph(title="Test Graph")
    graph.add_node("node1", "Node 1", "category")
    graph.add_node("node2", "Node 2", "category")
    return graph

def test_add_node_returns_clean_id(empty_graph):
    node_id = empty_graph.add_node("Test Node!", "Test Node", "category")
    assert node_id == "Test Node"  # Cleaned ID without punctuation
```

### Pattern 2: tmp_path for File-Based Tests

**What:** Use pytest's tmp_path fixture for temporary files in extractor/generator tests
**When to use:** Testing file I/O operations
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
def test_legal_extractor_reads_file(tmp_path):
    """Test extractor processes file correctly."""
    test_file = tmp_path / "constitution.txt"
    test_file.write_text("ARTICLE I - TEST\nSECTION 1. Content")

    from cosmograph.extractors import LegalDocumentExtractor
    extractor = LegalDocumentExtractor()
    graph = extractor.extract(test_file)

    assert len(graph.nodes) > 0
```

### Pattern 3: Jinja2 PackageLoader for Templates

**What:** Load templates from package using PackageLoader (not FileSystemLoader)
**When to use:** When templates are part of an installed package
**Example:**
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/#loaders
from jinja2 import Environment, PackageLoader

# Load from src/cosmograph/templates/
env = Environment(
    loader=PackageLoader("cosmograph", "templates"),
    autoescape=True  # Prevent XSS
)
template = env.get_template("visualization.html")
html = template.render(
    title=title,
    nodes_json=nodes_json,
    edges_json=edges_json,
    colors_json=colors_json,
    stats=stats
)
```

### Pattern 4: Pre-compiled Regex as Class Attributes

**What:** Compile regex patterns once at class definition time
**When to use:** Any class with regex patterns used repeatedly
**Example:**
```python
# Source: https://docs.python.org/3/library/re.html
import re

class LegalDocumentExtractor(BaseExtractor):
    # Pre-compile patterns as class attributes
    ARTICLE_PATTERN = re.compile(r"ARTICLE\s+([IVX]+)[—\-\s]+([A-Z\s]+)")
    SECTION_PATTERN = re.compile(r"(?:SECTION|SEC\.?)\s+(\d+)\.")
    DEFINITION_PATTERN = re.compile(
        r'"([A-Za-z\s]+)"\s+(?:means|shall mean|is defined as)\s+([^.]+)'
    )

    def _extract_constitution(self, text: str, doc_id: str, source: str) -> None:
        # Use pre-compiled patterns
        for match in self.ARTICLE_PATTERN.finditer(text):
            # ... process match
```

### Pattern 5: Set-Based Edge Deduplication

**What:** Use a set of tuples for O(1) edge existence checking
**When to use:** Graph.add_edge() for duplicate detection
**Example:**
```python
# Source: https://realpython.com/ref/builtin-types/frozenset/
@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _edge_keys: set[tuple[str, str, str]] = field(default_factory=set, repr=False)

    def add_edge(self, source: str, target: str, edge_type: str) -> bool:
        source_id = self._clean_id(source)
        target_id = self._clean_id(target)

        if source_id == target_id:
            return False

        edge_key = (source_id, target_id, edge_type)
        if edge_key in self._edge_keys:  # O(1) lookup
            return False

        self._edge_keys.add(edge_key)
        self.edges.append(Edge(source_id, target_id, edge_type))
        return True
```

### Anti-Patterns to Avoid

- **Testing implementation details:** Test behavior (add_node returns clean ID), not internals (_clean_id regex)
- **Fixtures with side effects:** Don't modify shared state in fixtures; use function scope by default
- **Over-mocking:** Don't mock Graph or dataclasses - they're fast enough to use directly
- **Template logic:** Keep business logic in Python, only presentation in Jinja2 templates

## Don't Hand-Roll

Problems that look simple but have existing solutions.

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporary test files | Manual file creation/cleanup | pytest `tmp_path` fixture | Automatic cleanup, unique per test |
| Test data sharing | Copying setup code | pytest conftest.py fixtures | DRY, automatic injection |
| HTML escaping | Manual string escaping | Jinja2 autoescape | Prevents XSS, handles all cases |
| Template loading | Manual file path handling | PackageLoader | Works with installed packages |
| Regex compilation | Module-level re.compile | Class-attribute re.compile | Encapsulation, clear ownership |

**Key insight:** pytest provides excellent infrastructure for testing. Use its fixtures (tmp_path, conftest.py) rather than building custom test helpers.

## Common Pitfalls

### Pitfall 1: Breaking CLI During Refactoring

**What goes wrong:** Refactoring generators or extractors without testing CLI end-to-end breaks user-facing functionality
**Why it happens:** Unit tests pass but integration points fail
**How to avoid:** Add CLI smoke test first using CliRunner, run it after each change
**Warning signs:** Imports fail, missing template files, changed signatures

### Pitfall 2: Jinja2 Double-Brace Confusion

**What goes wrong:** JavaScript/CSS code in Jinja2 templates has `{{` which Jinja interprets as variable start
**Why it happens:** The current HTML has D3.js code with `{{` used for both Python f-string escaping AND JavaScript template literals
**How to avoid:** Use `{% raw %}...{% endraw %}` blocks around JavaScript, or escape as `{{ '{{' }}`
**Warning signs:** Jinja2 TemplateSyntaxError, undefined variable errors in template

### Pitfall 3: Regex Pattern Order Matters

**What goes wrong:** Moving regex compilation changes when errors surface (from runtime to import time)
**Why it happens:** Invalid patterns now fail at class definition, not during extract()
**How to avoid:** Verify all patterns compile before committing; add unit tests for pattern validity
**Warning signs:** ImportError or re.error during `from cosmograph.extractors import ...`

### Pitfall 4: Edge Set and List Synchronization

**What goes wrong:** The `_edge_keys` set and `edges` list get out of sync
**Why it happens:** Only adding to list in add_edge() but forgetting edge deserialization
**How to avoid:** Always modify both together; add test for round-trip (serialize/deserialize)
**Warning signs:** Edge count mismatch, duplicate edges appearing after load

### Pitfall 5: Test Isolation Failures

**What goes wrong:** Tests pass individually but fail when run together
**Why it happens:** Module-level state, shared fixtures that mutate
**How to avoid:** Use function-scoped fixtures (default), create fresh Graph per test
**Warning signs:** Random test failures, order-dependent results

### Pitfall 6: Missing __init__.py Entry for Templates

**What goes wrong:** PackageLoader can't find templates after installing package
**Why it happens:** Package data not included in wheel/sdist
**How to avoid:** Add template files to pyproject.toml package data, or ensure `templates/__init__.py` exists
**Warning signs:** Works in dev, fails after `pip install`

## Code Examples

Verified patterns for this refactoring phase.

### Test for Graph._clean_id()

```python
# tests/test_models.py
import pytest
from cosmograph.models import Graph

class TestGraphCleanId:
    """Tests for ID cleaning/normalization."""

    def test_removes_special_characters(self):
        graph = Graph()
        result = graph._clean_id("Test!@#$Node")
        assert result == "TestNode"

    def test_collapses_whitespace(self):
        graph = Graph()
        result = graph._clean_id("Test   Node   Here")
        assert result == "Test Node Here"

    def test_truncates_to_100_chars(self):
        graph = Graph()
        long_input = "A" * 150
        result = graph._clean_id(long_input)
        assert len(result) == 100

    def test_handles_empty_string(self):
        graph = Graph()
        result = graph._clean_id("")
        assert result == ""
```

### Test for add_edge Deduplication

```python
# tests/test_models.py
class TestGraphAddEdge:
    """Tests for edge addition and deduplication."""

    @pytest.fixture
    def graph_with_nodes(self):
        graph = Graph()
        graph.add_node("node1", "Node 1", "category")
        graph.add_node("node2", "Node 2", "category")
        graph.add_node("node3", "Node 3", "category")
        return graph

    def test_adds_edge_successfully(self, graph_with_nodes):
        result = graph_with_nodes.add_edge("node1", "node2", "relates")
        assert result is True
        assert len(graph_with_nodes.edges) == 1

    def test_prevents_duplicate_edges(self, graph_with_nodes):
        graph_with_nodes.add_edge("node1", "node2", "relates")
        result = graph_with_nodes.add_edge("node1", "node2", "relates")
        assert result is False
        assert len(graph_with_nodes.edges) == 1

    def test_allows_different_edge_types(self, graph_with_nodes):
        graph_with_nodes.add_edge("node1", "node2", "relates")
        result = graph_with_nodes.add_edge("node1", "node2", "contains")
        assert result is True
        assert len(graph_with_nodes.edges) == 2

    def test_prevents_self_loops(self, graph_with_nodes):
        result = graph_with_nodes.add_edge("node1", "node1", "relates")
        assert result is False
```

### Jinja2 Template Structure

```html
{# src/cosmograph/templates/visualization.html #}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        {# ... rest of CSS ... #}
    </style>
</head>
<body>
    <div id="container">
        {# ... HTML structure ... #}
    </div>
    <script>
        {% raw %}
        const nodes = {{ nodes_json|safe }};
        const links = {{ edges_json|safe }};
        const categoryColors = {{ colors_json|safe }};

        // D3.js code with {{ }} template literals preserved
        node.on('mouseover', (e, d) => {
            tooltip.innerHTML = '<strong>' + d.label + '</strong>';
            // ...
        });
        {% endraw %}
    </script>
</body>
</html>
```

Note: Inside `{% raw %}` blocks, `{{ variable|safe }}` Jinja syntax still works. The raw block only affects literal `{{` that appear in JavaScript code.

### HTMLGenerator with Jinja2

```python
# src/cosmograph/generators/html.py
import json
from pathlib import Path

from jinja2 import Environment, PackageLoader

from ..models import Graph


class HTMLGenerator:
    """Generate interactive HTML visualization from a knowledge graph."""

    CATEGORY_COLORS = {
        # ... existing colors ...
    }

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("cosmograph", "templates"),
            autoescape=True
        )

    def generate(self, graph: Graph, output_path: Path, title: str = None) -> Path:
        """Generate an interactive HTML visualization."""
        title = title or graph.title
        template = self.env.get_template("visualization.html")

        html = template.render(
            title=title,
            nodes_json=json.dumps([n.to_dict() for n in graph.nodes.values()]),
            edges_json=json.dumps([e.to_dict() for e in graph.edges]),
            colors_json=json.dumps(self.CATEGORY_COLORS),
            stats=graph.get_stats()
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path
```

### Pre-compiled Regex in Extractor

```python
# src/cosmograph/extractors/legal.py
import re
from pathlib import Path
from typing import Optional

from ..models import Graph
from .base import BaseExtractor


class LegalDocumentExtractor(BaseExtractor):
    """Extract entities from legal documents."""

    # Pre-compiled patterns as class attributes
    _ARTICLE_PATTERN = re.compile(r"ARTICLE\s+([IVX]+)[—\-\s]+([A-Z\s]+)")
    _SECTION_PATTERN = re.compile(r"(?:SECTION|SEC\.?)\s+(\d+)\.")
    _ORDINANCE_SECTION_PATTERN = re.compile(r"Section\s+(\d+)[.:\s]+([A-Za-z\s]+)")
    _TITLE_PATTERN = re.compile(r"TITLE\s+([IVXLC\d]+)[:\s—\-]+([A-Z\s]+)")
    _CHAPTER_PATTERN = re.compile(r"CHAPTER\s+([IVXLC\d]+)[,:\s—\-]+([A-Z\s]+)")
    _OFFENSE_PATTERN = re.compile(
        r"(?:guilty of|commits?) (?:the offense of |an offense of )?([A-Za-z\s]+?)(?:\s+if|\s+when|\s+shall)",
        re.IGNORECASE
    )
    _DEFINITION_PATTERN = re.compile(
        r'"([A-Za-z\s]+)"\s+(?:means|shall mean|is defined as)\s+([^.]+)'
    )

    def _extract_constitution(self, text: str, doc_id: str, source: str) -> None:
        """Extract from constitutional documents."""
        for match in self._ARTICLE_PATTERN.finditer(text):
            # ... same logic, using pre-compiled pattern
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline HTML string in Python | Jinja2 templates in separate files | Jinja2 3.0+ (2021) | Better separation of concerns, IDE support |
| `re.finditer(pattern, text)` | `compiled_pattern.finditer(text)` | Always better for repeated use | Eliminates cache misses, clearer code |
| `for edge in self.edges` O(n) | `edge_key in self._edge_keys` O(1) | N/A (data structure choice) | Significant speedup for large graphs |
| pydantic for everything | Dataclasses for internal, pydantic for boundaries | 2023-2025 best practice | Better performance for internal models |

**Deprecated/outdated:**
- Using pydantic for internal domain objects (like Graph, Node, Edge) adds unnecessary overhead. Keep dataclasses.
- Python's regex cache (100 patterns) may be exhausted in large codebases; pre-compile critical patterns.

## Open Questions

Things that couldn't be fully resolved.

1. **Python regex cache size**
   - What we know: Python caches "the most recent patterns" automatically
   - What's unclear: Exact cache size not specified in docs (historically was 100)
   - Recommendation: Pre-compile anyway - it's explicit, has no downside, and removes uncertainty

2. **Package data inclusion for templates**
   - What we know: PackageLoader requires templates to be in installed package
   - What's unclear: Whether current pyproject.toml hatch config includes non-Python files
   - Recommendation: Test `pip install -e .` then verify template loading works; may need to add `[tool.hatch.build.targets.wheel.force-include]`

## Sources

### Primary (HIGH confidence)
- [Jinja2 API Documentation - Loaders](https://jinja.palletsprojects.com/en/stable/api/#loaders) - PackageLoader setup
- [Python re module documentation](https://docs.python.org/3/library/re.html) - re.compile() caching behavior
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Fixture patterns
- [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) - Temporary file handling

### Secondary (MEDIUM confidence)
- [Python Testing Best Practices 2025](https://danielsarney.com/blog/python-testing-best-practices-2025-building-reliable-applications/) - Testing patterns verified with pytest docs
- [Real Python frozenset](https://realpython.com/ref/builtin-types/frozenset/) - Set-based deduplication patterns
- [Pydantic vs Dataclasses comparison](https://medium.com/@laurentkubaski/pydantic-vs-data-classes-eaa36e01cd77) - Confirms dataclass usage for internal models

### Tertiary (LOW confidence)
- WebSearch results on regex performance - Claims of 62.5% speedup are anecdotal, specific to one use case

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already declared in pyproject.toml, verified with official docs
- Architecture patterns: HIGH - Standard pytest/Jinja2 patterns from official documentation
- Pitfalls: MEDIUM - Based on codebase analysis and general Python experience
- Performance claims: LOW - Regex/set performance gains are workload-dependent

**Research date:** 2026-01-21
**Valid until:** 2026-03-21 (stable libraries, patterns won't change)
