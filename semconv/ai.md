# AI Semantic Conventions

This document defines semantic conventions for AI/LLM interaction events in OISP.

## Overview

AI events capture interactions with Large Language Models and AI systems. They are designed to:

1. **Identify** what AI is being used (provider, model, capabilities)
2. **Attribute** who/what is making the request (user, process, agent)
3. **Measure** resource usage (tokens, latency, cost)
4. **Audit** without exposing sensitive content (redaction, hashing)

## Provider Identification

### `provider.name`

Canonical provider identifier. See [providers/registry.yaml](providers/registry.yaml) for the full list.

| Value | Description |
|-------|-------------|
| `openai` | OpenAI API (api.openai.com) |
| `anthropic` | Anthropic API (api.anthropic.com) |
| `google` | Google AI / Gemini API |
| `azure_openai` | Azure OpenAI Service |
| `aws_bedrock` | AWS Bedrock |
| `cohere` | Cohere API |
| `mistral` | Mistral AI API |
| `groq` | Groq API |
| `together` | Together AI |
| `fireworks` | Fireworks AI |
| `replicate` | Replicate |
| `huggingface` | Hugging Face Inference API |
| `ollama` | Ollama (local) |
| `lmstudio` | LM Studio (local) |
| `vllm` | vLLM (self-hosted) |
| `other` | Unknown or unlisted provider |

### `provider.endpoint`

The API endpoint URL. Used for fingerprinting and routing.

```
https://api.openai.com/v1/chat/completions
https://api.anthropic.com/v1/messages
```

## Model Identification

### `model.id`

The model identifier as sent in the request or returned by the API.

Examples:
- `gpt-4o`
- `gpt-4o-2024-11-20`
- `claude-3-5-sonnet-20241022`
- `gemini-1.5-pro-002`

### `model.family`

Higher-level model family grouping.

| Family | Models |
|--------|--------|
| `gpt-4` | gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini |
| `gpt-3.5` | gpt-3.5-turbo |
| `o1` | o1, o1-mini, o1-preview |
| `claude-3` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| `claude-3.5` | claude-3-5-sonnet, claude-3-5-haiku |
| `gemini-1.5` | gemini-1.5-pro, gemini-1.5-flash |
| `gemini-2` | gemini-2.0-flash |

### `model.capabilities`

Known model capabilities. Used for risk assessment and policy.

| Capability | Description |
|------------|-------------|
| `vision` | Can process images |
| `function_calling` | Supports tool/function calling |
| `streaming` | Supports streaming responses |
| `json_mode` | Supports structured JSON output |
| `system_messages` | Supports system messages |
| `reasoning` | Extended reasoning (o1-style) |
| `web_search` | Can search the web |
| `code_execution` | Can execute code |

## Request Attributes

### `request_type`

Type of AI request.

| Value | Description |
|-------|-------------|
| `chat` | Chat completion (messages array) |
| `completion` | Text completion (prompt string) |
| `embedding` | Text embedding |
| `image` | Image generation |
| `audio` | Audio generation or transcription |
| `moderation` | Content moderation |

### `streaming`

Boolean. Whether streaming was requested.

### `messages_count`

Integer. Number of messages in the request context.

### `has_system_prompt`

Boolean. Whether a system prompt was present.

### `has_rag_context`

Boolean. Whether RAG-injected context was detected.

Detection heuristics:
- Large user message with structured format
- References to "context" or "documents"
- Presence of citation markers

### `tools_count`

Integer. Number of tools/functions available to the model.

## Response Attributes

### `finish_reason`

Why generation stopped.

| Value | Description |
|-------|-------------|
| `stop` | Natural stop (completed) |
| `length` | Hit max_tokens limit |
| `tool_calls` | Model invoked tool(s) |
| `content_filter` | Blocked by content filter |
| `error` | Error occurred |

### `latency_ms`

Total response time in milliseconds.

### `time_to_first_token_ms`

Time to first token for streaming responses. Key metric for perceived latency.

## Token Usage

### `usage.prompt_tokens`

Tokens in the input/prompt.

### `usage.completion_tokens`

Tokens in the output/completion.

### `usage.cached_tokens`

Tokens served from prompt cache.

### `usage.reasoning_tokens`

Tokens used for internal reasoning (o1 models).

## Cost Estimation

OISP can estimate costs using the [LiteLLM model pricing database](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json).

### `usage.input_cost_usd`

Estimated input cost in USD.

### `usage.output_cost_usd`

Estimated output cost in USD.

### `usage.total_cost_usd`

Estimated total cost in USD.

## Authentication

### `auth.type`

How the request was authenticated.

| Value | Description |
|-------|-------------|
| `api_key` | API key authentication |
| `oauth` | OAuth token |
| `service_account` | Service account credentials |
| `session` | Session-based (browser) |
| `none` | No authentication |
| `unknown` | Could not determine |

### `auth.account_type`

Whether this is a personal or corporate account.

| Value | Description |
|-------|-------------|
| `personal` | Personal/individual account |
| `corporate` | Corporate/organization account |
| `shared` | Shared/team account |
| `unknown` | Could not determine |

Detection methods:
- API key prefix patterns (`sk-proj-` vs `sk-`)
- Organization header presence
- SSO indicators

### `auth.key_prefix`

First 8 characters of API key for identification without exposure.

## Content Handling

### Redaction

Sensitive content should be redacted before export. Use the `$redacted` marker:

```json
{
  "prompt": {
    "$redacted": {
      "reason": "pii_detected",
      "detector": "regex_email",
      "original_length": 1547,
      "hash": "sha256:abc123...",
      "preview": "Please help me with..."
    }
  }
}
```

### Content Hashing

When content is redacted, include a hash for correlation:

- Allows deduplication without content exposure
- Enables pattern detection across requests
- Supports "have we seen this before" queries

Recommended: SHA-256, truncated to 16 characters for space efficiency.

## Agent Context

When AI requests originate from an agent:

### `agent.name`

Agent identifier: `cursor`, `aider`, `claude-code`, `autogpt`, etc.

### `agent.type`

Agent category: `ide`, `cli`, `browser`, `server`, `autonomous`

### `agent.session_id`

Session identifier for grouping related requests.

## Examples

### Minimal AI Request Event

```json
{
  "oisp_version": "0.1",
  "event_id": "01HQXYZ123",
  "event_type": "ai.request",
  "ts": "2025-12-22T20:15:05.123456Z",
  "source": {
    "collector": "oisp-sensor",
    "capture_method": "tls_boundary"
  },
  "confidence": {
    "level": "high",
    "completeness": "metadata_only"
  },
  "data": {
    "provider": { "name": "openai" },
    "model": { "id": "gpt-4o" },
    "request_type": "chat",
    "streaming": true,
    "messages_count": 5,
    "has_system_prompt": true,
    "tools_count": 3
  }
}
```

### Full AI Response Event

```json
{
  "oisp_version": "0.1",
  "event_id": "01HQXYZ456",
  "event_type": "ai.response",
  "ts": "2025-12-22T20:15:07.456789Z",
  "source": {
    "collector": "oisp-sensor",
    "capture_method": "tls_boundary"
  },
  "confidence": {
    "level": "high",
    "completeness": "full"
  },
  "data": {
    "request_id": "01HQXYZ123",
    "provider": { "name": "openai" },
    "model": { "id": "gpt-4o" },
    "success": true,
    "finish_reason": "tool_calls",
    "tool_calls_count": 2,
    "usage": {
      "prompt_tokens": 1250,
      "completion_tokens": 89,
      "total_tokens": 1339
    },
    "latency_ms": 2345,
    "time_to_first_token_ms": 234
  }
}
```

