import { test, Page, BrowserContext } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';

/**
 * Documentation screencasts — records real walkthroughs of the platform with a
 * visible cursor and deliberate pacing, then saves a raw webm per cast into
 * tests/e2e/screencast-raw/. Turn them into web videos + posters with:
 *
 *   BASE_URL=http://localhost:8169 npx playwright test docs-screencasts
 *   tests/e2e/process-docs-videos.sh        # → static/video/*.mp4 + posters
 *
 * The account cast signs in with the same fixture as docs-screenshots
 * (DOCS_USER / DOCS_PASS); it is skipped if that sign-in fails.
 */
const BASE = process.env.BASE_URL || 'http://localhost:8169';
const DB = process.env.DOCS_DB || 'tvbo_dev';
const USER = process.env.DOCS_USER || 'docs-demo';
const PASS = process.env.DOCS_PASS || 'DocsDemo-2026';
const EXP = process.env.DOCS_EXPERIMENT_ID || '2';
const RAW = path.resolve(__dirname, '..', 'screencast-raw');
const SIZE = { width: 1280, height: 720 };
fs.mkdirSync(RAW, { recursive: true });

test.describe.configure({ retries: 1 });

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Injected into every page in the context: a cursor that glides (CSS transition)
// to wherever __moveCur is told, so the recording shows each action's location.
const CURSOR_INIT = () => {
  const add = () => {
    if (document.getElementById('__cur')) return;
    // These casts are footage of the app, not of the site around it. Switching to a
    // shorter panel leaves the old scroll behind and flashes the site footer for a
    // frame or two; taking it out of the layout removes the flash at the source.
    const hide = document.createElement('style');
    hide.textContent = 'footer{display:none!important}';
    (document.head || document.documentElement).appendChild(hide);
    const c = document.createElement('div');
    c.id = '__cur';
    c.style.cssText =
      'position:fixed;z-index:2147483647;left:640px;top:360px;width:24px;height:24px;' +
      'margin:-3px 0 0 -3px;pointer-events:none;transition:left .55s ease,top .55s ease;' +
      'filter:drop-shadow(0 1px 2px rgba(0,0,0,.55));';
    c.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M3 2 L3 19 L8 14 L11 21 ' +
      'L14 20 L11 13 L18 13 Z" fill="#111" stroke="#fff" stroke-width="1.4"/></svg>';
    (document.body || document.documentElement).appendChild(c);
  };
  (window as unknown as { __moveCur: (x: number, y: number) => void }).__moveCur = (x, y) => {
    const e = document.getElementById('__cur');
    if (e) { e.style.left = x + 'px'; e.style.top = y + 'px'; }
  };
  if (document.readyState !== 'loading') add();
  else document.addEventListener('DOMContentLoaded', add);
  new MutationObserver(() => { if (!document.getElementById('__cur')) add(); })
    .observe(document.documentElement, { childList: true });
};

class Cast {
  constructor(public page: Page) {}
  // Every locator action gets a short timeout so a missing/blocked target fails
  // fast and the cast continues, instead of auto-waiting to the 90s test timeout.
  // Waits for the target to exist first: click/type/pick drive the DOM directly, and
  // a querySelector miss is a silent no-op that records a cast where nothing happens.
  async to(sel: string) {
    await this.page.waitForSelector(sel, { timeout: 15000 }).catch(() => {});
    const el = this.page.locator(sel).first();
    await el.scrollIntoViewIfNeeded({ timeout: 1500 }).catch(() => {});
    const box = await el.boundingBox({ timeout: 1500 }).catch(() => null);
    if (!box) return;
    await this.page.evaluate(
      ([x, y]) => (window as unknown as { __moveCur?: (x: number, y: number) => void }).__moveCur?.(x, y),
      [box.x + box.width / 2, box.y + box.height / 2],
    );
    await sleep(700);
  }
  // The builder's panels keep Playwright's actionability checks from ever passing
  // (bootstrap btn-check labels, a canvas that never settles), so locator.click()
  // and .fill() just burn their timeouts and record a cast where nothing happens.
  // Drive the DOM directly instead — the cursor above still shows where it lands.
  async click(sel: string, dwell = 800) {
    await this.to(sel);
    await this.page.evaluate((s) => (document.querySelector(s) as HTMLElement | null)?.click(), sel);
    await sleep(dwell);
  }
  // Focus via the DOM, then send real key events: keeps the visible typewriter
  // effect without going through element actionability.
  async type(sel: string, text: string, dwell = 900) {
    await this.to(sel);
    await this.page.evaluate((s) => {
      const el = document.querySelector(s) as HTMLInputElement | null;
      if (!el) return;
      el.focus();
      el.value = '';
    }, sel);
    await this.page.keyboard.type(text, { delay: 70 });
    await this.page.evaluate((s) => document.querySelector(s)
      ?.dispatchEvent(new Event('change', { bubbles: true })), sel);
    await sleep(dwell);
  }
  // Picks the option whose visible text matches, so the cast is not tied to
  // database ids that shift between refreshes of the knowledge base.
  async pick(sel: string, label: RegExp, dwell = 1200) {
    await this.to(sel);
    const value = await this.page.evaluate(
      ([s, src, flags]) => [...((document.querySelector(s) as HTMLSelectElement | null)?.options || [])]
        .find((o) => new RegExp(src, flags).test(o.text.trim()))?.value,
      [sel, label.source, label.flags] as [string, string, string],
    );
    if (value !== undefined) {
      await this.page.evaluate(([s, v]) => {
        const el = document.querySelector(s) as HTMLSelectElement | null;
        if (!el) return;
        el.value = v;
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }, [sel, value] as [string, string]);
    }
    await sleep(dwell);
  }
}

