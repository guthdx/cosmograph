# Phase 2: PDF Extractor - Research

**Researched:** 2025-01-21
**Domain:** PDF text extraction with PyMuPDF
**Confidence:** HIGH

## Summary

PyMuPDF (formerly imported as `fitz`, now as `pymupdf`) is a mature, high-performance PDF library that provides comprehensive text extraction capabilities. The library is already specified as an optional dependency in the project's `pyproject.toml` under the `[pdf]` extras group.

The core workflow for PDF text extraction is straightforward: open a document, iterate through pages, and call `page.get_text()`. The library handles multi-page documents natively through page iteration. Detecting encrypted vs scanned PDFs requires specific property checks and heuristics.

**Primary recommendation:** Use the `pymupdf` import (not legacy `fitz`), iterate pages with `for page in doc`, extract text with `page.get_text()`, and implement heuristics for scanned PDF detection based on image coverage and text presence.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymupdf | >=1.23.0 | PDF text extraction | Already in pyproject.toml, high performance, comprehensive API |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| reportlab | >=4.0 | Test PDF generation | Creating fixture PDFs programmatically for tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pymupdf | pypdf | pypdf is pure Python (slower), fewer features |
| pymupdf | pdfplumber | Higher level API but depends on pdfminer |
| reportlab | fpdf2 | fpdf2 is simpler but less capable |

**Installation:**
```bash
pip install "cosmograph[pdf]"  # Includes pymupdf>=1.23.0
pip install reportlab  # For test fixture generation (dev only)
```

## Architecture Patterns

### Recommended Class Structure
```
src/cosmograph/extractors/
├── base.py          # BaseExtractor ABC (existing)
├── legal.py         # LegalDocumentExtractor (existing)
├── text.py          # TextExtractor (existing)
├── generic.py       # GenericExtractor (existing)
└── pdf.py           # NEW: PdfExtractor class
```

### Pattern 1: Extractor Implementation
**What:** Follow existing BaseExtractor pattern with PDF-specific additions
**When to use:** Always for the PDF extractor
**Example:**
```python
# Source: Existing codebase pattern + PyMuPDF docs
import pymupdf
from pathlib import Path
from .base import BaseExtractor
from ..models import Graph

class PdfExtractor(BaseExtractor):
    """Extract entities from PDF documents."""

    def supports(self, filepath: Path) -> bool:
        return filepath.suffix.lower() == ".pdf"

    def extract(self, filepath: Path) -> Graph:
        doc = pymupdf.open(filepath)
        try:
            # Check for encrypted PDF
            if doc.needs_pass:
                raise ValueError(f"PDF is password-protected: {filepath.name}")

            # Extract text from all pages
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"

            # Check for scanned PDF (no extractable text)
            if self._is_likely_scanned(doc, full_text):
                raise ValueError(f"PDF appears to be scanned (no extractable text): {filepath.name}")

            # Process text through existing extraction logic
            # ... (use extracted text)

            return self.graph
        finally:
            doc.close()
```

### Pattern 2: Scanned PDF Detection Heuristic
**What:** Detect scanned PDFs that have no extractable text
**When to use:** Before attempting text extraction
**Example:**
```python
# Source: PyMuPDF GitHub discussion #1653, #1853
def _is_likely_scanned(self, doc: pymupdf.Document, extracted_text: str) -> bool:
    """Heuristic to detect scanned PDFs without extractable text."""
    # Check 1: If we got meaningful text, it's not purely scanned
    text_stripped = extracted_text.strip()
    if len(text_stripped) > 100:  # Arbitrary threshold
        return False

    # Check 2: Look for images covering entire pages
    for page in doc:
        page_rect = page.rect
        images = page.get_images()
        if images:
            for img in images:
                # Get image bounding box
                img_bbox = page.get_image_bbox(img)
                if img_bbox:
                    # Check if image covers >95% of page
                    intersection = img_bbox & page_rect
                    coverage = abs(intersection) / abs(page_rect)
                    if coverage >= 0.95 and len(text_stripped) < 50:
                        return True

    # Check 3: Look for OCR-specific fonts (Tesseract)
    for page in doc:
        fonts = page.get_fonts()
        for font in fonts:
            if "GlyphlessFont" in str(font) or "GlyphLessFont" in str(font):
                # Has OCR text - not purely scanned, but may have limited text
                return False

    # If very little text and we reach here, likely scanned
    return len(text_stripped) < 20
```

