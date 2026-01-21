# Codebase Structure

**Analysis Date:** 2026-01-21

## Directory Layout

```
cosmograph/
├── src/
│   └── cosmograph/           # Main package
│       ├── __init__.py       # Version and package info
│       ├── cli.py            # Typer CLI commands
│       ├── models.py         # Graph, Node, Edge dataclasses
│       ├── extractors/       # Document extraction strategies
│       │   ├── __init__.py   # Public exports
│       │   ├── base.py       # BaseExtractor ABC
│       │   ├── legal.py      # Legal document extractor
│       │   ├── text.py       # Text/markdown extractor
│       │   └── generic.py    # Pattern-based extractor
│       ├── generators/       # Output format generators
│       │   ├── __init__.py   # Public exports
│       │   ├── html.py       # D3.js visualization
│       │   └── csv.py        # CSV export
│       └── templates/        # HTML templates (placeholder)
│           └── __init__.py
├── tests/                    # Test suite (empty scaffold)
│   └── __init__.py
├── test_output/              # Sample generated output
│   ├── index.html
│   ├── graph_nodes.csv
│   └── graph_data.csv
├── .planning/                # GSD planning documents
├── pyproject.toml            # Project config and dependencies
├── CLAUDE.md                 # Claude Code instructions
├── README.md                 # User documentation
└── .gitignore                # Git ignore patterns
```

## Directory Purposes

**src/cosmograph/:**
- Purpose: Main application package
- Contains: All production Python code
- Key files: `cli.py` (entry point), `models.py` (data structures)

**src/cosmograph/extractors/:**
- Purpose: Strategy implementations for document parsing
- Contains: One file per extractor type
- Key files: `base.py` (interface), `legal.py` (primary extractor)

**src/cosmograph/generators/:**
- Purpose: Output format implementations
- Contains: One file per output format
- Key files: `html.py` (main visualization), `csv.py` (data export)

**src/cosmograph/templates/:**
- Purpose: Reserved for Jinja2 templates (future use)
- Contains: Empty placeholder
- Key files: None currently

**tests/:**
- Purpose: Test suite location
- Contains: Empty scaffold
- Key files: None (tests not yet implemented)

**test_output/:**
- Purpose: Sample generated output for verification
- Contains: Example HTML and CSV files
- Key files: `index.html` (visualization), `graph_nodes.csv`, `graph_data.csv`

## Key File Locations

**Entry Points:**
- `src/cosmograph/cli.py`: CLI application (Typer)
- `src/cosmograph/__init__.py`: Package version

**Configuration:**
- `pyproject.toml`: Dependencies, build config, tool settings
- `.gitignore`: Version control exclusions

**Core Logic:**
- `src/cosmograph/models.py`: Graph data structures
- `src/cosmograph/extractors/legal.py`: Primary document extractor
- `src/cosmograph/generators/html.py`: Visualization generator

**Testing:**
- `tests/`: Test files (use `test_*.py` naming)
- `test_output/`: Sample output for manual verification

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `legal.py`, `base.py`)
- Test files: `test_*.py` or `*_test.py`
- Documentation: `UPPERCASE.md` (e.g., `CLAUDE.md`, `README.md`)

**Directories:**
- Packages: `snake_case` (e.g., `extractors/`, `generators/`)
- Special: Leading underscore not used

**Classes:**
- `PascalCase` (e.g., `LegalDocumentExtractor`, `HTMLGenerator`)
- Extractor suffix for extractors: `*Extractor`
- Generator suffix for generators: `*Generator`

**Functions:**
- `snake_case` (e.g., `add_node`, `read_text`)
- Private functions: `_leading_underscore` (e.g., `_clean_id`, `_extract_code`)

**Variables:**
- `snake_case` for local and instance variables
- `UPPER_SNAKE_CASE` for constants (e.g., `CATEGORY_COLORS`, `KEY_ENTITIES`)

## Where to Add New Code

**New Extractor:**
1. Create `src/cosmograph/extractors/new_extractor.py`
2. Inherit from `BaseExtractor`
3. Implement `supports()` and `extract()` methods
4. Add export to `src/cosmograph/extractors/__init__.py`
5. Add CLI option in `src/cosmograph/cli.py:_get_extractor()`
6. Tests: `tests/test_extractors.py`

**New Generator:**
1. Create `src/cosmograph/generators/new_format.py`
2. Implement `generate(graph, output_path)` method
3. Add export to `src/cosmograph/generators/__init__.py`
4. Add CLI option in `src/cosmograph/cli.py:generate()` command
5. Tests: `tests/test_generators.py`

**New CLI Command:**
1. Add command function in `src/cosmograph/cli.py`
2. Decorate with `@app.command()`
3. Follow existing pattern for argument/option handling

**New Model:**
1. Add dataclass to `src/cosmograph/models.py`
2. Include `to_dict()` method for serialization
3. Tests: `tests/test_models.py`

**Utilities:**
- Shared helpers: Add to `src/cosmograph/utils.py` (create if needed)
- Extractor-specific helpers: Keep in extractor file as private methods

## Special Directories

**.venv/:**
- Purpose: Python virtual environment
- Generated: Yes (via `python -m venv`)
- Committed: No

**output/:**
- Purpose: Default output location for generated graphs
- Generated: Yes (by `cosmograph generate`)
- Committed: No

**test_output/:**
- Purpose: Sample/reference output files
- Generated: Yes (manually or by test runs)
- Committed: Yes (for reference)

**.planning/:**
- Purpose: GSD planning and analysis documents
- Generated: Yes (by gsd commands)
- Committed: Yes

**build/, dist/, *.egg-info/:**
- Purpose: Python packaging artifacts
- Generated: Yes (by pip/hatch build)
- Committed: No

---

*Structure analysis: 2026-01-21*
