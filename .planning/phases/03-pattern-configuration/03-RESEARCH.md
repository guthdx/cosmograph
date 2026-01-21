# Phase 3: Pattern Configuration - Research

**Researched:** 2026-01-21
**Domain:** YAML configuration, regex pattern validation, CLI integration
**Confidence:** HIGH

## Summary

This phase implements YAML-based pattern configuration for the extraction system, allowing users to define custom entity extraction rules without code changes. The research confirms that:

1. **PyYAML + Pydantic** is the standard approach for validated YAML configuration in Python
2. **GenericExtractor already supports dynamic patterns** via constructor injection - this phase extends that pattern to file-based configuration
3. **Regex validation at load time** is straightforward using `re.compile()` with `re.error` exception handling
4. **Relationship triggers** require a proximity/co-occurrence model beyond simple entity extraction

**Primary recommendation:** Use Pydantic models to define and validate the YAML schema, with PyYAML for parsing. Extend GenericExtractor's existing pattern dictionary interface to accept a PatternConfig object loaded from YAML.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0+ | YAML parsing | De facto Python YAML library, already widely used |
| Pydantic | 2.x | Schema validation | Type-safe validation with clear error messages |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-yaml | 1.6+ | YAML+Pydantic integration | Optional - direct PyYAML+model_validate works fine |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic | Yamale (23andMe) | Yamale is YAML-specific schema; Pydantic integrates with existing codebase patterns |
| Pydantic | strictyaml | strictyaml is safer but less flexible; Pydantic already a natural fit |
| PyYAML | ruamel.yaml | ruamel preserves comments/formatting; not needed for this use case |

**Installation:**
```bash
pip install pyyaml pydantic
```

Note: Pydantic may already be available via optional dependencies. Check if it can be added to core dependencies or kept optional.

## Architecture Patterns

### Recommended Project Structure
```
src/cosmograph/
├── config/                    # NEW: Configuration handling
│   ├── __init__.py
│   ├── models.py              # Pydantic models for PatternConfig
│   └── loader.py              # YAML loading and validation
├── extractors/
│   ├── generic.py             # Modify to accept PatternConfig
│   └── ...
└── cli.py                     # Add --patterns option
```

### Pattern 1: Pydantic Model for YAML Schema

**What:** Define the expected YAML structure as Pydantic models
**When to use:** Always - provides validation and clear error messages
**Example:**
```python
# Source: Pydantic documentation - https://docs.pydantic.dev/latest/concepts/models/
from pydantic import BaseModel, field_validator
import re

class EntityPattern(BaseModel):
    """Single entity extraction pattern."""
    name: str                          # e.g., "proper_noun"
    pattern: str                       # regex string
    category: str                      # node category for matches
    description: str = ""              # optional description
    min_length: int = 2                # minimum match length

    @field_validator('pattern')
    @classmethod
    def validate_regex(cls, v: str) -> str:
        """Validate regex compiles successfully."""
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

class RelationshipTrigger(BaseModel):
    """Relationship creation rule."""
    name: str                          # e.g., "defines"
    source_categories: list[str]       # which entity types can be source
    target_categories: list[str]       # which entity types can be target
    proximity: int = 0                 # max character distance (0 = same sentence)
    trigger_pattern: str | None = None # optional pattern that must appear between

class PatternConfig(BaseModel):
    """Root configuration model."""
    version: str = "1.0"
    name: str = "default"
    description: str = ""
    min_occurrences: int = 2
    entity_patterns: list[EntityPattern]
    relationship_triggers: list[RelationshipTrigger] = []
```

### Pattern 2: YAML Configuration File Structure

**What:** The YAML format users will author
**When to use:** Default patterns.yaml and user-created files
**Example:**
```yaml
# Source: Design based on RASA and Semgrep patterns
version: "1.0"
name: "legal-documents"
description: "Patterns for legal document extraction"
min_occurrences: 2

entity_patterns:
  - name: proper_noun
    pattern: '\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    category: entity
    description: "Multi-word proper nouns"
    min_length: 3

  - name: section_reference
    pattern: '(?:Section|§)\s*(\d+(?:\.\d+)*)'
    category: reference
    description: "Section number references"

  - name: quoted_definition
    pattern: '"([^"]+)"\s+(?:means|shall mean)'
    category: definition
    description: "Quoted terms being defined"

relationship_triggers:
  - name: defines
    source_categories: [document, section]
    target_categories: [definition, term]
    proximity: 500  # characters

  - name: references
    source_categories: [section]
    target_categories: [reference]
    proximity: 0  # same sentence
```

### Pattern 3: Configuration Loader with Validation

