# Architecture

**Analysis Date:** 2026-01-21

## Pattern Overview

**Overall:** Pipeline Pattern with Strategy/Plugin Architecture

**Key Characteristics:**
- ETL-style pipeline: Extract (documents) -> Transform (graph model) -> Load (HTML/CSV output)
- Strategy pattern for extractors: Multiple extraction algorithms share a common interface
- Central graph model acts as the data transfer object between pipeline stages
- Self-contained output: Generated HTML embeds all data and D3.js visualization code

## Layers

**CLI Layer:**
- Purpose: Parse user input, orchestrate processing, display progress/output
- Location: `src/cosmograph/cli.py`
- Contains: Typer commands (generate, stats, serve), progress display, argument validation
- Depends on: Extractors, Generators, Models
- Used by: End users via terminal

**Models Layer:**
- Purpose: Define core data structures for knowledge graphs
- Location: `src/cosmograph/models.py`
- Contains: `Node`, `Edge`, `Graph` dataclasses with business logic
- Depends on: Nothing (pure Python stdlib)
- Used by: CLI, Extractors, Generators

**Extractors Layer:**
- Purpose: Parse documents and populate Graph instances
- Location: `src/cosmograph/extractors/`
- Contains: `BaseExtractor` ABC, specialized extractors (Legal, Text, Generic)
- Depends on: Models
- Used by: CLI

**Generators Layer:**
- Purpose: Serialize Graph to output formats
- Location: `src/cosmograph/generators/`
- Contains: `HTMLGenerator`, `CSVGenerator`
- Depends on: Models
- Used by: CLI

## Data Flow

**Document Processing Pipeline:**

1. CLI receives input path and options
2. CLI collects files matching pattern (glob)
3. CLI instantiates appropriate Extractor with shared Graph instance
4. Extractor processes each file, calling `graph.add_node()` and `graph.add_edge()`
5. After all files processed, CLI passes Graph to Generators
6. HTMLGenerator serializes graph to JSON, embeds in template
7. CSVGenerator writes nodes and edges to separate CSV files
8. CLI opens browser to view result

**State Management:**
- Graph instance is mutable and passed by reference to extractors
- Extractors accumulate data into single Graph across multiple files
- Graph handles deduplication via ID normalization in `_clean_id()`
- No persistence between CLI invocations (stateless processing)

## Key Abstractions

**BaseExtractor:**
- Purpose: Define interface for document processing strategies
- Examples: `src/cosmograph/extractors/base.py`
- Pattern: Abstract Base Class with template method (`read_text()`)
- Required methods: `extract(filepath)` returns Graph, `supports(filepath)` returns bool

**Graph:**
- Purpose: Central data structure holding all nodes and edges
- Examples: `src/cosmograph/models.py`
- Pattern: Repository pattern with add/query methods
- Key methods: `add_node()`, `add_edge()`, `to_json()`, `get_stats()`

**Node:**
- Purpose: Represent an entity in the knowledge graph
- Examples: `src/cosmograph/models.py`
- Pattern: Dataclass with serialization
- Fields: id, label, category, description, source_file, metadata

**Edge:**
- Purpose: Represent a relationship between nodes
- Examples: `src/cosmograph/models.py`
- Pattern: Dataclass with serialization
- Fields: source, target, edge_type, weight, metadata

## Entry Points

**CLI Entry Point:**
- Location: `src/cosmograph/cli.py:app`
- Triggers: `cosmograph` command (via pyproject.toml scripts entry)
- Responsibilities: Parse args, orchestrate processing, display output

**Package Entry Point:**
- Location: `src/cosmograph/__init__.py`
- Triggers: `import cosmograph`
- Responsibilities: Expose version number

**Commands:**
- `cosmograph generate <input>` - Main processing command
- `cosmograph stats <path>` - Display statistics for existing graph
- `cosmograph serve <path>` - Local HTTP server for visualization

## Error Handling

**Strategy:** Graceful degradation with warnings

**Patterns:**
- Individual file failures logged as warnings, processing continues
- Missing input paths cause immediate exit with error message
- Invalid extractor type silently falls back to LegalDocumentExtractor (auto mode)
- File read errors handled by `errors="ignore"` in `read_text()`

## Cross-Cutting Concerns

**Logging:** Rich console for user-facing output (no file logging)

**Validation:**
- Path existence checked at CLI entry
- Node ID sanitization in `Graph._clean_id()` (removes special chars, truncates to 100 chars)
- Edge deduplication and self-loop prevention in `Graph.add_edge()`

**Authentication:** Not applicable (local CLI tool)

**Progress Display:** Rich Progress spinner during document processing

---

*Architecture analysis: 2026-01-21*
