/** /my/api-keys — create (reveal once) and revoke personal API keys. */
(function () {
  'use strict';

  async function rpc(url, params) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: params || {} }),
    });
    const data = await resp.json();
    if (data.error) {
      const e = data.error;
      return { success: false, error: (e.data && e.data.message) || e.message || 'server error' };
    }
    return data.result || { success: false, error: 'no response' };
  }

  document.addEventListener('DOMContentLoaded', function () {
    const createBtn = document.getElementById('apiKeyCreate');
    const nameInput = document.getElementById('apiKeyName');
    const expiresSel = document.getElementById('apiKeyExpires');
    const reveal = document.getElementById('apiKeyReveal');
    const value = document.getElementById('apiKeyValue');
    const copyBtn = document.getElementById('apiKeyCopy');

    if (createBtn) {
      createBtn.addEventListener('click', async function () {
        createBtn.disabled = true;
        const res = await rpc('/my/api-keys/create', {
          name: (nameInput.value || '').trim(),
          expires_days: expiresSel ? parseInt(expiresSel.value, 10) || 0 : 0,
        });
        createBtn.disabled = false;
        if (res.success) {
          value.textContent = res.key;
          reveal.style.display = 'block';
          nameInput.value = '';
        } else {
          window.alert('Could not create key: ' + (res.error || 'unknown error'));
        }
      });
    }

    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(value.textContent || '').then(function () {
          copyBtn.textContent = 'Copied';
          setTimeout(function () { copyBtn.textContent = 'Copy'; }, 1500);
        });
      });
    }

    document.addEventListener('click', async function (ev) {
      const btn = ev.target.closest('[data-action="revoke-key"]');
      if (!btn) return;
      ev.preventDefault();
      if (!window.confirm('Revoke this key? Any client using it will stop working.')) return;
      btn.disabled = true;
      const res = await rpc('/my/api-keys/' + btn.dataset.keyId + '/revoke', {});
      if (res.success) window.location.reload();
      else {
        btn.disabled = false;
        window.alert('Could not revoke: ' + (res.error || 'unknown error'));
      }
    });
  });
})();
