<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/oximyHQ/oisp-spec/main/assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/oximyHQ/oisp-spec/main/assets/banner-light.svg">
  <img alt="OISP Spec - Open Interoperability Specification for AI activity observability" src="https://raw.githubusercontent.com/oximyHQ/oisp-spec/main/assets/banner-light.svg" width="100%">
</picture>

<div align="center">

# OISP Spec

**Open Inference Standard Protocol (OISP)** - The Open Interoperability Specification for AI activity observability. A universal schema for capturing AI interactions across every environment—browser, desktop, CLI, server—with support for 2,200+ models from every major provider.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Schema Version](https://img.shields.io/badge/schema-v0.1-green.svg)](schema/v0.1/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/OximyHQ/oisp-spec)

[Why OISP?](#why-oisp) · [Quick Start](#quick-start) · [Event Types](#event-types) · [Providers](#provider-support) · [Documentation](#documentation)

</div>

> **Want to see OISP in action?** Install [OISP Sensor](https://sensor.oximy.com) - our reference implementation that captures every AI interaction on your machine with zero instrumentation.
>
> ```bash
> curl -fsSL https://oisp.dev/install.sh | sudo sh
> ```

---

## The Problem

AI is everywhere - ChatGPT in the browser, Cursor on the desktop, Claude CLI in the terminal, custom agents on servers. But there's no standard way to observe what's happening:

- **Every tool logs differently** - CSV, JSON, custom formats, or nothing at all
- **Correlation is impossible** - How do you link a browser request to a file write?
- **Visibility gaps** - Did that agent actually execute the tool? What data was sent?
- **Compliance chaos** - Auditors want consistent, understandable records

## The Solution

OISP defines a **canonical event model** for capturing AI-related activity across diverse environments. One schema to rule them all.

```
┌─────────────────────────────────────────────────────────────────┐
│  Sources: eBPF, Browser Extensions, SDK, Audit Logs, Proxies   │
├─────────────────────────────────────────────────────────────────┤
│                       OISP Spec (this)                          │
│              Unified schema for all AI activity                 │
├─────────────────────────────────────────────────────────────────┤
│  Consumers: SIEMs, Observability, Compliance, Custom Tooling   │
└─────────────────────────────────────────────────────────────────┘
```

**One schema. Any source. Every consumer.**

---

## Why OISP?

Most organizations can't answer basic questions:

| Question | Without OISP | With OISP |
|----------|-------------|-----------|
| Which AI tools are being used? | Manual surveys, guessing | Automatic inventory |
| Which accounts (corporate vs personal)? | Unknown | Actor attribution |
| What data is being sent to AI providers? | Hope and pray | Full visibility |
| What actions do AI agents take? | Black box | Tool call tracing |

OISP provides a **unified event format** that enables:

1. **Inventory** - Discover all AI usage across your environment
2. **Visibility** - Understand data flows and agent behaviors
3. **Compliance** - Audit AI interactions consistently
4. **Control** - Build policies on a stable event substrate

---

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

---

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

### Validate Your Events

```bash
# Install jsonschema validator
pip install jsonschema

# Validate an event
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

---

## Event Types

| Event Type | Description | Schema |
|------------|-------------|--------|
| `process.exec` | Process execution | [process.schema.json](schema/v0.1/events/process.schema.json) |
| `process.exit` | Process termination | [process.schema.json](schema/v0.1/events/process.schema.json) |
| `network.connect` | Outbound connection | [network.schema.json](schema/v0.1/events/network.schema.json) |
| `network.flow` | Network flow summary | [network.schema.json](schema/v0.1/events/network.schema.json) |
| `file.read` | File read operation | [file.schema.json](schema/v0.1/events/file.schema.json) |
| `file.write` | File write operation | [file.schema.json](schema/v0.1/events/file.schema.json) |
| `ai.request` | AI API request | [ai.schema.json](schema/v0.1/events/ai.schema.json) |
| `ai.response` | AI API response | [ai.schema.json](schema/v0.1/events/ai.schema.json) |
| `ai.streaming_chunk` | Streaming response chunk | [ai.schema.json](schema/v0.1/events/ai.schema.json) |
| `agent.tool_call` | Agent invoking a tool | [agent.schema.json](schema/v0.1/events/agent.schema.json) |
| `agent.tool_result` | Tool execution result | [agent.schema.json](schema/v0.1/events/agent.schema.json) |
| `rag.retrieve` | RAG context retrieval | Coming soon |

---

## Examples

### AI Request (OpenAI)

```json
{
  "oisp_version": "0.1",
  "event_id": "01JGXYZ123ABC456DEF",
  "event_type": "ai.request",
  "ts": "2025-12-22T14:32:15.123456Z",
  
  "host": { "hostname": "dev-laptop", "os": "linux" },
  "actor": { "uid": 1000, "user": "alice" },
  "process": {
    "pid": 12345,
    "exe": "/usr/bin/cursor",
    "cmdline": "cursor /home/alice/project"
  },
  
  "source": {
    "collector": "oisp-sensor",
    "capture_method": "ebpf_uprobe"
  },
  
  "confidence": {
    "level": "high",
    "completeness": "full"
  },
  
  "data": {
    "provider": "openai",
    "model": "gpt-4o",
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "request": {
      "messages": [
        { "role": "system", "content": "You are a helpful assistant." },
        { "role": "user", "content": "Fix the bug in main.rs" }
      ],
      "tools": [
        { "type": "function", "function": { "name": "read_file" } },
        { "type": "function", "function": { "name": "write_file" } }
      ],
      "stream": true
    },
    "tokens": {
      "prompt": 1234
    }
  }
}
```

### Agent Tool Call

```json
{
  "oisp_version": "0.1",
  "event_id": "01JGXYZ789GHI012JKL",
  "event_type": "agent.tool_call",
  "ts": "2025-12-22T14:32:16.456789Z",
  
  "host": { "hostname": "dev-laptop", "os": "linux" },
  "actor": { "uid": 1000, "user": "alice" },
  "process": { "pid": 12345, "exe": "/usr/bin/cursor" },
  
  "source": {
    "collector": "oisp-sensor",
    "capture_method": "ebpf_uprobe"
  },
  
  "confidence": {
    "level": "high",
    "completeness": "full"
  },
  
  "trace": {
    "trace_id": "tr_01JGXYZ...",
    "parent_event_id": "01JGXYZ123ABC456DEF"
  },
  
  "data": {
    "tool_name": "write_file",
    "tool_call_id": "call_abc123",
    "arguments": {
      "path": "/home/alice/project/src/main.rs",
      "content": "fn main() { ... }"
    }
  }
}
```

See [examples/](examples/) for more complete examples.

---

## Provider Support

OISP includes fingerprinting rules for major AI providers:

| Provider | Status | Config |
|----------|:------:|--------|
| OpenAI | Complete | [openai.yaml](semconv/providers/openai.yaml) |
| Anthropic | Complete | [anthropic.yaml](semconv/providers/anthropic.yaml) |
| Google (Gemini) | Complete | [google.yaml](semconv/providers/google.yaml) |
| Azure OpenAI | Complete | [registry.yaml](semconv/providers/registry.yaml) |
| AWS Bedrock | Complete | [registry.yaml](semconv/providers/registry.yaml) |
| Cohere | Complete | [registry.yaml](semconv/providers/registry.yaml) |
| Mistral | Complete | [registry.yaml](semconv/providers/registry.yaml) |
| Groq | Complete | [registry.yaml](semconv/providers/registry.yaml) |
| Ollama (local) | Complete | [ollama.yaml](semconv/providers/ollama.yaml) |

### Adding a Provider

Providers are defined in YAML:

```yaml
# semconv/providers/example.yaml
provider:
  id: example
  name: Example AI
  
fingerprints:
  - type: domain
    pattern: "api.example.com"
    
  - type: header
    name: "x-example-version"
    
endpoints:
  chat:
    path: "/v1/chat/completions"
    method: POST
    
models:
  - id: example-large
    name: Example Large
    context_window: 128000
```

---

## Repository Structure

```
oisp-spec/
├── schema/                    # JSON Schema definitions
│   └── v0.1/
│       ├── envelope.schema.json    # Core event wrapper
│       ├── common/                  # Shared types
│       │   ├── actor.schema.json
│       │   ├── host.schema.json
│       │   ├── process.schema.json
│       │   └── confidence.schema.json
│       └── events/                  # Event type schemas
│           ├── ai.schema.json
│           ├── agent.schema.json
│           ├── file.schema.json
│           ├── network.schema.json
│           └── process.schema.json
│
├── proto/                     # Protocol Buffer definitions
│   └── oisp/v1/
│       ├── common.proto
│       └── events.proto
│
├── semconv/                   # Semantic conventions
│   ├── ai.md                  # AI-specific conventions
│   └── providers/             # Provider fingerprinting
│       ├── openai.yaml
│       ├── anthropic.yaml
│       └── ...
│
├── examples/                  # Concrete event examples
│   ├── ai-request-openai.json
│   ├── ai-response-openai.json
│   ├── agent-tool-call.json
│   └── ...
│
└── docs/                      # Extended documentation
    ├── overview.md
    └── implementors-guide.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Overview](docs/overview.md) | High-level introduction to OISP |
| [Implementor's Guide](docs/implementors-guide.md) | How to emit OISP events |
| [AI Conventions](semconv/ai.md) | AI-specific semantic conventions |
| [Provider Registry](semconv/providers/README.md) | Provider fingerprinting rules |
| [Changelog](CHANGELOG.md) | Version history |

---

## Implementations

### OISP Sensor - The Reference Implementation

<table>
<tr>
<td width="70%">

**[OISP Sensor](https://sensor.oximy.com)** is our official reference implementation. It captures every AI interaction on your machine - prompts, responses, tool calls, agent actions - with **zero instrumentation**.

- Full content capture on Linux via eBPF
- Metadata capture on macOS and Windows
- Real-time TUI and Web UI
- JSONL, WebSocket, and OTLP export

</td>
<td width="30%">

```bash
# One-line install
curl -fsSL https://oisp.dev/install.sh | sudo sh

# Run it
sudo oisp-sensor
```

</td>
</tr>
</table>

[View on GitHub](https://github.com/oximyhq/sensor) · [Documentation](https://sensor.oximy.com) · [Download](https://github.com/oximyhq/sensor/releases)

### Community

*Coming soon - contributions welcome!*

---

## Versioning

OISP follows semantic versioning:

| Version Type | Example | Changes |
|--------------|---------|---------|
| Major | v1, v2 | Breaking changes to schema |
| Minor | v0.1, v0.2 | Additive changes only |
| Patch | v0.1.1 | Bug fixes, clarifications |

Schema URLs follow the pattern: `https://oisp.dev/schema/v0.1/...`

---

## Related Projects

- **[OpenTelemetry](https://opentelemetry.io/)** - Observability framework we extend
- **[models.dev](https://models.dev)** - AI model registry we sync from (pricing, capabilities, provider endpoints)
- **[OpenAI API Spec](https://github.com/openai/openai-openapi)** - API structure reference

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where we especially need help:

- Additional provider fingerprints
- Language-specific SDK bindings
- Schema validation tools
- Documentation and examples

---

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

<div align="center">

**OISP Spec is part of the [Oximy](https://oximy.com) open-source ecosystem.**

[Website](https://oisp.dev) · [Specification](https://oisp.dev/spec) · [GitHub](https://github.com/oximyHQ/oisp-spec)

</div>
