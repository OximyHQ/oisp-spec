# OISP Spec

**Open Instrumentation for Security and Privacy** - A universal event schema for AI activity observability.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Schema Version](https://img.shields.io/badge/schema-v0.1-green.svg)](schema/v0.1/)

## What is OISP?

OISP defines a **canonical event model** for capturing AI-related activity across diverse environments:

- **Browser-based AI** (ChatGPT, Claude, Gemini web interfaces)
- **Desktop applications** (Copilot, Cursor, IDE plugins)
- **CLI tools** (llm, aider, claude-cli)
- **Server-side agents** (LangChain, AutoGPT, custom agents)
- **Enterprise suites** (Microsoft Copilot, Google Duet AI)

The goal: make "what AI is happening here?" answerable from day one.

## Why OISP?

Most organizations can't answer basic questions:
- Which AI tools are being used?
- Which accounts (corporate vs personal)?
- What data is being sent to AI providers?
- What actions do AI agents take after getting responses?

OISP provides a **unified event format** that enables:
1. **Inventory** - Discover all AI usage across your environment
2. **Visibility** - Understand data flows and agent behaviors
3. **Compliance** - Audit AI interactions consistently
4. **Control** - Build policies on a stable event substrate

## Design Principles

### 1. Confidence as First-Class

Every event explicitly declares what we know and don't know:

```json
{
  "confidence": {
    "level": "high",
    "completeness": "partial",
    "reasons": ["tls_boundary_capture", "response_truncated"]
  }
}
```

No silent failures. No lies by omission.

### 2. Multi-Source Normalization

Events from eBPF, browser extensions, vendor audit logs, and SDK instrumentation all map to the same schema. Correlation becomes possible.

### 3. Privacy by Default

The schema supports **redaction markers** - you can express "this field was redacted" without exposing the original content:

```json
{
  "prompt": {
    "$redacted": {
      "reason": "pii_detected",
      "original_length": 1547,
      "hash": "sha256:abc123..."
    }
  }
}
```

### 4. OpenTelemetry Aligned

OISP extends [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) where they exist, adding security-specific context.

## Repository Structure

```
oisp-spec/
├── schema/                    # JSON Schema definitions
│   └── v0.1/
│       ├── envelope.schema.json    # Core event wrapper
│       ├── common/                  # Shared types
│       └── events/                  # Event type schemas
│
├── proto/                     # Protocol Buffer definitions
│   └── oisp/v1/
│
├── semconv/                   # Semantic conventions
│   ├── ai.md                  # AI-specific conventions
│   └── providers/             # Provider fingerprinting
│
├── examples/                  # Concrete event examples
│
└── docs/                      # Extended documentation
```

## Quick Start

### Event Envelope

Every OISP event has this structure:

```json
{
  "oisp_version": "0.1",
  "event_id": "01HQXYZ123ABC...",
  "event_type": "ai.request",
  "ts": "2025-12-22T20:15:05.123456Z",
  
  "host": { "hostname": "dev-laptop", "os": "darwin" },
  "actor": { "uid": 501, "user": "alice" },
  "process": { "pid": 1234, "exe": "/usr/bin/curl" },
  
  "source": {
    "collector": "oisp-sensor",
    "capture_method": "ebpf_uprobe"
  },
  
  "confidence": {
    "level": "high",
    "completeness": "full"
  },
  
  "data": {
    // Event-type-specific payload
  }
}
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `process.exec` | Process execution |
| `process.exit` | Process termination |
| `network.connect` | Outbound connection |
| `network.flow` | Network flow summary |
| `file.read` | File read operation |
| `file.write` | File write operation |
| `ai.request` | AI API request |
| `ai.response` | AI API response |
| `ai.streaming_chunk` | Streaming response chunk |
| `agent.tool_call` | Agent invoking a tool |
| `agent.tool_result` | Tool execution result |
| `rag.retrieve` | RAG context retrieval |

## Provider Support

OISP includes fingerprinting rules for major AI providers. See [semconv/providers/](semconv/providers/).

| Provider | Status |
|----------|--------|
| OpenAI | Complete |
| Anthropic | Complete |
| Google (Gemini) | Complete |
| Azure OpenAI | Complete |
| AWS Bedrock | Complete |
| Cohere | Complete |
| Mistral | Complete |
| Ollama (local) | Complete |

## Related Projects

- **[oisp-sensor](https://github.com/oximyHQ/oisp-sensor)** - Reference sensor implementation
- **[OpenTelemetry](https://opentelemetry.io/)** - Observability framework we extend
- **[LiteLLM](https://github.com/BerriAI/litellm)** - Provider model registry we reference

## Versioning

OISP follows semantic versioning:
- **Major versions** (v1, v2): Breaking changes
- **Minor versions** (v0.1, v0.2): Additive changes only
- **Schema URL**: `https://oisp.dev/schema/v0.1/...`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

**OISP is part of the [Oximy](https://oximy.com) open-source ecosystem.**

