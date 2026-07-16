import { defineConfig, devices } from '@playwright/test';

// The builder runs in the local docker dev stack (`make dev-up`).
// Override with TVBO_BASE_URL when pointing at another instance.
const BASE_URL = process.env.TVBO_BASE_URL || 'http://localhost:8169';

// On the Charité LAN the CDN assets the platform loads client-side (Font Awesome,
// D3, three.js, MathJax, marked, Google Fonts) are only reachable through the
// corporate proxy. Route the browser through it — set at launch level so every
// context (including the ones the docs specs create by hand) inherits it — and
// always bypass the local Odoo dev stack. Picked up automatically from the
// standard proxy env vars (.bashrc exports them on Ethernet); a no-op off-LAN.
// Override or disable with TVBO_PROXY (empty string forces direct).
const PROXY =
  process.env.TVBO_PROXY ??
  process.env.HTTPS_PROXY ??
  process.env.https_proxy ??
  '';
const launchOptions = PROXY
  ? { proxy: { server: PROXY, bypass: 'localhost,127.0.0.1,::1' } }
  : undefined;

export default defineConfig({
  testDir: './specs',
  // Seed the docs fixture user + a sample saved model so the account-page
  // screenshots/screencasts run for real instead of skipping. No-ops gracefully
  // when the docker dev stack is not reachable.
  globalSetup: './global-setup.ts',
  // Experiment serialization and the docker-backed builder can be slow on a
  // cold stack; give each test generous headroom.
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    ...(launchOptions ? { launchOptions } : {}),
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
