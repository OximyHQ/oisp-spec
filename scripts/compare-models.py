#!/usr/bin/env python3
"""Compare OISP model registry with models.dev upstream.

This script compares the current OISP model registry with the latest models.dev data
to detect new models, removed models, new providers, and pricing changes.

Usage:
    python compare-models.py --current models.json --upstream models-dev.json --output diff.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def extract_models_from_models_dev(data: dict) -> dict:
    """Extract flat model dict from models.dev nested format.

    models.dev format:
    {
        "provider_id": {
            "models": {
                "model_id": { "cost": { "input": X, "output": Y } }
            }
        }
    }
    """
    models = {}
    for provider_id, provider_data in data.items():
        provider_models = provider_data.get("models", {})
        for model_id, model_data in provider_models.items():
            key = f"{provider_id}/{model_id}"
            cost = model_data.get("cost", {})
            models[key] = {
                "provider": provider_id,
                "model_id": model_id,
                "input_cost_per_1k": cost.get("input", 0) / 1000 if cost.get("input") else None,
                "output_cost_per_1k": cost.get("output", 0) / 1000 if cost.get("output") else None,
                "mode": "chat",  # Default
            }
    return models


def compare_models(current_path: str, upstream_path: str, output_path: str) -> bool:
    """Compare OISP model registry with models.dev upstream.

    Returns:
        True if changes were detected, False otherwise.
    """
    current = load_json(current_path)
    upstream_raw = load_json(upstream_path)

    # Current is already in our format: { "models": { "provider/model": {...} } }
    current_models = current.get("models", {})
    current_providers = set(current.get("providers", {}).keys())

    # Extract upstream models from models.dev format
    upstream_models = extract_models_from_models_dev(upstream_raw)
    upstream_providers = set(upstream_raw.keys())

    # Compare model sets
    current_model_keys = set(current_models.keys())
    upstream_model_keys = set(upstream_models.keys())

    new_models = upstream_model_keys - current_model_keys
    removed_models = current_model_keys - upstream_model_keys

    # Compare providers
    new_providers = upstream_providers - current_providers
    removed_providers = current_providers - upstream_providers

    # Check for pricing changes in existing models
    pricing_changes = []
    for model_key in current_model_keys & upstream_model_keys:
        current_model = current_models.get(model_key, {})
        upstream_model = upstream_models.get(model_key, {})

        current_input = current_model.get("input_cost_per_1k")
        current_output = current_model.get("output_cost_per_1k")
        upstream_input = upstream_model.get("input_cost_per_1k")
        upstream_output = upstream_model.get("output_cost_per_1k")

        # Skip if both are None
        if current_input is None and upstream_input is None:
            continue

        # Compare with tolerance for floating point
        def close(a, b, tol=1e-9):
            if a is None and b is None:
                return True
            if a is None or b is None:
                return False
            return abs(a - b) < tol

        if not close(current_input, upstream_input) or not close(current_output, upstream_output):
            pricing_changes.append({
                "model": model_key,
                "old_input": current_input,
                "new_input": upstream_input,
                "old_output": current_output,
                "new_output": upstream_output,
            })

    has_changes = bool(new_models or removed_models or new_providers or pricing_changes)

    if has_changes:
        with open(output_path, "w") as f:
            f.write("# Model Registry Drift Report\n\n")
            f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")

            if new_providers:
                f.write(f"## New Providers ({len(new_providers)})\n\n")
                for provider in sorted(list(new_providers)):
                    provider_data = upstream_raw.get(provider, {})
                    model_count = len(provider_data.get("models", {}))
                    f.write(f"- `{provider}` ({model_count} models)\n")
                f.write("\n")

            if new_models:
                f.write(f"## New Models ({len(new_models)})\n\n")
                f.write("Models available in models.dev but not in OISP:\n\n")
                for model in sorted(list(new_models))[:30]:
                    f.write(f"- `{model}`\n")
                if len(new_models) > 30:
                    f.write(f"\n... and {len(new_models) - 30} more models\n")
                f.write("\n")

            if removed_models:
                f.write(f"## Removed/Deprecated Models ({len(removed_models)})\n\n")
                f.write("Models in OISP but not in models.dev:\n\n")
                for model in sorted(list(removed_models))[:20]:
                    f.write(f"- `{model}`\n")
                if len(removed_models) > 20:
                    f.write(f"\n... and {len(removed_models) - 20} more models\n")
                f.write("\n")

            if pricing_changes:
                f.write(f"## Pricing Changes ({len(pricing_changes)})\n\n")
                f.write("| Model | Old Input | New Input | Old Output | New Output |\n")
                f.write("|-------|-----------|-----------|------------|------------|\n")
                for change in pricing_changes[:20]:
                    old_in = f"${change['old_input']:.6f}" if change['old_input'] else "N/A"
                    new_in = f"${change['new_input']:.6f}" if change['new_input'] else "N/A"
                    old_out = f"${change['old_output']:.6f}" if change['old_output'] else "N/A"
                    new_out = f"${change['new_output']:.6f}" if change['new_output'] else "N/A"
                    f.write(f"| `{change['model']}` | {old_in} | {new_in} | {old_out} | {new_out} |\n")
                if len(pricing_changes) > 20:
                    f.write(f"\n... and {len(pricing_changes) - 20} more pricing changes\n")
                f.write("\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- New providers: {len(new_providers)}\n")
            f.write(f"- New models: {len(new_models)}\n")
            f.write(f"- Removed models: {len(removed_models)}\n")
            f.write(f"- Pricing changes: {len(pricing_changes)}\n")
            f.write("\n")

            if new_models or new_providers or pricing_changes:
                f.write("**Action Required**: Run `gh workflow run sync-models.yml` to sync changes.\n")

        print(f"Changes detected! Report written to {output_path}")
        print(f"  - New providers: {len(new_providers)}")
        print(f"  - New models: {len(new_models)}")
        print(f"  - Removed models: {len(removed_models)}")
        print(f"  - Pricing changes: {len(pricing_changes)}")
        return True
    else:
        print("No changes detected between OISP and models.dev registries.")
        # Create empty file to indicate check ran
        Path(output_path).touch()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Compare OISP model registry with models.dev upstream"
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Path to current OISP models.json",
    )
    parser.add_argument(
        "--upstream",
        required=True,
        help="Path to models.dev upstream JSON",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output diff report (markdown)",
    )
    args = parser.parse_args()

    try:
        changes_detected = compare_models(args.current, args.upstream, args.output)
        # Exit 0 regardless - the workflow checks file content
        sys.exit(0)
    except Exception as e:
        print(f"Error comparing models: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
