# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Cosmograph** is a document-to-knowledge-graph service for Iyeska client work. It extracts entities and relationships from legal codes, policies, and project documents, producing interactive D3.js visualizations.

**Current Version**: v0.1.0 (CLI) → Evolving to v0.2.0 (Web Service)
**Status**: Planning complete, ready for Phase 1 execution

## Iyeska Infrastructure Context

This project follows Iyeska standard stack (see `~/terminal_projects/claude_code/CLAUDE.md`):

| Component | Technology | Notes |
|-----------|------------|-------|
| Backend | FastAPI 0.115+ | v0.2.0 addition |
| Frontend | React + TypeScript + Vite | v0.2.0 addition |
| Python | 3.13 (MacPorts) | `/opt/local/bin/python3.13` |
| Deployment | PM2 on Ubuntu 192.168.11.20 | cosmograph.iyeska.net |
| Dev Proxy | Traefik | cosmograph.localhost |

**Data Sovereignty**: All processing on Iyeska infrastructure. LLM calls require explicit approval.

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

# Run API (v0.2.0+)
uvicorn cosmograph.api.main:app --reload

# Frontend dev (v0.2.0+)
cd frontend && npm run dev
```

## Architecture (Current v0.1)

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

## Architecture (Target v0.2)

```
src/cosmograph/
├── cli.py              # Keep CLI for power users
├── api/                # NEW: FastAPI application
│   ├── main.py         # FastAPI app, routes
│   └── schemas.py      # Pydantic request/response
├── extractors/         # Existing + new
│   ├── base.py
│   ├── legal.py
│   ├── text.py
│   ├── generic.py
│   ├── pdf.py          # NEW: pymupdf-based
│   └── llm.py          # NEW: Claude API
├── config/             # NEW: Pattern configuration
│   └── patterns.yaml   # Custom extraction rules
├── generators/
│   ├── html.py
│   └── csv.py
├── models.py
└── templates/          # Jinja2 templates
    └── graph.html.j2   # Moved from inline string
frontend/               # NEW: React app
├── src/
└── package.json
```

## Key Design Decisions

1. **Self-contained HTML**: Generated visualization embeds all data, no external fetches required
2. **Extractor pattern**: Each extractor inherits `BaseExtractor`, implements `extract()` and `supports()`
3. **Graph model**: Central `Graph` class handles deduplication and ID cleaning
4. **Approval gates**: LLM extraction requires explicit operator confirmation (data sovereignty)
5. **Progressive extraction**: Patterns first, LLM for what patterns miss (cost control)

## Adding New Extractors

1. Create new file in `src/cosmograph/extractors/`
2. Inherit from `BaseExtractor`
3. Implement `supports(filepath)` and `extract(filepath)`
4. Add to `extractors/__init__.py`
5. Add CLI option in `cli.py:_get_extractor()`

```python
class MyExtractor(BaseExtractor):
    def supports(self, filepath: Path) -> bool:
        return filepath.suffix == ".myext"

    def extract(self, filepath: Path) -> Graph:
        text = self.read_text(filepath)
        # Extract entities, add to self.graph
        return self.graph
```

## Common Tasks

### Process legal documents
```bash
cosmograph generate "/path/to/CRST Codes" -e legal -t "CRST Legal Framework" -p "*.txt"
```

### Process PDFs (v0.2.0+)
```bash
cosmograph generate ./contracts/ -e pdf -t "Contract Analysis"
```

### Use LLM extraction (v0.2.0+)
```bash
cosmograph generate ./docs/ -e llm -t "Project Analysis"
# Prompts for confirmation with token estimate before API call
```

### Add new category color
Edit `src/cosmograph/generators/html.py`:
```python
CATEGORY_COLORS = {
    # ... existing colors
    "new_category": "#hexcolor",
}
```

## Development Roadmap

See `.planning/milestones/v0.2.0/ROADMAP.md` for detailed phases:

1. **Phase 1**: Foundation cleanup (tests, tech debt)
2. **Phase 2**: PDF extractor
3. **Phase 3**: Pattern configuration (YAML)
4. **Phase 4**: LLM extractor with approval gate
5. **Phase 5**: FastAPI backend
6. **Phase 6**: React frontend
7. **Phase 7**: Deployment to Iyeska HQ

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_extractors.py -v

# With coverage
pytest --cov=src/cosmograph --cov-report=html
```

## Dependencies

**Core:**
- typer: CLI framework
- rich: Terminal formatting
- pydantic: Data validation

**Document Processing:**
- pymupdf: PDF support
- jinja2: Template rendering

**LLM (optional):**
- anthropic: Claude API (`pip install -e ".[llm]"`)

**Development:**
- pytest, pytest-cov: Testing
- ruff: Linting/formatting
- mypy: Type checking

## Planning Files

- `.planning/PROJECT.md` - Vision, principles, milestones
- `.planning/REQUIREMENTS.md` - v0.2.0 requirements
- `.planning/milestones/v0.2.0/ROADMAP.md` - Phase breakdown
- `.planning/codebase/*.md` - Architecture analysis

## GSD Commands

```bash
/gsd:progress       # Check project status, next action
/gsd:plan-phase     # Plan next phase in detail
/gsd:execute-phase  # Execute planned phase
```
