# OISP Scripts

Utility scripts for maintaining the OISP specification.

## sync-models.py

Synchronizes model data from [LiteLLM's model registry](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json).

### Why?

Maintaining model capabilities, context windows, and pricing for 500+ models across 20+ providers is impossible manually. LiteLLM already maintains this data, so we sync from them.

### Usage

```bash
# Run locally
python scripts/sync-models.py

# Custom output directory
python scripts/sync-models.py --output-dir ./custom-output
```

### Output

The script generates three files in `semconv/providers/_generated/`:

1. **models.yaml** - Human-readable YAML format
2. **models.json** - Machine-readable JSON for programmatic use
3. **models.ts** - TypeScript types and helper functions

### Automation

This script runs automatically via GitHub Actions:
- Weekly on Sunday at midnight UTC
- On push to `main` if `scripts/sync-models.py` changes
- Manually via workflow dispatch

See `.github/workflows/sync-models.yml`

### Data Extracted

For each model, we extract:
- Model ID (provider's identifier)
- Provider (normalized to OISP canonical names)
- Mode (chat, embedding, image, etc.)
- Context window (max input/output tokens)
- Pricing (cost per 1K tokens)
- Capabilities (vision, function calling, etc.)
- Deprecation status

### Provider Mapping

LiteLLM uses different provider names than OISP. The mapping is:

| LiteLLM | OISP |
|---------|------|
| `gemini` | `google` |
| `vertex_ai` | `google` |
| `azure` | `azure_openai` |
| `bedrock` | `aws_bedrock` |
| `together_ai` | `together` |
| `fireworks_ai` | `fireworks` |
| `ollama_chat` | `ollama` |
| `lm_studio` | `lmstudio` |

See the full mapping in `sync-models.py`.

