# Codebase Concerns

**Analysis Date:** 2026-01-21

## Tech Debt

**Test Suite Empty:**
- Issue: Tests directory exists but contains only an empty `__init__.py`
- Files: `tests/__init__.py`
- Impact: No automated testing, regressions can go unnoticed. pyproject.toml defines pytest config but no tests exist.
- Fix approach: Add unit tests for extractors, models, and generators. Start with models.py since it has pure logic.

**Inline HTML Template in Python:**
- Issue: 190+ lines of HTML/CSS/JavaScript embedded as f-string in Python code
- Files: `src/cosmograph/generators/html.py` (lines 56-248)
- Impact: Hard to maintain, no syntax highlighting in editors, string escaping complexity with curly braces (uses double braces throughout)
- Fix approach: Move template to Jinja2 file in `templates/` directory. Jinja2 is already a dependency but unused.

**Unused Dependencies:**
- Issue: `pymupdf` and `jinja2` declared as dependencies but not used anywhere in the codebase
- Files: `pyproject.toml` (lines 30-31)
- Impact: Bloated install size, unused code paths. Comments say "PDF support (future)" but no implementation exists.
- Fix approach: Either implement PDF extraction using pymupdf, or move to optional dependencies group until needed.

**Auto Extractor Defaults to Legal:**
- Issue: The "auto" extractor option defaults to LegalDocumentExtractor rather than detecting document type
- Files: `src/cosmograph/cli.py` (line 201)
- Impact: Generic documents get incorrect extraction. Comment says "Default to legal for now" indicating known shortcut.
- Fix approach: Implement actual auto-detection based on file content or let extractors vote via `supports()` method.

**Import Inside Method:**
- Issue: `re` module imported inside `Graph._clean_id()` method instead of at module top
- Files: `src/cosmograph/models.py` (line 94)
- Impact: Minor performance hit on repeated calls, unconventional Python style
- Fix approach: Move `import re` to top of file with other imports.

**Templates Module Empty:**
- Issue: `templates/__init__.py` exists but is empty placeholder
- Files: `src/cosmograph/templates/__init__.py`
- Impact: Module structure suggests planned templating system that was never implemented
- Fix approach: Either implement Jinja2 templates for HTML generation or remove the module.

## Known Bugs

**Duplicate Edge Check Performance:**
- Symptoms: O(n) linear scan on every edge addition
- Files: `src/cosmograph/models.py` (lines 83-86)
- Trigger: Large documents create many edges, each addition scans all existing edges
- Workaround: None - becomes slow with thousands of edges

**Stats Command Missing Edge File:**
- Symptoms: If edges file doesn't exist, total_edges silently set to 0 without warning
- Files: `src/cosmograph/cli.py` (lines 154-156)
- Trigger: Run `cosmograph stats` on directory without `graph_data.csv`
- Workaround: Ensure both CSV files exist

## Security Considerations

**External CDN Dependency:**
- Risk: HTML visualization loads D3.js from `https://d3js.org/d3.v7.min.js` at runtime
- Files: `src/cosmograph/generators/html.py` (line 62)
- Current mitigation: None - requires internet connection
- Recommendations: Either bundle D3.js inline (increases file size) or add option for local file serving. Data sovereignty principles suggest avoiding external fetches.

**SimpleHTTPRequestHandler in Serve Command:**
- Risk: Uses Python's basic HTTP server with no security headers, directory listing enabled
- Files: `src/cosmograph/cli.py` (lines 183-189)
- Current mitigation: Local use only (localhost binding)
- Recommendations: Add warning that this is for local development only, not production. Consider adding --bind flag to restrict to localhost.

## Performance Bottlenecks

**Edge Deduplication:**
- Problem: Linear scan through all edges on every `add_edge()` call
- Files: `src/cosmograph/models.py` (lines 83-86)
- Cause: Uses list iteration instead of set-based lookup
- Improvement path: Use a set of (source, target, type) tuples for O(1) duplicate checking

