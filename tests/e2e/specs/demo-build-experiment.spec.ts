import { test } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as ci from '../helpers/cinematic';

/**
 * Cinematic demo: BUILD AN EXPERIMENT in the Experiment Builder, tab by tab.
 *
 * Completes the docs narrative between "find & inspect a model" (KG) and
 * "run in Python": it shows assembling a full SimulationExperiment — dynamics,
 * network, observations, run settings — then exporting it. Drives the real
 * builder against a prefilled example; writes the mp4 into the docs static/video.
 *
 *   BASE_URL=http://localhost:8169 npx playwright test -c playwright.demo.config.ts demo-build-experiment
 */
const STATIC = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static');
const VIDEO_DIR = path.resolve(__dirname, '..', 'demo-output', 'video-raw-build');
const DEST = path.join(STATIC, 'video', 'tvbo-build-an-experiment.mp4');
const EXP = process.env.DOCS_EXPERIMENT_ID || '2';

test('Builder demo: build an experiment tab by tab', async ({ browser }) => {
  test.setTimeout(240_000);
  fs.mkdirSync(VIDEO_DIR, { recursive: true });

  const { context, page } = await ci.openCinematicPage(browser, { videoDir: VIDEO_DIR });
  await page.goto(`/tvbo/configurator?experiment=${EXP}`, { waitUntil: 'networkidle' });
  await ci.ensureCursor(page);
  await page.waitForSelector('.nav-tabs', { timeout: 40_000 });
  await page.waitForTimeout(3000); // let the example prefill every tab

  await ci.caption(page, 'The Experiment Builder — assemble a whole simulation, tab by tab');
  await ci.highlight(page, page.locator('.nav-tabs'), 2400);
  await page.waitForTimeout(2400);

  // Click the tab WITHOUT a caption, wait for its panel to actually render (the
  // builder re-renders slowly + rebuilds the 3D graph), THEN caption — so the
  // narration never races ahead of the panel it describes.
  const tab = async (target: string, cap: string) => {
    await ci.click(page, `[data-bs-target="${target}"]`);
    await page.locator(target).waitFor({ state: 'visible', timeout: 30_000 }).catch(() => {});
    await page.waitForTimeout(1800); // let the panel content / 3D settle
    await ci.caption(page, cap);
    await page.waitForTimeout(2600);
  };
  await tab('#dynamics-panel', 'Dynamics — the local neural-mass model and its parameters');
  await tab('#network-panel', 'Network — the connectome the model runs on');
  await tab('#observations-panel', 'Observations — what to record (BOLD, EEG, …)');
  await tab('#run-panel', 'Run — integration settings, then simulate');
  await page.waitForTimeout(1600);

  // Back to General to show the export affordances.
  await ci.click(page, '[data-bs-target="#general-panel"]', { caption: 'Export it — download the YAML or copy the Python' });
  await page.waitForTimeout(1600);
  const dl = page.locator('#builderDownloadYaml');
  if (await dl.count()) await ci.highlight(page, dl, 2600);
  await page.waitForTimeout(2600);

  const out = await ci.finish(context, page, DEST);
  // eslint-disable-next-line no-console
  console.log('video -> ' + out);
});
