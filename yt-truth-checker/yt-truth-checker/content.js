// content.js — YT Truth Checker 2
// Uses mouseover with broad selector matching for YouTube's current DOM.

(() => {
  'use strict';

  const cache = new Map();
  let tooltip = null;
  let hoverTimer = null;
  let hideTimer = null;
  let currentTitle = null;
  let settings = { enableHover: true, deepSearch: false };

  // ── Settings ───────────────────────────────────────────────────
  function loadSettings(cb) {
    chrome.storage.local.get(['enableHover', 'enableDeepSearch'], (data) => {
      if (data.enableHover !== undefined) settings.enableHover = data.enableHover;
      if (data.enableDeepSearch !== undefined) settings.deepSearch = data.enableDeepSearch;
      if (cb) cb();
    });
  }

  chrome.storage.onChanged.addListener((changes) => {
    if (changes.enableHover) settings.enableHover = changes.enableHover.newValue;
    if (changes.enableDeepSearch) settings.deepSearch = changes.enableDeepSearch.newValue;
  });

  // ── Tooltip ────────────────────────────────────────────────────
  function ensureTooltip() {
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = 'ytc-tooltip';
      document.body.appendChild(tooltip);
    }
    return tooltip;
  }

  function showLoading(anchorEl) {
    const t = ensureTooltip();
    t.className = 'ytc-tooltip ytc-loading';
    t.innerHTML = '<div class="ytc-spinner"></div><span>Checking with Claude...</span>';
    positionTooltip(anchorEl);
    requestAnimationFrame(() => t.classList.add('ytc-visible'));
  }

  function showResult(result, anchorEl) {
    const t = ensureTooltip();
    const verdict = result.verdict || 'UNVERIFIABLE';
    t.className = 'ytc-tooltip ytc-result ytc-verdict-' + verdict;

    let flagsHtml = '';
    if (result.red_flags && result.red_flags.length > 0) {
      flagsHtml = '<div class="ytc-red-flags">' +
        result.red_flags.map(f => '<span class="ytc-flag">\u2691 ' + esc(f) + '</span>').join('') +
      '</div>';
    }

    const deepBadge = result._deepSearched
      ? '<span class="ytc-deep-badge">&#x1F50D; Deep Search</span>'
      : '';

    t.innerHTML =
      '<div class="ytc-verdict-bar">' +
        '<span class="ytc-verdict-label">' + verdictIcon(verdict) + ' ' + esc(verdict) + '</span>' +
        '<span class="ytc-confidence">' + esc(result.confidence || 'unknown') + ' confidence</span>' +
      '</div>' +
      '<div class="ytc-summary">' + esc(result.summary || 'No summary available.') + '</div>' +
      flagsHtml +
      '<div class="ytc-footer">' +
        deepBadge +
        '<button class="ytc-copy-btn" title="Copy to clipboard">\uD83D\uDCCB</button>' +
      '</div>';

    t.querySelector('.ytc-copy-btn').addEventListener('click', function(e) {
      e.stopPropagation();
      var flags = (result.red_flags && result.red_flags.length)
        ? '\nFlags:\n' + result.red_flags.map(function(f) { return '\u2022 ' + f; }).join('\n')
        : '';
      var text = verdict + ' (' + (result.confidence || 'unknown') + ' confidence)\n' +
        (result.summary || '') + flags;
      navigator.clipboard.writeText(text).then(function() {
        var btn = t.querySelector('.ytc-copy-btn');
        btn.textContent = '\u2713';
        setTimeout(function() { btn.textContent = '\uD83D\uDCCB'; }, 1500);
      });
    });

    positionTooltip(anchorEl);
    requestAnimationFrame(() => t.classList.add('ytc-visible'));
  }

  function showError(msg) {
    const t = ensureTooltip();
    t.className = 'ytc-tooltip ytc-error ytc-visible';
    t.textContent = '\u26A0 ' + msg;
  }

  function hideTooltip() {
    if (tooltip) tooltip.classList.remove('ytc-visible');
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() {
      // Don't hide if mouse is currently over the tooltip
      if (tooltip && tooltip.matches(':hover')) return;
      hideTooltip();
      currentTitle = null;
    }, 1000);
  }

  function cancelHide() {
    clearTimeout(hideTimer);
  }

  function positionTooltip(anchorEl) {
    if (!tooltip || !anchorEl) return;
    const rect = anchorEl.getBoundingClientRect();
    let top = rect.bottom + window.scrollY + 8;
    let left = rect.left + window.scrollX;
    if (left + 330 > window.innerWidth) left = window.innerWidth - 340;
    if (left < 8) left = 8;
    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
  }

  function verdictIcon(v) {
    var icons = { TRUE:'\u2713', FALSE:'\u2717', MISLEADING:'\u26A0', CLICKBAIT:'\uD83C\uDFA3', OPINION:'\uD83D\uDCAC', UNVERIFIABLE:'?' };
    return icons[v] || '?';
  }

  function esc(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // ── Find title from any element ────────────────────────────────
  // Find video info using elementsFromPoint to pierce Shadow DOM
  function findTitleFromPoint(x, y) {
    var els = document.elementsFromPoint(x, y);
    var renderer = null;
    for (var i = 0; i < els.length; i++) {
      var tag = els[i].tagName;
      if (tag === 'YTD-RICH-ITEM-RENDERER' || tag === 'YTD-VIDEO-RENDERER' ||
          tag === 'YTD-COMPACT-VIDEO-RENDERER' || tag === 'YTD-GRID-VIDEO-RENDERER' ||
          tag === 'YTD-RICH-GRID-MEDIA') {
        renderer = els[i];
        break;
      }
    }
    if (!renderer) return null;

    var titleLink = renderer.querySelector('a.ytLockupMetadataViewModelTitle') ||
                    renderer.querySelector('a#video-title-link') ||
                    renderer.querySelector('a#video-title') ||
                    renderer.querySelector('a.yt-lockup-metadata-view-model__title');

    if (!titleLink) return null;

    var text = (titleLink.textContent || '').trim();
    if (text.length < 10) return null;

    console.log('[YTTruth2] Found title via elementsFromPoint:', text.substring(0, 50));
    return { text: text, element: titleLink, renderer: renderer, url: titleLink.href };
  }

  // Legacy closest()-based lookup (for direct title hovers)
  function findTitleInfo(el) {
    if (!el || !el.closest) return null;

    var titleLink = el.closest('a.ytLockupMetadataViewModelTitle') ||
                    el.closest('a#video-title-link') ||
                    el.closest('a#video-title');

    if (!titleLink) {
      var span = el.closest('span.ytAttributedStringHost');
      if (span) titleLink = span.closest('a.ytLockupMetadataViewModelTitle');
    }

    if (!titleLink && el.id === 'video-title') {
      titleLink = el.closest('a#video-title-link') || el;
    }

    if (!titleLink) return null;

    var renderer = titleLink.closest(
      'ytd-rich-item-renderer, ytd-video-renderer, ytd-compact-video-renderer, ' +
      'ytd-grid-video-renderer, ytd-playlist-video-renderer, ytd-reel-item-renderer'
    );

    var text = (titleLink.textContent || '').trim();
    if (text.length < 10) return null;

    console.log('[YTTruth2] Found title via closest():', text.substring(0, 50));
    return { text: text, element: titleLink, renderer: renderer, url: titleLink.href };
  }

  // ── API Call ────────────────────────────────────────────────────
  function sendMsg(msg) {
    return new Promise(function(resolve, reject) {
      try {
        chrome.runtime.sendMessage(msg, function(response) {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (response && response.success) {
            resolve(response.result);
          } else {
            reject(new Error((response && response.error) || 'Unknown error'));
          }
        });
      } catch (e) {
        reject(e);
      }
    });
  }

  function checkTitle(title, videoUrl) {
    const msg = { action: 'checkTitle', title: title };
    if (videoUrl) msg.videoUrl = videoUrl;
    return sendMsg(msg).catch(function(err) {
      if (err.message && err.message.includes('Extension context invalidated')) {
        // Extension was updated/reloaded — prompt user to refresh
        return Promise.reject(new Error('Extension updated — please refresh the page'));
      }
      // Retry once in case service worker was just asleep
      return sendMsg(msg);
    });
  }

  // ── Badge on thumbnail ─────────────────────────────────────────
  function addBadge(renderer, verdict) {
    if (!renderer) return;
    var thumb = renderer.querySelector('ytd-thumbnail, a#thumbnail, .ytd-thumbnail');
    if (!thumb || thumb.querySelector('.ytc-inline-badge')) return;
    if (getComputedStyle(thumb).position === 'static') thumb.style.position = 'relative';
    var badge = document.createElement('div');
    badge.className = 'ytc-inline-badge ytc-badge-' + verdict;
    badge.textContent = verdict;
    thumb.appendChild(badge);
  }

  // ── Event Handling ─────────────────────────────────────────────
  // NOTE: Must use capture phase (true) — YouTube calls stopPropagation() in bubble phase
  document.addEventListener('mouseover', function(e) {
    if (!settings.enableHover) return;

    // Try closest() first (fast), fall back to elementsFromPoint (pierces Shadow DOM)
    var info = findTitleInfo(e.target) || findTitleFromPoint(e.clientX, e.clientY);
    if (!info) return;

    if (info.text === currentTitle) return;

    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(function() {
      currentTitle = info.text;
      console.log('[YTTruth2] Hover detected:', info.text.substring(0, 60));
      console.log('[YTTruth2]   URL:', info.url);
      console.log('[YTTruth2]   renderer:', info.renderer ? info.renderer.tagName : 'none');

      if (cache.has(info.text)) {
        console.log('[YTTruth2]   -> cache hit');
        var cached = cache.get(info.text);
        showResult(cached, info.element);
        addBadge(info.renderer, cached.verdict);
        return;
      }

      console.log('[YTTruth2]   -> sending to background for API check...');
      showLoading(info.element);

      checkTitle(info.text, info.url).then(function(result) {
        console.log('[YTTruth2]   -> result:', result.verdict, '(' + result.confidence + ')');
        cache.set(info.text, result);
        if (currentTitle === info.text) {
          showResult(result, info.element);
        }
        addBadge(info.renderer, result.verdict);
      }).catch(function(err) {
        console.error('[YTTruth2] Error:', err);
        if (currentTitle === info.text) {
          showError(err.message);
        }
      });
    }, 800);
  }, true); // capture phase — YouTube stops propagation in bubble phase

  document.addEventListener('mouseover', function(e) {
    if (tooltip && tooltip.contains(e.target)) {
      cancelHide();
    }
  }, true);

  document.addEventListener('mouseout', function(e) {
    if (tooltip && tooltip.contains(e.target) && !tooltip.contains(e.relatedTarget)) {
      scheduleHide();
      return;
    }

    var leaving = findTitleInfo(e.target);
    var entering = e.relatedTarget ? findTitleInfo(e.relatedTarget) : null;

    if (leaving && !entering) {
      clearTimeout(hoverTimer);
      scheduleHide();
    }
  }, true);

  window.addEventListener('scroll', function() {
    clearTimeout(hoverTimer);
    cancelHide();
    hideTooltip();
    currentTitle = null;
  }, { passive: true });

  // ── Init ───────────────────────────────────────────────────────
  loadSettings(function() {
    console.log('[YT Truth Checker 2] Loaded \u2713 | Server-side analysis');
  });
})();
