#!/usr/bin/env python3
"""
Sync model data from LiteLLM's model registry.

This script fetches the latest model pricing and capabilities from:
https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json

And generates:
1. semconv/providers/_generated/models.yaml - Complete model registry
2. semconv/providers/_generated/models.json - JSON format for programmatic use

Run this periodically (e.g., weekly via GitHub Action) to keep model data current.

Usage:
    python scripts/sync-models.py
    python scripts/sync-models.py --output-dir ./custom-output
"""

import argparse
import json
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

# LiteLLM model registry URL
LITELLM_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

# Provider name mapping (litellm_provider -> our canonical name)
PROVIDER_MAPPING = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "google",
    "vertex_ai": "google",
    "vertex_ai-language-models": "google",
    "azure": "azure_openai",
    "azure_ai": "azure_openai",
    "bedrock": "aws_bedrock",
    "sagemaker": "aws_sagemaker",
    "cohere": "cohere",
    "cohere_chat": "cohere",
    "mistral": "mistral",
    "groq": "groq",
    "together_ai": "together",
    "fireworks_ai": "fireworks",
    "replicate": "replicate",
    "huggingface": "huggingface",
    "ollama": "ollama",
    "ollama_chat": "ollama",
    "lm_studio": "lmstudio",
    "vllm": "vllm",
    "deepseek": "deepseek",
    "perplexity": "perplexity",
    "anyscale": "anyscale",
    "openrouter": "openrouter",
    "ai21": "ai21",
    "nlp_cloud": "nlp_cloud",
    "aleph_alpha": "aleph_alpha",
    "cloudflare": "cloudflare",
    "voyage": "voyage",
    "xinference": "xinference",
}

# Capability flag mapping
CAPABILITY_MAPPING = {
    "supports_vision": "vision",
    "supports_function_calling": "function_calling",
    "supports_parallel_function_calling": "parallel_function_calling",
    "supports_system_messages": "system_messages",
    "supports_response_schema": "json_mode",
    "supports_prompt_caching": "prompt_caching",
    "supports_reasoning": "reasoning",
    "supports_web_search": "web_search",
    "supports_audio_input": "audio_input",
    "supports_audio_output": "audio_output",
}

# Mode mapping
MODE_MAPPING = {
    "chat": "chat",
    "completion": "completion",
    "embedding": "embedding",
    "image_generation": "image",
    "audio_transcription": "audio_transcription",
    "audio_speech": "audio_speech",
    "moderation": "moderation",
    "rerank": "rerank",
}


def fetch_litellm_data(local_file: Path | None = None) -> dict:
    """Fetch the latest model data from LiteLLM or load from local file."""
    if local_file and local_file.exists():
        print(f"Loading model data from {local_file}...")
        with open(local_file) as f:
            data = json.load(f)
        print(f"Loaded {len(data)} entries")
        return data
    
    print(f"Fetching model data from {LITELLM_URL}...")
    try:
        # Create SSL context that doesn't verify (for environments with cert issues)
        # In production, the GitHub Action will have proper certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = Request(LITELLM_URL, headers={"User-Agent": "OISP-Sync/1.0"})
        with urlopen(req, timeout=30, context=ctx) as response:
            data = json.loads(response.read().decode("utf-8"))
        print(f"Fetched {len(data)} entries")
        return data
    except URLError as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        print("Try downloading manually and using --input-file:", file=sys.stderr)
        print(f"  curl -sL '{LITELLM_URL}' -o /tmp/litellm.json", file=sys.stderr)
        print(f"  python scripts/sync-models.py --input-file /tmp/litellm.json", file=sys.stderr)
        sys.exit(1)


