# Phase 4: LLM Extractor - Research

**Researched:** 2026-01-21
**Domain:** Anthropic Claude API, Entity Extraction, Knowledge Graphs
**Confidence:** HIGH

## Summary

This research covers implementing an LLM-powered entity and relationship extractor using the Anthropic Claude API. The implementation requires careful attention to token management, cost estimation, rate limiting, and data sovereignty compliance.

The Anthropic Python SDK (v0.76.0+) provides comprehensive support for our needs including: synchronous/async clients, token counting API, structured outputs via JSON schema, and built-in httpx-based networking. Document chunking should use semantic or token-based strategies to fit within Claude's 200K context window while maintaining extraction quality.

**Primary recommendation:** Use Claude Sonnet 4.5 ($3/$15 per MTok) with structured JSON outputs for schema-guaranteed extraction. Implement token counting before API calls for cost transparency. Use the tenacity library for exponential backoff rate limiting.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.76.0 | Claude API client | Official SDK, type-safe, async support |
| tenacity | >=8.2.0 | Retry/backoff logic | De facto standard for Python retries |
| pydantic | >=2.0 | Schema definition | Integrates with SDK's structured outputs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tiktoken | >=0.5.0 | Offline token estimation | Rough pre-estimation without API call |
| httpx | (via anthropic) | HTTP client | Comes with SDK, handles retries |
| python-dotenv | >=1.0.0 | Credential management | Load ANTHROPIC_API_KEY from .env |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| anthropic SDK | Direct REST calls | Lose type safety, structured outputs, retries |
| tenacity | Custom backoff | More code, less tested |
| Sonnet 4.5 | Haiku 4.5 | 3x cheaper but lower extraction quality |
| Sonnet 4.5 | Opus 4.5 | Better quality but 67% more expensive |

**Installation:**
```bash
pip install anthropic>=0.76.0 tenacity>=8.2.0 python-dotenv>=1.0.0
# Or add to pyproject.toml [llm] extras
```

## Architecture Patterns

### Recommended Project Structure
```
src/cosmograph/extractors/
├── base.py           # BaseExtractor ABC (existing)
├── llm.py            # NEW: LlmExtractor class
└── llm_utils/        # NEW: LLM support utilities
    ├── __init__.py
    ├── chunking.py   # Document chunking strategies
    ├── prompts.py    # Extraction prompts/schemas
    ├── rate_limit.py # Rate limiting helpers
    └── schemas.py    # Pydantic models for extraction
```

### Pattern 1: Token-Aware Processing Pipeline

**What:** Estimate tokens before API call, get operator approval, then process
**When to use:** Any LLM extraction operation (data sovereignty requirement)
**Example:**
```python
# Source: Anthropic Token Counting API docs
import anthropic

async def extract_with_approval(self, document: str) -> Graph:
    client = anthropic.Anthropic()

    # 1. Count tokens first (free API call)
    count_response = client.messages.count_tokens(
        model="claude-sonnet-4-5",
        system=self.system_prompt,
        messages=[{"role": "user", "content": document}],
    )

    # 2. Estimate cost
    input_tokens = count_response.input_tokens
    estimated_output = min(input_tokens // 2, 4096)  # Conservative estimate
    cost = self._calculate_cost(input_tokens, estimated_output)

    # 3. Get operator approval (data sovereignty gate)
    if not self._get_approval(input_tokens, cost):
        raise OperatorDeclinedError("Operator declined LLM extraction")

    # 4. Process with structured output
    response = client.beta.messages.create(
        model="claude-sonnet-4-5",
        betas=["structured-outputs-2025-11-13"],
        max_tokens=estimated_output,
        messages=[{"role": "user", "content": document}],
        output_format=self.extraction_schema,
    )

    return self._parse_response(response)
```

### Pattern 2: Structured Output with Pydantic