### Pattern 3: Multi-page Document Processing
**What:** Process all pages as single document (per requirements)
**When to use:** Always for PDF extraction
**Example:**
```python
# Source: PyMuPDF Tutorial docs
def _extract_all_text(self, doc: pymupdf.Document) -> str:
    """Extract text from all pages, preserving order."""
    pages_text = []
    for page_num, page in enumerate(doc):
        page_text = page.get_text(sort=True)  # sort=True for reading order
        pages_text.append(page_text)
    return "\n\n".join(pages_text)
```

### Anti-Patterns to Avoid
- **Using `import fitz`:** Legacy import name; use `import pymupdf` for new code
- **Not closing documents:** Always use try/finally or context manager to close docs
- **Ignoring `needs_pass`:** Always check for encrypted PDFs before extraction
- **Extracting images by default:** Slows extraction significantly; use flags to exclude

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF parsing | Custom PDF parser | pymupdf | PDF spec is 1000+ pages, edge cases everywhere |
| Text reordering | Custom layout algorithm | `get_text(sort=True)` | PyMuPDF handles reading order |
| OCR detection | Manual font analysis | Check fonts + text presence | Heuristic approach is standard |
| Encryption detection | Parsing PDF headers | `doc.needs_pass` | Built-in property handles all cases |

**Key insight:** PDF is an incredibly complex format. PyMuPDF wraps MuPDF (the same engine Firefox uses). Trust the library for parsing; focus on domain-specific extraction logic.

## Common Pitfalls

### Pitfall 1: Using Legacy Import Name
**What goes wrong:** Code uses `import fitz` which is deprecated
**Why it happens:** Older tutorials and documentation use the legacy name
**How to avoid:** Always use `import pymupdf`
**Warning signs:** Deprecation warnings, IDE type hints may not work

### Pitfall 2: Forgetting to Close Documents
**What goes wrong:** File handles leak, memory issues
**Why it happens:** Exception paths bypass cleanup
**How to avoid:** Use try/finally or with-statement pattern
**Warning signs:** "Too many open files" errors, growing memory usage

### Pitfall 3: Assuming Text is in Reading Order
**What goes wrong:** Extracted text is jumbled (headers at end, columns mixed)
**Why it happens:** PDFs store text in creation order, not visual order
**How to avoid:** Use `page.get_text(sort=True)` to sort by position
**Warning signs:** Headers appearing at document end, multi-column text interleaved

### Pitfall 4: Not Handling Empty/Scanned PDFs Gracefully
**What goes wrong:** Silent failures or cryptic errors
**Why it happens:** Scanned PDFs have images but no text objects
**How to avoid:** Check text length, provide meaningful error messages
**Warning signs:** Empty output, users confused about why extraction "failed"

### Pitfall 5: Slow Extraction Due to Image Processing
**What goes wrong:** Text extraction takes unexpectedly long
**Why it happens:** Default flags include image extraction
**How to avoid:** Use `flags` parameter to exclude images when not needed
**Warning signs:** Simple documents taking seconds to process

## Code Examples

Verified patterns from official sources:

### Opening and Extracting Text
```python
# Source: https://pymupdf.readthedocs.io/en/latest/tutorial.html
import pymupdf

doc = pymupdf.open("document.pdf")
for page in doc:
    text = page.get_text()
    print(text)
doc.close()
```

### Checking for Encrypted PDF
```python
# Source: https://pymupdf.readthedocs.io/en/latest/document.html
import pymupdf

doc = pymupdf.open("document.pdf")
if doc.needs_pass:
    # Requires password
    success = doc.authenticate("password")
    if not success:
        raise ValueError("Authentication failed")
# Now safe to extract
```

### Text Extraction with Reading Order
```python
# Source: https://pymupdf.readthedocs.io/en/latest/recipes-text.html
page = doc[0]
text = page.get_text(sort=True)  # Sorts by position (top-left to bottom-right)
```

### Block-Based Extraction (for structure)
```python
# Source: https://pymupdf.readthedocs.io/en/latest/recipes-text.html
page = doc[0]
blocks = page.get_text("blocks")
# Each block: (x0, y0, x1, y1, "text", block_no, block_type)
for block in blocks:
    if block[6] == 0:  # 0 = text block, 1 = image block
        print(block[4])  # The text content
```

