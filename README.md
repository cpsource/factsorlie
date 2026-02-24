# Facts or Lie — YouTube Truth Checker

A web platform and Chrome extension that uses Claude AI to check whether YouTube video headlines are true, false, misleading, or clickbait.

## Overview

**factsorlie.com** provides a server-side API that analyzes YouTube video titles using Claude AI. The **YT Truth Checker 2** Chrome extension connects to this API — just hover over any YouTube video title for ~1 second and get an instant verdict. No API key required.

## Verdicts

| Verdict | Color | Meaning |
|---------|-------|---------|
| ✓ TRUE | Green | Core claim is factually accurate |
| ✗ FALSE | Red | Core claim is factually wrong |
| ⚠ MISLEADING | Orange | Kernel of truth, deceptive framing |
| 🎣 CLICKBAIT | Yellow | Exaggerated language dramatizing mundane events |
| 💬 OPINION | Blue | Subjective view, not a factual claim |
| ? UNVERIFIABLE | Gray | Can't determine truth from headline alone |

## Architecture

```
User hovers on YouTube title
  → Chrome extension (yt-truth-checker-2) detects hover
    → POSTs title to https://factsorlie.com/query
      → Flask app calls Anthropic API (Claude Sonnet) server-side
      → Returns JSON verdict
    → Extension displays tooltip + badge on thumbnail
```

With **Deep Search** enabled, the extension first scrapes the video's description, view count, and upload date from the YouTube page, then sends that metadata along with the title to the server for richer analysis.

## Components

### Flask Web App (`app.py`)

- `/` — Landing page with visit counter
- `/submit` — Submit statements as fact or lie
- `/query` — POST endpoint for AI truth-checking (accepts `title` and optional `videoMeta`)
- `/health` — Health check

### Chrome Extension (`yt-truth-checker-2/`)

- Hover over any YouTube video title for a tooltip with Claude's analysis
- Toggle hover detection and Deep Search from the popup
- Results cached per session — re-hovering is instant
- Badges appear on thumbnails for previously checked videos
- No API key needed — all AI calls go through factsorlie.com

See [yt-truth-checker-2/README-install.md](https://github.com/cpsource/factsorlie/blob/master/yt-truth-checker-2/README-install.md) for installation and publishing instructions.

## Setup

### Server

```bash
# Ensure ANTHROPIC_API_KEY is set in /home/ubuntu/.env
docker-compose up --build -d
```

### Extension

1. Open `chrome://extensions/` and enable **Developer mode**
2. Click **Load unpacked** and select the `yt-truth-checker-2/` directory
3. Visit YouTube and hover over video titles

## Testing

```bash
./tools/qa/run_tests.sh
```

Runs all tests inside the Flask container using the `myproject` venv.

## Project Structure

```
factsorlie/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Flask container (myproject venv)
├── docker-compose.yml      # Flask + Apache + Redis
├── templates/              # HTML templates
├── yt-truth-checker-2/     # Chrome extension (server-side API)
│   ├── manifest.json
│   ├── background.js       # Sends requests to factsorlie.com/query
│   ├── content.js          # Hover detection + tooltip UI
│   ├── popup.html/js       # Settings popup
│   ├── styles.css          # Tooltip and badge styles
│   ├── icons/
│   ├── build-release.sh    # Build release zip
│   └── Makefile
├── apache/                 # Apache reverse proxy config
├── tools/qa/               # Test suite
│   ├── run_tests.sh
│   ├── test_health.py
│   └── test_query.py
└── README.md               # This file
```
