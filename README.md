# Cosmograph

Generate interactive knowledge graph visualizations from documents.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Multiple extractors**: Legal documents, generic text, markdown
- **Interactive visualization**: D3.js-powered force-directed graph
- **Search & filter**: Find nodes by name/description, filter by category
- **Export formats**: HTML (standalone), CSV (nodes & edges)
- **Zero dependencies for viewing**: Generated HTML is self-contained

## Installation

```bash
# Clone the repository
git clone https://github.com/guthdx/cosmograph.git
cd cosmograph

# Install with pip
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Generate from a single file
cosmograph generate document.txt -t "My Graph"

# Generate from a directory of documents
cosmograph generate ./documents/ -p "*.txt" -t "Project Knowledge Graph"

# Generate with legal document extractor
cosmograph generate ./legal-docs/ -e legal -t "Legal Framework"

# View statistics for existing graph
cosmograph stats ./output/

# Serve locally
cosmograph serve ./output/ -p 8080
```

## Usage

### Basic Generation

```bash
cosmograph generate <input> [OPTIONS]
```

**Arguments:**
- `input`: File or directory containing documents

**Options:**
- `-o, --output`: Output directory (default: ./output)
- `-t, --title`: Graph title
- `-e, --extractor`: Extractor type (auto, legal, text, generic)
- `-p, --pattern`: File pattern for directories (default: *.txt)
- `--html-only`: Skip CSV generation
- `--no-open`: Don't open browser after generation

### Extractors

| Extractor | Best For |
|-----------|----------|
| `legal` | Codes, ordinances, constitutions, legal documents |
| `text` | Markdown files, general text with headers |
| `generic` | Any text using pattern matching |
| `auto` | Automatically selects based on content |

### Output Files

```
output/
├── index.html        # Interactive visualization
├── graph_nodes.csv   # Node definitions
└── graph_data.csv    # Edge relationships
```

## Visualization Features

- **Hover**: Highlight connected nodes
- **Click**: View node details
- **Search**: Filter by name or description
- **Categories**: Toggle visibility by category
- **Zoom/Pan**: Navigate large graphs
- **Drag**: Reposition nodes

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Project Structure

```
cosmograph/
├── src/cosmograph/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── models.py           # Graph, Node, Edge models
│   ├── extractors/         # Document extractors
│   │   ├── base.py         # Base extractor class
│   │   ├── legal.py        # Legal document extractor
│   │   ├── text.py         # Text/markdown extractor
│   │   └── generic.py      # Pattern-based extractor
│   └── generators/         # Output generators
│       ├── html.py         # HTML visualization
│       └── csv.py          # CSV export
├── tests/
├── pyproject.toml
└── README.md
```

## Roadmap

- [ ] PDF extraction (text-based and OCR)
- [ ] LLM-powered entity extraction (Claude, GPT)
- [ ] Custom extraction patterns via config
- [ ] Multiple visualization themes
- [ ] Export to other formats (GEXF, GraphML)
- [ ] Web UI for configuration

## License

MIT License - see LICENSE file for details.

## Credits

Built by [Iyeska LLC](https://iyeska.net) for tribal and client knowledge management.

Visualization powered by [D3.js](https://d3js.org/).
