import { test, expect, APIRequestContext } from '@playwright/test';
import {
  newSession,
  login,
  jsonrpc,
  ensurePortalUser,
  ADMIN_LOGIN,
  ADMIN_PASSWORD,
} from '../helpers/auth';

/**
 * Portal "save & share your models" end-to-end coverage.
 *
 * Proves the full ownership/visibility contract against the live stack:
 *   - a portal user (with a user account) can save a model -> it lands in their
 *     /my/models dashboard and starts private;
 *   - private models never leak to the public list, the public detail page,
 *     or another user's shared gallery;
 *   - sharing a model surfaces it to every other logged-in user;
 *   - only the owner can change visibility or delete.
 *
 * Requires the dev stack (`make dev-up`). Admin creds default to admin/admin —
 * override with TVBO_ADMIN_LOGIN / TVBO_ADMIN_PASSWORD / TVBO_DB.
 */

const stamp = Date.now();
const ALICE = { login: `e2e_alice_${stamp}`, password: 'alicepw123', name: `E2E Alice ${stamp}` };
const BOB = { login: `e2e_bob_${stamp}`, password: 'bobpw123', name: `E2E Bob ${stamp}` };
const SHARED_NAME = `E2E-Shared-${stamp}`;
const PRIVATE_NAME = `E2E-Private-${stamp}`;

let admin: APIRequestContext;
let alice: APIRequestContext;
let bob: APIRequestContext;
let sharedId: number;
let privateId: number;

/** Save a model through the builder's "Save to Database" endpoint. */
async function saveModel(ctx: APIRequestContext, name: string): Promise<number> {
  const res = await jsonrpc(ctx, '/tvbo/configurator/save', {
    model_data: { name, label: name, description: `e2e model ${name}` },
  });
  expect(res.success, `save failed: ${JSON.stringify(res)}`).toBeTruthy();
  expect(typeof res.model_id).toBe('number');
  return res.model_id as number;
}

test.describe.configure({ mode: 'serial' });

test.describe('TVBO portal: save & share models', () => {
  test.beforeAll(async () => {
    admin = await newSession();
    await login(admin, ADMIN_LOGIN, ADMIN_PASSWORD);

    await ensurePortalUser(admin, ALICE.login, ALICE.password, ALICE.name);
    await ensurePortalUser(admin, BOB.login, BOB.password, BOB.name);

    alice = await newSession();
    await login(alice, ALICE.login, ALICE.password);
    bob = await newSession();
    await login(bob, BOB.login, BOB.password);
  });

  test.afterAll(async () => {
    // Best-effort cleanup of the records/users this run created.
    for (const id of [sharedId, privateId]) {
      if (id) await jsonrpc(alice, `/my/models/${id}/delete`, {}).catch(() => {});
    }
    await admin?.dispose();
    await alice?.dispose();
    await bob?.dispose();
  });

  test('portal user can save a model; it appears (private) in their dashboard', async () => {
    sharedId = await saveModel(alice, SHARED_NAME);
    privateId = await saveModel(alice, PRIVATE_NAME);

    const resp = await alice.get('/my/models');
    expect(resp.ok()).toBeTruthy();
    const html = await resp.text();
    expect(html, 'saved model shown in My Models').toContain(SHARED_NAME);
    expect(html).toContain(PRIVATE_NAME);
    // New models default to private -> the dashboard offers a "Share" action.
    expect(html).toContain('Share');
  });

  test('a private model is not exposed publicly', async () => {
    const pub = await newSession(); // unauthenticated
    const list = await pub.get('/tvbo/models');
    expect(list.ok()).toBeTruthy();
    expect(await list.text(), 'private model absent from public list').not.toContain(SHARED_NAME);

    const detail = await pub.get(`/tvbo/model/${privateId}`, { maxRedirects: 0 });
    expect(detail.status(), 'private model detail is 404 for the public').toBe(404);
    await pub.dispose();
  });

  test('/my/models and /tvbo/models/shared require login', async () => {
    const anon = await newSession();
    for (const path of ['/my/models', '/tvbo/models/shared']) {
      const resp = await anon.get(path, { maxRedirects: 0 });
      expect([301, 302, 303], `${path} should redirect anonymous users`).toContain(resp.status());
      const loc = resp.headers()['location'] || '';
      expect(loc, `${path} redirects to login`).toContain('/web/login');
    }
    await anon.dispose();
  });

  test('owner can share a model and it reaches another user’s gallery', async () => {
    const res = await jsonrpc(alice, `/my/models/${sharedId}/visibility`, { visibility: 'shared' });
    expect(res.success).toBeTruthy();
    expect(res.visibility).toBe('shared');

    // Bob (a different logged-in user) now sees it, attributed to Alice.
    const gallery = await bob.get('/tvbo/models/shared');
    expect(gallery.ok()).toBeTruthy();
    const html = await gallery.text();
    expect(html, 'shared model visible to other users').toContain(SHARED_NAME);
    expect(html, 'shared model attributed to its owner').toContain(ALICE.name);
    // Alice's still-private model must NOT appear in the shared gallery.
    expect(html, 'private model stays out of the gallery').not.toContain(PRIVATE_NAME);
  });

  test('shared model becomes viewable on its public detail page', async () => {
    const pub = await newSession();
    const detail = await pub.get(`/tvbo/model/${sharedId}`);
    expect(detail.ok(), 'shared model detail is public').toBeTruthy();
    expect(await detail.text()).toContain(SHARED_NAME);
    await pub.dispose();
  });

  test('non-owners cannot change visibility or delete', async () => {
    const share = await jsonrpc(bob, `/my/models/${sharedId}/visibility`, { visibility: 'private' });
    expect(share.success, 'bob cannot re-private alice’s model').toBeFalsy();

    const del = await jsonrpc(bob, `/my/models/${sharedId}/delete`, {});
    expect(del.success, 'bob cannot delete alice’s model').toBeFalsy();

    // And bob's own dashboard does not list models he does not own.
    const mine = await bob.get('/my/models');
    expect(await mine.text()).not.toContain(SHARED_NAME);
  });

  test('re-saving a model updates in place instead of duplicating', async () => {
    const name = `E2E-Update-${stamp}`;
    const r1 = await jsonrpc(alice, '/tvbo/configurator/save', {
      model_data: { name, label: name, description: 'v1' },
    });
    expect(r1.success).toBeTruthy();
    const r2 = await jsonrpc(alice, '/tvbo/configurator/save', {
      model_data: { name, label: name, description: 'v2 updated' },
    });
    expect(r2.success).toBeTruthy();
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
    // auth='user' -> Odoo raises a session/access error rather than succeeding.
    const succeeded = body.result && body.result.success;
    expect(succeeded, 'anonymous save must not succeed').toBeFalsy();
    await anon.dispose();
  });
});
