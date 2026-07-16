import { test, expect, APIRequestContext } from '@playwright/test';
import {
  newSession,
  login,
  jsonrpc,
  callKw,
  ensurePortalUser,
  ADMIN_LOGIN,
  ADMIN_PASSWORD,
} from '../helpers/auth';

/**
 * Portal "share & publish your models" end-to-end coverage.
 *
 * Proves the two distinct sharing mechanisms against the live stack:
 *   - a portal user can save a model -> it lands in /my/models as a private draft;
 *   - PEER-TO-PEER sharing (/share) grants a named colleague access instantly:
 *     it appears on their /my/shared page and their public detail page, but NOT
 *     in the community gallery and NOT on the public model list;
 *   - PUBLISHING is gated: /submit runs automated validation and (on pass) queues
 *     for review — it never publishes directly. A reviewer (admin, who inherits
 *     the Publication Reviewer group) approves via the ORM, and only then does the
 *     model reach the community gallery; withdrawing removes it again;
 *   - only the owner can submit / withdraw / share / delete.
 *
 * Requires the dev stack (`make dev-up`). Admin creds default to admin/admin —
 * override with TVBO_ADMIN_LOGIN / TVBO_ADMIN_PASSWORD / TVBO_DB.
 */

const stamp = Date.now();
const ALICE = { login: `e2e_alice_${stamp}`, password: 'alicepw123', name: `E2E Alice ${stamp}` };
const BOB = { login: `e2e_bob_${stamp}`, password: 'bobpw123', name: `E2E Bob ${stamp}` };
const P2P_NAME = `E2E-P2P-${stamp}`;
const PUB_NAME = `E2E-Publish-${stamp}`;
const PRIVATE_NAME = `E2E-Private-${stamp}`;

let admin: APIRequestContext;
let alice: APIRequestContext;
let bob: APIRequestContext;
let bobUid: number;
let p2pId: number;
let pubId: number;
let privateId: number;

/** Save a model through the builder's "Save to Database" endpoint. */
async function saveModel(ctx: APIRequestContext, name: string): Promise<number> {
  const res = await jsonrpc(ctx, '/tvbo/configurator/save', {
    model_data: {
      name,
      label: name,
      description: `An end-to-end fixture model named ${name} with enough descriptive text.`,
    },
  });
  expect(res.success, `save failed: ${JSON.stringify(res)}`).toBeTruthy();
  expect(typeof res.model_id).toBe('number');
  return res.model_id as number;
}

/** Admin looks up the share row + publication state for a saved model. */
async function shareState(dynId: number): Promise<{ id: number; state: string } | null> {
  const ids: number[] = await callKw(admin, 'tvbo.model_share', 'search', [
    [['dynamics_id', '=', dynId]],
  ]);
  if (!ids.length) return null;
  const rows = await callKw(admin, 'tvbo.model_share', 'read', [ids, ['publication_state']]);
  return { id: ids[0], state: rows[0].publication_state };
}

test.describe.configure({ mode: 'serial' });

