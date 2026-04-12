// background.js — sends check requests to factsorlie.com/query
// If deep search is enabled, fetches video metadata first and includes it.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkTitle') {
    console.log('[YTTruth2-BG] Received checkTitle:', request.title?.substring(0, 50));
    (async () => {
      try {
        const { enableDeepSearch } = await chrome.storage.local.get(['enableDeepSearch']);
        console.log('[YTTruth2-BG] deepSearch:', !!enableDeepSearch, '| videoUrl:', request.videoUrl?.substring(0, 60));
        let videoMeta = null;
        if (enableDeepSearch && request.videoUrl) {
          console.log('[YTTruth2-BG] Fetching video metadata...');
          videoMeta = await fetchVideoMeta(request.videoUrl).catch(() => null);
          console.log('[YTTruth2-BG] videoMeta:', videoMeta ? 'found' : 'null');
        }
        const sourceUrl = request.videoUrl || request.sourceUrl || null;
        console.log('[YTTruth2-BG] Calling handleCheck -> factsorlie.com/query');
        const result = await handleCheck(request.title, videoMeta, sourceUrl);
        console.log('[YTTruth2-BG] Result:', result.verdict, '(' + result.confidence + ')');
        sendResponse({ success: true, result: { ...result, _deepSearched: !!videoMeta } });
      } catch (err) {
        console.error('[YTTruth2-BG] Error:', err.message);
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true; // keep channel open for async
  }
});

async function fetchVideoMeta(videoUrl) {
  const res = await fetch(videoUrl);
  const html = await res.text();
  // uploadDate from JSON-LD
  let uploadDate = '';
  const ldIdx = html.indexOf('application/ld+json');
  if (ldIdx !== -1) {
    const jsonStart = html.indexOf('>', ldIdx) + 1;
    const jsonEnd = html.indexOf('</script>', jsonStart);
    if (jsonEnd !== -1) {
      try {
        const ld = JSON.parse(html.substring(jsonStart, jsonEnd).trim());
        uploadDate = ld.uploadDate || '';
      } catch (e) {}
    }
  }

  // description and viewCount from ytInitialPlayerResponse
  const descMatch = html.match(/"shortDescription":"((?:[^"\\]|\\.)*)"/);
  const viewMatch = html.match(/"viewCount":"(\d+)"/);
  const description = descMatch ? JSON.parse('"' + descMatch[1] + '"') : '';
  const viewCount   = viewMatch ? viewMatch[1] : '';

  if (!uploadDate && !description && !viewCount) return null;
  return { description, uploadDate, viewCount };
}

async function handleCheck(title, videoMeta = null, sourceUrl = null) {
  const body = { title };
  if (videoMeta) body.videoMeta = videoMeta;
  if (sourceUrl) body.sourceUrl = sourceUrl;

  const response = await fetch('https://factsorlie.com/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`API ${response.status}: ${errBody.substring(0, 200)}`);
  }

  return response.json();
}
