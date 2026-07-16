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
const ADMIN = process.env.TVBO_ADMIN_LOGIN || 'admin';
const ADMIN_PASS = process.env.TVBO_ADMIN_PASSWORD || 'admin';
const EXP = process.env.DOCS_EXPERIMENT_ID || '2'; // a populated example experiment
const OUT = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static', 'img');

test.use({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
test.describe.configure({ retries: 2 });

fs.mkdirSync(OUT, { recursive: true });
const shot = (page: Page, name: string) => page.screenshot({ path: path.join(OUT, name) });
const settle = (ms = 1500) => new Promise((r) => setTimeout(r, ms));

// Warm the Odoo server (QWeb template + asset-bundle compilation is the dominant
// cold-load cost and is shared server-side) so the first screenshot is not taken
// against a still-compiling page.
test.beforeAll(async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  for (const url of ['/', '/tvbo/agents', '/tvbo/kg', `/tvbo/configurator?experiment=${EXP}`, '/web/login', '/my/models', '/my/api-keys']) {
    await page.goto(`${BASE}${url}`, { waitUntil: 'load', timeout: 60000 }).catch(() => {});
    await settle(300);
  }
  await ctx.close();
});

/**
 * Draw numbered callouts on the page before a screenshot. `marks` pairs a CSS
 * selector with the number shown in the doc text, so annotated screenshots stay
 * in sync with the steps that reference them. Missing/zero-size targets are
 * skipped, so a renamed selector degrades to a plain (un-annotated) box.
 */
async function annotate(page: Page, marks: { selector: string; n: number }[]) {
  await page.evaluate((items) => {
    const layer = document.createElement('div');
    layer.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none;';
    document.body.appendChild(layer);
    for (const m of items) {
      const el = document.querySelector(m.selector) as HTMLElement | null;
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const box = document.createElement('div');
      box.style.cssText =
        `position:absolute;left:${Math.max(2, r.left - 5)}px;top:${Math.max(2, r.top - 5)}px;` +
        `width:${r.width + 8}px;height:${r.height + 8}px;border:3px solid #e11d48;border-radius:8px;`;
      layer.appendChild(box);
      const badge = document.createElement('div');
      badge.textContent = String(m.n);
      badge.style.cssText =
        `position:absolute;left:${Math.max(6, r.left - 13)}px;top:${Math.max(6, r.top - 13)}px;` +
        'width:26px;height:26px;background:#e11d48;color:#fff;border-radius:50%;display:flex;' +
        'align-items:center;justify-content:center;font:700 15px -apple-system,sans-serif;' +
        'box-shadow:0 1px 4px rgba(0,0,0,.5);';
      layer.appendChild(badge);
    }
  }, marks);
}

async function signIn(page: Page, user = USER, pass = PASS): Promise<boolean> {
  const res = await page.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db: DB, login: user, password: pass } },
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

test('register', async ({ page }) => {
  await page.goto(`${BASE}/web/signup`, { waitUntil: 'networkidle' });
  await settle(800);
  await shot(page, 'register.png');
});

test('agents', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/agents`, { waitUntil: 'networkidle' });
  await settle(1200);
  await shot(page, 'agents.png');
});

test('kg-list-view', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/kg`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.result-card', { timeout: 30000 });
  await settle(2000);
  // Callouts keyed to the numbered list in knowledge-graph/list-view.md.
  await annotate(page, [
    { selector: '#kgHeroSearchInput', n: 1 }, // search
    { selector: '.facet-title', n: 2 },       // Class filter
    { selector: '#graphViewBtn', n: 3 },      // view toggle
    { selector: '.result-card', n: 4 },       // a result card
  ]);
  await shot(page, 'kg-list-view.png');
});

test('kg-detail', async ({ page }) => {
  await page.goto(`${BASE}/tvbo/kg`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.result-card', { timeout: 30000 });
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
  ['#run-panel', 'builder-run.png'],
];
for (const [target, file] of TABS) {
  test(`builder ${file}`, async ({ page }) => {
    await page.goto(`${BASE}/tvbo/configurator?experiment=${EXP}`, { waitUntil: 'networkidle' });
    await settle(3000); // let the experiment prefill all tabs
    if (target !== '#general-panel') {
      await page.locator(`[data-bs-target="${target}"]`).click();
      await settle(1500);
      if (target === '#run-panel') {
        // Callouts keyed to experiment-builder/export.md (Run on the platform).
        await annotate(page, [
          { selector: '#runDuration', n: 1 },      // settings
          { selector: '#runSimulationBtn', n: 2 }, // Run Simulation
        ]);
      }
    } else {
      // Callouts keyed to experiment-builder/building.md.
      await annotate(page, [
        { selector: '.nav-tabs', n: 1 },           // tab row
        { selector: '#builderDownloadYaml', n: 2 }, // Download
        { selector: '#builderCopyPython', n: 3 },   // Copy Python
      ]);
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
    // Callouts keyed to account/save-to-account.md and account/publishing.md.
    await annotate(page, [
      { selector: '.tvbo-model-card', n: 1 },        // a saved model
      { selector: '[data-action="share"]', n: 2 },   // Share with a colleague (p2p)
      { selector: '[data-action="submit"]', n: 3 },  // Submit for review (publish)
    ]);
    await shot(page, 'my-models.png');
  });

  test('shared-with-me', async ({ page }) => {
    test.skip(!(await signIn(page)), 'fixture sign-in unavailable');
    await page.goto(`${BASE}/my/shared`, { waitUntil: 'networkidle' });
    await settle(1200);
    await shot(page, 'shared-with-me.png');
  });

  test('api-keys', async ({ page }) => {
    test.skip(!(await signIn(page)), 'fixture sign-in unavailable');
    await page.goto(`${BASE}/my/api-keys`, { waitUntil: 'networkidle' });
    await settle(1500);
    await annotate(page, [
      { selector: '#apiKeyName', n: 1 },   // name the key
      { selector: '#apiKeyCreate', n: 2 }, // Create key
    ]);
    await shot(page, 'api-keys.png');
  });
});

// Reviewer backend — the peer-review queue (account/reviewing.md, staff only).
// Needs an internal/admin user; skips cleanly if that sign-in is unavailable.
test.describe('reviewer', () => {
  test('publications-queue', async ({ page }) => {
    test.skip(!(await signIn(page, ADMIN, ADMIN_PASS)), 'admin sign-in unavailable');
    // Odoo 19 web-client URL for an action by its XML id. The web client keeps a
    // persistent bus/longpoll connection open, so 'networkidle' never fires —
    // wait for the DOM, then for the list/content to actually render.
    await page.goto(`${BASE}/odoo/action-tvbo.action_publication_review`, {
      waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('.o_list_view, .o_content', { timeout: 30000 }).catch(() => {});
    await settle(2000);
    await shot(page, 'publications-queue.png');
  });
});