test.describe('TVBO portal: share & publish models', () => {
  test.beforeAll(async () => {
    admin = await newSession();
    await login(admin, ADMIN_LOGIN, ADMIN_PASSWORD);

    await ensurePortalUser(admin, ALICE.login, ALICE.password, ALICE.name);
    bobUid = await ensurePortalUser(admin, BOB.login, BOB.password, BOB.name);

    alice = await newSession();
    await login(alice, ALICE.login, ALICE.password);
    bob = await newSession();
    await login(bob, BOB.login, BOB.password);
  });

  test.afterAll(async () => {
    for (const id of [p2pId, pubId, privateId]) {
      if (id) await jsonrpc(alice, `/my/models/${id}/delete`, {}).catch(() => {});
    }
    await admin?.dispose();
    await alice?.dispose();
    await bob?.dispose();
  });

  test('saved models land in My Models as private drafts', async () => {
    p2pId = await saveModel(alice, P2P_NAME);
    pubId = await saveModel(alice, PUB_NAME);
    privateId = await saveModel(alice, PRIVATE_NAME);

    const html = await (await alice.get('/my/models')).text();
    expect(html, 'saved model shown').toContain(P2P_NAME);
    expect(html).toContain(PRIVATE_NAME);
    // New workflow controls (not the old instant Share toggle).
    expect(html, 'offers Submit for review').toContain('Submit for review');
    expect(html, 'offers peer-to-peer Share').toContain('Share with');
    // Drafts start private.
    const st = await shareState(privateId);
    expect(st?.state).toBe('draft');
  });

  test('a private draft is not exposed publicly', async () => {
    const pub = await newSession();
    const list = await pub.get('/tvbo/models');
    expect(await list.text(), 'draft absent from public list').not.toContain(PRIVATE_NAME);
    const detail = await pub.get(`/tvbo/model/${privateId}`, { maxRedirects: 0 });
    expect(detail.status(), 'draft detail is 404 for the public').toBe(404);
    await pub.dispose();
  });

  test('/my/models, /my/shared and the gallery require login', async () => {
    const anon = await newSession();
    for (const path of ['/my/models', '/my/shared', '/tvbo/models/shared']) {
      const resp = await anon.get(path, { maxRedirects: 0 });
      expect([301, 302, 303], `${path} redirects anon`).toContain(resp.status());
      expect(resp.headers()['location'] || '').toContain('/web/login');
    }
    await anon.dispose();
  });

  // ---------------------------------------------------------------- p2p
  test('peer-to-peer share grants a colleague access without publishing', async () => {
    const res = await jsonrpc(alice, `/my/models/${p2pId}/share`, { login: BOB.login });
    expect(res.success, `share failed: ${JSON.stringify(res)}`).toBeTruthy();

    // Bob sees it on his "Shared with me" page and can open its detail page.
    const shared = await (await bob.get('/my/shared')).text();
    expect(shared, 'shared model on Bob’s /my/shared').toContain(P2P_NAME);
    const detail = await bob.get(`/tvbo/model/${p2pId}`);
    expect(detail.ok(), 'collaborator can view detail').toBeTruthy();
    expect(await detail.text()).toContain(P2P_NAME);

    // But it is NOT public: absent from the community gallery and public list.
    expect(await (await bob.get('/tvbo/models/shared')).text(),
      'p2p share stays out of the gallery').not.toContain(P2P_NAME);
    expect(await (await bob.get('/my/models')).text(),
      'not on Bob’s own dashboard').not.toContain(P2P_NAME);

    // Owner can revoke it again.
    const un = await jsonrpc(alice, `/my/models/${p2pId}/unshare`, { user_id: bobUid });
    expect(un.success).toBeTruthy();
    expect(await (await bob.get('/my/shared')).text(),
      'unshared model gone from Bob’s page').not.toContain(P2P_NAME);
  });

  // ------------------------------------------------------------ publish
  test('submitting runs validation and gates publication (never publishes directly)', async () => {
    const res = await jsonrpc(alice, `/my/models/${pubId}/submit`, {});
    // Whatever the validation verdict, submitting alone must not publish.
    const gallery = await (await bob.get('/tvbo/models/shared')).text();
    expect(gallery, 'submit does not publish by itself').not.toContain(PUB_NAME);
    // The response always carries a structured validation report.
    expect(res.report, 'submit returns a validation report').toBeTruthy();
    expect(Array.isArray(res.report.checks)).toBeTruthy();
    if (res.success) {
      expect(res.state).toBe('in_review');
    } else {
      // A validation failure keeps it out of review with actionable issues.
      expect(res.report.checks.some((c: any) => !c.ok && !c.skipped)).toBeTruthy();
    }
  });

  test('a reviewer approval publishes it; withdraw unpublishes', async () => {
    // Ensure it is in review (submit again if the first attempt did not pass).
    let st = await shareState(pubId);
    if (st?.state !== 'in_review') {
      await jsonrpc(alice, `/my/models/${pubId}/submit`, {});
      st = await shareState(pubId);
    }
    test.skip(st?.state !== 'in_review',
      'model did not pass automated validation in this environment');

    // Admin inherits Publication Reviewer via base.group_system -> approve via ORM.
    await callKw(admin, 'tvbo.model_share', 'action_approve', [[st!.id]]);
    expect((await shareState(pubId))?.state).toBe('published');

    // Now visible to everyone in the community gallery, attributed to Alice.
    const gallery = await (await bob.get('/tvbo/models/shared')).text();
    expect(gallery, 'published model in the gallery').toContain(PUB_NAME);
    expect(gallery, 'attributed to its owner').toContain(ALICE.name);

    // Owner withdraws -> back to private draft, gone from the gallery.
    const wd = await jsonrpc(alice, `/my/models/${pubId}/withdraw`, {});
    expect(wd.success).toBeTruthy();
    expect((await shareState(pubId))?.state).toBe('draft');
    expect(await (await bob.get('/tvbo/models/shared')).text()).not.toContain(PUB_NAME);
  });

  // --------------------------------------------------------- access control
  test('non-owners cannot submit, withdraw, share or delete', async () => {
    for (const [path, params] of [
      [`/my/models/${p2pId}/submit`, {}],
      [`/my/models/${p2pId}/withdraw`, {}],
      [`/my/models/${p2pId}/share`, { login: BOB.login }],
      [`/my/models/${p2pId}/delete`, {}],
    ] as [string, Record<string, unknown>][]) {
      const res = await jsonrpc(bob, path, params);
      expect(res.success, `bob must not succeed on ${path}`).toBeFalsy();
    }
    // And Bob's dashboard never lists models he does not own.
    expect(await (await bob.get('/my/models')).text()).not.toContain(P2P_NAME);
  });

  test('re-saving a model updates in place instead of duplicating', async () => {
    const name = `E2E-Update-${stamp}`;
    const r1 = await jsonrpc(alice, '/tvbo/configurator/save', {
      model_data: { name, label: name, description: 'v1' },
    });
    const r2 = await jsonrpc(alice, '/tvbo/configurator/save', {
      model_data: { name, label: name, description: 'v2 updated' },
    });
    expect(r2.model_id, 'same record id -> updated, not duplicated').toBe(r1.model_id);
    expect(r2.message).toContain('updated');
    await jsonrpc(alice, `/my/models/${r1.model_id}/delete`, {}).catch(() => {});
  });

  test('saving requires authentication', async () => {
    const anon = await newSession();
    const resp = await anon.post('/tvbo/configurator/save', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        jsonrpc: '2.0',
        method: 'call',
        params: { model_data: { name: `E2E-Anon-${stamp}` } },
        id: 1,
      },
    });
    const body = await resp.json();
    expect(body.result && body.result.success, 'anonymous save must not succeed').toBeFalsy();
    await anon.dispose();
  });
});