**What:** Use Pydantic models for guaranteed JSON schema compliance
**When to use:** Parsing LLM responses into Graph nodes/edges
**Example:**
```python
# Source: Anthropic Structured Outputs docs
from pydantic import BaseModel
from typing import List
from anthropic import transform_schema

class ExtractedEntity(BaseModel):
    name: str
    category: str
    description: str

class ExtractedRelationship(BaseModel):
    source: str
    target: str
    relationship_type: str

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]

# Use with SDK
response = client.beta.messages.parse(
    model="claude-sonnet-4-5",
    betas=["structured-outputs-2025-11-13"],
    max_tokens=4096,
    output_format=ExtractionResult,
    messages=[{"role": "user", "content": document}],
)

result = response.parsed_output  # Type-safe ExtractionResult
```

### Pattern 3: Exponential Backoff with Tenacity

**What:** Automatic retries with jitter for rate limit handling
**When to use:** All API calls
**Example:**
```python
# Source: Tenacity docs + OpenAI cookbook patterns
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)
from anthropic import RateLimitError

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError),
)
def call_claude_api(client, **kwargs):
    return client.messages.create(**kwargs)
```

### Pattern 4: Document Chunking Strategy

**What:** Split large documents into processable chunks with overlap
**When to use:** Documents exceeding context window or for better extraction
**Example:**
```python
# Token-based chunking with overlap
def chunk_document(text: str, max_tokens: int = 100000, overlap_tokens: int = 500) -> List[str]:
    """Chunk document by approximate token count."""
    # Approximate: 1 token ~= 4 characters in English
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars

        # Find paragraph boundary for cleaner splits
        if end < len(text):
            boundary = text.rfind('\n\n', start, end)
            if boundary > start + (max_chars // 2):
                end = boundary

        chunks.append(text[start:end])
        start = end - overlap_chars  # Overlap for context continuity

    return chunks
```

### Anti-Patterns to Avoid
- **Sending full documents without token estimation:** Leads to surprise costs, violates data sovereignty
- **Not chunking large documents:** Loses context in "lost in the middle" problem
- **Fixed retry delays:** Causes thundering herd, use exponential backoff with jitter
- **Parsing JSON with regex:** Use structured outputs for guaranteed schema compliance
- **Hardcoding API keys:** Always use environment variables

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Character-based estimation | `client.messages.count_tokens()` | SDK provides exact counts, free API |
| JSON parsing | Regex extraction | Structured outputs with Pydantic | Schema guaranteed, type-safe |
| Rate limiting | Simple sleep() | tenacity with exponential backoff | Handles jitter, retries, edge cases |
| Retry logic | Manual try/except loops | tenacity decorators | Production-tested, configurable |
| Cost estimation | Manual calculation | SDK token counts + pricing table | Accurate, maintainable |

**Key insight:** The Anthropic SDK provides battle-tested solutions for token counting, structured outputs, and async operations. Custom implementations introduce bugs and maintenance burden.

## Common Pitfalls

### Pitfall 1: Ignoring Token Limits
**What goes wrong:** API rejects request, wasted computation on document preparation
**Why it happens:** Documents exceed 200K context window, or output tokens capped
**How to avoid:** Always count tokens before API call, chunk large documents
**Warning signs:** 400 errors with "maximum context length" message

### Pitfall 2: Underestimating Output Tokens
**What goes wrong:** Response truncated mid-extraction, incomplete data
**Why it happens:** `max_tokens` set too low for extraction output
**How to avoid:** Set `max_tokens` based on expected output size (entity count * ~100 tokens)
**Warning signs:** `stop_reason: "max_tokens"` in response

### Pitfall 3: Not Handling Refusals
**What goes wrong:** App crashes when Claude refuses extraction request
**Why it happens:** Claude maintains safety properties even with structured outputs
**How to avoid:** Check `stop_reason: "refusal"` and handle gracefully
**Warning signs:** Invalid JSON despite structured output mode

### Pitfall 4: Rate Limit Thundering Herd
**What goes wrong:** Multiple retries hit at same time, prolonged 429 errors
**Why it happens:** Fixed retry delays without jitter
**How to avoid:** Use `wait_random_exponential` for randomized backoff
**Warning signs:** Repeated 429 errors in logs

### Pitfall 5: Lost-in-the-Middle Effect
**What goes wrong:** LLM misses entities in middle of long documents
**Why it happens:** Attention bias toward beginning and end of context
**How to avoid:** Chunk documents, process separately, merge results
**Warning signs:** Entities from middle sections consistently missing

