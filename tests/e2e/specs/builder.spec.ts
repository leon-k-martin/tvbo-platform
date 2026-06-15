import { test, expect, APIRequestContext } from '@playwright/test';
import { validateYaml, validateYamls, summarize } from '../helpers/validate';

const CONFIGURATOR = '/tvbo/configurator';

/** Call an Odoo type="json"/"jsonrpc" controller and return its `result`. */
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

test.describe('TVBO model/experiment builder', () => {
  test('configurator page renders with builder controls', async ({ page }) => {
    await page.goto(CONFIGURATOR);
    await expect(page.getByRole('heading', { name: 'Experiment Builder' })).toBeVisible();
    await expect(page.locator('#builderDownloadYaml')).toBeVisible();
    await expect(page.locator('#configTabs')).toBeVisible();
  });

  test('schema endpoint exposes SimulationExperiment and pickable building blocks', async ({ request }) => {
    const resp = await request.get('/tvbo/api/configurator/schema');
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBeTruthy();
    const classes = body.data.classes;
    expect(classes.SimulationExperiment).toBeTruthy();
    // The building blocks a user assembles an experiment from must be pickable.
    for (const cls of ['Dynamics', 'Network', 'Coupling', 'Integrator', 'Observation']) {
      expect(classes[cls], `class ${cls} present`).toBeTruthy();
      expect(classes[cls].pickable, `class ${cls} pickable from DB`).toBeTruthy();
    }
  });

  test('every seeded experiment serializes to tvbo-valid YAML', async ({ request }) => {
    // Validating every experiment pays one (heavy) tvbo import for the whole
    // batch; give the cold-stack import generous headroom.
    test.setTimeout(180_000);

    const resp = await request.get('/tvbo/api/configurator/experiments');
    const body = await resp.json();
    expect(body.success).toBeTruthy();
    const experiments: Array<{ id: number; label?: string; name?: string }> = body.data || [];
    expect(experiments.length, 'seeded experiments present').toBeGreaterThan(0);

    // Fetch each experiment's YAML, retrying transient connection failures.
    // The `--dev=reload` server restarts whenever an addon file changes, which
    // drops in-flight connections (ECONNRESET/refused) — retry across that
    // window rather than failing the structural check on an infra hiccup.
    async function fetchYaml(id: number, label: string): Promise<string> {
      let lastErr = '';
      for (let attempt = 1; attempt <= 5; attempt++) {
        try {
          const r = await request.get(`/tvbo/api/configurator/experiment/${id}/yaml`, { timeout: 30_000 });
          const ct = r.headers()['content-type'] || '';
          const text = await r.text();
          if (ct.includes('yaml')) return text;
          lastErr = `non-YAML (ct=${ct}): ${text.slice(0, 200)}`;
        } catch (e: any) {
          lastErr = e?.message || String(e);
        }
        await new Promise((res) => setTimeout(res, 1500 * attempt));
      }
      throw new Error(`experiment ${id} (${label}) YAML fetch failed after retries: ${lastErr}`);
    }

    const fetched: Array<{ exp: { id: number; label?: string }; text: string }> = [];
    for (const exp of experiments) {
      fetched.push({ exp, text: await fetchYaml(exp.id, exp.label || String(exp.id)) });
    }

    // Validate all of them in a single tvbo import instead of one spawn each.
    const reports = validateYamls(
      fetched.map(({ exp, text }) => ({ text, label: `experiment ${exp.id} (${exp.label})` })),
    );
    reports.forEach((report, i) => {
      const { exp } = fetched[i];
      expect(report.valid, `experiment ${exp.id} (${exp.label}) invalid: ${summarize(report)}`).toBeTruthy();
    });
  });

  test('UI: ?experiment deep-link (KG -> builder) loads and downloads valid YAML', async ({ page, request }) => {
    const body = await (await request.get('/tvbo/api/configurator/experiments')).json();
    const experiments = body.data || [];
    expect(experiments.length, 'seeded experiments present').toBeGreaterThan(0);
    const exp = experiments[0];

    // Deep link the same way a Knowledge-Graph card's "Open in Experiment Builder" does.
    await page.goto(`${CONFIGURATOR}?experiment=${exp.id}`);
    // The base spec loads via a slow (tvbo-importing) /spec fetch that completes
    // AFTER prefill. Wait until it's applied (assembled spec carries the loaded
    // observations) before downloading — clicking earlier hits a half-loaded spec
    // and downloadYaml()'s validation alert() would block the test until timeout.
    await expect(page.locator('#dynamicsModelsList .card')).not.toHaveCount(0, { timeout: 40_000 });
    await expect
      .poll(async () => page.evaluate(() => {
        try { return !!(window.assembleExperimentSpec() as any).observations; } catch { return false; }
      }), { timeout: 60_000 })
      .toBeTruthy();
    // Safety net: surface an unexpected validation alert instead of hanging 60s.
    page.on('dialog', (d) => { void d.dismiss(); throw new Error(`unexpected dialog: ${d.message()}`); });

    const downloadPromise = page.waitForEvent('download', { timeout: 60_000 });
    await page.locator('#builderDownloadYaml').click();
    const download = await downloadPromise;
    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const c of stream) chunks.push(Buffer.from(c));
    const yamlText = Buffer.concat(chunks).toString('utf-8');

    const report = validateYaml(yamlText);
    expect(report.valid, `downloaded YAML invalid for exp ${exp.id}: ${summarize(report)}`).toBeTruthy();
  });

  test('UI: ?experiment deep-link populates the Dynamics tab (regression: empty Local Dynamics)', async ({ page, request }) => {
    // Find a seeded experiment that actually carries a dynamics model, and the
    // model's name, straight from the same API the builder loads from.
    const list = (await (await request.get('/tvbo/api/configurator/experiments')).json()).data || [];
    expect(list.length, 'seeded experiments present').toBeGreaterThan(0);
    let targetId: number | null = null;
    let dynName = '';
    for (const e of list) {
      const det = (await (await request.get(`/tvbo/api/configurator/experiment/${e.id}`)).json()).data;
      const dyn = Array.isArray(det?.dynamics) ? det.dynamics[0] : det?.dynamics;
      if (dyn && dyn.name) { targetId = e.id; dynName = dyn.name; break; }
    }
    expect(targetId, 'a seeded experiment with dynamics exists').not.toBeNull();

    await page.goto(`${CONFIGURATOR}?experiment=${targetId}`);
    await page.locator('#dynamics-tab').click();

    // The loaded model must surface in the "Local Dynamics" list — not the empty
    // placeholder. (The downloaded-YAML check above passes from baseSpec even when
    // this list is broken, so assert the tab's own rendered state here.)
    const modelsList = page.locator('#dynamicsModelsList');
    await expect(modelsList).not.toContainText('No dynamics models added yet', { timeout: 30_000 });
    await expect(modelsList.locator('.card')).not.toHaveCount(0, { timeout: 30_000 });
    await expect(modelsList).toContainText(dynName, { timeout: 30_000 });
  });

  test('UI: loading an experiment populates EVERY tab that has data (full sweep)', async ({ page, request }) => {
    test.setTimeout(300_000);
    // prefillExperiment() fills every list container synchronously regardless of
    // which tab is active, so once the Dynamics list has hydrated we can read all
    // row counts at once. Observations split into base vs derived (pipeline/source).
    const isDerived = (o: any) => !!(o && (o.pipeline || o.source_observations));
    const list = (await (await request.get('/tvbo/api/configurator/experiments')).json()).data || [];
    expect(list.length, 'seeded experiments present').toBeGreaterThan(0);

    let checked = 0;
    for (const e of list) {
      const det = (await (await request.get(`/tvbo/api/configurator/experiment/${e.id}`)).json()).data;
      const checks: Array<{ sel: string; n: number; what: string }> = [];
      const push = (field: string, sel: string) => {
        if (Array.isArray(det[field]) && det[field].length) checks.push({ sel, n: det[field].length, what: field });
      };
      push('functions', '#functionsRows .builder-row');
      push('algorithms', '#algorithmsRows .builder-row');
      push('optimizations', '#optimizationRows .builder-row');
      push('explorations', '#explorationsRows .builder-row');
      push('continuations', '#continuationsRows .builder-row');
      const obs = Array.isArray(det.observations) ? det.observations : [];
      const base = obs.filter((o: any) => !isDerived(o)).length;
      const der = obs.filter((o: any) => isDerived(o)).length;
      if (base) checks.push({ sel: '#observationsRows .builder-row', n: base, what: 'observations(base)' });
      if (der) checks.push({ sel: '#derivedObservationsRows .builder-row', n: der, what: 'derived observations' });
      const hasDyn = !!det.dynamics;
      if (!checks.length && !hasDyn) continue;

      await page.goto(`${CONFIGURATOR}?experiment=${e.id}`);
      // Hydration barrier: prefill runs synchronously, so once a dynamics card is
      // rendered, every list container is filled too.
      if (hasDyn) {
        await expect(
          page.locator('#dynamicsModelsList .card'),
          `exp ${e.id}: Dynamics tab empty but experiment has a dynamics model`,
        ).not.toHaveCount(0, { timeout: 60_000 });
        checked++;
      }
      for (const c of checks) {
        await expect
          .soft(page.locator(c.sel), `exp ${e.id}: "${c.what}" rows != API count (${c.n})`)
          .toHaveCount(c.n, { timeout: 15_000 });
        checked++;
      }
    }
    expect(checked, 'list/dynamics tabs exercised across experiments').toBeGreaterThan(0);
  });

  test('UI: synthetic experiment loads events + explicit network nodes', async ({ page, request }) => {
    // No seeded experiment exercises events or an explicit node list. Deep-link a
    // real experiment first so every tab is fully initialized, then drive
    // prefillExperiment() with a synthetic spec and assert events + node tabs.
    const list = (await (await request.get('/tvbo/api/configurator/experiments')).json()).data || [];
    expect(list.length).toBeGreaterThan(0);
    await page.goto(`${CONFIGURATOR}?experiment=${list[0].id}`);
    // Dynamics card == prefill ran == every tab container (events, custom nodes)
    // is initialized in the DOM (some are in hidden panels, hence no visible wait).
    await expect(page.locator('#dynamicsModelsList .card')).not.toHaveCount(0, { timeout: 40_000 });
    await page.evaluate(() => {
      window.prefillExperiment({
        label: 'Synthetic events + nodes',
        dynamics: { name: 'JansenRit' },
        events: [
          { name: 'ev_a', event_type: 'parameter_change', target_variable: 'a', condition: 't > 100' },
          { name: 'ev_b', event_type: 'reset', target_regions: '0,1' },
        ],
        network: {
          number_of_nodes: 2,
          nodes: [
            { id: 0, label: 'L', position: { x: 1, y: 2, z: 3 }, dynamics: { name: 'JansenRit' } },
            { id: 1, label: 'R', position: { x: 4, y: 5, z: 6 } },
          ],
        },
      });
    });
    await expect(page.locator('#eventsRows .builder-row'), 'events not loaded').toHaveCount(2, { timeout: 15_000 });
    await expect(page.locator('#customNetworkNodes .builder-row'), 'explicit nodes not loaded').toHaveCount(2, {
      timeout: 15_000,
    });
    // The loaded node label/coords must round-trip into the row inputs.
    await expect(page.locator('#customNetworkNodes .builder-row').first().locator('.node-label')).toHaveValue('L');
  });

  test('UI: scalar object sections (integration) prefill their fields', async ({ page, request }) => {
    // prefillSection() fills [data-field] inputs; verify a loaded experiment's
    // integration settings actually reach the Integration tab inputs.
    const list = (await (await request.get('/tvbo/api/configurator/experiments')).json()).data || [];
    let target: number | null = null;
    for (const e of list) {
      const det = (await (await request.get(`/tvbo/api/configurator/experiment/${e.id}`)).json()).data;
      if (det.integration && typeof det.integration === 'object') { target = e.id; break; }
    }
    expect(target, 'an experiment with integration settings exists').not.toBeNull();

    await page.goto(`${CONFIGURATOR}?experiment=${target}`);
    await page.locator('#integration-tab').click();
    // At least one [data-field] input in the integration section must be filled.
    await expect
      .poll(async () =>
        page.evaluate(() => {
          const c = document.querySelector('[data-section="integration"]');
          if (!c) return -1;
          return Array.from(c.querySelectorAll('[data-field]')).filter(
            (el) => (el as HTMLInputElement).value && (el as HTMLInputElement).value.trim() !== '',
          ).length;
        }),
        { timeout: 30_000 },
      )
      .toBeGreaterThan(0);
  });

  test('UI: references round-trip intact (commas within a citation are preserved)', async ({ page, request }) => {
    // Find an experiment whose references are multi-line citations containing
    // commas — the exact shape that the old comma-split shattered.
    const list = (await (await request.get('/tvbo/api/configurator/experiments')).json()).data || [];
    let target: number | null = null;
    let expectedRefs: string[] = [];
    for (const e of list) {
      const det = (await (await request.get(`/tvbo/api/configurator/experiment/${e.id}`)).json()).data;
      if (typeof det.references === 'string' && det.references.includes(',') && det.references.includes('\n')) {
        target = e.id;
        expectedRefs = det.references.split(/\r?\n+/).map((s: string) => s.trim()).filter(Boolean);
        break;
      }
    }
    expect(target, 'an experiment with multi-line, comma-containing references exists').not.toBeNull();
    expect(expectedRefs.length).toBeGreaterThan(1);

    await page.goto(`${CONFIGURATOR}?experiment=${target}`);
    await expect(page.locator('#dynamicsModelsList .card')).not.toHaveCount(0, { timeout: 40_000 });
    // The references textarea is filled during prefill (general section).
    await expect.poll(async () => page.locator('#experimentReferences').inputValue().catch(() => '')).not.toBe('');

    // The assembled spec must list one entry per citation, NOT comma-fragments.
    const refs = await page.evaluate(() => (window.assembleExperimentSpec() as { references?: string[] }).references);
    expect(Array.isArray(refs), 'references serialized as a list').toBeTruthy();
    expect(refs, 'each reference is a full citation, not a comma-fragment').toEqual(expectedRefs);
  });

  test('instance /spec endpoint returns a schema-valid building block', async ({ request }) => {
    // Backs the KG "Open in Experiment Builder" seed for non-experiment cards.
    const list = await (await request.get('/tvbo/api/configurator/instances/Dynamics?limit=1')).json();
    expect(list.success).toBeTruthy();
    expect((list.data || []).length).toBeGreaterThan(0);
    const recId = list.data[0].id;
    const spec = await (await request.get(`/tvbo/api/configurator/instances/Dynamics/${recId}/spec`)).json();
    expect(spec.success, `instance spec failed: ${JSON.stringify(spec.errors || spec.error)}`).toBeTruthy();
    expect(spec.data.name, 'dynamics has a name').toBeTruthy();
  });

  test('serialize endpoint validates an assembled experiment (keyed-dict and list forms)', async ({ request }) => {
    const keyedForm = {
      id: 1,
      label: 'E2E Keyed',
      dynamics: { name: 'JansenRit', parameters: { A: { value: 3.25 }, B: { value: 22.0 } } },
      integration: { method: 'Heun', step_size: 0.1, duration: 1000 },
    };
    const keyed = await rpc(request, '/tvbo/api/configurator/experiment/serialize', { experiment: keyedForm });
    expect(keyed.success, `keyed serialize failed: ${JSON.stringify(keyed)}`).toBeTruthy();
    const keyedReport = validateYaml(keyed.yaml);
    expect(keyedReport.valid, `keyed YAML invalid: ${summarize(keyedReport)}`).toBeTruthy();

    // List-form collections (as JS builder/Odoo emit) must serialize identically.
    const listForm = {
      id: 2,
      label: 'E2E List',
      dynamics: { name: 'JansenRit', parameters: [{ name: 'A', value: 3.25 }, { name: 'B', value: 22.0 }] },
      integration: { method: 'Heun', step_size: 0.1, duration: 1000 },
    };
    const list = await rpc(request, '/tvbo/api/configurator/experiment/serialize', { experiment: listForm });
    expect(list.success, `list serialize failed: ${JSON.stringify(list)}`).toBeTruthy();
    const listReport = validateYaml(list.yaml);
    expect(listReport.valid, `list YAML invalid: ${summarize(listReport)}`).toBeTruthy();
  });

  test('serialize endpoint reports structured errors for invalid input', async ({ request }) => {
    const res = await rpc(request, '/tvbo/api/configurator/experiment/serialize', {
      experiment: { label: 'missing id' },
    });
    expect(res.success).toBeFalsy();
    expect(res.error).toBe('validation_error');
    expect(Array.isArray(res.errors)).toBeTruthy();
  });

  test('from-scratch experiment with network + tvboptim interop serializes valid', async ({ request }) => {
    const experiment = {
      id: 1,
      label: 'From Scratch + tvboptim',
      description: 'Assembled from building blocks with a tvboptim Bold monitor.',
      dynamics: { name: 'ReducedWongWang', parameters: { w: { value: 0.9 }, J_N: { value: 0.2609 } } },
      network: { number_of_nodes: 2, parameters: { conduction_speed: { value: 3.0, unit: 'mm_per_ms' } } },
      coupling: { name: 'Linear' },
      integration: { method: 'Heun', step_size: 0.1, duration: 1000 },
      observations: {
        // tvboptim interoperability: external class plugged in via class_reference.
        bold: {
          name: 'bold',
          class_reference: { module: 'tvboptim.observations.tvb_monitors', name: 'Bold' },
        },
      },
    };
    const res = await rpc(request, '/tvbo/api/configurator/experiment/serialize', { experiment });
    expect(res.success, `serialize failed: ${JSON.stringify(res.errors || res.error)}`).toBeTruthy();
    expect(res.yaml).toContain('class_reference');
    expect(res.yaml).toContain('tvboptim');
    const report = validateYaml(res.yaml);
    expect(report.valid, `from-scratch YAML invalid: ${summarize(report)}`).toBeTruthy();
  });

  test('UI: building from scratch (no base) downloads valid YAML', async ({ page }) => {
    await page.goto(CONFIGURATOR);
    // No experiment loaded -> assemble purely from the builder's own state.
    const labelInput = page.locator('#experimentLabel, #builderSpecName, #experimentName').first();
    await labelInput.waitFor({ state: 'visible' });
    await labelInput.fill('My Brand New Experiment');

    // Drive the assembler + server validator the way the Download button does.
    const result = await page.evaluate(async () => {
      const spec = window.assembleExperimentSpec();
      const res = await window.serializeExperiment(spec);
      return { ok: res.ok, errors: res.errors, error: res.error, hasYaml: !!res.yaml };
    });
    expect(result.ok, `from-scratch assemble/serialize failed: ${JSON.stringify(result.errors || result.error)}`).toBeTruthy();
    expect(result.hasYaml).toBeTruthy();
  });
});

declare global {
  interface Window {
    assembleExperimentSpec: () => Record<string, unknown>;
    serializeExperiment: (spec: unknown, format?: string) => Promise<{ ok: boolean; yaml?: string; data?: unknown; error?: string; errors?: Array<{ loc: string[]; msg: string }> }>;
    setBaseSpec: (spec: unknown) => void;
    prefillExperiment: (exp: Record<string, unknown>) => void;
  }
}
