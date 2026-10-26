/**
 * Portal dashboard: Customize lets the user move, remove and add widgets. Each change is saved to /my/dashboard/widgets straight away; adding, removing or resetting reloads the page so the server renders the new set, still in Customize mode.
 */
(function () {
  'use strict';

  const root = document.querySelector('.o_tvbo_dashboard');
  if (!root) return;
  const grid = root.querySelector('.o_tvbo_widgets');
  const toggle = root.querySelector('[data-dashboard-customize]');

  async function save(keys) {
    const resp = await fetch('/my/dashboard/widgets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { keys: keys } }),
    });
    return (await resp.json()).result;
  }

  function shownKeys() {
    return Array.from(grid.querySelectorAll('.o_tvbo_widget'), (widget) => widget.dataset.key);
  }

  async function saveAndReload(keys) {
    await save(keys);
    window.location.hash = 'customize';
    window.location.reload();
  }

  function setCustomizing(on) {
    root.classList.toggle('is-customizing', on);
    toggle.textContent = on ? 'Done' : 'Customize';
    toggle.setAttribute('aria-pressed', on);
    history.replaceState(null, '', on ? '#customize' : window.location.pathname);
  }

  toggle.addEventListener('click', () => setCustomizing(!root.classList.contains('is-customizing')));
  if (window.location.hash === '#customize') setCustomizing(true);

  root.addEventListener('click', async (ev) => {
    const button = ev.target.closest('button');
    if (!button) return;
    const widget = button.closest('.o_tvbo_widget');
    if (button.dataset.move) {
      const sibling = button.dataset.move === '-1' ? widget.previousElementSibling : widget.nextElementSibling;
      if (!sibling) return;
      if (button.dataset.move === '-1') sibling.before(widget);
      else sibling.after(widget);
      button.focus();
      await save(shownKeys());
    } else if ('remove' in button.dataset) {
      await saveAndReload(shownKeys().filter((key) => key !== widget.dataset.key));
    } else if (button.dataset.add) {
      await saveAndReload(shownKeys().concat(button.dataset.add));
    } else if ('reset' in button.dataset) {
      await saveAndReload(null);
    }
  });
})();