### Pitfall 6: Missing Data Sovereignty Gate
**What goes wrong:** Document content sent to external API without operator awareness
**Why it happens:** Automatic processing without explicit approval step
**How to avoid:** Always show token estimate and cost, require explicit confirmation
**Warning signs:** Compliance violations, operator surprise at API usage

## Code Examples

Verified patterns from official sources:

### Token Counting Before API Call
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/token-counting
import anthropic

client = anthropic.Anthropic()

def estimate_extraction_cost(document: str, system_prompt: str) -> dict:
    """Count tokens and estimate cost before extraction."""
    response = client.messages.count_tokens(
        model="claude-sonnet-4-5",
        system=system_prompt,
        messages=[{"role": "user", "content": document}],
    )

    input_tokens = response.input_tokens
    # Conservative output estimate: extraction typically < 25% of input
    estimated_output = min(input_tokens // 4, 4096)

    # Sonnet 4.5 pricing: $3/MTok input, $15/MTok output
    input_cost = (input_tokens / 1_000_000) * 3.00
    output_cost = (estimated_output / 1_000_000) * 15.00
    total_cost = input_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "estimated_output_tokens": estimated_output,
        "estimated_cost_usd": total_cost,
    }
```

### Structured Output Extraction
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
from pydantic import BaseModel
from typing import List, Optional
import anthropic

class Entity(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None

class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str

class ExtractionResult(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]

def extract_graph(client: anthropic.Anthropic, document: str) -> ExtractionResult:
    """Extract entities and relationships using structured output."""
    response = client.beta.messages.parse(
        model="claude-sonnet-4-5",
        betas=["structured-outputs-2025-11-13"],
        max_tokens=4096,
        output_format=ExtractionResult,
        system="""You are a knowledge graph extraction expert. Extract entities and relationships from the provided document.

For entities, identify:
- People, organizations, government bodies
- Legal concepts, definitions, regulations
- Locations, dates, documents referenced

For relationships, identify connections like:
- "defines", "references", "amends", "supersedes"
- "establishes", "governs", "authorizes"
- "belongs_to", "contains", "reports_to"

Be thorough but precise. Only extract clearly stated facts.""",
        messages=[{"role": "user", "content": document}],
    )

    return response.parsed_output
```

### Rate-Limited API Wrapper
```python
# Source: Tenacity docs + Anthropic rate limit docs
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from anthropic import RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

class RateLimitedClient:
    """Anthropic client with automatic rate limit handling."""

    def __init__(self):
        self.client = anthropic.Anthropic()

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((RateLimitError,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def create_message(self, **kwargs):
        """Create message with automatic retry on rate limits."""
        return self.client.messages.create(**kwargs)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((RateLimitError,)),
    )
    def count_tokens(self, **kwargs):
        """Count tokens with automatic retry."""
        return self.client.messages.count_tokens(**kwargs)
```

