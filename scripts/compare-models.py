#!/usr/bin/env python3
"""Compare OISP model registry with LiteLLM upstream.

This script compares the current OISP model registry with the latest LiteLLM data
to detect new models, removed models, and pricing changes.

Usage:
    python compare-models.py --current models.json --upstream litellm.json --output diff.md
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


def compare_models(current_path: str, upstream_path: str, output_path: str) -> bool:
    """Compare OISP model registry with LiteLLM upstream.

    Returns:
        True if changes were detected, False otherwise.
    """
    current = load_json(current_path)
    upstream = load_json(upstream_path)

    # Get model sets
    current_models = set(current.get("models", {}).keys())
    upstream_models = set(upstream.keys())

    new_models = upstream_models - current_models
    removed_models = current_models - upstream_models

    # Check for pricing changes in existing models
    pricing_changes = []
    for model_id in current_models & upstream_models:
        current_model = current.get("models", {}).get(model_id, {})
        upstream_model = upstream.get(model_id, {})

        # Compare pricing
        current_input = current_model.get("input_cost_per_1k")
        current_output = current_model.get("output_cost_per_1k")
        upstream_input = upstream_model.get("input_cost_per_token", 0) * 1000
        upstream_output = upstream_model.get("output_cost_per_token", 0) * 1000

        if current_input != upstream_input or current_output != upstream_output:
            pricing_changes.append({
                "model": model_id,
                "old_input": current_input,
                "new_input": upstream_input,
                "old_output": current_output,
                "new_output": upstream_output,
            })

    has_changes = bool(new_models or removed_models or pricing_changes)

    if has_changes:
        with open(output_path, "w") as f:
            f.write("# Model Registry Drift Report\n\n")
            f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")

            if new_models:
                f.write(f"## New Models ({len(new_models)})\n\n")
                f.write("Models available in LiteLLM but not in OISP:\n\n")
                for model in sorted(list(new_models))[:30]:
                    upstream_model = upstream.get(model, {})
                    mode = upstream_model.get("mode", "unknown")
                    f.write(f"- `{model}` ({mode})\n")
                if len(new_models) > 30:
                    f.write(f"\n... and {len(new_models) - 30} more models\n")
                f.write("\n")

            if removed_models:
                f.write(f"## Removed/Deprecated Models ({len(removed_models)})\n\n")
                f.write("Models in OISP but not in LiteLLM:\n\n")
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
                    f.write(
                        f"| `{change['model']}` | "
                        f"${change['old_input']:.6f} | ${change['new_input']:.6f} | "
                        f"${change['old_output']:.6f} | ${change['new_output']:.6f} |\n"
                    )
                if len(pricing_changes) > 20:
                    f.write(f"\n... and {len(pricing_changes) - 20} more pricing changes\n")
                f.write("\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- New models: {len(new_models)}\n")
            f.write(f"- Removed models: {len(removed_models)}\n")
            f.write(f"- Pricing changes: {len(pricing_changes)}\n")
            f.write("\n")

            if new_models or pricing_changes:
                f.write("**Action Required**: Run `gh workflow run sync-models.yml` to sync changes.\n")

        print(f"Changes detected! Report written to {output_path}")
        print(f"  - New models: {len(new_models)}")
        print(f"  - Removed models: {len(removed_models)}")
        print(f"  - Pricing changes: {len(pricing_changes)}")
        return True
    else:
        print("No changes detected between OISP and LiteLLM registries.")
        # Create empty file to indicate check ran
        Path(output_path).touch()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Compare OISP model registry with LiteLLM upstream"
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Path to current OISP models.json",
    )
    parser.add_argument(
        "--upstream",
        required=True,
        help="Path to LiteLLM upstream JSON",
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
