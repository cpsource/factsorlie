// x-content.js — YT Truth Checker 2 for X.com (Twitter)
// Detects tweet hover events and checks tweet text via factsorlie.com/query.

(() => {
  'use strict';

  const cache = new Map();
  let tooltip = null;
  let hoverTimer = null;
  let hideTimer = null;
  let currentText = null;
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
      hideTooltip();
      currentText = null;
    }, 300);
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

  // ── Find tweet info from any element ───────────────────────────
  function findTweetInfo(el) {
    if (!el || !el.closest) return null;

    var article = el.closest('article[data-testid="tweet"]');
    if (!article) return null;

    var tweetTextEl = article.querySelector('div[data-testid="tweetText"]');
    if (!tweetTextEl) return null;

    var text = (tweetTextEl.textContent || '').trim();
    if (text.length < 20) return null;

    // Extract author for context
    var authorEl = article.querySelector('div[data-testid="User-Name"]');
    var author = authorEl ? (authorEl.textContent || '').trim() : '';

    return { text: text, element: tweetTextEl, article: article, author: author };
  }

  // ── API Call ───────────────────────────────────────────────────
  function checkTitle(title) {
    return new Promise(function(resolve, reject) {
      const msg = { action: 'checkTitle', title: title };
      chrome.runtime.sendMessage(
        msg,
        function(response) {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (response && response.success) {
            resolve(response.result);
          } else {
            reject(new Error((response && response.error) || 'Unknown error'));
          }
        }
      );
    });
  }

  // ── Event Handling ─────────────────────────────────────────────
  document.addEventListener('mouseover', function(e) {
    if (!settings.enableHover) return;

    var info = findTweetInfo(e.target);
    if (!info) return;

    if (info.text === currentText) return;

    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(function() {
      currentText = info.text;
      // Prepend author for context if available
      var queryText = info.author
        ? info.author + ': ' + info.text
        : info.text;
      console.log('[YTTruth2-X] Hover detected:', info.text.substring(0, 60));

      if (cache.has(info.text)) {
        var cached = cache.get(info.text);
        showResult(cached, info.element);
        return;
      }

      showLoading(info.element);

      checkTitle(queryText).then(function(result) {
        cache.set(info.text, result);
        if (currentText === info.text) {
          showResult(result, info.element);
        }
      }).catch(function(err) {
        console.error('[YTTruth2-X] Error:', err);
        if (currentText === info.text) {
          showError(err.message);
        }
      });
    }, 800);
  });

  document.addEventListener('mouseover', function(e) {
    if (tooltip && tooltip.contains(e.target)) {
      cancelHide();
    }
  });

  document.addEventListener('mouseout', function(e) {
    if (tooltip && tooltip.contains(e.target) && !tooltip.contains(e.relatedTarget)) {
      scheduleHide();
      return;
    }

    var leaving = findTweetInfo(e.target);
    var entering = e.relatedTarget ? findTweetInfo(e.relatedTarget) : null;

    if (leaving && !entering) {
      clearTimeout(hoverTimer);
      scheduleHide();
    }
  });

  window.addEventListener('scroll', function() {
    clearTimeout(hoverTimer);
    cancelHide();
    hideTooltip();
    currentText = null;
  }, { passive: true });

  // ── Init ───────────────────────────────────────────────────────
  loadSettings(function() {
    console.log('[YT Truth Checker 2 — X.com] Loaded \u2713 | Server-side analysis');
  });
})();