### Approval Gate for Data Sovereignty
```python
# Source: Project requirements (data sovereignty compliance)
from rich.console import Console
from rich.table import Table
import hashlib

console = Console()

def approval_gate(
    document: str,
    token_estimate: dict,
    interactive: bool = True,
) -> bool:
    """Display extraction details and get operator approval."""

    # Create audit log entry (hash, not content)
    doc_hash = hashlib.sha256(document.encode()).hexdigest()[:16]

    # Display cost estimate
    table = Table(title="LLM Extraction Request")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Document Hash", doc_hash)
    table.add_row("Input Tokens", f"{token_estimate['input_tokens']:,}")
    table.add_row("Est. Output Tokens", f"{token_estimate['estimated_output_tokens']:,}")
    table.add_row("Est. Cost (USD)", f"${token_estimate['estimated_cost_usd']:.4f}")

    console.print(table)
    console.print("\n[yellow]This will send document content to Anthropic's Claude API.[/yellow]")

    if not interactive:
        return True  # Non-interactive mode (e.g., batch processing with prior approval)

    response = console.input("\n[bold]Proceed with extraction? [y/N]: [/bold]")
    return response.lower() in ('y', 'yes')
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex JSON parsing | Structured outputs (beta) | Nov 2025 | Guaranteed schema compliance |
| Manual token estimation | Token counting API | Nov 2024 | Exact counts, free API |
| Fixed retry delays | Exponential backoff + jitter | Standard practice | Better rate limit handling |
| Free-form text output | JSON schema mode | Nov 2025 | Type-safe extraction |

**Deprecated/outdated:**
- `claude-3-sonnet-20240229`: Use `claude-sonnet-4-5` instead
- Manual JSON parsing with try/except: Use structured outputs
- tiktoken for Anthropic models: Use official token counting API (more accurate)

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal chunk size for extraction quality**
   - What we know: Smaller chunks avoid lost-in-the-middle, larger chunks have more context
   - What's unclear: Ideal balance for legal document extraction specifically
   - Recommendation: Start with 50K tokens, experiment, document findings

2. **Hybrid mode merge strategy**
   - What we know: Pattern extraction should run first, LLM for gaps
   - What's unclear: How to identify "gaps" algorithmically, merge conflict resolution
   - Recommendation: Implement simple deduplication first, iterate based on results

3. **Cost-quality tradeoff between models**
   - What we know: Haiku cheaper (3x), Sonnet more capable
   - What's unclear: Extraction quality difference for legal documents specifically
   - Recommendation: Default to Sonnet, offer Haiku option for budget-constrained use

## Sources

### Primary (HIGH confidence)
- [Anthropic SDK GitHub](https://github.com/anthropics/anthropic-sdk-python) - Client usage, async, streaming
- [Token Counting API](https://platform.claude.com/docs/en/build-with-claude/token-counting) - Free token counting
- [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - JSON schema mode
- [Rate Limits](https://platform.claude.com/docs/en/api/rate-limits) - Tier limits, retry-after
- [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) - Token costs by model

### Secondary (MEDIUM confidence)
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry library
- [Pinecone Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/) - Chunking patterns
- [OpenAI Rate Limit Cookbook](https://cookbook.openai.com/examples/how_to_handle_rate_limits) - Backoff patterns

### Tertiary (LOW confidence)
- [Medium: LLM Knowledge Graph Construction](https://medium.com/@claudiubranzan/from-llms-to-knowledge-graphs-building-production-ready-graph-systems-in-2025-2b4aff1ec99a) - Extraction patterns
- [Testing APIs with Pytest](https://codilime.com/blog/testing-apis-with-pytest-mocks-in-python/) - Mocking patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDK documentation verified
- Architecture patterns: HIGH - Based on official docs and established patterns
- Token counting: HIGH - Free API with official docs
- Structured outputs: HIGH - Official beta feature, well documented
- Rate limiting: HIGH - Official docs + tenacity is standard
- Pricing: HIGH - Official pricing page verified
- Chunking strategies: MEDIUM - General LLM patterns, not Anthropic-specific
- Extraction prompts: MEDIUM - Based on community patterns, needs validation

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - APIs stable but structured outputs in beta)

---

## Appendix: Pricing Quick Reference

### Claude Sonnet 4.5 (Recommended for this project)
| Usage Type | Price per Million Tokens |
|------------|--------------------------|
| Input | $3.00 |
| Output | $15.00 |
| Batch Input (50% off) | $1.50 |
| Batch Output (50% off) | $7.50 |
| Cache Read | $0.30 |
| Cache Write (5m) | $3.75 |

### Cost Estimation Formula
```python
def estimate_cost(input_tokens: int, output_tokens: int, model: str = "sonnet-4.5") -> float:
    """Estimate API cost in USD."""
    prices = {
        "sonnet-4.5": {"input": 3.00, "output": 15.00},
        "haiku-4.5": {"input": 1.00, "output": 5.00},
        "opus-4.5": {"input": 5.00, "output": 25.00},
    }
    p = prices.get(model, prices["sonnet-4.5"])
    return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]
```

### Rate Limits by Tier (Claude Sonnet 4.x)
| Tier | RPM | ITPM | OTPM |
|------|-----|------|------|
| 1 | 50 | 30,000 | 8,000 |
| 2 | 1,000 | 450,000 | 90,000 |
| 3 | 2,000 | 800,000 | 160,000 |
| 4 | 4,000 | 2,000,000 | 400,000 |

*Note: Cached tokens do not count toward ITPM limits on Claude 4.x models*
