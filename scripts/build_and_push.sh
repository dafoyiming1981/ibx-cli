#!/usr/bin/env bash
# build_and_push.sh — Build ibx-cli wheel, container image, and push to Artifactory
#
# Usage:
#   bash scripts/build_and_push.sh [IMAGE_TAG]
#
# Example:
#   bash scripts/build_and_push.sh 0.1.0
#   bash scripts/build_and_push.sh latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default tag
TAG="${1:-latest}"

# Artifactory registry — modify to match your company's registry
REGISTRY="artifactory.company.com"
IMAGE_NAME="${REGISTRY}/ibx-cli:${TAG}"

cd "$REPO_ROOT"

echo "=== Step 1: Building wheel ==="
python3 -m pip install --quiet build
python3 -m build --wheel
WHEEL_FILE=$(ls dist/ibx_cli-*.whl | tail -1)
echo "Built: ${WHEEL_FILE}"

echo "=== Step 2: Building container image ==="
podman build -t "${IMAGE_NAME}" -f Containerfile .
echo "Image: ${IMAGE_NAME}"

echo "=== Step 3: Pushing to Artifactory ==="
podman push "${IMAGE_NAME}"
echo "Pushed: ${IMAGE_NAME}"

echo ""
echo "=== Run commands ==="
echo "  podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z ${IMAGE_NAME} dns zones"
echo "  podman run --rm -e IBX_HOST=... -e IBX_USERNAME=... -e IBX_PASSWORD=... ${IMAGE_NAME} dns a"
