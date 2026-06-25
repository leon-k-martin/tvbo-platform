import { test, expect, APIRequestContext } from '@playwright/test';
import { validateYaml, summarize } from '../helpers/validate';

// Dedicated coverage for the three experiment-builder user flows:
//   1. Load an example experiment  -> re-serialized YAML is tvbo-valid and
//      reproduces the example's content (round-trip identity).
//   2. Build an experiment fully by hand, with MULTIPLE entries per section
//      -> the assembled YAML is tvbo-valid (readable/runnable by tvbo).
//   3. Pick a single building block from the Knowledge Graph into the
//      workspace, refine it, and have the refinement land in the experiment.
const CONFIGURATOR = '/tvbo/configurator';

async function getJson(request: APIRequestContext, url: string) {
  const r = await request.get(url);
  expect(r.ok(), `${url} HTTP ${r.status()}`).toBeTruthy();
  return r.json();
}

/** Wait until the builder has hydrated an assembled spec carrying dynamics. */
async function waitForAssembled(page: any) {
  await expect(page.locator('#dynamicsModelsList .card')).not.toHaveCount(0, { timeout: 60_000 });
  await expect
    .poll(async () => page.evaluate(() => {
      try { return !!(window.assembleExperimentSpec() as any).dynamics; } catch { return false; }
    }), { timeout: 60_000 })
    .toBeTruthy();
}

