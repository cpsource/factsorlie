#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION=$(grep '"version"' "$SCRIPT_DIR/manifest.json" | sed 's/.*"version": "\(.*\)".*/\1/')
OUT="$SCRIPT_DIR/yt-truth-checker-2-v${VERSION}.zip"

echo "Building release v${VERSION}..."

rm -f "$OUT"
cd "$SCRIPT_DIR"
zip -r "$OUT" manifest.json background.js content.js popup.html popup.js styles.css icons/

echo "Created: $OUT"
