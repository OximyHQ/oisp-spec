#!/usr/bin/env python3
"""
Build OISP Spec Bundle

Combines all spec components into a single JSON bundle that sensors can fetch
at runtime. This enables dynamic provider/model updates without recompiling.

The bundle includes:
1. Provider fingerprinting rules (from semconv/providers/*.yaml)
2. Model registry (from semconv/providers/_generated/models.json)
3. Extraction rules for parsing requests/responses

Output: dist/oisp-spec-bundle.json

Usage:
    python scripts/build-bundle.py
    python scripts/build-bundle.py --output ./custom-path.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SPEC_ROOT = Path(__file__).parent.parent
PROVIDERS_DIR = SPEC_ROOT / "semconv" / "providers"
SCHEMA_DIR = SPEC_ROOT / "schema" / "v0.1"


def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)


def load_registry() -> dict:
    """Load the main provider registry."""
    return load_yaml(PROVIDERS_DIR / "registry.yaml")


def load_provider_configs() -> dict[str, dict]:
    """Load all provider-specific YAML files."""
    providers = {}
    
    for yaml_file in PROVIDERS_DIR.glob("*.yaml"):
        if yaml_file.name in ("registry.yaml",):
            continue
            
        try:
            config = load_yaml(yaml_file)
            if "provider" in config:
                provider_id = config["provider"]
                providers[provider_id] = config
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}", file=sys.stderr)
    
    return providers


def load_models() -> dict:
    """Load the generated models registry."""
    models_path = PROVIDERS_DIR / "_generated" / "models.json"
    if models_path.exists():
        return load_json(models_path)
    return {"models": {}, "providers": {}}


def build_domain_index(registry: dict, provider_configs: dict) -> dict:
    """Build a domain -> provider lookup index."""
    index = {}
    
    # From registry
    if "domain_lookup" in registry:
        index.update(registry["domain_lookup"])
    
    # From provider configs
    for provider_id, config in provider_configs.items():
        for url in config.get("base_urls", []):
            # Extract domain from URL
            domain = url.replace("https://", "").replace("http://", "").rstrip("/")
            index[domain] = provider_id
    
    return index


def build_domain_patterns(registry: dict, provider_configs: dict) -> list[dict]:
    """Build domain patterns for wildcard matching."""
    patterns = []
    
    # From registry
    for entry in registry.get("domain_patterns", []):
        patterns.append({
            "pattern": entry["pattern"],
            "provider": entry["provider"],
            "regex": glob_to_regex(entry["pattern"])
        })
    
    # From provider configs
    for provider_id, config in provider_configs.items():
        for domain in config.get("domains", []):
            if "*" in domain:
                patterns.append({
                    "pattern": domain,
                    "provider": provider_id,
                    "regex": glob_to_regex(domain)
                })
    
    return patterns


def glob_to_regex(pattern: str) -> str:
    """Convert glob pattern to regex."""
    # Escape special regex chars except *
    escaped = re.escape(pattern).replace(r"\*", ".*")
    return f"^{escaped}$"


def build_extraction_rules(provider_configs: dict) -> dict[str, dict]:
    """Build extraction rules for each provider."""
    rules = {}
    
    for provider_id, config in provider_configs.items():
        if "endpoints" not in config:
            continue
            
        provider_rules = {
            "endpoints": {},
            "auth": config.get("auth", {}),
            "response_headers": config.get("response_headers", {}),
            "model_families": config.get("model_families", {}),
            "features": config.get("features", {}),
        }
        
        for endpoint_name, endpoint_config in config["endpoints"].items():
            provider_rules["endpoints"][endpoint_name] = {
                "path": endpoint_config.get("path", ""),
                "method": endpoint_config.get("method", "POST"),
                "request_type": endpoint_config.get("request_type", "chat"),
                "streaming": endpoint_config.get("streaming", {}),
                "request_extraction": endpoint_config.get("request_extraction", {}),
                "response_extraction": endpoint_config.get("response_extraction", {}),
            }
        
        rules[provider_id] = provider_rules
    
    return rules


def build_fingerprints(provider_configs: dict) -> dict[str, dict]:
    """Build fingerprinting rules for each provider."""
    fingerprints = {}
    
    for provider_id, config in provider_configs.items():
        if "fingerprints" in config:
            fingerprints[provider_id] = config["fingerprints"]
    
    return fingerprints


def build_bundle() -> dict:
    """Build the complete spec bundle."""
    registry = load_registry()
    provider_configs = load_provider_configs()
    models = load_models()
    
    bundle = {
        "$schema": "https://oisp.dev/schema/v0.1/bundle.schema.json",
        "version": registry.get("version", "0.1"),
        "bundle_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "oisp-spec",
        
        # Provider metadata
        "providers": {},
        
        # Quick lookups
        "domain_index": build_domain_index(registry, provider_configs),
        "domain_patterns": build_domain_patterns(registry, provider_configs),
        
        # Extraction rules for parsing
        "extraction_rules": build_extraction_rules(provider_configs),
        
        # Fingerprinting rules
        "fingerprints": build_fingerprints(provider_configs),
        
        # Model registry
        "models": models.get("models", {}),
        "model_stats": models.get("stats", {}),
    }
    
    # Build provider list with metadata
    for provider_id, provider_data in registry.get("providers", {}).items():
        bundle["providers"][provider_id] = {
            "id": provider_id,
            "display_name": provider_data.get("display_name", provider_id),
            "type": provider_data.get("type", "cloud"),
            "domains": provider_data.get("domains", []),
            "features": provider_data.get("features", []),
            "auth": provider_data.get("auth", {}),
            "api_endpoint": provider_data.get("api_endpoint"),  # From models.dev
            "models_dev_id": provider_data.get("models_dev_id"),  # Original models.dev ID
        }
    
    return bundle


def main():
    parser = argparse.ArgumentParser(description="Build OISP Spec Bundle")
    parser.add_argument(
        "--output",
        type=Path,
        default=SPEC_ROOT / "dist" / "oisp-spec-bundle.json",
        help="Output path for bundle"
    )
    parser.add_argument(
        "--minify",
        action="store_true",
        help="Minify JSON output"
    )
    args = parser.parse_args()
    
    # Build bundle
    print("Building OISP Spec Bundle...")
    bundle = build_bundle()
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Write bundle
    indent = None if args.minify else 2
    with open(args.output, "w") as f:
        json.dump(bundle, f, indent=indent, sort_keys=True)
    
    # Print stats
    print(f"Bundle written to: {args.output}")
    print(f"  Providers: {len(bundle['providers'])}")
    print(f"  Domains indexed: {len(bundle['domain_index'])}")
    print(f"  Domain patterns: {len(bundle['domain_patterns'])}")
    print(f"  Extraction rules: {len(bundle['extraction_rules'])}")
    print(f"  Models: {len(bundle['models'])}")
    
    # Also write a minified version
    if not args.minify:
        min_path = args.output.with_suffix(".min.json")
        with open(min_path, "w") as f:
            json.dump(bundle, f, separators=(",", ":"), sort_keys=True)
        print(f"  Minified: {min_path}")


if __name__ == "__main__":
    main()