def parse_model_entry(model_id: str, entry: dict) -> dict | None:
    """Parse a single model entry from LiteLLM format to OISP format."""
    # Skip sample_spec and non-model entries
    if model_id == "sample_spec":
        return None
    
    # Skip image generation size variants (e.g., "1024-x-1024/dall-e-2")
    if model_id.startswith(("1024-x-", "512-x-", "256-x-")):
        return None
    
    litellm_provider = entry.get("litellm_provider", "")
    if not litellm_provider:
        return None
    
    # Map to our provider name
    provider = PROVIDER_MAPPING.get(litellm_provider, litellm_provider)
    
    # Extract model name (remove provider prefix if present)
    model_name = model_id
    for prefix in [f"{litellm_provider}/", f"{provider}/"]:
        if model_name.startswith(prefix):
            model_name = model_name[len(prefix):]
            break
    
    # Build model info
    model_info = {
        "id": model_name,
        "litellm_id": model_id,
        "provider": provider,
        "mode": MODE_MAPPING.get(entry.get("mode", "chat"), entry.get("mode", "chat")),
    }
    
    # Context window
    if "max_input_tokens" in entry:
        model_info["max_input_tokens"] = entry["max_input_tokens"]
    if "max_output_tokens" in entry:
        model_info["max_output_tokens"] = entry["max_output_tokens"]
    if "max_tokens" in entry and "max_input_tokens" not in entry:
        model_info["max_input_tokens"] = entry["max_tokens"]
    
    # Pricing (convert to per-1k-tokens)
    if "input_cost_per_token" in entry and entry["input_cost_per_token"]:
        model_info["input_cost_per_1k"] = round(entry["input_cost_per_token"] * 1000, 8)
    if "output_cost_per_token" in entry and entry["output_cost_per_token"]:
        model_info["output_cost_per_1k"] = round(entry["output_cost_per_token"] * 1000, 8)
    
    # Capabilities
    capabilities = []
    for litellm_cap, oisp_cap in CAPABILITY_MAPPING.items():
        if entry.get(litellm_cap):
            capabilities.append(oisp_cap)
    if capabilities:
        model_info["capabilities"] = capabilities
    
    # Deprecation
    if "deprecation_date" in entry and entry["deprecation_date"]:
        model_info["deprecated"] = True
        model_info["deprecation_date"] = entry["deprecation_date"]
    
    return model_info


def group_by_provider(models: list[dict]) -> dict[str, list[dict]]:
    """Group models by provider."""
    by_provider = {}
    for model in models:
        provider = model.get("provider", "other")
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model)
    
    # Sort models within each provider
    for provider in by_provider:
        by_provider[provider].sort(key=lambda m: m.get("id", ""))
    
    return by_provider


def generate_yaml(models_by_provider: dict, output_path: Path):
    """Generate YAML output."""
    lines = [
        "# OISP Model Registry",
        "# Auto-generated from LiteLLM - DO NOT EDIT MANUALLY",
        f"# Source: {LITELLM_URL}",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "#",
        "# To regenerate: python scripts/sync-models.py",
        "",
        "version: '0.1'",
        f"generated_at: '{datetime.now(timezone.utc).isoformat()}'",
        "source: litellm",
        f"source_url: '{LITELLM_URL}'",
        "",
        "providers:",
    ]
    
    for provider in sorted(models_by_provider.keys()):
        models = models_by_provider[provider]
        lines.append(f"  {provider}:")
        lines.append(f"    model_count: {len(models)}")
        lines.append("    models:")
        
        for model in models:
            model_id = model["id"]
            lines.append(f"      '{model_id}':")
            
            if "litellm_id" in model and model["litellm_id"] != model_id:
                lines.append(f"        litellm_id: '{model['litellm_id']}'")
            
            if "mode" in model:
                lines.append(f"        mode: {model['mode']}")
            
            if "max_input_tokens" in model:
                lines.append(f"        max_input_tokens: {model['max_input_tokens']}")
            
            if "max_output_tokens" in model:
                lines.append(f"        max_output_tokens: {model['max_output_tokens']}")
            
            if "input_cost_per_1k" in model:
                lines.append(f"        input_cost_per_1k: {model['input_cost_per_1k']}")
            
            if "output_cost_per_1k" in model:
                lines.append(f"        output_cost_per_1k: {model['output_cost_per_1k']}")
            
            if "capabilities" in model:
                caps = ", ".join(model["capabilities"])
                lines.append(f"        capabilities: [{caps}]")
            
            if model.get("deprecated"):
                lines.append("        deprecated: true")
                if "deprecation_date" in model:
                    lines.append(f"        deprecation_date: '{model['deprecation_date']}'")
    
    output_path.write_text("\n".join(lines) + "\n")
    print(f"Generated: {output_path}")