### Performance-Optimized Extraction (Exclude Images)
```python
# Source: https://pymupdf.readthedocs.io/en/latest/app1.html
# Excluding images can cut processing time by ~50%
text = page.get_text(flags=pymupdf.TEXT_PRESERVE_WHITESPACE)
```

### Creating Test PDFs with PyMuPDF Story
```python
# Source: https://pymupdf.readthedocs.io/en/latest/story-class.html
import pymupdf

HTML = """
<html>
<body>
    <h1>Test Document</h1>
    <p>This is test content for PDF extractor.</p>
</body>
</html>
"""

MEDIABOX = pymupdf.paper_rect("letter")
WHERE = MEDIABOX + (36, 36, -36, -36)  # margins

story = pymupdf.Story(html=HTML)
writer = pymupdf.DocumentWriter("test.pdf")

more = 1
while more:
    dev = writer.begin_page(MEDIABOX)
    more, _ = story.place(WHERE)
    story.draw(dev)
    writer.end_page()

writer.close()
```

### Alternative: Creating Test PDFs with ReportLab
```python
# Source: https://www.reportlab.com/docs/reportlab-userguide.pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_test_pdf(filepath):
    c = canvas.Canvas(str(filepath), pagesize=letter)
    c.drawString(100, 750, "TITLE I: GENERAL PROVISIONS")
    c.drawString(100, 700, "Section 1. Definitions.")
    c.drawString(100, 650, "This is test content.")
    c.save()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `import fitz` | `import pymupdf` | v1.23+ | Use new import for new code |
| Manual text reordering | `sort=True` parameter | v1.19+ | Built-in reading order |
| Separate OCR library | `get_textpage_ocr()` | v1.18+ | Integrated OCR support |

**Deprecated/outdated:**
- **`fitz` import:** Still works but `pymupdf` is the current standard
- **Manual page iteration via index:** Use `for page in doc:` iterator instead

## Open Questions

Things that couldn't be fully resolved:

1. **Structure Preservation Depth**
   - What we know: `get_text("blocks")` provides structural blocks; `sort=True` orders by position
   - What's unclear: How well this preserves legal document hierarchy (titles, chapters, sections) compared to plain text
   - Recommendation: Test with real legal PDFs; may need to combine block extraction with existing LegalDocumentExtractor regex patterns

2. **OCR'd PDF Handling**
   - What we know: PyMuPDF has OCR capabilities via `get_textpage_ocr()`
   - What's unclear: Whether to attempt OCR automatically or just detect and report
   - Recommendation: Per requirements, "graceful failure with message" for scanned PDFs; OCR is out of scope for Phase 2

3. **Performance with Large Documents**
   - What we know: Image exclusion cuts time ~50%; library is generally fast
   - What's unclear: Performance with 100+ page legal documents
   - Recommendation: Profile with real documents; consider progress callbacks for long operations

## Sources

### Primary (HIGH confidence)
- [PyMuPDF Document Class](https://pymupdf.readthedocs.io/en/latest/document.html) - Document opening, encryption, page iteration
- [PyMuPDF Text Recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html) - Text extraction options and flags
- [PyMuPDF Tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html) - Basic usage patterns, import statement
- [PyMuPDF Appendix 1](https://pymupdf.readthedocs.io/en/latest/app1.html) - Text extraction flags, performance
- [PyMuPDF Story Class](https://pymupdf.readthedocs.io/en/latest/story-class.html) - Programmatic PDF creation

### Secondary (MEDIUM confidence)
- [PyMuPDF Discussion #1653](https://github.com/pymupdf/PyMuPDF/discussions/1653) - Identifying scanned PDFs
- [PyMuPDF Discussion #1853](https://github.com/pymupdf/PyMuPDF/discussions/1853) - Scanned vs digital PDF detection
- [Pytest Fixtures Documentation](https://docs.pytest.org/en/stable/explanation/fixtures.html) - Test fixture patterns

### Tertiary (LOW confidence)
- WebSearch results on testing PDF fixtures - multiple sources, general patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pymupdf is already in pyproject.toml, docs are authoritative
- Architecture: HIGH - follows existing extractor pattern from codebase
- Pitfalls: HIGH - verified from official documentation
- Scanned PDF detection: MEDIUM - based on GitHub discussions, heuristic approach

**Research date:** 2025-01-21
**Valid until:** 2025-02-21 (PyMuPDF is stable, API unlikely to change)