test.describe('Experiment builder — the three core flows', () => {
  // -------------------------------------------------------------------- //
  // Flow 1: select an example experiment -> identical, valid YAML
  // -------------------------------------------------------------------- //
  test('Flow 1: loading an example experiment round-trips to identical, valid YAML', async ({ page, request }) => {
    test.setTimeout(150_000);

    // Pick a seeded experiment that actually carries a dynamics model and at
    // least one observation, straight from the API the builder loads from.
    const list = (await getJson(request, '/tvbo/api/configurator/experiments')).data || [];
    expect(list.length, 'seeded experiments present').toBeGreaterThan(0);
    let targetId: number | null = null;
    let det: any = null;
    for (const e of list) {
      const d = (await getJson(request, `/tvbo/api/configurator/experiment/${e.id}`)).data;
      const dyn = Array.isArray(d?.dynamics) ? d.dynamics[0] : d?.dynamics;
      const obs = Array.isArray(d?.observations) ? d.observations : (d?.observations ? [d.observations] : []);
      if (dyn?.name && obs.length) { targetId = e.id; det = d; break; }
    }
    expect(targetId, 'a seeded experiment with dynamics + observations exists').not.toBeNull();
    const dynName: string = (Array.isArray(det.dynamics) ? det.dynamics[0] : det.dynamics).name;
    const obsNames: string[] = (Array.isArray(det.observations) ? det.observations : [det.observations])
      .map((o: any) => o?.name).filter(Boolean);

    // The canonical server serialization must itself be tvbo-valid.
    const serverYaml = await (await request.get(`/tvbo/api/configurator/experiment/${targetId}/yaml`)).text();
    const serverRep = validateYaml(serverYaml);
    expect(serverRep.valid, `server YAML invalid: ${summarize(serverRep)}`).toBeTruthy();

    // Load the same experiment into the builder UI and re-assemble it.
    await page.goto(`${CONFIGURATOR}?experiment=${targetId}`);
    await waitForAssembled(page);

    const r = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec() as any;
      const res = await window.serializeExperiment(spec);
      const dyn = Array.isArray(spec.dynamics) ? spec.dynamics[0] : spec.dynamics;
      return { ok: res.ok, yaml: res.yaml, errors: res.errors, error: res.error, dynName: dyn?.name };
    });
    expect(r.ok, `re-serialize failed: ${JSON.stringify(r.errors || r.error)}`).toBeTruthy();

    // Round-trip identity: the re-emitted YAML is valid AND reproduces the
    // example's dynamics + observations (content identity, not byte identity —
    // Odoo normalizes ordering/whitespace).
    const rep = validateYaml(r.yaml);
    expect(rep.valid, `round-trip YAML invalid: ${summarize(rep)}`).toBeTruthy();
    expect(r.dynName, 'dynamics model name preserved through the UI round-trip').toBe(dynName);
    expect(r.yaml).toContain(dynName);
    for (const name of obsNames) {
      expect(r.yaml, `observation "${name}" preserved`).toContain(name);
    }
  });

  // -------------------------------------------------------------------- //
  // Flow 2: build fully by hand, multiple entries per section -> valid YAML
  // -------------------------------------------------------------------- //
  test('Flow 2: a fully hand-built experiment with multiple entries serializes valid', async ({ page }) => {
    test.setTimeout(150_000);
    await page.goto(CONFIGURATOR);

    // -- General --
    await page.locator('#experimentLabel').first().fill('Manual Multi-Entry Experiment');
    await page.locator('#experimentName').first().fill('manual_multi');

    // -- Dynamics: a model with TWO parameters and TWO state variables --
    await page.locator('#dynamics-tab').click();
    // Showing the Dynamics tab lazily runs initializeBuilder(), which renders the
    // "Add Dynamics Model" button — wait for it before clicking.
    await expect(page.locator('#addDynamicsModel')).toBeVisible({ timeout: 15_000 });
    // The dynamics editor is an in-page panel; Odoo's sticky header can overlap
    // a button after auto-scroll-to-center, so editor clicks use { force: true }
    // (they are genuinely visible + enabled — only hit-testing is fooled).
    await page.locator('#addDynamicsModel').click({ force: true });
    await expect(page.locator('#editorModelName')).toBeVisible({ timeout: 15_000 });
    await page.locator('#editorModelName').fill('TwoStateModel');

    await page.locator('#addEditorParam').click({ force: true });
    await page.locator('#addEditorParam').click({ force: true });
    const params = page.locator('#editorParamsContainer .param-row');
    await expect(params, 'two parameter rows added').toHaveCount(2);
    await params.nth(0).locator('.p-name').fill('a');
    await params.nth(0).locator('.p-value').fill('1.0');
    await params.nth(1).locator('.p-name').fill('b');
    await params.nth(1).locator('.p-value').fill('2.0');

    // State Variables sit in a collapsed accordion section — expand it and wait
    // for the open animation to finish before adding rows.
    await page.locator('.accordion-button[data-bs-target="#stateVarsSection"]').click({ force: true });
    await expect(page.locator('#stateVarsSection')).toHaveClass(/show/, { timeout: 5_000 });
    await page.locator('#addEditorStateVar').click({ force: true });
    await page.locator('#addEditorStateVar').click({ force: true });
    const svs = page.locator('#editorStateVarsContainer .sv-row');
    await expect(svs, 'two state-variable rows added').toHaveCount(2);
    await svs.nth(0).locator('.sv-name').fill('x');
    await svs.nth(0).locator('.sv-expr').fill('a - x + y');
    await svs.nth(0).locator('.sv-voi').check({ force: true });
    await svs.nth(1).locator('.sv-name').fill('y');
    await svs.nth(1).locator('.sv-expr').fill('b - y');

    await page.locator('#saveEditorModel').click({ force: true });
    await expect(page.locator('#dynamicsModelsList .card')).toContainText('TwoStateModel', { timeout: 15_000 });

    // -- Observations: TWO entries (real "add row" path) --
    await page.evaluate(() => {
      window.addObservationRow('raw', 'x', 'monitor', '1');
      window.addObservationRow('avg', 'y', 'monitor', '10');
    });
    await expect(page.locator('#observationsRows .builder-row'), 'two observation rows').toHaveCount(2);

    // -- Assemble + serialize through the same path the Download button uses --
    const r = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec() as any;
      const res = await window.serializeExperiment(spec);
      const dyn = Array.isArray(spec.dynamics) ? spec.dynamics[0] : spec.dynamics;
      return {
        ok: res.ok, yaml: res.yaml, errors: res.errors, error: res.error,
        nParams: Object.keys((dyn && dyn.parameters) || {}).length,
        nSv: Object.keys((dyn && dyn.state_variables) || {}).length,
      };
    });
    expect(r.ok, `manual serialize failed: ${JSON.stringify(r.errors || r.error)}`).toBeTruthy();

    // Multiplicity survived assembly...
    expect(r.nParams, 'both parameters assembled').toBeGreaterThanOrEqual(2);
    expect(r.nSv, 'both state variables assembled').toBeGreaterThanOrEqual(2);

    // ...and the YAML is tvbo-valid and carries every hand-entered item.
    const rep = validateYaml(r.yaml);
    expect(rep.valid, `hand-built YAML invalid: ${summarize(rep)}`).toBeTruthy();
    for (const token of ['TwoStateModel', 'a', 'b', 'x', 'y', 'raw', 'avg']) {
      expect(r.yaml, `"${token}" present in YAML`).toContain(token);
    }
  });

  // -------------------------------------------------------------------- //
  // Flow 3: pick a single KG component -> workspace -> refine -> add
  // -------------------------------------------------------------------- //
  test('Flow 3: pick a KG Dynamics component, refine it, and add it to the experiment', async ({ page, request }) => {
    test.setTimeout(150_000);

    // A Dynamics building block, exactly what a KG card "Open in Experiment
    // Builder" deep-links via ?dynamics=<id>.
    const dynResp = await getJson(request, '/tvbo/api/configurator/dynamics');
    const blocks: any[] = dynResp.data || dynResp;
    expect(Array.isArray(blocks) && blocks.length, 'KG has Dynamics building blocks').toBeTruthy();
    const block = blocks.find((d) => d && d.name) || blocks[0];
    expect(block?.name, 'a named Dynamics block exists').toBeTruthy();

    // Open it in the builder the way the KG card does.
    await page.goto(`${CONFIGURATOR}?dynamics=${block.id}`);
    await expect(
      page.locator('#dynamicsModelsList .card'),
      'KG component seeded into the workspace',
    ).toContainText(block.name, { timeout: 60_000 });

    // It is part of the assembled experiment.
    const seededName = await page.evaluate(() => {
      const s = window.assembleExperimentSpec() as any;
      const d = Array.isArray(s.dynamics) ? s.dynamics[0] : s.dynamics;
      return d?.name;
    });
    expect(seededName, 'seeded component is in the experiment').toBe(block.name);

    // Refine: show the Dynamics workspace, open the component's editor, add a param.
    await page.locator('#dynamics-tab').click();
    await page.locator('#dynamicsModelsList .edit-model-btn').first().click({ force: true });
    await expect(page.locator('#editorModelName')).toBeVisible({ timeout: 15_000 });
    await page.locator('#addEditorParam').click({ force: true });
    const newRow = page.locator('#editorParamsContainer .param-row').last();
    await newRow.locator('.p-name').fill('refined_gain');
    await newRow.locator('.p-value').fill('0.42');
    await page.locator('#saveEditorModel').click({ force: true });

    // The refinement is carried into the assembled experiment and serializes valid.
    const r = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec() as any;
      const res = await window.serializeExperiment(spec);
      return { ok: res.ok, yaml: res.yaml, errors: res.errors, error: res.error };
    });
    expect(r.ok, `refined serialize failed: ${JSON.stringify(r.errors || r.error)}`).toBeTruthy();
    expect(r.yaml, 'refinement present in the experiment YAML').toContain('refined_gain');
    const rep = validateYaml(r.yaml);
    expect(rep.valid, `refined YAML invalid: ${summarize(rep)}`).toBeTruthy();
  });
});
