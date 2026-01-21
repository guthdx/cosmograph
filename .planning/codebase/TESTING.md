# Testing Patterns

**Analysis Date:** 2026-01-21

## Test Framework

**Runner:**
- pytest 7.0.0+
- Config: `pyproject.toml` (section `[tool.pytest.ini_options]`)

**Assertion Library:**
- pytest built-in assertions

**Coverage:**
- pytest-cov 4.0.0+

**Run Commands:**
```bash
pytest                                    # Run all tests
pytest tests/test_extractors.py -v        # Run specific file verbose
pytest --cov=src/cosmograph               # Run with coverage
pytest --cov=src/cosmograph --cov-report=html  # Coverage with HTML report
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root
- NOT co-located with source code

**Naming:**
- Test files: `test_*.py` (standard pytest discovery)
- Test functions: `test_*`

**Structure:**
```
cosmograph/
├── src/cosmograph/        # Source code
│   ├── models.py
│   ├── extractors/
│   └── generators/
└── tests/                 # Tests separate from source
    ├── __init__.py        # Empty, marks as package
    └── test_*.py          # Test modules
```

**Configuration in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Test Structure

**Current State:**
The `tests/` directory contains only `__init__.py` with a docstring. No test implementations exist yet.

**Recommended Suite Organization (based on codebase patterns):**
```python
"""Tests for Cosmograph models."""

import pytest
from cosmograph.models import Graph, Node, Edge


class TestGraph:
    """Tests for the Graph class."""

    def test_add_node_creates_node(self):
        """Test that add_node creates a new node."""
        graph = Graph()
        node_id = graph.add_node("test-node", "Test Node", "category")
        assert node_id in graph.nodes
        assert graph.nodes[node_id].label == "Test Node"

    def test_add_node_deduplicates(self):
        """Test that adding same node twice doesn't create duplicates."""
        graph = Graph()
        id1 = graph.add_node("same-id", "First", "category")
        id2 = graph.add_node("same-id", "Second", "category")
        assert id1 == id2
        assert len(graph.nodes) == 1

    def test_add_edge_prevents_self_loops(self):
        """Test that self-referential edges are rejected."""
        graph = Graph()
        graph.add_node("node1", "Node 1", "category")
        result = graph.add_edge("node1", "node1", "relates")
        assert result is False


class TestExtractors:
    """Tests for extractor classes."""

    def test_legal_extractor_supports_txt(self):
        """Test that LegalDocumentExtractor supports .txt files."""
        from pathlib import Path
        from cosmograph.extractors import LegalDocumentExtractor

        extractor = LegalDocumentExtractor()
        assert extractor.supports(Path("document.txt")) is True
        assert extractor.supports(Path("document.pdf")) is False
```

**Patterns to Follow:**
- Group related tests in classes (`TestGraph`, `TestExtractors`)
- Use descriptive method names explaining what is tested
- One assertion per test when practical
- Use fixtures for repeated setup

## Mocking

**Framework:** pytest built-in or unittest.mock

**Recommended Patterns:**
```python
from unittest.mock import Mock, patch
from pathlib import Path

def test_extractor_reads_file(tmp_path):
    """Test that extractor reads file content."""
    # Create temp file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")

    from cosmograph.extractors import TextExtractor
    extractor = TextExtractor()
    text = extractor.read_text(test_file)
    assert text == "Test content"


@patch('cosmograph.cli.webbrowser.open')
def test_generate_opens_browser(mock_open, tmp_path):
    """Test that generate opens browser when flag is set."""
    # ... test implementation
    mock_open.assert_called_once()
```

**What to Mock:**
- File system operations when not testing actual file handling
- External dependencies (webbrowser, http server)
- Time-dependent operations

**What NOT to Mock:**
- Core business logic (Graph, Node, Edge operations)
- Extraction logic - use actual test files
- Data transformations

## Fixtures and Factories

**Recommended Test Data Patterns:**
```python
import pytest
from cosmograph.models import Graph, Node


@pytest.fixture
def empty_graph():
    """Provide an empty graph for testing."""
    return Graph(title="Test Graph")


