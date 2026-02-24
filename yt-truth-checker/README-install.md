# YT Truth Checker 2 — Installation & Publishing

## Local Installation (Developer Mode)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked** and select the `yt-truth-checker-2/` directory
4. The extension icon should appear in your toolbar
5. Visit YouTube — hover over any video title for ~1 second to see the truth analysis tooltip

No API key needed — the extension calls `factsorlie.com/query` which handles the AI analysis server-side.

## Building a Release Zip

```bash
cd yt-truth-checker-2
make release
```

This creates `yt-truth-checker-2-v<VERSION>.zip` ready for upload.

To clean up old zips:

```bash
make clean
```

## Publishing to the Chrome Web Store

**One-time setup:**
1. Go to https://chrome.google.com/webstore/devconsole
2. Pay the **$5 one-time developer registration fee**
3. Verify your identity (email, possibly ID depending on region)

**Publish:**
1. Build the release zip with `make release`
2. In the Developer Dashboard, click **New Item** → upload the zip
3. Fill in the listing details:
   - Description, screenshots, category (Productivity or News)
   - At least one 1280×800 screenshot and a 128×128 icon
   - Privacy policy URL
4. Under **Privacy practices**, declare:
   - You communicate with a remote server (factsorlie.com)
   - The `host_permissions` justification (factsorlie.com for API, youtube.com for content script)
   - The `storage` permission is used to save user preferences (hover toggle, deep search toggle)
5. Click **Submit for review**

**Review takes** anywhere from a few hours to a few days. Google checks for malware, policy violations, and manifest correctness.

**Tips before submitting:**
- Add a privacy policy URL — e.g. "This extension sends YouTube video titles to factsorlie.com for AI-powered truth analysis. No personal data is collected. User preferences are stored locally."
- Take 2-3 screenshots of the tooltip in action on YouTube
- Bump the version in `manifest.json` each time you update

## Extension Settings

Open the extension popup to configure:
- **Enable on hover** — toggle whether hovering over titles triggers analysis
- **Deep Search** — when enabled, fetches video description and metadata for richer analysis
