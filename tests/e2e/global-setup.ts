import { execFileSync } from 'node:child_process';
import * as path from 'node:path';

/**
 * Seed the documentation fixture so the account-page captures (My Models, API
 * Keys) run for real rather than skipping: a `docs-demo` user with a known
 * password and one private saved model. Idempotent. Runs the seed in the dev
 * stack's odoo container via `docker compose exec`; if that is unavailable
 * (e.g. CI against a remote instance), it logs and continues, and the account
 * tests fall back to skipping.
 */
const DB = process.env.DOCS_DB || 'tvbo_dev';
const USER = process.env.DOCS_USER || 'docs-demo';
const PASS = process.env.DOCS_PASS || 'DocsDemo-2026';

const SEED = `
u = env['res.users'].sudo()
fx = u.search([('login','=','${USER}')], limit=1)
if not fx:
    fx = u.create({'name':'Docs Demo','login':'${USER}','email':'${USER}@example.com',
                   'group_ids':[(6,0,[env.ref('base.group_user').id])]})
fx.password = '${PASS}'
MS = env['tvbo.model_share'].sudo()
dyn = (env['tvbo.dynamics'].sudo().search([('name','=','Generic2dOscillator')], limit=1)
       or env['tvbo.dynamics'].sudo().search([], limit=1))
if dyn and not MS.search([('owner_user_id','=',fx.id),('dynamics_id','=',dyn.id)], limit=1):
    MS.create({'owner_user_id':fx.id,'dynamics_id':dyn.id,'visibility':'private'})
env.cr.commit()
print('FIXTURE_OK', fx.id)
`;

export default function globalSetup() {
  const repo = path.resolve(__dirname, '..', '..');
  try {
    const out = execFileSync(
      'docker',
      ['compose', 'exec', '-T', 'odoo', 'odoo', 'shell', '-d', DB,
       '--no-http', '--db_host=postgres', '--db_user=odoo', '--db_password=odoo'],
      { cwd: repo, input: SEED, encoding: 'utf8', timeout: 90_000, stdio: ['pipe', 'pipe', 'pipe'] },
    );
    console.log(out.includes('FIXTURE_OK')
      ? '[docs] fixture user seeded'
      : '[docs] fixture seed ran but no confirmation; account tests may skip');
  } catch (e) {
    console.warn('[docs] fixture seed skipped (docker stack not reachable):', (e as Error).message);
  }
}
