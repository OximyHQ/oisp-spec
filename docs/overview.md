# OISP Architecture Overview

This document provides a comprehensive overview of the OISP (Open Inference Standard Protocol) specification. OISP is the Open Interoperability Specification for AI activity observability—a universal schema for capturing AI interactions across every environment—browser, desktop, CLI, server—with support for 2,200+ models from every major provider.

## Vision

OISP addresses a critical gap in enterprise security: **visibility into AI activity**.

Most organizations cannot answer basic questions:
- Which AI tools are being used across browser, desktop, CLI, and IDE?
- Which accounts are being used - corporate SSO or personal?
- What data paths exist - copy/paste, file uploads, API calls, RAG?
- What happens after an AI agent gets a response - file writes, network egress?

OISP provides a **universal event substrate** for AI activity that enables inventory, detection, and control.

## Core Principles

### 1. Confidence as First-Class

Every OISP event explicitly declares what we know and don't know:

```json
{
  "confidence": {
    "level": "high",
    "completeness": "partial",
    "reasons": ["tls_boundary_capture", "response_truncated"],
    "missing": ["full_response_body"]
  }
}
```

This is a key differentiator from existing solutions that silently drop events they can't fully capture.

### 2. Multi-Source Normalization

Events from different capture methods normalize to the same schema:

| Source | Capture Method | Example |
|--------|---------------|---------|
| eBPF | Kernel tracepoints, kprobes, uprobes | Process exec, file writes |
| TLS boundary | SSL_read/SSL_write interception | AI API request/response content |
| Browser extension | DOM/network interception | ChatGPT web interface |
| Vendor audit logs | API ingestion | Microsoft Copilot via Purview |
| SDK instrumentation | Explicit tracing | LangChain integration |

All sources produce the same event structure, enabling cross-source correlation.

### 3. Privacy by Default

The spec includes first-class support for redaction:

```json
{
  "prompt": {
    "$redacted": {
      "reason": "pii_detected",
      "detector": "regex_email",
      "original_length": 1547,
      "hash": "sha256:abc123..."
    }
  }
}
```

Sensors should default to metadata-only capture, with explicit opt-in for content.

### 4. OpenTelemetry Aligned

OISP extends [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) where they exist, particularly the [GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/).

## Event Model

### Envelope

Every OISP event shares a common envelope:

```
┌─────────────────────────────────────────────────────────────┐
│ Event Envelope                                               │
├─────────────────────────────────────────────────────────────┤
│ oisp_version    │ Schema version (e.g., "0.1")              │
│ event_id        │ Unique ID (ULID recommended)              │
│ event_type      │ Hierarchical type (e.g., "ai.request")    │
│ ts              │ Timestamp (RFC 3339, microseconds)        │
├─────────────────────────────────────────────────────────────┤
│ host            │ Device/host context                       │
│ actor           │ User/identity context                     │
│ process         │ Process context                           │
├─────────────────────────────────────────────────────────────┤
│ source          │ How this event was captured               │
│ confidence      │ What we know and don't know               │
├─────────────────────────────────────────────────────────────┤
│ data            │ Event-type-specific payload               │
│ attrs           │ Additional custom attributes              │
│ ext             │ Namespaced extensions                     │
└─────────────────────────────────────────────────────────────┘
```

### Event Types

Events are organized hierarchically:

```
process.exec        Process execution
process.exit        Process termination
process.fork        Process fork

network.connect     Outbound connection
network.accept      Inbound connection
network.flow        Flow summary
network.dns         DNS query/response

file.open           File open
file.read           File read
file.write          File write
file.delete         File deletion
file.rename         File rename/move

ai.request          AI API request
ai.response         AI API response
ai.streaming_chunk  Streaming response chunk
ai.embedding        Embedding request

agent.tool_call     Agent invoking a tool
agent.tool_result   Tool execution result
agent.plan_step     Agent planning/reasoning
agent.rag_retrieve  RAG context retrieval
agent.session       Session lifecycle
```

## Capture Architecture

