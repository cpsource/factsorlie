# Facts or Lie — YouTube & X/Twitter Truth Checker

A web platform and Chrome extension that uses Claude AI to check whether YouTube video headlines and X/Twitter posts are true, false, misleading, or clickbait.

## Overview

**factsorlie.com** provides a server-side API that analyzes text using Claude AI. The **YT Truth Checker** Chrome extension connects to this API — just hover over any YouTube video title or X/Twitter tweet for ~1 second and get an instant verdict. No API key required.

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
User hovers on YouTube title or X/Twitter tweet
  → Chrome extension (yt-truth-checker) detects hover
    → POSTs text to https://factsorlie.com/query
      → Flask app calls Anthropic API (Claude Sonnet) server-side
      → Returns JSON verdict
    → Extension displays tooltip + badge on thumbnail
```

With **Deep Search** enabled (YouTube only), the extension first scrapes the video's description, view count, and upload date from the YouTube page, then sends that metadata along with the title to the server for richer analysis.

## Components

### Flask Web App (`app.py`)

- `/` — Landing page with visit counter
- `/submit` — Submit statements as fact or lie
- `/query` — POST endpoint for AI truth-checking (accepts `title` and optional `videoMeta`)
- `/health` — Health check

### Chrome Extension (`yt-truth-checker/`)

- **YouTube**: Hover over any video title for a tooltip with Claude's analysis
- **X/Twitter**: Hover over any tweet to fact-check its content
- Toggle hover detection and Deep Search from the popup
- Results cached per session — re-hovering is instant
- Badges appear on thumbnails for previously checked videos (YouTube)
- No API key needed — all AI calls go through factsorlie.com

See [yt-truth-checker/README-install.md](https://github.com/cpsource/factsorlie/blob/master/yt-truth-checker/README-install.md) for installation and publishing instructions.

## Setup

### Server

```bash
# Ensure ANTHROPIC_API_KEY is set in /home/ubuntu/.env
docker-compose up --build -d
```

### Extension

1. Open `chrome://extensions/` and enable **Developer mode**
2. Click **Load unpacked** and select the `yt-truth-checker/yt-truth-checker/` directory
3. Visit YouTube or X/Twitter and hover over video titles or tweets

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
├── yt-truth-checker/     # Chrome extension (server-side API)
│   ├── manifest.json
│   ├── background.js       # Sends requests to factsorlie.com/query
│   ├── content.js          # YouTube hover detection + tooltip UI
│   ├── x-content.js        # X/Twitter hover detection + tooltip UI
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