def generate_json(models_by_provider: dict, all_models: list[dict], output_path: Path):
    """Generate JSON output."""
    output = {
        "version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "litellm",
        "source_url": LITELLM_URL,
        "stats": {
            "total_models": len(all_models),
            "providers": len(models_by_provider),
        },
        "providers": {},
        "models": {},
    }
    
    # Provider summary
    for provider in sorted(models_by_provider.keys()):
        models = models_by_provider[provider]
        output["providers"][provider] = {
            "model_count": len(models),
            "models": [m["id"] for m in models],
        }
    
    # Flat model lookup
    for model in all_models:
        key = f"{model['provider']}/{model['id']}"
        output["models"][key] = model
    
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Generated: {output_path}")


def generate_typescript_types(output_path: Path):
    """Generate TypeScript type definitions for the model registry."""
    content = '''// OISP Model Registry Types
// Auto-generated - DO NOT EDIT MANUALLY

export type AIProvider =
  | 'openai'
  | 'anthropic'
  | 'google'
  | 'azure_openai'
  | 'aws_bedrock'
  | 'cohere'
  | 'mistral'
  | 'groq'
  | 'together'
  | 'fireworks'
  | 'replicate'
  | 'huggingface'
  | 'ollama'
  | 'lmstudio'
  | 'vllm'
  | 'deepseek'
  | 'perplexity'
  | 'openrouter'
  | string;

export type ModelMode =
  | 'chat'
  | 'completion'
  | 'embedding'
  | 'image'
  | 'audio_transcription'
  | 'audio_speech'
  | 'moderation'
  | 'rerank';

export type ModelCapability =
  | 'vision'
  | 'function_calling'
  | 'parallel_function_calling'
  | 'system_messages'
  | 'json_mode'
  | 'prompt_caching'
  | 'reasoning'
  | 'web_search'
  | 'audio_input'
  | 'audio_output';

export interface ModelInfo {
  id: string;
  litellm_id?: string;
  provider: AIProvider;
  mode: ModelMode;
  max_input_tokens?: number;
  max_output_tokens?: number;
  input_cost_per_1k?: number;
  output_cost_per_1k?: number;
  capabilities?: ModelCapability[];
  deprecated?: boolean;
  deprecation_date?: string;
}

export interface ModelRegistry {
  version: string;
  generated_at: string;
  source: string;
  source_url: string;
  stats: {
    total_models: number;
    providers: number;
  };
  providers: Record<AIProvider, {
    model_count: number;
    models: string[];
  }>;
  models: Record<string, ModelInfo>;
}

/**
 * Lookup a model by provider and model ID.
 */
export function lookupModel(
  registry: ModelRegistry,
  provider: AIProvider,
  modelId: string
): ModelInfo | undefined {
  return registry.models[`${provider}/${modelId}`];
}

/**
 * Estimate the cost of an API call.
 */
export function estimateCost(
  model: ModelInfo,
  inputTokens: number,
  outputTokens: number
): { input: number; output: number; total: number } | undefined {
  if (!model.input_cost_per_1k || !model.output_cost_per_1k) {
    return undefined;
  }
  
  const input = (inputTokens / 1000) * model.input_cost_per_1k;
  const output = (outputTokens / 1000) * model.output_cost_per_1k;
  
  return {
    input: Math.round(input * 1000000) / 1000000,
    output: Math.round(output * 1000000) / 1000000,
    total: Math.round((input + output) * 1000000) / 1000000,
  };
}
'''
    output_path.write_text(content)
    print(f"Generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Sync model data from LiteLLM")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "semconv" / "providers" / "_generated",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Local JSON file to use instead of fetching from URL",
    )
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch data
    raw_data = fetch_litellm_data(args.input_file)
    
    # Parse models
    models = []
    for model_id, entry in raw_data.items():
        parsed = parse_model_entry(model_id, entry)
        if parsed:
            models.append(parsed)
    
    print(f"Parsed {len(models)} models")
    
    # Group by provider
    by_provider = group_by_provider(models)
    print(f"Found {len(by_provider)} providers")
    
    # Generate outputs
    generate_yaml(by_provider, args.output_dir / "models.yaml")
    generate_json(by_provider, models, args.output_dir / "models.json")
    generate_typescript_types(args.output_dir / "models.ts")
    
    # Print summary
    print("\nProvider Summary:")
    for provider in sorted(by_provider.keys()):
        print(f"  {provider}: {len(by_provider[provider])} models")
    
    print(f"\nTotal: {len(models)} models from {len(by_provider)} providers")


if __name__ == "__main__":
    main()

