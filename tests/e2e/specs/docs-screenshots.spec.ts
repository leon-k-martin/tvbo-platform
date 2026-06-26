import { test, Page } from '@playwright/test';
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
 * Account-page shots (My Models, API Keys) sign in as a fixture user via
 * /web/session/authenticate. Seed it once against the target DB:
 *   user  DOCS_USER (default docs-demo) / DOCS_PASS (default DocsDemo-2026)
 *   plus one tvbo.model_share owned by that user so My Models is not empty.
 * They are skipped automatically if the sign-in fails.
 */
const BASE = process.env.BASE_URL || 'http://localhost:8169';
const DB = process.env.DOCS_DB || 'tvbo_dev';
const USER = process.env.DOCS_USER || 'docs-demo';
const PASS = process.env.DOCS_PASS || 'DocsDemo-2026';
const EXP = process.env.DOCS_EXPERIMENT_ID || '2'; // a populated example experiment
const OUT = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static', 'img');

test.use({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
test.describe.configure({ retries: 2 });

fs.mkdirSync(OUT, { recursive: true });
const shot = (page: Page, name: string) => page.screenshot({ path: path.join(OUT, name) });
const settle = (ms = 1500) => new Promise((r) => setTimeout(r, ms));

async function signIn(page: Page): Promise<boolean> {
  const res = await page.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db: DB, login: USER, password: PASS } },
  });
  const body = await res.json().catch(() => ({}));
  return !!body?.result?.uid;
}

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
  // Search a well-documented model so the detail card is rich (full parameters).
  await page.goto(`${BASE}/tvbo/kg`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.result-card', { timeout: 30000 });
  const search = page.locator('#kgSearchInput, #o_kg_search, input[type="search"]').first();
  await search.fill('Generic2dOscillator').catch(() => {});
  await settle(1800);
  await page.locator('.result-card').first().click();
  await page.waitForSelector('.kg-modal-backdrop, .kg-modal', { timeout: 15000 });
  await settle(2000); // MathJax / equation render
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

// Experiment Builder — one shot per documented tab, with a populated example
// loaded so the tabs show real content (a model, a connectome, observations).
const TABS: [string, string][] = [
  ['#general-panel', 'builder-general.png'],
  ['#dynamics-panel', 'builder-dynamics.png'],
  ['#network-panel', 'builder-network.png'],
  ['#observations-panel', 'builder-observations.png'],
];
for (const [target, file] of TABS) {
  test(`builder ${file}`, async ({ page }) => {
    await page.goto(`${BASE}/tvbo/configurator?experiment=${EXP}`, { waitUntil: 'networkidle' });
    await settle(3000); // let the experiment prefill all tabs
    if (target !== '#general-panel') {
      await page.locator(`[data-bs-target="${target}"]`).click();
      await settle(1500);
    }
    await shot(page, file);
  });
}

// Account pages — require a signed-in fixture user; skip cleanly if unavailable.
test.describe('account', () => {
  test('my-models', async ({ page }) => {
    test.skip(!(await signIn(page)), 'fixture sign-in unavailable');
    await page.goto(`${BASE}/my/models`, { waitUntil: 'networkidle' });
    await settle(1500);
    await shot(page, 'my-models.png');
  });

  test('api-keys', async ({ page }) => {
    test.skip(!(await signIn(page)), 'fixture sign-in unavailable');
    await page.goto(`${BASE}/my/api-keys`, { waitUntil: 'networkidle' });
    await settle(1500);
    await shot(page, 'api-keys.png');
  });
});
