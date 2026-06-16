import { test, expect } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as ci from '../helpers/cinematic';

/**
 * VIDEO 1 — the core workflow, as a continuous narrated screencast with a
 * red-circle cursor and red-square highlights:
 *
 *   browse the Knowledge Graph → SELECT a curated experiment (loads fully)
 *   → change a couple of fields → download the YAML spec.
 *
 * The KG catalog fetch (~4.5s, server-side, uncacheable) is trimmed off the
 * front of the recording so the video starts on the loaded grid. The downloaded
 * YAML is written to demo-output/demo_experiment.yaml for the Python demo.
 */
const OUT = path.resolve(__dirname, '..', 'demo-output');
const VIDEO_DIR = path.join(OUT, 'video-raw');
const BUNDLE_PATH = path.join(OUT, 'demo_bundle.zip');
const freezeRAF = () => {
  (window as any).requestAnimationFrame = () => 0;
  (window as any).cancelAnimationFrame = () => {};
};

test('Workflow demo: pick an experiment in the KG → tweak → download', async ({ browser }) => {
  test.setTimeout(150_000);
  fs.mkdirSync(OUT, { recursive: true });

  const { context, page } = await ci.openCinematicPage(browser, { videoDir: VIDEO_DIR });
  const t0 = Date.now();
  const mark = (s: string) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${s}`);

  // === 1. Knowledge Graph (the slow catalog fetch is trimmed off the front) ==
  await page.goto('/tvbo/kg', { waitUntil: 'domcontentloaded' });
  await ci.ensureCursor(page);
  await page.waitForSelector('#resultsGrid .result-card', { timeout: 30_000 });
  const trimStart = (Date.now() - t0) / 1000; // video begins here, on the loaded grid
  await page.evaluate(freezeRAF).catch(() => {});
  mark('KG ready');
  await ci.caption(page, 'Browse the Knowledge Graph and pick a simulation experiment');
  await page.waitForTimeout(600);

  // === 2. Select an EXPERIMENT (loads the full, populated experiment) ========
  // A bifurcation experiment is single-node, so the downloaded spec also runs
  // standalone in the Python demo (no external connectome data needed).
  await ci.type(page, '#kgHeroSearchInput', 'Peak Frequency', { caption: 'Search for an experiment' });
  await page.waitForTimeout(1200);
  await page.evaluate(freezeRAF).catch(() => {});
  const expLink = page.locator('#resultsGrid a.kg-open-builder[href*="experiment="]').first();
  await expLink.waitFor({ state: 'visible', timeout: 8000 });
  const href = await expLink.getAttribute('href');
  await ci.highlight(page, expLink, 1200);
  await ci.caption(page, 'Open it in the Experiment Builder');
  await page.waitForTimeout(900);
  await page.goto(href!, { waitUntil: 'domcontentloaded' });
  mark('goto done');

  // === 3. Builder loads the full experiment ==================================
  await ci.ensureCursor(page);
  await page.waitForSelector('#experimentLabel', { state: 'visible', timeout: 20_000 });
  mark('#experimentLabel visible');
  await page.evaluate(freezeRAF).catch(() => {}); // freeze the 3D loop ASAP
  await page.waitForTimeout(2800); // hydrate: fields + live YAML populate from the experiment
  mark('experiment loaded');
  await ci.caption(page, 'The full experiment loads — dynamics, an 84-node connectome, observations & algorithms');
  await page.waitForTimeout(900);

  // === 4. Change a couple of fields (one tab — no jumping) ===================
  await ci.click(page, '#general-tab', { caption: 'Adjust a few fields' });
  await ci.type(page, '#experimentLabel', 'JR peak frequency — my run', { caption: 'Edit the label' });
  await ci.type(page, '#experimentDescription', 'Customized Jansen-Rit peak-frequency experiment from the knowledge graph.', {
    caption: 'Edit the description',
  });
  mark('fields changed');
  await ci.caption(page, 'The live YAML preview updates and validates as you edit');
  await page.waitForTimeout(1400);

  // === 5. Download a self-contained bundle (monolithic YAML + connectome HDF5) =
  const downloadPromise = page.waitForEvent('download', { timeout: 30_000 });
  await ci.click(page, '#builderDownloadYaml', { caption: 'Download: one YAML + the connectome as HDF5' });
  const download = await downloadPromise;
  await download.saveAs(BUNDLE_PATH);
  mark('downloaded');
  await ci.caption(page, 'Downloaded a self-contained bundle — experiment.yaml + connectome.h5');
  await page.waitForTimeout(2000);

  const videoPath = await ci.finish(context, page, path.join(OUT, 'tvbo-experiment-builder-workflow.mp4'), trimStart);
  mark('done -> ' + videoPath + ' (trimmed ' + trimStart.toFixed(1) + 's)');
  expect(fs.existsSync(BUNDLE_PATH), 'downloaded bundle exists').toBeTruthy();
});