// Pages the casts record. Warming them once compiles the QWeb templates and
// frontend asset bundles server-side (the dominant cold-load cost in Odoo, and
// shared across browser contexts), so the in-recording navigation is fast and
// the video does not open on a long white cold-load.
const WARM_URLS = [
  `${BASE}/tvbo/kg`,
  `${BASE}/tvbo/configurator?experiment=${EXP}`,
  `${BASE}/web/login`,
  `${BASE}/my/models`,
  `${BASE}/my/api-keys`,
];

test.beforeAll(async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: SIZE });
  const page = await ctx.newPage();
  for (const url of WARM_URLS) {
    await page.goto(url, { waitUntil: 'load', timeout: 60000 }).catch(() => {});
    await sleep(400); // let deferred assets / JS finish compiling server-side
  }
  await ctx.close();
});

async function record(browser, name: string, steps: (c: Cast) => Promise<void>) {
  const ctx: BrowserContext = await browser.newContext({
    viewport: SIZE,
    recordVideo: { dir: RAW, size: SIZE },
  });
  await ctx.addInitScript(CURSOR_INIT);
  const page = await ctx.newPage();
  await steps(new Cast(page));
  const video = page.video();
  await ctx.close();
  if (video) fs.renameSync(await video.path(), path.join(RAW, `${name}.webm`));
}

test('cast: knowledge-graph tour', async ({ browser }) => {
  await record(browser, 'tvbo-knowledge-graph-tour', async (c) => {
    // The graph view IS the tour — deep-link straight to it (#graph is handled by
    // initViewFromHash). Previously this ended on the card list because the toggle
    // click was best-effort and barely dwelt.
    await c.page.goto(`${BASE}/tvbo/kg#graph`, { waitUntil: 'load', timeout: 30000 });
    // Fallback: if the hash did not activate the graph, use the toggle.
    const graphOn = await c.page.locator('#graphContainer:not(.hidden)')
      .first().waitFor({ state: 'visible', timeout: 8000 }).then(() => true).catch(() => false);
    if (!graphOn) await c.click('#graphViewBtn');
    // Wait for the force-directed layout to actually draw nodes before dwelling.
    await c.page.waitForSelector('#graphSvg circle', { timeout: 30000 }).catch(() => {});
    await sleep(4200);                        // let the layout settle — the payoff shot
    // Search narrows the graph live — show it responding.
    await c.type('#kgHeroSearchInput', 'Kuramoto');
    await sleep(3400);
  });
});

test('cast: build an experiment', async ({ browser }) => {
  // Heaviest cast by far: video capture plus the builder's WebGL scene starves the
  // page's main thread, so each step lands far slower than it plays back. The dead
  // time is cut out afterwards by process-docs-videos.sh.
  test.setTimeout(600_000);
  //
  // Starts from an EMPTY builder and actually fills it in. Deep-linking a saved
  // experiment (?experiment=N) made a cast of four tab clicks over a form that
  // was already complete — 83s in which nothing visibly happened.
  await record(browser, 'tvbo-build-an-experiment', async (c) => {
    // domcontentloaded, not load: the builder pulls the whole model catalogue and a
    // three.js scene, so waiting for `load` idles the cast for ~30s on a ready page.
    await c.page.goto(`${BASE}/tvbo/configurator`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await c.page.waitForSelector('#experimentName', { timeout: 25000 }).catch(() => {});
    await sleep(1200);

    await c.type('#experimentName', 'Resting-state alpha', 400);
    await c.type('#experimentLabel', 'alpha-84', 700);

    await c.click('[data-bs-target="#dynamics-panel"]', 500);
    await c.click('#addDynamicsModel', 600);
    await c.page.waitForSelector('#editorBaseModel', { state: 'visible', timeout: 10000 }).catch(() => {});
    await c.pick('#editorBaseModel', /^JansenRit$/, 1800);

    await c.click('[data-bs-target="#network-panel"]', 500);
    await c.type('#customNetworkLabel', 'Desikan-Killiany', 300);
    await c.type('#customGlobalCoupling', '0.05', 300);
    await c.type('#randomNodeCount', '84', 300);
    await c.click('#generateRandomNetwork', 2600);   // the 3D panel draws the network

    await c.click('[data-bs-target="#integration-panel"]', 500);
    await c.pick('#integratorMethod', /^Heun$/, 600);
    await c.type('#integratorDuration', '2000', 800);

    // The payoff: the whole thing as one schema-valid specification.
    await c.click('[data-bs-target="#preview-panel"]', 2800);
  });
});

test('cast: your account', async ({ browser }) => {
  // Sign in via the form so the cast shows the real login, then visit the
  // account pages. Skips if the fixture is unavailable.
  const probe = await browser.newContext();
  const ok = await probe.request
    .post(`${BASE}/web/session/authenticate`, {
      data: { jsonrpc: '2.0', method: 'call', params: { db: DB, login: USER, password: PASS } },
    })
    .then((r) => r.json())
    .then((b) => !!b?.result?.uid)
    .catch(() => false);
  await probe.close();
  test.skip(!ok, 'fixture sign-in unavailable');

  await record(browser, 'tvbo-account-tour', async (c) => {
    await c.page.goto(`${BASE}/web/login`, { waitUntil: 'load', timeout: 30000 });
    await sleep(1200);
    await c.type('input[name="login"]', USER);
    await c.type('input[name="password"]', PASS);
    await c.click('button[type="submit"]');
    await c.page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
    await sleep(1600);
    await c.page.goto(`${BASE}/my/models`, { waitUntil: 'load', timeout: 30000 });
    await sleep(2600);
    await c.to('.tvbo-model-card');
    await sleep(1500);
    await c.page.goto(`${BASE}/my/api-keys`, { waitUntil: 'load', timeout: 30000 });
    await sleep(2400);
  });
});
