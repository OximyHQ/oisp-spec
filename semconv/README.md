# OISP Semantic Conventions

This directory contains semantic conventions for OISP events, following and extending [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/).

## Structure

- **ai.md** - AI/LLM interaction semantic conventions
- **providers/** - Provider-specific fingerprinting rules

## Naming Conventions

### Attribute Naming

- Use `snake_case` for all attribute names
- Use dot notation for namespacing: `ai.provider.name`, `process.pid`
- Prefix custom attributes with `oisp.` to avoid conflicts

### Provider Names

Use canonical lowercase names:
- `openai` (not "OpenAI")
- `anthropic` (not "Anthropic")
- `azure_openai` (not "Azure OpenAI")
- `aws_bedrock` (not "AWS Bedrock")

### Model IDs

Preserve the provider's model ID exactly as returned:
- `gpt-4o`
- `claude-3-5-sonnet-20241022`
- `gemini-1.5-pro`

## OpenTelemetry Alignment

We align with OTel's [GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) where they exist:

| OTel Attribute | OISP Equivalent | Notes |
|----------------|-----------------|-------|
| `gen_ai.system` | `provider.name` | We use more specific naming |
| `gen_ai.request.model` | `model.id` | Same semantics |
| `gen_ai.response.finish_reasons` | `finish_reason` | Singular in OISP |
| `gen_ai.usage.input_tokens` | `usage.prompt_tokens` | Same semantics |
| `gen_ai.usage.output_tokens` | `usage.completion_tokens` | Same semantics |

## Extension Points

When adding new attributes not covered by this spec:

1. Check if OTel has a convention first
2. If not, use `oisp.` prefix for OISP-specific attributes
3. Use `ext.<namespace>.` for vendor-specific extensions
4. Use `x.` for experimental attributes