**What:** Load and validate YAML files
**When to use:** At application startup or when --patterns flag provided
**Example:**
```python
# Source: PyYAML safe_load + Pydantic model_validate pattern
import yaml
from pathlib import Path
from .models import PatternConfig

def load_patterns(filepath: Path) -> PatternConfig:
    """Load and validate pattern configuration from YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in {filepath}: {e}")

    if raw_data is None:
        raise ValueError(f"Empty configuration file: {filepath}")

    # Pydantic validates structure and regex patterns
    return PatternConfig.model_validate(raw_data)
```

### Pattern 4: GenericExtractor Integration

**What:** Modify GenericExtractor to accept PatternConfig
**When to use:** When loading patterns from file
**Example:**
```python
class GenericExtractor(BaseExtractor):
    def __init__(
        self,
        graph: Optional[Graph] = None,
        patterns: Optional[dict[str, str]] = None,  # Existing interface
        config: Optional[PatternConfig] = None,     # NEW: config object
        min_occurrences: int = 2,
    ):
        super().__init__(graph)

        if config:
            # Build patterns dict from config
            pattern_strings = {
                ep.name: ep.pattern for ep in config.entity_patterns
            }
            self.min_occurrences = config.min_occurrences
            self._pattern_metadata = {
                ep.name: ep for ep in config.entity_patterns
            }
        else:
            pattern_strings = patterns or self.DEFAULT_PATTERNS
            self.min_occurrences = min_occurrences
            self._pattern_metadata = {}

        # Compile patterns once at init
        self._compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in pattern_strings.items()
        }
```

### Anti-Patterns to Avoid
- **Regex in YAML without validation:** Never load patterns without compiling them first - fail fast on invalid regex
- **Global mutable config:** Don't store loaded config in module-level variables; pass explicitly
- **Ignoring capture groups:** Patterns MUST have exactly one capture group for the entity value

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | PyYAML `safe_load` | Edge cases with YAML syntax, security (no arbitrary code execution) |
| Schema validation | Manual dict checking | Pydantic models | Type coercion, nested validation, clear error messages |
| Regex validation | String inspection | `re.compile()` + try/except | Only way to truly validate regex syntax |
| Default patterns file | Hardcoded fallback | Bundled YAML file | Easier to maintain, users can copy as template |

**Key insight:** YAML configuration seems simple but has many edge cases (multiline strings, special characters, escaping). Pydantic's validation errors are much clearer than manual checking.

## Common Pitfalls

### Pitfall 1: YAML String Quoting for Regex
**What goes wrong:** Regex special characters get interpreted by YAML parser
**Why it happens:** YAML has its own escaping rules that interact with regex escaping
**How to avoid:** Use single quotes for regex patterns in YAML: `pattern: '\bword\b'`
**Warning signs:** Patterns work in Python but fail when loaded from YAML; backslashes disappear

### Pitfall 2: Capture Group Mismatch
**What goes wrong:** Pattern has no capture group or multiple groups
**Why it happens:** Existing code uses `match.group(1)` assuming one capture group
**How to avoid:** Validate that patterns have exactly one capture group during load
**Warning signs:** IndexError when extracting, wrong entity values extracted

Example validation:
```python
@field_validator('pattern')
@classmethod
def validate_regex(cls, v: str) -> str:
    try:
        compiled = re.compile(v)
        if compiled.groups != 1:
            raise ValueError(
                f"Pattern must have exactly 1 capture group, found {compiled.groups}"
            )
    except re.error as e:
        raise ValueError(f"Invalid regex: {e}")
    return v
```

### Pitfall 3: Category Name Collision
**What goes wrong:** User-defined categories conflict with existing node categories
**Why it happens:** No namespace isolation between pattern configs
**How to avoid:** Document reserved category names; optionally prefix user categories
**Warning signs:** Graph visualization shows unexpected colors; category counts wrong

### Pitfall 4: Empty Pattern File
**What goes wrong:** `yaml.safe_load()` returns `None` for empty files
**Why it happens:** Empty YAML is valid YAML
**How to avoid:** Explicit check for `None` after loading
**Warning signs:** AttributeError when accessing config properties

### Pitfall 5: Relationship Proximity Complexity
**What goes wrong:** Simple character-distance proximity misses sentence boundaries
**Why it happens:** "500 characters" might span multiple unrelated paragraphs
**How to avoid:** For v1, use conservative defaults; document limitations
**Warning signs:** Spurious relationships between unrelated entities

## Code Examples

Verified patterns from official sources:

### Loading YAML with Pydantic Validation
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
import yaml
from pydantic import BaseModel, ValidationError

class Config(BaseModel):
    name: str
    patterns: list[str]

def load_config(path: str) -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)  # Raises ValidationError if invalid
```

### Regex Validation with Detailed Errors
```python
# Source: https://labex.io/tutorials/python-how-to-manage-regex-compilation-exceptions-418960
import re