### Signal Sources

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kernel/OS     │    │  Network/TLS    │    │    Vendor       │
│   Telemetry     │    │    Boundary     │    │   Audit Logs    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Process exec  │    │ • HTTP content  │    │ • Copilot logs  │
│ • File I/O      │    │ • AI payloads   │    │ • SaaS usage    │
│ • Network flows │    │ • Model IDs     │    │ • Auth events   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    OISP Normalizer    │
                    │                       │
                    │ • Schema validation   │
                    │ • Provider detection  │
                    │ • Redaction           │
                    │ • Enrichment          │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    OISP Events        │
                    │                       │
                    │ Consistent schema     │
                    │ regardless of source  │
                    └───────────────────────┘
```

### Confidence Levels

Different capture methods produce different confidence levels:

| Method | Confidence | Completeness | Notes |
|--------|------------|--------------|-------|
| eBPF + TLS boundary | High | Full | Best case: kernel + plaintext |
| eBPF only | High | Metadata only | Process/network without content |
| MITM proxy | High | Full | Requires certificate installation |
| Browser extension | Medium | Full | Limited to browser context |
| Vendor audit log | High | Vendor reported | Depends on vendor completeness |
| Heuristic detection | Low | Inferred | Pattern matching only |

## Provider Fingerprinting

OISP includes rules to identify AI providers from network traffic:

```yaml
# From registry.yaml
openai:
  domains:
    - api.openai.com
  endpoints:
    chat_completions:
      path: "/v1/chat/completions"
      method: POST
      request_type: chat
```

When a sensor sees traffic to `api.openai.com/v1/chat/completions`, it can:
1. Identify the provider as `openai`
2. Extract the model from the request body
3. Parse token usage from the response
4. Generate a properly attributed `ai.request` / `ai.response` event pair

## Model Data Source

Model capabilities and pricing data is sourced from [models.dev](https://models.dev) - a community-maintained AI model registry that tracks:

- **74+ providers** with API endpoint URLs
- Context window sizes and max output tokens
- Pricing (input/output/cache per 1M tokens)
- Capabilities (vision, function calling, reasoning, streaming)
- Provider logos (SVG)
- Knowledge cutoff dates

The registry is automatically synced weekly via GitHub Actions. API endpoint URLs are especially valuable for OISP Sensor to detect which provider traffic is going to.

This enables automatic enrichment of events with model metadata and cost estimation.

## Extension Points

### Custom Attributes (`attrs`)

For additional metadata not covered by the schema:

```json
{
  "attrs": {
    "deployment_id": "prod-v2",
    "experiment_group": "control"
  }
}
```

### Namespaced Extensions (`ext`)

For vendor-specific or integration-specific data:

```json
{
  "ext": {
    "oximy.detection_score": 0.85,
    "langfuse.trace_id": "abc123"
  }
}
```

### Experimental Fields (`x`)

For fields under development:

```json
{
  "x": {
    "new_classifier_v2": { ... }
  }
}
```

## Versioning

OISP follows semantic versioning:

- **v0.x**: Development phase, breaking changes possible
- **v1.x**: Stable, additive changes only in minor versions
- **v2.x**: Next major version with breaking changes

Schema URLs include the major version: `https://oisp.dev/schema/v0.1/...`

## Related Projects

- **oisp-sensor**: Reference sensor implementation (separate repo)
- **OpenTelemetry**: Observability framework we extend
- **models.dev**: AI model registry we sync from (pricing, capabilities, endpoints)

## Try It Now: OISP Sensor

Want to see OISP in action? **[OISP Sensor](https://sensor.oisp.dev)** is our reference implementation that captures every AI interaction on your machine with zero instrumentation.

```bash
# Install
curl -fsSL https://sensor.oisp.dev/install.sh | sudo sh

# Run with TUI
sudo oisp-sensor

# Or with Web UI
sudo oisp-sensor --web
```

OISP Sensor implements the complete OISP event model:
- Captures AI requests/responses at the TLS boundary (eBPF on Linux)
- Correlates agent tool calls with actual system operations
- Outputs events in OISP schema format (JSONL, WebSocket, OTLP)

[Get Started](https://sensor.oisp.dev) | [GitHub](https://github.com/oximyhq/sensor)

## Next Steps

- [Implementor's Guide](implementors-guide.md): How to build an OISP-compliant sensor
- [Semantic Conventions](../semconv/README.md): Attribute naming and conventions
- [Examples](../examples/): Concrete event examples

