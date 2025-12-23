#!/bin/bash
# Setup git hooks for oisp-spec
#
# Usage: ./scripts/setup-hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$ROOT_DIR/.git/hooks"

echo "Setting up git hooks for oisp-spec..."

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for oisp-spec
#
# Automatically:
# 1. Syncs models from LiteLLM if provider files changed
# 2. Regenerates the spec bundle
# 3. Publishes bundle to site/ for oisp.dev hosting

set -e

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Warning: python3 not found, skipping auto-generation"
    exit 0
fi

# Check for PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Warning: PyYAML not installed (pip install pyyaml), skipping auto-generation"
    exit 0
fi

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

# Check if provider YAML files changed (triggers model sync + bundle rebuild)
PROVIDER_YAML_CHANGES=$(echo "$STAGED_FILES" | grep -E '^semconv/providers/[^_].*\.yaml$' || true)

# Check if any source files changed that affect the bundle
BUNDLE_SOURCE_CHANGES=$(echo "$STAGED_FILES" | grep -E '^semconv/|^schema/' || true)

NEEDS_REBUILD=false

# If provider YAMLs changed, sync models first
if [ -n "$PROVIDER_YAML_CHANGES" ]; then
    echo "Provider definitions changed, syncing models..."
    python3 ./scripts/sync-models.py 2>/dev/null || {
        echo "Warning: Model sync failed (network issue?), continuing..."
    }
    
    # Stage generated model files
    git add semconv/providers/_generated/ 2>/dev/null || true
    NEEDS_REBUILD=true
fi

# If any bundle source changed, rebuild
if [ -n "$BUNDLE_SOURCE_CHANGES" ] || [ "$NEEDS_REBUILD" = true ]; then
    echo "Regenerating spec bundle..."
    python3 ./scripts/build-bundle.py
    
    # Publish to site
    mkdir -p ./site/spec/v0.1
    cp ./dist/oisp-spec-bundle.json ./site/spec/v0.1/bundle.json
    if [ -f ./dist/oisp-spec-bundle.min.json ]; then
        cp ./dist/oisp-spec-bundle.min.json ./site/spec/v0.1/bundle.min.json
    fi
    
    # Stage all generated files
    git add dist/oisp-spec-bundle.json 2>/dev/null || true
    git add dist/oisp-spec-bundle.min.json 2>/dev/null || true
    git add site/spec/v0.1/ 2>/dev/null || true
    
    echo "Bundle regenerated and staged."
fi

exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo "Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will automatically:"
echo "  1. Sync models from LiteLLM when provider/*.yaml files change"
echo "  2. Regenerate the spec bundle when semconv/ or schema/ changes"
echo "  3. Publish bundle to site/spec/v0.1/ for oisp.dev"
echo "  4. Stage all generated files"
echo ""
