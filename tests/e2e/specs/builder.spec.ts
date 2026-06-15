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
    await page.waitForTimeout(5000); // allow the auto-loader to hydrate the base spec

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
  }
}
