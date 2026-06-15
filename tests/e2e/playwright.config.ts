import { defineConfig, devices } from '@playwright/test';

// The builder runs in the local docker dev stack (`make dev-up`).
// Override with TVBO_BASE_URL when pointing at another instance.
const BASE_URL = process.env.TVBO_BASE_URL || 'http://localhost:8169';

export default defineConfig({
  testDir: './specs',
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
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
