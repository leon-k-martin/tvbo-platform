/**
 * Portal "My Models" actions: share / make-private toggle and delete.
 *
 * Buttons opt in via data attributes:
 *   data-action="visibility" data-model-id="..." data-visibility="shared|private"
 *   data-action="delete"     data-model-id="..."
 * Both call the owner-only jsonrpc endpoints in controllers/portal.py.
 */
(function () {
  'use strict';

  async function rpc(url, params) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: params || {} }),
    });
    const body = await resp.json();
    return body.result || { success: false, error: 'no response' };
  }

  function setBusy(btn, busy) {
    btn.disabled = busy;
    btn.classList.toggle('disabled', busy);
  }

  async function onVisibility(btn) {
    const id = btn.dataset.modelId;
    const next = btn.dataset.visibility; // target visibility
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/visibility', { visibility: next });
    if (res.success) {
      window.location.reload();
    } else {
      setBusy(btn, false);
      window.alert('Could not update sharing: ' + (res.error || 'unknown error'));
    }
  }

  async function onDelete(btn) {
    const id = btn.dataset.modelId;
    const name = btn.dataset.modelName || 'this model';
    if (!window.confirm('Delete ' + name + '? This cannot be undone.')) return;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/delete', {});
    if (res.success) {
      window.location.reload();
    } else {
      setBusy(btn, false);
      window.alert('Could not delete: ' + (res.error || 'unknown error'));
    }
  }

  document.addEventListener('click', function (ev) {
    const btn = ev.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    if (action !== 'visibility' && action !== 'delete') return;
    ev.preventDefault();
    if (action === 'visibility') onVisibility(btn);
    else onDelete(btn);
  });
})();
