# External Integrations

**Analysis Date:** 2026-01-21

## APIs & External Services

**Current:**
- None - Cosmograph operates fully offline with no external API calls

**Planned (Roadmap):**
- Anthropic Claude API - LLM-powered entity extraction
  - SDK/Client: `anthropic>=0.18.0` (optional dependency)
  - Auth: `ANTHROPIC_API_KEY` (not yet implemented)
- OpenAI API - LLM-powered entity extraction
  - SDK/Client: `openai>=1.0.0` (optional dependency)
  - Auth: `OPENAI_API_KEY` (not yet implemented)

## Data Storage

**Databases:**
- None - No database required

**File Storage:**
- Local filesystem only
- Input: Text files (`.txt`, `.md`, `.text`)
- Output: `./output/` directory (configurable via `-o` flag)
  - `index.html` - Interactive D3.js visualization
  - `graph_nodes.csv` - Node definitions
  - `graph_data.csv` - Edge relationships

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- None - CLI tool with no authentication required

## Monitoring & Observability

**Error Tracking:**
- None - Console output via Rich library

**Logs:**
- Console output only
- Progress bars and status messages via `rich.progress`
- Warnings for failed file processing

## CI/CD & Deployment

**Hosting:**
- Not applicable - Local CLI tool
- PyPI publication planned (based on package structure)

**CI Pipeline:**
- None configured (no `.github/workflows/` detected)

## Environment Configuration

**Required env vars:**
- None for core functionality

**Future env vars (when LLM features implemented):**
- `ANTHROPIC_API_KEY` - For Claude-powered entity extraction
- `OPENAI_API_KEY` - For GPT-powered entity extraction

**Secrets location:**
- Standard environment variables (no secrets management currently)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## CDN Dependencies

**D3.js (visualization library):**
- URL: `https://d3js.org/d3.v7.min.js`
- Loaded at runtime in generated HTML
- Purpose: Force-directed graph rendering, zoom/pan, drag interactions

**Note:** Generated HTML files fetch D3.js from CDN when opened in browser. The visualization requires internet connectivity on first load (D3.js may be cached by browser after).

## Local Server

**Built-in HTTP Server:**
- Command: `cosmograph serve ./output/ -p 8080`
- Uses Python's `http.server.SimpleHTTPRequestHandler`
- Purpose: Local viewing of generated visualizations
- No external dependencies

## File Format Support

**Current Input Formats:**
- `.txt` - Plain text files
- `.md` - Markdown files
- `.text` - Alternative text extension

**Planned Input Formats (Roadmap):**
- PDF (via PyMuPDF) - Text extraction and OCR

**Output Formats:**
- HTML - Self-contained D3.js visualization
- CSV - Nodes and edges as separate files

## Third-Party Library Integration

**Rich (Terminal UI):**
- `Console` - Styled terminal output
- `Progress` - Progress bars with spinners
- `Table` - Statistics display

**Typer (CLI Framework):**
- Argument parsing
- Command routing
- Help text generation

**Standard Library Usage:**
- `csv` - CSV file generation
- `json` - Graph data serialization
- `re` - Regex-based entity extraction
- `webbrowser` - Auto-open generated HTML
- `http.server` - Built-in serve command
- `dataclasses` - Model definitions

---

*Integration audit: 2026-01-21*