@pytest.fixture
def sample_graph():
    """Provide a graph with sample data."""
    graph = Graph(title="Sample Graph")
    graph.add_node("doc1", "Document 1", "document", "Test document")
    graph.add_node("sec1", "Section 1", "section", "First section")
    graph.add_edge("doc1", "sec1", "contains")
    return graph


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for extraction tests."""
    filepath = tmp_path / "sample.txt"
    filepath.write_text('''# Header One

"Term" means something specific.

## Header Two

More content here.
''')
    return filepath
```

**Location:**
- Simple fixtures: In test files
- Shared fixtures: In `tests/conftest.py`

## Coverage

**Requirements:** Not enforced (no minimum threshold configured)

**View Coverage:**
```bash
# Terminal output
pytest --cov=src/cosmograph --cov-report=term-missing

# HTML report
pytest --cov=src/cosmograph --cov-report=html
# Opens htmlcov/index.html
```

**Target Areas for Coverage:**
- `models.py`: Graph operations, ID cleaning, deduplication logic
- `extractors/*.py`: Pattern matching, entity extraction
- `generators/*.py`: Output generation, JSON serialization
- `cli.py`: Command handling, error cases

## Test Types

**Unit Tests:**
- Test individual classes and methods in isolation
- Focus on: `Graph`, `Node`, `Edge`, extractors, generators
- Use temporary files for file-based tests

**Integration Tests:**
- Test extractor + graph + generator pipeline
- Test CLI commands end-to-end
- Verify output files are created correctly

**E2E Tests:**
- Use Typer's `CliRunner` for CLI testing
- Not currently implemented

**Example CLI Test:**
```python
from typer.testing import CliRunner
from cosmograph.cli import app

runner = CliRunner()

def test_version_flag():
    """Test --version flag outputs version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Cosmograph" in result.output

def test_generate_missing_path():
    """Test generate with non-existent path fails."""
    result = runner.invoke(app, ["generate", "/nonexistent/path"])
    assert result.exit_code == 1
    assert "Error" in result.output
```

## Common Patterns

**Async Testing:**
- Not applicable (codebase is synchronous)

**Error Testing:**
```python
def test_add_edge_returns_false_for_missing_nodes():
    """Test that adding edge with missing nodes fails gracefully."""
    graph = Graph()
    # No nodes added
    result = graph.add_edge("missing1", "missing2", "relates")
    # Current implementation adds edge anyway - this tests current behavior
    assert result is True  # Note: may want to change this behavior

def test_generate_nonexistent_path_exits(runner, tmp_path):
    """Test that generate with non-existent path exits with error."""
    result = runner.invoke(app, ["generate", str(tmp_path / "nonexistent")])
    assert result.exit_code == 1
```

**Temporary Files:**
```python
def test_csv_generator_creates_files(tmp_path):
    """Test CSV generator creates expected files."""
    from cosmograph.generators import CSVGenerator
    from cosmograph.models import Graph

    graph = Graph()
    graph.add_node("n1", "Node 1", "category")

    generator = CSVGenerator()
    nodes_file, edges_file = generator.generate(graph, tmp_path)

    assert nodes_file.exists()
    assert edges_file.exists()
    assert nodes_file.name == "graph_nodes.csv"
    assert edges_file.name == "graph_data.csv"
```

## Test Data

**Sample Documents:**
Create test fixtures in `tests/fixtures/` (recommended):
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── fixtures/
│   ├── sample_legal.txt
│   ├── sample_ordinance.txt
│   └── sample_constitution.txt
├── test_models.py
├── test_extractors.py
├── test_generators.py
└── test_cli.py
```

**Fixture Content Example:**
```text
# tests/fixtures/sample_constitution.txt
ARTICLE I — NAME AND TERRITORY

SECTION 1. The name of this government shall be the Test Tribe.

SECTION 2. The territory shall include all lands within the boundaries.
```

## Gaps and Recommendations

**Current Gaps:**
- No test implementations exist (only empty `tests/__init__.py`)
- No fixtures directory
- No conftest.py for shared fixtures
- No test coverage baseline established

**Priority Tests to Add:**
1. `test_models.py` - Graph, Node, Edge operations
2. `test_extractors.py` - Each extractor with sample files
3. `test_generators.py` - HTML and CSV output verification
4. `test_cli.py` - Command invocation and error handling

**Recommended conftest.py:**
```python
"""Shared pytest fixtures for Cosmograph tests."""

import pytest
from pathlib import Path
from cosmograph.models import Graph


@pytest.fixture
def empty_graph():
    """Empty graph for testing."""
    return Graph()


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"
```

---

*Testing analysis: 2026-01-21*
