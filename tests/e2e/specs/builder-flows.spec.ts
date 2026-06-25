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

/** Call an Odoo type="jsonrpc" controller and return its `result`. */
async function rpc(request: APIRequestContext, url: string, params: Record<string, unknown>) {
  const resp = await request.post(url, {
    headers: { 'Content-Type': 'application/json' },
    data: { jsonrpc: '2.0', method: 'call', params, id: 1 },
  });
  expect(resp.ok(), `${url} HTTP ${resp.status()}`).toBeTruthy();
  const body = await resp.json();
  expect(body.error, `${url} JSON-RPC error: ${JSON.stringify(body.error)}`).toBeFalsy();
  return body.result;
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
  // These flows drive the live builder UI (lazy-initialized tabs, an accordion
  // modal editor, a sticky header, a running 3D canvas), which is inherently
  // timing-sensitive under load. Allow a small retry budget so transient UI-init
  // races don't flake the suite; the API-driven specs stay at the global retries=0.
  test.describe.configure({ retries: 2 });

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
    await expect(page.locator('#addDynamicsModel')).toBeVisible({ timeout: 25_000 });
    // The dynamics editor is an in-page panel; Odoo's sticky header can overlap
    // a button after auto-scroll-to-center, so editor clicks use { force: true }
    // (they are genuinely visible + enabled — only hit-testing is fooled).
    await page.locator('#addDynamicsModel').click({ force: true });
    await expect(page.locator('#editorModelName')).toBeVisible({ timeout: 25_000 });
    await page.locator('#editorModelName').fill('TwoStateModel');

    // Add rows one at a time, confirming each appears before the next click —
    // two rapid force-clicks can race under load and drop a row.
    const addParam = page.locator('#addEditorParam').first();
    const params = page.locator('#editorParamsContainer').first().locator('.param-row');
    await addParam.click({ force: true });
    await expect(params).toHaveCount(1, { timeout: 20_000 });
    await addParam.click({ force: true });
    await expect(params, 'two parameter rows added').toHaveCount(2, { timeout: 20_000 });
    await params.nth(0).locator('.p-name').fill('a');
    await params.nth(0).locator('.p-value').fill('1.0');
    await params.nth(1).locator('.p-name').fill('b');
    await params.nth(1).locator('.p-value').fill('2.0');

    // Expand the State Variables accordion. Open the collapse directly via JS
    // (rather than clicking the header button) so this can never hang on button
    // hit-testing under load; the bounded wait fails fast if the editor DOM isn't
    // ready instead of stalling for the whole test timeout.
    await page.locator('#stateVarsSection').first().waitFor({ state: 'attached', timeout: 15_000 });
    await page.evaluate(() => {
      document.querySelectorAll('#stateVarsSection').forEach((s) => s.classList.add('show'));
      document
        .querySelectorAll('.accordion-button[data-bs-target="#stateVarsSection"]')
        .forEach((b) => b.classList.remove('collapsed'));
    });
    const addSv = page.locator('#addEditorStateVar').first();
    await expect(addSv).toBeVisible({ timeout: 20_000 });
    const svs = page.locator('#editorStateVarsContainer').first().locator('.sv-row');
    await addSv.click({ force: true });
    await expect(svs).toHaveCount(1, { timeout: 20_000 });
    await addSv.click({ force: true });
    await expect(svs, 'two state-variable rows added').toHaveCount(2, { timeout: 20_000 });
    await svs.nth(0).locator('.sv-name').fill('x');
    await svs.nth(0).locator('.sv-expr').fill('a - x + y');
    await svs.nth(0).locator('.sv-voi').check({ force: true });
    await svs.nth(1).locator('.sv-name').fill('y');
    await svs.nth(1).locator('.sv-expr').fill('b - y');

    await page.locator('#saveEditorModel').click({ force: true });
    await expect(page.locator('#dynamicsModelsList .card')).toContainText('TwoStateModel', { timeout: 25_000 });

    // -- Observations: TWO entries on the unified Observation model --
    await page.evaluate(() => {
      // a basic monitor: source = a state variable + sampling period
      window.addObservationRow('raw', 'x', '1');
      // an external/library monitor via class_reference (no deprecated type)
      window.addObservationRow('bold', 'S_e', '1000', 'tvboptim.observations.tvb_monitors:Bold');
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
    for (const token of ['TwoStateModel', 'a', 'b', 'x', 'y', 'raw', 'bold']) {
      expect(r.yaml, `"${token}" present in YAML`).toContain(token);
    }
    // the external monitor maps onto the unified Observation's class_reference
    // (proving monitor/imaging_modality are no longer needed)
    expect(r.yaml, 'class_reference present').toContain('class_reference');
    expect(r.yaml).toContain('tvboptim');
  });

  // -------------------------------------------------------------------- //
  // Flow 3: pick a KG component -> workspace -> refine -> add ANOTHER -> both
  // -------------------------------------------------------------------- //
  test('Flow 3: pick a KG component, refine it, then add a second selection to the builder', async ({ page, request }) => {
    test.setTimeout(150_000);

    // Two distinct Dynamics building blocks: A is opened via the KG deep-link
    // (?dynamics=<id>, what a card's "Open in Experiment Builder" does); B is the
    // second selection added from inside the builder.
    const dynResp = await getJson(request, '/tvbo/api/configurator/dynamics');
    const blocks: any[] = (dynResp.data || dynResp).filter((d: any) => d && d.name);
    expect(blocks.length, 'KG has at least two named Dynamics blocks').toBeGreaterThan(1);
    const blockA = blocks[0];
    const blockB = blocks[1];

    // 1. Open component A in the builder; wait for the builder to be ready.
    await page.goto(`${CONFIGURATOR}?dynamics=${blockA.id}`);
    await page.locator('#dynamics-tab').click();
    await expect(page.locator('#addDynamicsModel'), 'builder initialized').toBeVisible({ timeout: 30_000 });
    await expect(
      page.locator('#dynamicsModelsList .card'),
      'KG component A seeded into the workspace',
    ).toContainText(blockA.name, { timeout: 60_000 });

    // 2. Refine A: open its editor and add a distinguishing parameter.
    await page.locator('#dynamicsModelsList .edit-model-btn').first().click({ force: true });
    await expect(page.locator('#editorModelName')).toBeVisible({ timeout: 25_000 });
    await page.locator('#addEditorParam').click({ force: true });
    const newRow = page.locator('#editorParamsContainer .param-row').last();
    await newRow.locator('.p-name').fill('refined_gain');
    await newRow.locator('.p-value').fill('0.42');
    await page.locator('#saveEditorModel').click({ force: true });
    await expect(page.locator('#dynamicsModelsList .card'), 'one model after refine').toHaveCount(1);

    // 3. Add a SECOND selection from the building-block picker (another KG choice).
    await page.locator('#addDynamicsModel').click({ force: true });
    await expect(page.locator('#editorBaseModel')).toBeVisible({ timeout: 25_000 });
    await page.locator('#editorBaseModel').selectOption(String(blockB.id));
    // Selecting a base model loads it (fills the editor name + params).
    await expect(page.locator('#editorModelName'), 'second selection loaded').not.toHaveValue('', { timeout: 25_000 });
    await page.locator('#saveEditorModel').click({ force: true });

    // 4. BOTH components are now in the builder's workspace.
    await expect(page.locator('#dynamicsModelsList .card'), 'two models in the workspace').toHaveCount(2);
    await expect(page.locator('#dynamicsModelsList')).toContainText(blockA.name);
    await expect(page.locator('#dynamicsModelsList')).toContainText(blockB.name);

    // 5. The experiment (built on the refined first model) still serializes valid,
    //    carrying the refinement.
    const r = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec() as any;
      const res = await window.serializeExperiment(spec);
      return { ok: res.ok, yaml: res.yaml, errors: res.errors, error: res.error };
    });
    expect(r.ok, `serialize failed: ${JSON.stringify(r.errors || r.error)}`).toBeTruthy();
    expect(r.yaml, 'refinement present in the experiment YAML').toContain('refined_gain');
    const rep = validateYaml(r.yaml);
    expect(rep.valid, `YAML invalid: ${summarize(rep)}`).toBeTruthy();
  });
});

