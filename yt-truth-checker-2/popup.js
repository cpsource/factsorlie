document.addEventListener('DOMContentLoaded', () => {
  const enableHover = document.getElementById('enableHover');
  const enableDeepSearch = document.getElementById('enableDeepSearch');
  const status = document.getElementById('status');

  // Load saved settings
  chrome.storage.local.get(['enableHover', 'enableDeepSearch'], (data) => {
    if (data.enableHover !== undefined) enableHover.checked = data.enableHover;
    if (data.enableDeepSearch !== undefined) enableDeepSearch.checked = data.enableDeepSearch;
  });

  function saveSettings(msg) {
    chrome.storage.local.set({
      enableHover: enableHover.checked,
      enableDeepSearch: enableDeepSearch.checked
    }, () => {
      status.style.color = '#4caf50';
      status.textContent = msg;
      setTimeout(() => { status.textContent = ''; }, 2000);
    });
  }

  enableHover.addEventListener('change', () => {
    saveSettings(enableHover.checked ? 'Hover enabled \u2713' : 'Hover disabled');
  });

  enableDeepSearch.addEventListener('change', () => {
    saveSettings(enableDeepSearch.checked ? 'Deep Search enabled \u2713' : 'Deep Search disabled');
  });
});
