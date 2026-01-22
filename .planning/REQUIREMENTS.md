# REQUIREMENTS.md

## Milestone: v0.2.0 - Web Foundation

**Goal**: Iyeska team can process client documents through a web interface on Iyeska HQ infrastructure

**Duration Estimate**: 4-6 phases
**Complexity**: Medium (wrapping existing functionality + 4 new features)

---

## Functional Requirements

### FR-1: PDF Document Support

**Priority**: High (blocks most client work)

**User Story**: As an operator, I can upload PDF documents directly so I don't need to pre-convert them to text.

**Acceptance Criteria**:
- System accepts .pdf files alongside .txt and .md
- PDF text extraction preserves structure (headers, sections, paragraphs)
- Multi-page PDFs process as single document
- Error handling for encrypted/scanned PDFs (graceful failure with message)

**Technical Notes**:
- pymupdf already in dependencies (unused)
- Create `PdfExtractor` following `BaseExtractor` pattern
- Consider OCR placeholder for scanned docs (v0.3+ feature)

---

### FR-2: LLM-Powered Extraction ✓ Complete

**Priority**: High (differentiator feature)
**Status**: Complete (Phase 4, 2026-01-21)

**User Story**: As an operator, I can use Claude to extract entities and relationships that pattern matching misses.

**Acceptance Criteria**:
- Operator explicitly chooses LLM extraction (not automatic)
- System shows estimated token cost before processing
- LLM identifies: entities (people, organizations, concepts), relationships, document structure
- Results merge with pattern-extracted data (deduplication)
- Rate limiting to prevent runaway costs

**Technical Notes**:
- anthropic SDK in `[llm]` optional dependencies
- Implement as `LlmExtractor` inheriting `BaseExtractor`
- Chunk long documents (context window management)
- Store API key in environment (ANTHROPIC_API_KEY)
- Consider hybrid mode: patterns first, LLM for gaps

**Data Sovereignty Gate**:
- Explicit confirmation before any content sent to Claude API
- Log what was sent (hash, not content) for audit

---

### FR-3: Custom Pattern Configuration

**Priority**: Medium (power feature)

**User Story**: As an operator, I can define custom extraction patterns for specific document types without modifying code.

**Acceptance Criteria**:
- YAML configuration file for pattern rules
- Patterns define: entity types, regex patterns, relationship triggers
- Load patterns at runtime (no rebuild needed)
- Validate pattern syntax on load
- Support multiple pattern files (per-project)

**Example Pattern Config**:
```yaml
# patterns.yaml
entities:
  - name: board_member
    patterns:
      - "Board Member: ([A-Za-z ]+)"
      - "([A-Z][a-z]+ [A-Z][a-z]+), Board"
    category: person

  - name: policy
    patterns:
      - "Policy (\\d+\\.\\d+)"
      - "(?:Section|§) (\\d+)"
    category: policy

relationships:
  - trigger: "appointed by"
    source_type: person
    target_type: organization
    relation: "appointed_by"
```

**Technical Notes**:
- Create `PatternConfig` class for loading/validating
- Modify `GenericExtractor` to use dynamic patterns
- Consider JSON alternative for simpler tooling

---

### FR-4: Web Interface

**Priority**: High (core deliverable)
**Status**: Backend complete (Phase 5, 2026-01-21), Frontend pending (Phase 6)

**User Story**: As an operator, I can upload documents and view results through a web browser instead of command line.

**Acceptance Criteria**:
- Upload single or multiple files (drag & drop or file picker)
- Select extraction method: pattern | llm | hybrid
- Progress indicator during processing
- View generated graph in browser
- Download HTML and CSV outputs
- Clear error messages for failures

**Technical Notes**:
- FastAPI backend with file upload endpoints
- React frontend with minimal UI (not over-designed)
- WebSocket or polling for progress updates
- Serve generated HTML directly or embed graph component

---

## Non-Functional Requirements

### NFR-1: Local-First Architecture

- All processing happens on Iyeska HQ infrastructure
- No external service dependencies except explicit LLM calls
- Generated visualizations work completely offline
- Network requests only for LLM extraction (with approval gate)

### NFR-2: Performance

- Process 100-page PDF in under 60 seconds (pattern extraction)
- LLM extraction: depends on API, show progress
- UI responsive during processing (async/background)

### NFR-3: Security

- File uploads sanitized (no path traversal)
- Temporary files cleaned after processing
- No sensitive data in logs (document content)
- CORS restricted to known origins

### NFR-4: Maintainability

- Keep CLI working (power user path)
- API wraps existing extractors (minimal duplication)
- Tests for new extractors and API endpoints
- Type hints throughout

---

## Out of Scope (v0.2.0)

Explicitly NOT included in this milestone:

1. **User Authentication** - Internal tool, no login required
2. **Job Persistence** - Results exist only during session
3. **Multi-Tenancy** - Single operator use
4. **Billing/Metering** - LLM costs absorbed
5. **Client Self-Service** - Operator-only access
6. **Background Workers** - Synchronous processing
7. **OCR for Scanned PDFs** - Text-based PDFs only

These are candidates for v0.3.0+.

---

## Technical Constraints

### Must Use (Iyeska Stack Compliance)

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend | FastAPI 0.115+ | Standard stack |
| Frontend | React + TypeScript + Vite | Standard stack |
| Python | 3.13 (MacPorts) | Standard stack |
| Deployment | PM2 on Ubuntu 192.168.11.20 | Iyeska HQ |
| Proxy | Traefik (cosmograph.localhost for dev) | Standard stack |

### Already Have (Reuse)

| Component | Status | Notes |
|-----------|--------|-------|
| Extractor framework | Working | BaseExtractor, Graph, Node, Edge |
| Legal extractor | Working | CRST codes processed |
| HTML generator | Working | D3.js visualization |
| CSV generator | Working | Export format |
| pymupdf | Installed | Not implemented |
| anthropic SDK | In [llm] extras | Not implemented |

---

## Risk Assessment

### High Risk

**LLM Cost Runaway**
- Mitigation: Explicit approval gate, token estimation, rate limits
- Fallback: Pattern-only mode always available

### Medium Risk

**PDF Complexity**
- Some PDFs have complex layouts, tables, multi-column
- Mitigation: Start with simple text PDFs, graceful degradation for complex

**Scope Creep**
- "Just add one more feature" syndrome
- Mitigation: Strict adherence to this requirements doc

### Low Risk

**Performance**
- Current CLI handles hundreds of files
- Web adds HTTP overhead but should be fine for v0.2 scale

---

## Definition of Done

v0.2.0 is complete when:

1. [ ] PDF extractor processes test legal documents
2. [ ] LLM extractor works with approval gate
3. [ ] Pattern config loads from YAML
4. [ ] Web UI uploads files and displays results
5. [ ] Deployed to 192.168.11.20 via PM2
6. [ ] Accessible at cosmograph.localhost (dev) / cosmo.iyeska.net (prod)
7. [ ] One real client document set processed end-to-end
8. [ ] CLI still works (regression check)

---

*Requirements finalized: 2026-01-21*
