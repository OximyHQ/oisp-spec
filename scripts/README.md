# OISP Scripts

Utility scripts for maintaining the OISP specification.

## sync-models.py

Synchronizes model data from [models.dev](https://models.dev) - a community-maintained AI model registry.

### Why models.dev?

models.dev provides:
- **74+ providers** with 1,900+ models
- **API endpoints** for each provider (useful for traffic detection)
- **SVG logos** for UI display
- **Structured pricing** (input, output, cache read/write, reasoning tokens)
- **Model capabilities** (vision, function calling, reasoning, etc.)
- **Clean JSON API** at `https://models.dev/api.json`

### Usage

```bash
# Run locally
python scripts/sync-models.py

# Custom output directory
python scripts/sync-models.py --output-dir ./custom-output

# Use local file (for testing/offline)
curl -sL 'https://models.dev/api.json' -o /tmp/models.json
python scripts/sync-models.py --input-file /tmp/models.json
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

For each **provider**, we extract:
- Provider ID (canonical name)
- API endpoint URL (for traffic detection!)
- Documentation URL
- Environment variables
- Logo URL (`https://models.dev/logos/{provider}.svg`)

For each **model**, we extract:
- Model ID
- Provider
- Mode (chat, embedding, image, etc.)
- Context window (max input/output tokens)
- Pricing (cost per 1K tokens - input, output, cache, reasoning)
- Capabilities (vision, function calling, reasoning, etc.)
- Knowledge cutoff date
- Open weights flag
- Deprecation status

### Provider Mapping

models.dev uses hyphenated provider IDs, which we normalize:

| models.dev | OISP |
|------------|------|
| `google-vertex` | `google_vertex` |
| `amazon-bedrock` | `aws_bedrock` |
| `together-ai` | `together` |
| `fireworks-ai` | `fireworks` |
| `ollama-cloud` | `ollama` |

See the full mapping in `sync-models.py`.

### API Endpoints

For providers where models.dev doesn't include API endpoints, we maintain our own mapping:

```python
PROVIDER_API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1",
    # ... see sync-models.py for full list
}
```

These endpoints are critical for OISP Sensor to detect which AI provider traffic is going to.

## compare-models.py

Compares the current OISP registry with latest models.dev data to detect drift.

### Usage

```bash
python scripts/compare-models.py \
  --current semconv/providers/_generated/models.json \
  --upstream /tmp/models-dev-latest.json \
  --output /tmp/diff.md
```

### Output

Generates a markdown report showing:
- New providers
- New models
- Removed/deprecated models
- Pricing changes

## build-bundle.py

Builds the final OISP specification bundle from source YAML files.

### Usage

```bash
python scripts/build-bundle.py
```

### Output

Generates `dist/oisp-spec-bundle.json` which is copied to `spec/v0.1/bundle.json`.
