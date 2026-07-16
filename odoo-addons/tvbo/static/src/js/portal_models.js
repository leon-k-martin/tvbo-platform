/**
 * Portal "My Models" actions.
 *
 * Two independent sharing mechanisms, plus delete. Buttons opt in via
 * data attributes and call the owner-only jsonrpc endpoints in
 * controllers/portal.py:
 *
 *   Publish workflow (gated by validation + peer review):
 *     data-action="submit"    data-model-id="..."   -> /my/models/<id>/submit
 *     data-action="withdraw"  data-model-id="..."   -> /my/models/<id>/withdraw
 *   Peer-to-peer sharing (instant, no review):
 *     data-action="share"     data-model-id="..."   -> /my/models/<id>/share
 *     data-action="unshare"   data-model-id data-user-id -> /my/models/<id>/unshare
 *   data-action="delete"      data-model-id="..."   -> /my/models/<id>/delete
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

  // Render a validation report (list of failed/skipped checks) as readable text.
  function formatReport(report) {
    if (!report || !Array.isArray(report.checks)) return '';
    const lines = report.checks
      .filter(function (c) { return !c.ok || c.skipped; })
      .map(function (c) {
        const mark = c.skipped ? '•' : '✗';
        return mark + ' ' + (c.label || c.id) + ': ' + (c.detail || '');
      });
    return lines.join('\n');
  }

  async function onSubmit(btn) {
    const id = btn.dataset.modelId;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/submit', {});
    if (res.success) {
      window.alert(res.message || 'Submitted for peer review.');
      window.location.reload();
    } else {
      setBusy(btn, false);
      const detail = formatReport(res.report);
      window.alert(
        (res.message || 'Could not submit.') + (detail ? '\n\n' + detail : ''));
    }
  }

  async function onWithdraw(btn) {
    const id = btn.dataset.modelId;
    if (!window.confirm('Withdraw this model? It will return to a private draft.')) return;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/withdraw', {});
    if (res.success) window.location.reload();
    else { setBusy(btn, false); window.alert('Could not withdraw: ' + (res.error || 'unknown error')); }
  }

  async function onShare(btn) {
    const id = btn.dataset.modelId;
    const login = window.prompt('Share with which colleague?\nEnter their account login or email:');
    if (!login) return;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/share', { login: login });
    if (res.success) window.location.reload();
    else { setBusy(btn, false); window.alert('Could not share: ' + (res.error || 'unknown error')); }
  }

  async function onUnshare(btn) {
    const id = btn.dataset.modelId;
    const userId = btn.dataset.userId;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/unshare', { user_id: userId });
    if (res.success) window.location.reload();
    else { setBusy(btn, false); window.alert('Could not remove: ' + (res.error || 'unknown error')); }
  }

  async function onDelete(btn) {
    const id = btn.dataset.modelId;
    const name = btn.dataset.modelName || 'this model';
    if (!window.confirm('Delete ' + name + '? This cannot be undone.')) return;
    setBusy(btn, true);
    const res = await rpc('/my/models/' + id + '/delete', {});
    if (res.success) window.location.reload();
    else { setBusy(btn, false); window.alert('Could not delete: ' + (res.error || 'unknown error')); }
  }

  const HANDLERS = {
    submit: onSubmit,
    withdraw: onWithdraw,
    share: onShare,
    unshare: onUnshare,
    delete: onDelete,
  };

  document.addEventListener('click', function (ev) {
    const btn = ev.target.closest('[data-action]');
    if (!btn) return;
    const handler = HANDLERS[btn.dataset.action];
    if (!handler) return;
    ev.preventDefault();
    handler(btn);
  });
})();
