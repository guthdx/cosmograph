# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Cosmograph** is a CLI tool for generating interactive knowledge graph visualizations from documents. It extracts entities and relationships from text files and creates self-contained HTML visualizations using D3.js.

## Build & Development Commands

```bash
# Setup
/opt/local/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run CLI
cosmograph --help
cosmograph generate ./docs/ -t "My Graph"

# Testing
pytest
pytest --cov=src/cosmograph

# Linting
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

## Architecture

```
src/cosmograph/
├── cli.py          # Typer CLI - entry point
├── models.py       # Graph, Node, Edge dataclasses
├── extractors/     # Document processors
│   ├── base.py     # BaseExtractor ABC
│   ├── legal.py    # Legal docs (codes, ordinances)
│   ├── text.py     # Plain text/markdown
│   └── generic.py  # Pattern-based extraction
└── generators/     # Output formats
    ├── html.py     # D3.js visualization
    └── csv.py      # CSV export
```

## Key Design Decisions

1. **Self-contained HTML**: Generated visualization has data embedded, no external fetches required (avoids CORS issues with file:// URLs)

2. **Extractor pattern**: Each extractor inherits from `BaseExtractor` and implements `extract()` and `supports()` methods

3. **Graph model**: Central `Graph` class with `add_node()` and `add_edge()` methods that handle deduplication and ID cleaning

4. **Category colors**: Predefined in `HTMLGenerator.CATEGORY_COLORS` for consistent theming

## Adding New Extractors

1. Create new file in `src/cosmograph/extractors/`
2. Inherit from `BaseExtractor`
3. Implement `supports(filepath)` and `extract(filepath)`
4. Add to `extractors/__init__.py`
5. Add CLI option in `cli.py:_get_extractor()`

Example:
```python
class MyExtractor(BaseExtractor):
    def supports(self, filepath: Path) -> bool:
        return filepath.suffix == ".myext"

    def extract(self, filepath: Path) -> Graph:
        text = self.read_text(filepath)
        # Extract entities, add to self.graph
        return self.graph
```

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_extractors.py -v

# With coverage
pytest --cov=src/cosmograph --cov-report=html
```

## Common Tasks

### Process CRST legal documents
```bash
cosmograph generate "/path/to/CRST Codes" -e legal -t "CRST Legal Framework" -p "*.txt"
```

### Add new category color
Edit `src/cosmograph/generators/html.py`:
```python
CATEGORY_COLORS = {
    # ... existing colors
    "new_category": "#hexcolor",
}
```

## Dependencies

- **typer**: CLI framework
- **rich**: Terminal formatting
- **pydantic**: Data validation
- **pymupdf**: PDF support (future)
- **jinja2**: Template rendering (future)
