import { defineConfig, devices } from '@playwright/test';

/**
 * Dedicated config for the cinematic screencast demos (kept separate from the
 * fast functional suite in playwright.config.ts). Videos are recorded manually
 * per-test via the cinematic helper, so `video` here stays off; `slowMo` makes
 * the (already animated) cursor moves read smoothly.
 *
 * Run with:  npx playwright test -c playwright.demo.config.ts
 */

// Route the browser through the Charité proxy on the LAN so client-side CDN
// assets (Font Awesome, D3, three.js, MathJax, marked, Google Fonts) load and
// the demos don't record empty graphs / missing icons. Bypasses the local Odoo
// dev stack. Picked up from the standard proxy env vars; a no-op off-LAN.
// Override or disable with TVBO_PROXY (empty string forces direct). Mirrors
// playwright.config.ts.
const PROXY =
  process.env.TVBO_PROXY ??
  process.env.HTTPS_PROXY ??
  process.env.https_proxy ??
  '';
const proxyOpt = PROXY ? { proxy: { server: PROXY, bypass: 'localhost,127.0.0.1,::1' } } : {};
export default defineConfig({
  testDir: './specs',
  testMatch: /demo-.*\.spec\.ts/,
  timeout: 360_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.TVBO_BASE_URL || 'http://localhost:8169',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    actionTimeout: 20_000,
    navigationTimeout: 40_000,
    launchOptions: { slowMo: 45, ...proxyOpt },
  },
  projects: [{ name: 'demo', use: { ...devices['Desktop Chrome'] } }],
});