**Regex Compilation on Every Extract:**
- Problem: Regex patterns compiled fresh on each method call
- Files: `src/cosmograph/extractors/legal.py`, `src/cosmograph/extractors/text.py`, `src/cosmograph/extractors/generic.py`
- Cause: `re.finditer()` called with pattern strings instead of pre-compiled patterns
- Improvement path: Pre-compile patterns as class attributes using `re.compile()`

## Fragile Areas

**Graph._clean_id() Node ID Generation:**
- Files: `src/cosmograph/models.py` (lines 91-97)
- Why fragile: Aggressive cleaning removes most punctuation and truncates to 100 chars. Two different nodes could end up with same ID.
- Safe modification: Ensure all ID generation goes through this method consistently
- Test coverage: None - needs unit tests for edge cases

**Extractor Pattern Matching:**
- Files: `src/cosmograph/extractors/legal.py` (lines 67-155)
- Why fragile: Hardcoded regex patterns for specific document formats (Roman numerals, ARTICLE/SECTION/CHAPTER). Will miss variations.
- Safe modification: Keep patterns in class constants, add comprehensive test documents
- Test coverage: None

**HTML Template String Escaping:**
- Files: `src/cosmograph/generators/html.py` (lines 56-248)
- Why fragile: Double curly braces `{{` used throughout for CSS, JavaScript must match Python f-string escaping. Single typo breaks entire visualization.
- Safe modification: Test any changes with actual graph generation
- Test coverage: None

## Scaling Limits

**In-Memory Graph Storage:**
- Current capacity: Entire graph held in memory as dict and list
- Limit: Large document sets (1000+ files) could exhaust memory
- Scaling path: Stream processing, disk-backed storage, or database for intermediate results

**Single-Threaded Processing:**
- Current capacity: Files processed sequentially in for loop
- Limit: Processing time linear with file count
- Scaling path: Add multiprocessing for extraction phase (`concurrent.futures.ProcessPoolExecutor`)

## Dependencies at Risk

**No Lockfile:**
- Risk: Dependencies specified with loose versions (e.g., `>=0.9.0`), builds may differ across machines
- Impact: "Works on my machine" issues, security vulnerabilities from outdated transitive deps
- Migration plan: Generate `requirements.lock` or switch to `uv.lock` for reproducible builds

**pydantic Dependency Unused:**
- Risk: pydantic v2 declared as dependency but not imported anywhere
- Impact: Unnecessary complexity in dependency tree
- Migration plan: Either use pydantic for models (replace dataclasses) or remove from dependencies

## Missing Critical Features

**No PDF Support:**
- Problem: pymupdf is a dependency but PDF extraction not implemented
- Blocks: Cannot process PDF legal documents (common format for codes/ordinances)

**No LLM Integration:**
- Problem: `[llm]` optional dependencies declared but no extraction using AI
- Blocks: Cannot extract semantic relationships beyond regex patterns

**No Relationship Extraction Between Nodes:**
- Problem: Only document-to-entity edges created, no entity-to-entity relationships
- Blocks: Cannot show "Tribal Council appoints Chief Judge" type connections

**No Incremental Updates:**
- Problem: Must regenerate entire graph when documents change
- Blocks: Cannot efficiently update visualizations for large document sets

## Test Coverage Gaps

**100% Untested:**
- What's not tested: Entire codebase - 0 test files with actual tests
- Files: `tests/__init__.py` (empty), no test_*.py files exist
- Risk: Any refactoring could break functionality undetected
- Priority: High

**Critical paths needing tests:**
- `Graph.add_node()` and `Graph.add_edge()` - core data model
- `LegalDocumentExtractor.extract()` - main extraction logic
- `HTMLGenerator.generate()` - output generation
- `cli.generate()` - end-to-end workflow

---

*Concerns audit: 2026-01-21*
