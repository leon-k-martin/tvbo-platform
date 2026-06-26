import { test, expect, Page } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';

/**
 * Documentation screenshots — the single source of truth for every UI image in
 * the tvbo_platform_docs guide (/docs). Each test drives a real platform surface
 * and writes a PNG straight into the docs module's static/img/, so the guide's
 * screenshots regenerate on demand and never go stale:
 *
 *   BASE_URL=http://localhost:8169 npx playwright test docs-screenshots
 *
 * Auth-gated surfaces (My Models, API Keys) need a logged-in fixture user and
 * are intentionally out of scope here — they are documented in prose.
 */
const BASE = process.env.BASE_URL || 'http://localhost:8169';
const OUT = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static', 'img');
const VP = { width: 1440, height: 900 };

test.use({ viewport: VP, deviceScaleFactor: 2 });
test.describe.configure({ mode: 'serial', retries: 2 });

fs.mkdirSync(OUT, { recursive: true });
const shot = (page: Page, name: string) => page.screenshot({ path: path.join(OUT, name) });
const settle = (ms = 1500) => new Promise((r) => setTimeout(r, ms));

test('home', async ({ page }) => {
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  await settle(1200);
  await shot(page, 'home.png');
});

test('login', async ({ page }) => {
  await page.goto(`${BASE}/web/login`, { waitUntil: 'networkidle' });
  await settle(800);
  await shot(page, 'login.png');
});

test('kg-list-view', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/kg`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.result-card', { timeout: 30000 });
  await settle(2000);
  await shot(page, 'kg-list-view.png');
});

test('kg-detail', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/kg`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.result-card', { timeout: 30000 });
  await settle(1500);
  await page.locator('.result-card').first().click();
  await page.waitForSelector('.kg-modal-backdrop, .kg-modal', { timeout: 15000 });
  await settle(2000); // let MathJax/equation render
  await shot(page, 'kg-detail.png');
});

test('kg-graph-view', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/kg#graph`, { waitUntil: 'networkidle' });
  await settle(1200);
  const btn = page.locator('#graphViewBtn');
  if (await btn.count()) await btn.click().catch(() => {});
  await page
    .waitForFunction(() => {
      const svg = document.getElementById('graphSvg');
      return svg && svg.querySelectorAll('circle').length > 3;
    }, { timeout: 30000 })
    .catch(() => {});
  await settle(3500); // force layout settle
  await shot(page, 'kg-graph-view.png');
});

// Experiment Builder — one screenshot per documented tab.
const TABS: [string, string][] = [
  ['#general-panel', 'builder-general.png'],
  ['#dynamics-panel', 'builder-dynamics.png'],
  ['#network-panel', 'builder-network.png'],
  ['#observations-panel', 'builder-observations.png'],
];
for (const [target, file] of TABS) {
  test(`builder ${file}`, async ({ page }) => {
    await page.goto(`${BASE}/tvbo/configurator`, { waitUntil: 'networkidle' });
    await settle(2000);
    if (target !== '#general-panel') {
      await page.locator(`[data-bs-target="${target}"]`).click();
      await settle(1200);
    }
    await shot(page, file);
  });
}
