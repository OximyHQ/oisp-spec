# OISP Spec

Open Inference Standard Protocol - canonical event schema for AI activity observability.

## Quick Reference

```bash
# Validate schemas
python -c "import jsonschema; ..."  # See README for full command

# Build docs site
cd site && npm run build

# Generate code from proto
protoc --python_out=. proto/oisp/v1/*.proto
```

## Repository Structure

```
schema/v0.1/
├── envelope.schema.json     # Core event wrapper (MUST understand first)
├── common/                  # Shared type definitions
│   ├── actor.schema.json    # User/process attribution
│   ├── host.schema.json     # Machine identification
│   ├── process.schema.json  # Process metadata
│   └── confidence.schema.json # Capture confidence levels
└── events/                  # Event-specific payloads
    ├── ai.schema.json       # ai.request, ai.response
    ├── agent.schema.json    # agent.tool_call, agent.tool_result
    ├── file.schema.json     # file.read, file.write
    ├── network.schema.json  # network.connect, network.flow
    └── process.schema.json  # process.exec, process.exit

proto/oisp/v1/              # Protocol Buffer definitions (mirrors schema/)

semconv/                    # Semantic conventions
├── ai.md                   # AI-specific field meanings
└── providers/              # Provider fingerprinting rules (YAML)
    ├── openai.yaml
    ├── anthropic.yaml
    └── registry.yaml       # Full provider registry

examples/                   # Concrete event examples (use for testing)
```

## Key Concepts

**Event envelope**: Every event has the same wrapper structure:
- `oisp_version`, `event_id`, `event_type`, `ts`
- `host`, `actor`, `process` - attribution
- `source` - how the event was captured
- `confidence` - capture completeness
- `data` - event-type-specific payload

**Confidence as first-class**: Events explicitly declare what's known vs unknown:
```json
{
  "confidence": {
    "level": "high",
    "completeness": "partial",
    "reasons": ["response_truncated"]
  }
}
```

**Redaction markers**: Support privacy without losing structure:
```json
{
  "prompt": {
    "$redacted": { "reason": "pii_detected", "hash": "sha256:..." }
  }
}
```

## Common Tasks

**Add new event type:**
1. Create schema in `schema/v0.1/events/`
2. Add example in `examples/`
3. Update proto definitions in `proto/`
4. Document in `docs/`

**Add AI provider:**
1. Create YAML in `semconv/providers/` with fingerprints and endpoints
2. Add to `registry.yaml`
3. Create example event

**Modify envelope:**
- DO NOT add required fields (breaking change)
- New optional fields are OK
- Update both JSON Schema and Proto

## Schema Versioning

- Current: `v0.1` (pre-stable)
- Breaking changes = major version bump
- Additive changes = minor version bump
- Schema URL pattern: `https://oisp.dev/schema/v0.1/...`

## Validation

```bash
# Validate event against schema
python -c "
import json, jsonschema
with open('schema/v0.1/envelope.schema.json') as f:
    schema = json.load(f)
with open('examples/ai-request-openai.json') as f:
    event = json.load(f)
jsonschema.validate(event, schema)
print('Valid!')
"
```
