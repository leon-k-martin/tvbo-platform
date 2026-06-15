import { APIRequestContext, request as pwRequest } from '@playwright/test';

// The portal tests authenticate against the live Odoo dev stack. Each "user"
// gets its own APIRequestContext (own cookie jar) so sessions never collide.
export const BASE_URL = process.env.TVBO_BASE_URL || 'http://localhost:8169';
export const DB = process.env.TVBO_DB || 'tvbo_dev';
export const ADMIN_LOGIN = process.env.TVBO_ADMIN_LOGIN || 'admin';
export const ADMIN_PASSWORD = process.env.TVBO_ADMIN_PASSWORD || 'admin';

/** A fresh, unauthenticated browser-like session. */
export async function newSession(): Promise<APIRequestContext> {
  return await pwRequest.newContext({ baseURL: BASE_URL });
}

/** Call an Odoo type="json"/"jsonrpc" endpoint and return its `result`. */
export async function jsonrpc(
  ctx: APIRequestContext,
  url: string,
  params: Record<string, unknown>,
): Promise<any> {
  const resp = await ctx.post(url, {
    headers: { 'Content-Type': 'application/json' },
    data: { jsonrpc: '2.0', method: 'call', params, id: 1 },
  });
  const body = await resp.json();
  if (body.error) throw new Error(`${url}: ${JSON.stringify(body.error)}`);
  return body.result;
}

/** Authenticate a session as the given user; returns the uid. */
export async function login(
  ctx: APIRequestContext,
  loginName: string,
  password: string,
): Promise<number> {
  const result = await jsonrpc(ctx, '/web/session/authenticate', {
    db: DB,
    login: loginName,
    password,
  });
  if (!result || !result.uid) {
    throw new Error(`login failed for ${loginName}: ${JSON.stringify(result)}`);
  }
  return result.uid;
}

/** Generic ORM call over the web session (admin-only operations in tests). */
export async function callKw(
  ctx: APIRequestContext,
  model: string,
  method: string,
  args: unknown[],
  kwargs: Record<string, unknown> = {},
): Promise<any> {
  return await jsonrpc(ctx, '/web/dataset/call_kw', { model, method, args, kwargs });
}

/**
 * Ensure a portal user exists with the given credentials (idempotent: resets
 * the password if the user already exists). Must be called from an admin
 * session. Returns the user id.
 */
export async function ensurePortalUser(
  adminCtx: APIRequestContext,
  loginName: string,
  password: string,
  name: string,
): Promise<number> {
  const ref = await callKw(adminCtx, 'ir.model.data', 'check_object_reference', [
    'base',
    'group_portal',
  ]);
  const portalGroupId = ref[1];
  const existing: number[] = await callKw(
    adminCtx,
    'res.users',
    'search',
    [[['login', '=', loginName]]],
    { limit: 1 },
  );
  if (existing.length) {
    await callKw(adminCtx, 'res.users', 'write', [existing, { password }]);
    return existing[0];
  }
  // Odoo 19 renamed res.users.groups_id -> group_ids.
  return await callKw(adminCtx, 'res.users', 'create', [
    { name, login: loginName, password, group_ids: [[6, 0, [portalGroupId]]] },
  ]);
}
