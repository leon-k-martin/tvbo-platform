import { defineConfig, devices } from '@playwright/test';
import { proxyLaunchOptions } from './proxy';

/**
 * Dedicated config for the cinematic screencast demos (kept separate from the
 * fast functional suite in playwright.config.ts). Videos are recorded manually
 * per-test via the cinematic helper, so `video` here stays off; `slowMo` makes
 * the (already animated) cursor moves read smoothly.
 *
 * Run with:  npx playwright test -c playwright.demo.config.ts
 */

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
    launchOptions: { slowMo: 45, ...proxyLaunchOptions() },
  },
  projects: [{ name: 'demo', use: { ...devices['Desktop Chrome'] } }],
});
