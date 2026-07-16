// Shared proxy resolution for the Playwright configs. On the Charité LAN the CDN
// assets the platform loads client-side (Font Awesome, D3, three.js, MathJax,
// marked, Google Fonts) are only reachable through the corporate proxy; route the
// browser through it (at launch level, so hand-made contexts inherit it) while
// bypassing the local Odoo dev stack. Picked up automatically from the standard
// proxy env vars (.bashrc exports them on Ethernet); a no-op off-LAN.
// Override or disable with TVBO_PROXY (empty string forces a direct connection).
export function proxyLaunchOptions() {
  const proxy =
    process.env.TVBO_PROXY ?? process.env.HTTPS_PROXY ?? process.env.https_proxy ?? '';
  return proxy ? { proxy: { server: proxy, bypass: 'localhost,127.0.0.1,::1' } } : {};
}
