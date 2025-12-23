# Provider Fingerprinting

This directory contains fingerprinting rules for AI providers. These rules enable OISP sensors to:

1. **Identify** AI traffic from network observations
2. **Extract** model IDs, token counts, and other metadata
3. **Normalize** provider-specific formats to OISP schema

## How Fingerprinting Works

When a sensor intercepts network traffic:

1. **Domain matching**: Does the destination match known AI endpoints?
2. **Path matching**: Does the request path match known API patterns?
3. **Header inspection**: Are there provider-specific headers?
4. **Payload extraction**: Extract model, tokens, etc. from request/response

## Registry

The main registry is in [registry.yaml](registry.yaml). It provides:

- Canonical provider names
- Domain patterns
- Links to detailed provider files

## Provider Files

Each provider has a YAML file with:

```yaml
provider: openai
display_name: "OpenAI"
domains:
  - api.openai.com
  
endpoints:
  chat_completions:
    path: "/v1/chat/completions"
    method: POST
    request_type: chat
    # ... extraction rules
```

## Model Data Source

Model capabilities and pricing data is sourced from:

- [LiteLLM model_prices_and_context_window.json](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)

We periodically sync this data to keep model information current.

## Adding a New Provider

1. Add entry to `registry.yaml`
2. Create `<provider>.yaml` with fingerprinting rules
3. Add example events to `/examples/`
4. Submit PR with evidence (API docs, traffic samples)

## Confidence Levels

Fingerprinting produces different confidence levels:

| Signal | Confidence |
|--------|------------|
| Domain + path + model in payload | `high` |
| Domain + path only | `medium` |
| Domain only | `low` |
| Heuristic (content patterns) | `inferred` |

