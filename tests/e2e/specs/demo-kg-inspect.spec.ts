import { test } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as ci from '../helpers/cinematic';

/**
 * Cinematic demo: FIND AND INSPECT A MODEL in the Knowledge Graph.
 *
 * This is the video the knowledge-graph guide ("## Watch: find and inspect a
 * model") actually needs — it was previously pointed at the *specify-and-run*
 * screencast, which is a different step. Records a real browse → search →
 * inspect flow against the live KG (now populated; it used to show only the
 * ontology). Writes the mp4 straight into the docs module's static/video.
 *
 *   BASE_URL=http://localhost:8169 npx playwright test -c playwright.demo.config.ts demo-kg-inspect
 */
const STATIC = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static');
const VIDEO_DIR = path.resolve(__dirname, '..', 'demo-output', 'video-raw-kg');
const DEST = path.join(STATIC, 'video', 'tvbo-find-and-inspect-a-model.mp4');

test('KG demo: find and inspect a model', async ({ browser }) => {
  test.setTimeout(180_000);
  fs.mkdirSync(VIDEO_DIR, { recursive: true });

  const { context, page } = await ci.openCinematicPage(browser, { videoDir: VIDEO_DIR });
  await page.goto('/tvbo/kg', { waitUntil: 'networkidle' });
  await ci.ensureCursor(page);
  await page.waitForSelector('.result-card', { timeout: 30_000 });
  await page.waitForTimeout(900);

  await ci.caption(page, 'The Knowledge Graph — every curated model, network and study in one searchable place');
  await page.waitForTimeout(2000);

  // 1 — search for a model
  await ci.type(page, '#kgHeroSearchInput', 'Jansen', { caption: 'Search for a model — e.g. Jansen-Rit' });
  await page.waitForTimeout(1600);
  // Robust against the live-filter behaviour: if the search matched nothing,
  // clear it so there is always a card to open.
  if ((await page.locator('.result-card').count()) === 0) {
    await page.locator('#kgHeroSearchInput')
      .evaluate((e: any) => { e.value = ''; e.dispatchEvent(new Event('input', { bubbles: true })); })
      .catch(() => {});
    await page.waitForSelector('.result-card', { timeout: 10_000 });
  }

  const card = page.locator('.result-card').first();
  await ci.highlight(page, card, 1300);
  await page.waitForTimeout(900);

  // 2 — open it to inspect
  await ci.click(page, '.result-card', { caption: 'Open it to inspect the model' });
  await page.waitForSelector('.kg-modal-backdrop, .kg-modal', { timeout: 15_000 });
  await page.waitForTimeout(2400); // MathJax / equations render

  await ci.caption(page, 'Its state variables, equations and parameters — the complete specification');
  await page.waitForTimeout(2600);
  await ci.scrollBy(page, 380);
  await page.waitForTimeout(1800);

  await ci.caption(page, 'Load it straight into Python, or open it in the Experiment Builder');
  await page.waitForTimeout(2400);

  const out = await ci.finish(context, page, DEST);
  // eslint-disable-next-line no-console
  console.log('video -> ' + out);
});