def validate_regex(pattern: str) -> tuple[bool, str]:
    """Validate a regex pattern, returning (is_valid, error_message)."""
    try:
        compiled = re.compile(pattern)
        return True, ""
    except re.error as e:
        return False, f"Position {e.pos}: {e.msg}" if hasattr(e, 'pos') else str(e)
```

### Typer Optional Path Argument
```python
# Source: https://typer.tiangolo.com/tutorial/parameter-types/path/
from pathlib import Path
from typing import Annotated
import typer

@app.command()
def generate(
    input_path: Path = typer.Argument(...),
    patterns: Annotated[Path | None, typer.Option(
        "--patterns",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to patterns.yaml configuration file"
    )] = None,
):
    if patterns:
        config = load_patterns(patterns)
        extractor = GenericExtractor(config=config)
```

### Default Patterns YAML Template
```yaml
# patterns.yaml - Default extraction patterns
# Copy and modify for custom document types
version: "1.0"
name: "default"
description: "Generic document extraction patterns"
min_occurrences: 2

entity_patterns:
  - name: proper_noun
    pattern: '\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    category: proper_noun
    description: "Multi-word capitalized phrases (names, places)"
    min_length: 3

  - name: acronym
    pattern: '\b([A-Z]{2,6})\b'
    category: acronym
    description: "Uppercase acronyms 2-6 characters"
    min_length: 2

  - name: quoted_term
    pattern: '"([^"]+)"'
    category: quoted_term
    description: "Text in double quotes"
    min_length: 2

  - name: section_ref
    pattern: '(?:Section|§)\s*(\d+(?:\.\d+)*)'
    category: section_ref
    description: "Section number references"
    min_length: 1

relationship_triggers:
  - name: mentions
    source_categories: [document]
    target_categories: [proper_noun, acronym, quoted_term, section_ref]
    proximity: 0  # Document-level (any occurrence)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded regex in extractors | YAML-configured patterns | This phase | Enables per-project customization without code changes |
| Class-level pattern compilation | Instance-level with config injection | Phase 1 (GenericExtractor) | Already supports dynamic patterns |
| Manual dict validation | Pydantic model validation | Pydantic 2.0 (2023) | Better error messages, type safety |

**Deprecated/outdated:**
- pydantic 1.x syntax: Use `model_validate()` not `parse_obj()`, use `@field_validator` not `@validator`

## Open Questions

Things that couldn't be fully resolved:

1. **Relationship Trigger Implementation Scope**
   - What we know: Co-occurrence and proximity-based relationships are standard
   - What's unclear: How complex should v1 relationship triggers be?
   - Recommendation: Start with document-level "mentions" only (current behavior). Defer proximity-based triggers to future phase if needed.

2. **Multiple Pattern Files**
   - What we know: FR-3 requires "support multiple pattern files (per-project)"
   - What's unclear: Merge semantics (override? extend? namespace?)
   - Recommendation: For v1, support single --patterns file. Document that multiple file support is planned.

3. **Pattern File Discovery**
   - What we know: Need to specify path via CLI
   - What's unclear: Should we auto-discover `patterns.yaml` in input directory?
   - Recommendation: CLI-explicit only for v1. Auto-discovery adds complexity.

4. **Bundled Default Patterns Location**
   - What we know: Need a default patterns.yaml shipped with package
   - What's unclear: Best practice for bundling data files with Python packages
   - Recommendation: Use `importlib.resources` for Python 3.11+ to load bundled YAML

## Sources

### Primary (HIGH confidence)
- [Pydantic Models Documentation](https://docs.pydantic.dev/latest/concepts/models/) - Model definition, nested models, model_validate
- [Pydantic Validators Documentation](https://docs.pydantic.dev/latest/concepts/validators/) - field_validator decorator, validation modes
- [Typer Path Documentation](https://typer.tiangolo.com/tutorial/parameter-types/path/) - CLI Path options with validation

### Secondary (MEDIUM confidence)
- [freeCodeCamp YAML Regex Tutorial](https://www.freecodecamp.org/news/how-to-use-regular-expressions-in-yaml-file/) - YAML structure for regex patterns
- [LabEx Regex Compilation Exceptions](https://labex.io/tutorials/python-how-to-manage-regex-compilation-exceptions-418960) - re.error handling patterns
- [RASA RegexEntityExtractor](https://dev.to/aniket_kuyate_15acc4e6587/understanding-the-regexentityextractor-in-rasa-4903) - YAML structure for entity patterns

### Tertiary (LOW confidence)
- WebSearch results for co-occurrence relationship extraction - Validates approach but specifics need verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyYAML and Pydantic are well-documented, widely used
- Architecture: HIGH - Patterns verified against existing codebase and official docs
- Pitfalls: MEDIUM - Based on general YAML/regex experience, some project-specific

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - stable domain)
