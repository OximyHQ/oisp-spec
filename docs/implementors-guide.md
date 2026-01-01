# OISP Implementor's Guide

This guide explains how to build an OISP-compliant sensor or integrate OISP event generation into your system.

> **Reference Implementation Available**: Before building your own, check out [OISP Sensor](https://sensor.oximy.com) - our reference implementation that handles all the complexities described below. It's open source and can serve as a starting point or reference for your own implementation.
>
> ```bash
> curl -fsSL https://oisp.dev/install.sh | sudo sh
> ```

## Overview

An OISP implementation typically involves:

1. **Capture**: Collect raw signals (process, network, file, AI)
2. **Decode**: Parse protocols and extract meaning
3. **Normalize**: Transform to OISP event format
4. **Enrich**: Add context (provider detection, cost estimation)
5. **Redact**: Apply privacy controls
6. **Export**: Send to downstream consumers

## Event Generation

### Required Fields

Every OISP event MUST include:

```json
{
  "oisp_version": "0.1",
  "event_id": "01JFWK8X2N3M4P5Q6R7S8T9U0V",
  "event_type": "ai.request",
  "ts": "2025-12-22T14:30:15.123456Z",
  "source": {
    "collector": "my-sensor"
  },
  "confidence": {
    "level": "high",
    "completeness": "full"
  }
}
```

### Event ID Generation

We recommend **ULID** (Universally Unique Lexicographically Sortable Identifier):

```
01JFWK8X2N3M4P5Q6R7S8T9U0V
├───────────┘└──────────────┤
  Timestamp     Randomness
  (48 bits)     (80 bits)
```

Benefits:
- Lexicographically sortable (time-ordered)
- Globally unique
- Timestamp extractable from ID

Libraries:
- Rust: `ulid`
- Python: `python-ulid`
- Go: `github.com/oklog/ulid`
- JavaScript: `ulid`

### Timestamp Precision

Use RFC 3339 with microsecond precision:

```
2025-12-22T14:30:15.123456Z
                   └──────┘
                   Microseconds
```

Always use UTC (indicated by `Z` suffix).

### Event Type Hierarchy

Event types follow a hierarchical naming convention:

```
{category}.{action}
{category}.{subcategory}.{action}
```

Examples:
- `process.exec`
- `network.connect`
- `ai.request`
- `agent.tool_call`

## Confidence Metadata

### Confidence Levels

| Level | Description | Use When |
|-------|-------------|----------|
| `high` | High certainty in accuracy | Kernel-level capture, verified process attribution |
| `medium` | Reasonable certainty | Some inference involved, timing-based correlation |
| `low` | Significant uncertainty | Heuristic detection, partial data |
| `inferred` | Best guess | Pattern matching, no direct observation |

### Completeness Levels

| Level | Description | Use When |
|-------|-------------|----------|
| `full` | All available data captured | Complete request/response, no truncation |
| `partial` | Some data missing | Response truncated, headers only |
| `metadata_only` | Only metadata, no content | Flow information without payload |
| `redacted` | Content intentionally removed | Privacy controls applied |
| `sampled` | Statistically sampled | High-volume traffic sampling |
| `vendor_reported` | Data from vendor audit logs | Third-party telemetry |

### Documenting Limitations

Always document what you know and don't know:

```json
{
  "confidence": {
    "level": "medium",
    "completeness": "partial",
    "reasons": [
      "tls_boundary_capture",
      "response_truncated_at_64kb"
    ],
    "missing": [
      "full_response_body",
      "request_timing"
    ],
    "process_attribution": "timing_correlation"
  }
}
```

## Provider Detection

### Domain-Based Detection

Use the provider registry for initial classification:

```python
PROVIDER_DOMAINS = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
    "generativelanguage.googleapis.com": "google",
    # ... etc
}

def detect_provider(domain: str) -> str | None:
    # Exact match
    if domain in PROVIDER_DOMAINS:
        return PROVIDER_DOMAINS[domain]
    
    # Pattern match (e.g., *.openai.azure.com)
    for pattern, provider in DOMAIN_PATTERNS:
        if fnmatch(domain, pattern):
            return provider
    
    return None
```

### Endpoint-Based Detection

Refine detection using request path:

```python
OPENAI_ENDPOINTS = {
    "/v1/chat/completions": ("chat", True),   # (type, streaming_capable)
    "/v1/completions": ("completion", True),
    "/v1/embeddings": ("embedding", False),
    # ...
}

def detect_request_type(provider: str, path: str) -> dict:
    if provider == "openai":
        if path in OPENAI_ENDPOINTS:
            req_type, streaming = OPENAI_ENDPOINTS[path]
            return {"request_type": req_type, "streaming_capable": streaming}
    # ...
```

### Model Extraction

Extract model from request/response:

```python
def extract_model(provider: str, body: dict) -> dict | None:
    if provider in ("openai", "anthropic"):
        model_id = body.get("model")
        if model_id:
            return {
                "id": model_id,
                "family": infer_family(model_id)
            }
    elif provider == "google":
        # Model is in URL path, not body
        pass
    return None
```

### Token Usage Extraction

Map provider-specific fields to OISP:

```python
def extract_usage(provider: str, response: dict) -> dict:
    if provider == "openai":
        usage = response.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens")
        }
    elif provider == "anthropic":
        usage = response.get("usage", {})
        return {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens")
        }
    elif provider == "google":
        metadata = response.get("usageMetadata", {})
        return {
            "prompt_tokens": metadata.get("promptTokenCount"),
            "completion_tokens": metadata.get("candidatesTokenCount")
        }
    return {}
```

## Redaction

### Default Safe Posture

By default, redact all content and export metadata only:

```python
def redact_message(message: dict) -> dict:
    content = message.get("content", "")
    return {
        "role": message.get("role"),
        "content": {
            "$redacted": {
                "reason": "default_safe",
                "original_length": len(content),
                "hash": sha256_truncated(content)
            }
        }
    }
```

### PII Detection

Run detectors before export:

```python
PII_PATTERNS = {
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "api_key": r'\b(sk-|sk-proj-|sk-ant-)[a-zA-Z0-9]{20,}\b',
}

def detect_pii(content: str) -> list[dict]:
    findings = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            findings.append({"type": pii_type, "count": len(matches)})
    return findings
```

### Redaction Marker

When redacting, preserve metadata for correlation:

```python
def create_redaction_marker(content: str, reason: str, detector: str = None) -> dict:
    findings = detect_pii(content) if reason == "pii_detected" else []
    
    return {
        "$redacted": {
            "reason": reason,
            "detector": detector,
            "original_length": len(content),
            "hash": sha256(content.encode())[:16],  # Truncated hash
            "preview": safe_preview(content, max_len=50),
            "findings": findings if findings else None
        }
    }

def safe_preview(content: str, max_len: int = 50) -> str:
    """Generate a safe preview by taking first N chars if no PII detected."""
    preview = content[:max_len]
    if detect_pii(preview):
        return None  # Don't include preview if it contains PII
    return preview + "..." if len(content) > max_len else preview
```

## Process Context

### Process Attribution

Link network events to processes:

```python
# Linux: Use socket inode → process mapping
def get_process_for_socket(inode: int) -> dict | None:
    # Read /proc/*/fd/* to find matching socket
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        fd_dir = pid_dir / "fd"
        for fd in fd_dir.iterdir():
            try:
                target = fd.resolve()
                if f"socket:[{inode}]" in str(target):
                    return read_process_info(int(pid_dir.name))
            except:
                pass
    return None
```

### Process Tree

Capture ancestry for context:

```python
def get_process_tree(pid: int, max_depth: int = 5) -> list[dict]:
    tree = []
    current_pid = pid
    
    for _ in range(max_depth):
        info = read_process_info(current_pid)
        if not info or current_pid == 1:
            break
        tree.append({
            "pid": info["pid"],
            "exe": info["exe"],
            "name": info["name"]
        })
        current_pid = info["ppid"]
    
    return tree
```

## Streaming Responses

### SSE Reassembly

For streaming AI responses, reassemble the full response:

```python
class StreamingResponseAssembler:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.chunks = []
        self.start_time = time.time()
        self.first_token_time = None
    
    def add_chunk(self, chunk: str):
        if not self.chunks:
            self.first_token_time = time.time()
        
        # Parse SSE format: "data: {...}"
        if chunk.startswith("data: "):
            data = json.loads(chunk[6:])
            self.chunks.append(data)
    
    def finalize(self) -> dict:
        # Merge chunks into complete response
        full_content = ""
        tool_calls = []
        finish_reason = None
        usage = None
        
        for chunk in self.chunks:
            if "choices" in chunk:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    full_content += delta["content"]
                if "tool_calls" in delta:
                    tool_calls.extend(delta["tool_calls"])
                if chunk["choices"][0].get("finish_reason"):
                    finish_reason = chunk["choices"][0]["finish_reason"]
            if "usage" in chunk:
                usage = chunk["usage"]
        
        return {
            "request_id": self.request_id,
            "content": full_content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "usage": usage,
            "latency_ms": int((time.time() - self.start_time) * 1000),
            "time_to_first_token_ms": int((self.first_token_time - self.start_time) * 1000) if self.first_token_time else None
        }
```

## Export Formats

### OTLP (Recommended)

Map OISP events to OpenTelemetry spans:

```python
def oisp_to_otlp_span(event: dict) -> Span:
    span = Span()
    span.trace_id = event.get("trace_context", {}).get("trace_id") or generate_trace_id()
    span.span_id = generate_span_id()
    span.name = event["event_type"]
    span.start_time_unix_nano = parse_timestamp_nano(event["ts"])
    
    # Map OISP fields to span attributes
    span.attributes.append(KeyValue("oisp.version", event["oisp_version"]))
    span.attributes.append(KeyValue("oisp.event_id", event["event_id"]))
    
    # Add AI-specific attributes with gen_ai prefix for OTel compatibility
    if event["event_type"].startswith("ai."):
        data = event.get("data", {})
        if "provider" in data:
            span.attributes.append(KeyValue("gen_ai.system", data["provider"]["name"]))
        if "model" in data:
            span.attributes.append(KeyValue("gen_ai.request.model", data["model"]["id"]))
    
    return span
```

### JSON Lines

Simple line-delimited JSON:

```python
def export_jsonl(events: list[dict], output: IO):
    for event in events:
        output.write(json.dumps(event, separators=(',', ':')) + '\n')
```

### Webhook

POST events to HTTP endpoint:

```python
async def export_webhook(events: list[dict], url: str, batch_size: int = 100):
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={"events": batch})
```

## Validation

### Schema Validation

Validate events against JSON Schema:

```python
import jsonschema

def load_schemas():
    schema_dir = Path("schema/v0.1")
    return {
        "envelope": json.load(open(schema_dir / "envelope.schema.json")),
        "ai": json.load(open(schema_dir / "events/ai.schema.json")),
        # ...
    }

def validate_event(event: dict, schemas: dict) -> list[str]:
    errors = []
    
    # Validate envelope
    try:
        jsonschema.validate(event, schemas["envelope"])
    except jsonschema.ValidationError as e:
        errors.append(f"Envelope: {e.message}")
    
    # Validate event-type-specific data
    event_type = event.get("event_type", "")
    category = event_type.split(".")[0]
    if category in schemas:
        try:
            jsonschema.validate(event.get("data", {}), schemas[category])
        except jsonschema.ValidationError as e:
            errors.append(f"Data: {e.message}")
    
    return errors
```

## Testing

### Example Events

Use the examples in `/examples/` as test cases:

```python
def test_example_events():
    schemas = load_schemas()
    examples_dir = Path("examples")
    
    for example_file in examples_dir.glob("*.json"):
        event = json.load(open(example_file))
        errors = validate_event(event, schemas)
        assert not errors, f"{example_file.name}: {errors}"
```

### Capture Testing

Test with known AI API calls:

```python
def test_openai_detection():
    # Simulate captured traffic
    request = {
        "method": "POST",
        "host": "api.openai.com",
        "path": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
    }
    
    event = capture_to_oisp_event(request)
    
    assert event["event_type"] == "ai.request"
    assert event["data"]["provider"]["name"] == "openai"
    assert event["data"]["model"]["id"] == "gpt-4o"
    assert event["data"]["streaming"] == True
```

## Best Practices

1. **Always set confidence**: Never emit events without confidence metadata
2. **Prefer metadata over content**: Default to `completeness: metadata_only`
3. **Hash for correlation**: Include content hashes even when redacting
4. **Link related events**: Use `related_events` for request/response pairs
5. **Validate before export**: Check events against schema before sending
6. **Use ULID for IDs**: Enables time-based ordering and debugging
7. **Capture process context**: Always include process info when available
8. **Document limitations**: Be explicit about what's missing or uncertain