// Section coverage: a single from-scratch experiment exercising every major
// section at once (dynamics + network + coupling + integration + observations),
// serialized through the same endpoint the builder uses. API-driven, so it has
// no UI-timing flakiness and complements the UI flows above.
test.describe('Experiment builder — full-section serialization coverage', () => {
  test('a complete experiment (network + coupling + integration + unified observations) serializes valid', async ({ request }) => {
    const experiment = {
      id: 1,
      label: 'Full Section Coverage',
      description: 'Every major section assembled from building blocks.',
      dynamics: {
        name: 'ReducedWongWang',
        parameters: { w: { value: 0.9 }, J_N: { value: 0.2609 } },
        state_variables: { S: { name: 'S', equation: { rhs: '-S / tau_s + w' }, initial_value: 0.1 } },
      },
      // Multi-node network with the connectome weight normalization transform.
      network: {
        number_of_nodes: 2,
        parameters: { conduction_speed: { value: 3.0, unit: 'mm_per_ms' } },
        transforms: [{ name: 'weight', equation: { rhs: 'W / W_max' } }],
      },
      coupling: { name: 'Linear' },
      integration: { method: 'Heun', step_size: 0.1, duration: 1000 },
      // Unified Observation: a plain monitor + an external/library one via class_reference.
      observations: {
        raw: { name: 'raw', source: ['S'], period: 1 },
        bold: {
          name: 'bold',
          class_reference: { module: 'tvboptim.observations.tvb_monitors', name: 'Bold' },
        },
      },
    };
    const res = await rpc(request, '/tvbo/api/configurator/experiment/serialize', { experiment });
    expect(res.success, `serialize failed: ${JSON.stringify(res.errors || res.error)}`).toBeTruthy();

    // Every section must survive into the YAML...
    for (const token of ['ReducedWongWang', 'Linear', 'Heun', 'conduction_speed', 'W / W_max', 'class_reference']) {
      expect(res.yaml, `"${token}" present`).toContain(token);
    }
    // ...and the whole thing must be tvbo-valid.
    const rep = validateYaml(res.yaml);
    expect(rep.valid, `complete experiment invalid: ${summarize(rep)}`).toBeTruthy();
  });

  test('#4 multi-model: per-node dynamics assigned in the network reach the assembled experiment', async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto(CONFIGURATOR);
    await page.waitForFunction(
      () => typeof window.prefillExperiment === 'function' && typeof window.assembleExperimentSpec === 'function',
      { timeout: 30_000 },
    );
    // Let the builder finish loading its model catalogue + initializing tabs
    // before prefilling (the node rows depend on it).
    await page.waitForTimeout(2500);

    // A 2-node network where each node runs a DIFFERENT model (per-node dynamics)
    // — the multi-model case. prefill drives the real Network-tab node rows.
    await page.evaluate(() => {
      window.prefillExperiment({
        id: 1,
        label: 'Per-node dynamics',
        network: {
          number_of_nodes: 2,
          nodes: [
            { id: 0, label: 'L', position: { x: 1, y: 0, z: 0 }, dynamics: { name: 'JansenRit' } },
            { id: 1, label: 'R', position: { x: -1, y: 0, z: 0 }, dynamics: { name: 'Generic2dOscillator' } },
          ],
        },
      });
      const cr = document.getElementById('networkModeCustom');
      if (cr) (cr as HTMLInputElement).checked = true;
    });
    // Node rows must be populated before assembling.
    await expect(page.locator('#customNetworkNodes .builder-row')).toHaveCount(2, { timeout: 15_000 });

    const r = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec() as any;
      const res = await window.serializeExperiment(spec);
      const nodes = (spec.network && spec.network.nodes) || [];
      return {
        ok: res.ok, yaml: res.yaml, errors: res.errors, error: res.error,
        nodeDyn: nodes.map((n: any) => n && n.dynamics && n.dynamics.name).filter(Boolean),
      };
    });

    expect(r.ok, `per-node serialize failed: ${JSON.stringify(r.errors || r.error)}`).toBeTruthy();
    // Each node kept its own model — the second model is no longer dropped.
    expect(r.nodeDyn, 'both per-node models present').toEqual(
      expect.arrayContaining(['JansenRit', 'Generic2dOscillator']),
    );
    const rep = validateYaml(r.yaml);
    expect(rep.valid, `per-node YAML invalid: ${summarize(rep)}`).toBeTruthy();
    expect(r.yaml).toContain('JansenRit');
  });
});
