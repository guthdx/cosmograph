# Technology Stack

**Analysis Date:** 2026-01-21

## Languages

**Primary:**
- Python 3.11+ - All application code (required: `>=3.11`, classifiers show 3.11, 3.12, 3.13 support)

**Secondary:**
- JavaScript (ES6+) - D3.js visualization embedded in generated HTML output
- HTML5/CSS3 - Self-contained visualization output

## Runtime

**Environment:**
- Python 3.11, 3.12, or 3.13 (recommended: `/opt/local/bin/python3.13`)
- Virtual environment: `.venv/`

**Package Manager:**
- pip (via hatchling build backend)
- Lockfile: None (no `requirements.lock` or `poetry.lock` present)

## Frameworks

**Core:**
- Typer 0.9.0+ - CLI framework for command-line interface
- Pydantic 2.0.0+ - Data validation (used indirectly, in dependencies list)

**Testing:**
- pytest 7.0.0+ - Test runner
- pytest-cov 4.0.0+ - Coverage reporting

**Build/Dev:**
- Hatchling - Build backend (modern Python packaging)
- Ruff 0.1.0+ - Linting and formatting
- mypy 1.0.0+ - Static type checking

## Key Dependencies

**Critical (Core Functionality):**
- `typer>=0.9.0` - CLI commands: `generate`, `stats`, `serve`
- `rich>=13.0.0` - Terminal output formatting, progress bars, tables
- `pydantic>=2.0.0` - Data validation (declared but minimally used currently)
- `jinja2>=3.1.0` - Template rendering (declared for future use, not yet implemented)

**Document Processing:**
- `pymupdf>=1.23.0` - PDF support (declared for roadmap, not yet implemented)

**Optional (LLM Integration - Roadmap):**
- `anthropic>=0.18.0` - Claude API integration (install via `pip install -e ".[llm]"`)
- `openai>=1.0.0` - GPT API integration (install via `pip install -e ".[llm]"`)

**Frontend (CDN-loaded in generated HTML):**
- D3.js v7 - Force-directed graph visualization (loaded from `https://d3js.org/d3.v7.min.js`)

## Configuration

**Environment:**
- No environment variables required for core functionality
- Future LLM integration will require `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

**Build:**
- `pyproject.toml` - All project configuration (PEP 621 compliant)

**Tool Configuration in pyproject.toml:**
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Platform Requirements

**Development:**
- Python 3.11+ (MacPorts recommended on macOS: `/opt/local/bin/python3.13`)
- No external services required
- No database required

**Production:**
- CLI tool - runs locally
- Output: Self-contained HTML files (no server required for viewing)
- Optional: `cosmograph serve` provides built-in HTTP server on port 8080

## Installation Commands

```bash
# Standard installation
pip install -e .

# With development tools
pip install -e ".[dev]"

# With LLM support (future)
pip install -e ".[llm]"
```

## Entry Point

- CLI entry point: `cosmograph` command
- Module path: `cosmograph.cli:app`
- Location: `src/cosmograph/cli.py`

---

*Stack analysis: 2026-01-21*
