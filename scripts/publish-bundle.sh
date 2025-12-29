#!/bin/bash
# Publish OISP Spec Bundle to site for hosting at oisp.dev
#
# Usage: ./scripts/publish-bundle.sh
#
# This script:
# 1. Runs build-bundle.py to generate the latest bundle
# 2. Copies the bundle to site/spec/v0.1/ for GitHub Pages hosting
# 3. The bundle will be available at https://oisp.dev/spec/v0.1/bundle.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building spec bundle..."
python3 "$SCRIPT_DIR/build-bundle.py"

echo "Publishing to spec/v0.1/..."
mkdir -p "$ROOT_DIR/spec/v0.1"
cp "$ROOT_DIR/dist/oisp-spec-bundle.json" "$ROOT_DIR/spec/v0.1/bundle.json"

# Also copy minified version
if [ -f "$ROOT_DIR/dist/oisp-spec-bundle.min.json" ]; then
    cp "$ROOT_DIR/dist/oisp-spec-bundle.min.json" "$ROOT_DIR/spec/v0.1/bundle.min.json"
fi

echo ""
echo "Bundle published successfully!"
echo "After pushing, it will be available at:"
echo "  https://oisp.dev/spec/v0.1/bundle.json"
echo ""

