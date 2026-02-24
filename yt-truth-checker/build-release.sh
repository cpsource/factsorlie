#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXT_DIR="$SCRIPT_DIR/yt-truth-checker"
VERSION=$(grep '"version"' "$EXT_DIR/manifest.json" | sed 's/.*"version": "\(.*\)".*/\1/')
OUT="$SCRIPT_DIR/yt-truth-checker-v${VERSION}.zip"

echo "Building release v${VERSION}..."

rm -f "$OUT"
cd "$EXT_DIR"
zip -r "$OUT" manifest.json background.js content.js popup.html popup.js styles.css icons/

echo "Created: $OUT"
