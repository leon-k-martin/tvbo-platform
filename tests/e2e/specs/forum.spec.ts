import { test, expect, Page, APIRequestContext } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';
import { writeShot } from '../helpers/shot';
import { newSession, login, callKw, ensurePortalUser, ADMIN_LOGIN, ADMIN_PASSWORD, DB } from '../helpers/auth';

/**
 * Community forum (Odoo website_forum) — behaviour and documentation captures.
 *
 * The behavioural tests pin the decisions that are easy to regress silently:
 * /forum lands on the forum itself rather than Odoo's room picker, a topic
 * carries its own kind (Question or Discussion) and only questions offer the
 * accepted-answer flow, discussions take more than one reply per person, the
 * TVBO palette actually reaches Odoo's own templates, anonymous visitors can
 * read but not post, and the karma gates behave as configured in
 * data/forum_data.xml. The screenshot tests write straight into the docs
 * module's static/img/, so /docs/forum never shows a stale UI:
 *
 *   npx playwright test forum
 */
const BASE = process.env.TVBO_BASE_URL || process.env.BASE_URL || 'http://localhost:8169';
const FORUM_USER = process.env.FORUM_USER || 'forum-demo';
const FORUM_PASS = process.env.FORUM_PASS || 'ForumDemo-2026';
const OUT = path.resolve(__dirname, '..', '..', '..', 'odoo-addons', 'tvbo_platform_docs', 'static', 'img');

test.use({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
test.describe.configure({ mode: 'serial' });

fs.mkdirSync(OUT, { recursive: true });
const shot = (page: Page, name: string) => writeShot(page, OUT, name);
const settle = (ms = 800) => new Promise((r) => setTimeout(r, ms));

type Forum = { id: number; name: string; mode: string; slug: string };

let admin: APIRequestContext;
let forum: Forum;
let userId: number;

/** Odoo builds forum URLs as /forum/<slugified-name>-<id>; the id is mandatory. */
const slugify = (name: string, id: number) =>
  `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-${id}`;

/** Authenticate the browser context itself, so page.goto() is logged in. */
async function signIn(page: Page, user: string, pass: string) {
  const res = await page.request.post(`${BASE}/web/session/authenticate`, {
    headers: { 'Content-Type': 'application/json' },
    data: { jsonrpc: '2.0', method: 'call', params: { db: DB, login: user, password: pass } },
  });
  const body = await res.json();
  return Boolean(body?.result?.uid);
}

/** Give the fixture user a known karma level (email validation grants 3). */
async function setKarma(karma: number) {
  await callKw(admin, 'res.users', 'write', [[userId], { karma }]);
}

/** Fixture posts, torn down in afterAll so the dev forum does not silt up. */
const created: number[] = [];

async function createPost(vals: Record<string, unknown>): Promise<number> {
  const id: number = await callKw(admin, 'forum.post', 'create', [{ forum_id: forum.id, ...vals }]);
  created.push(id);
  return id;
}

test.beforeAll(async () => {
  admin = await newSession();
  await login(admin, ADMIN_LOGIN, ADMIN_PASSWORD);

  const forums: Forum[] = await callKw(
    admin, 'forum.forum', 'search_read',
    [[['active', '=', true]], ['id', 'name', 'mode']],
  );
  // Exactly one active forum is the whole point: Odoo's /forum only redirects
  // to the forum itself while there is nothing to choose between.
  if (forums.length !== 1) {
    throw new Error(`expected a single forum, got: ${forums.map((f) => f.name).join(', ') || 'none'}`);
  }
  forum = { ...forums[0], slug: slugify(forums[0].name, forums[0].id) };

  userId = await ensurePortalUser(admin, FORUM_USER, FORUM_PASS, 'Forum Demo');
  // forum_post() bounces users without a valid email straight to their profile.
  await callKw(admin, 'res.users', 'write', [[userId], { email: `${FORUM_USER}@example.com` }]);

  // Drop anything a previous run left behind. Without this the fixture's posts
  // pile up in the dev database and the shipped docs screenshots show the same
  // question three times.
  const stale: number[] = await callKw(admin, 'forum.post', 'search', [[['create_uid', '=', userId]]]);
  if (stale.length) await callKw(admin, 'forum.post', 'unlink', [stale]);
});

test.afterAll(async () => {
  if (created.length) await callKw(admin, 'forum.post', 'unlink', [created]);
});

// ---------------------------------------------------------------- behaviour

test('/forum opens the forum itself, with no room to pick first', async ({ page }) => {
  const res = await page.goto(`${BASE}/forum`, { waitUntil: 'load' });
  expect(res?.status()).toBe(200);
  await expect(page).toHaveURL(new RegExp(`/forum/${forum.slug}$`));
  // `discussions` mode is what lets a thread take more than one reply per person;
  // the Q&A half is carried by forum.post.topic_type instead.
  expect(forum.mode).toBe('discussions');
});

test('forum pages carry the TVBO header, footer and palette', async ({ page }) => {
  await page.goto(`${BASE}/forum/${forum.slug}`, { waitUntil: 'load' });
  await expect(page.locator('header a.navbar-brand')).toContainText('The Virtual Brain Ontology');
  await expect(page.locator('header a.nav-link[href="/forum"]')).toHaveText('Community');
  await expect(page.locator('footer')).toContainText('Charité');

  // The palette must reach Odoo's own SCSS rather than being patched per page.
  // Bootstrap 5.3 resolves button colours through custom properties, so assert
  // on --btn-bg (backgroundColor is masked on hidden/overridden buttons).
  const btnBg = await page.evaluate(() => {
    const el = document.createElement('button');
    el.className = 'btn btn-primary';
    document.body.appendChild(el);
    const v = getComputedStyle(el).getPropertyValue('--btn-bg').trim();
    el.remove();
    return v;
  });
  expect(btnBg.toLowerCase(), 'btn-primary should use the TVBO palette').toBe('#3498db');
});

test('Odoo\'s stock palette is fully replaced in the frontend bundle', async ({ page }) => {
  await page.goto(`${BASE}/forum`, { waitUntil: 'load' });
  const href = await page.locator('link[href*="web.assets_frontend"]').first().getAttribute('href');
  expect(href, 'frontend asset bundle should be linked').toBeTruthy();
  const css = await (await page.request.get(new URL(href!, BASE).toString())).text();
  expect(css.toLowerCase(), 'TVBO blue should be compiled into the bundle').toContain('#3498db');
  expect(css.toLowerCase(), "Odoo's stock purple should be gone").not.toContain('714b67');
});

test('a topic carries its kind through the index and the thread', async ({ page }) => {
  const questionId = await createPost({
    name: 'Why do my connectome weights go NaN after export?',
    content: '<p>Normalization looks fine in the notebook but the exported YAML blows up.</p>',
    topic_type: 'question',
  });
  const discussionId = await createPost({
    name: 'Is anyone fitting E/I balance to resting-state FC?',
    content: '<p>Curious which cost functions people settled on.</p>',
    topic_type: 'discussion',
  });

  await page.goto(`${BASE}/forum/${forum.slug}`, { waitUntil: 'load' });
  await expect(page.locator('.tvbo-tt-badge--question').first()).toBeVisible();
  await expect(page.locator('.tvbo-tt-badge--discussion').first()).toBeVisible();

  await page.goto(`${BASE}/forum/${forum.slug}/${questionId}`, { waitUntil: 'load' });
  await expect(page.locator('.tvbo-tt-badge--question')).toBeVisible();
  await page.goto(`${BASE}/forum/${forum.slug}/${discussionId}`, { waitUntil: 'load' });
  await expect(page.locator('.tvbo-tt-badge--discussion')).toBeVisible();
});

test('the index filters by kind', async ({ page }) => {
  await page.goto(`${BASE}/forum/${forum.slug}?filters=discussions`, { waitUntil: 'load' });
  await expect(page.locator('.tvbo-tt-badge--question')).toHaveCount(0);
  await expect(page.locator('.tvbo-tt-badge--discussion').first()).toBeVisible();

  await page.goto(`${BASE}/forum/${forum.slug}?filters=questions`, { waitUntil: 'load' });
  await expect(page.locator('.tvbo-tt-badge--discussion')).toHaveCount(0);
  await expect(page.locator('.tvbo-tt-badge--question').first()).toBeVisible();
});

test('only questions offer the accepted-answer flow', async ({ page }) => {
  const question = await createPost({
    name: 'Which integrator supports additive noise out of the box?',
    content: '<p>Comparing the available backends.</p>',
    topic_type: 'question',
  });
  const discussion = await createPost({
    name: 'What should the schema cover next?',
    content: '<p>Wishlist thread.</p>',
    topic_type: 'discussion',
  });
  for (const parent of [question, discussion]) {
    await createPost({ name: 'Re:', content: '<p>A reply.</p>', parent_id: parent });
  }

  expect(await signIn(page, ADMIN_LOGIN, ADMIN_PASSWORD)).toBeTruthy();
  await page.goto(`${BASE}/forum/${forum.slug}/${question}`, { waitUntil: 'load' });
  await expect(page.locator('.o_wforum_validate_toggler')).toHaveCount(1);
  await page.goto(`${BASE}/forum/${forum.slug}/${discussion}`, { waitUntil: 'load' });
  await expect(page.locator('.o_wforum_validate_toggler')).toHaveCount(0);
});

test('a discussion takes more than one reply from the same person', async () => {
  // Odoo's post_display assumes a single reply per user, which only holds in
  // `questions` mode — two of them used to make the thread page 500.
  const discussion = await createPost({
    name: 'Reproducibility practices for whole-brain models',
    content: '<p>How are people pinning their environments?</p>',
    topic_type: 'discussion',
  });
  for (const i of [1, 2]) {
    await createPost({ name: 'Re:', content: `<p>Reply ${i}.</p>`, parent_id: discussion });
  }

  const ctx = await newSession();
  await login(ctx, ADMIN_LOGIN, ADMIN_PASSWORD);
  const res = await ctx.get(`${BASE}/forum/${forum.slug}/${discussion}`);
  expect(res.status()).toBe(200);
  expect(await res.text()).toContain('tvbo-tt-badge--discussion');
});

test('a reply inherits the topic kind of its thread', async () => {
  const discussion = await createPost({
    name: 'Which atlas do you default to?',
    content: '<p>And why.</p>',
    topic_type: 'discussion',
  });
  const reply = await createPost({ name: 'Re:', content: '<p>DK, mostly.</p>', parent_id: discussion });
  const [post] = await callKw(admin, 'forum.post', 'read', [[reply], ['topic_type']]);
  expect(post.topic_type).toBe('discussion');
});

test('anonymous visitors can read but are sent to login to post', async ({ page }) => {
  const res = await page.goto(`${BASE}/forum/${forum.slug}`, { waitUntil: 'load' });
  expect(res?.status()).toBe(200);
  await page.goto(`${BASE}/forum/${forum.slug}/ask`, { waitUntil: 'load' });
  await expect(page).toHaveURL(/\/web\/login/);
});

test('the login-only /ask route stays out of the sitemap', async ({ page }) => {
  // Making /ask auth="public" lets Odoo enumerate it unless sitemap=False, which
  // would publish a URL that only ever 303s to the login page.
  const xml = await (await page.request.get(`${BASE}/sitemap.xml`)).text();
  expect(xml).not.toContain('/ask');
});

test('the welcome banner can actually be dismissed', async ({ page }) => {
  // Odoo 19 binds dismissal to .js_close_intro; Bootstrap's data-bs-dismiss does
  // nothing here because the banner's wrapper is a <section>, not an .alert.
  await page.goto(`${BASE}/forum/${forum.slug}`, { waitUntil: 'load' });
  const intro = page.locator('.forum_intro');
  await expect(intro).toBeVisible();
  // Retried because Odoo starts its interactions after load: a click that lands
  // first is simply swallowed, and the longer the post list the likelier that is.
  // onCloseIntroClick collapses the banner by adding .h-0, it does not remove it.
  await expect(async () => {
    await page.locator('.js_close_intro').first().click();
    await expect(intro).toHaveClass(/h-0/, { timeout: 1000 });
  }).toPass({ timeout: 15000 });
});

test('the post form offers both kinds, question first', async ({ page }) => {
  await setKarma(5);
  expect(await signIn(page, FORUM_USER, FORUM_PASS)).toBeTruthy();
  await page.goto(`${BASE}/forum/${forum.slug}/ask`, { waitUntil: 'load' });
  await expect(page.locator('input[name="topic_type"]')).toHaveCount(2);
  await expect(page.locator('input[name="topic_type"][value="question"]')).toBeChecked();
});

test('posting as a discussion stores it as one', async () => {
  // Submitted as a raw form POST rather than through the page: the content
  // field is a wysiwyg, and the point here is that the controller carries
  // topic_type onto the record, not that the editor works.
  await setKarma(5);
  const ctx = await newSession();
  await login(ctx, FORUM_USER, FORUM_PASS);

  const askHtml = await (await ctx.get(`${BASE}/forum/${forum.slug}/ask`)).text();
  const csrf = askHtml.match(/name="csrf_token"[^>]*value="([^"]+)"/)?.[1];
  expect(csrf, 'ask form should carry a csrf token').toBeTruthy();

  const title = 'Where should TVBO go in 2027?';
  const res = await ctx.post(`${BASE}/forum/${forum.slug}/new`, {
    form: { csrf_token: csrf!, post_name: title, content: '<p>Open thread on priorities.</p>', topic_type: 'discussion' },
    maxRedirects: 0,
  });
  expect(res.status()).toBe(303);

  const [post] = await callKw(
    admin, 'forum.post', 'search_read', [[['name', '=', title]], ['topic_type']],
  );
  expect(post.topic_type).toBe('discussion');
});

test('karma gates: 0 karma cannot ask, 3 karma can', async () => {
  const ctx = await newSession();
  await login(ctx, FORUM_USER, FORUM_PASS);

  await setKarma(0);
  await expect(
    callKw(ctx, 'forum.post', 'create', [{
      forum_id: forum.id,
      name: 'Karma gate probe (should fail)',
      content: '<p>probe</p>',
    }]),
    'a 0-karma account must not be able to ask',
  ).rejects.toThrow(/karma/i);

  // 3 karma is exactly what confirming an email address grants.
  await setKarma(3);
  const postId: number = await callKw(ctx, 'forum.post', 'create', [{
    forum_id: forum.id,
    name: 'How do I add a custom Dynamics to TVBO?',
    content: '<p>I want to add a two-variable oscillator to the schema. Where do the state variables and parameters go?</p>',
  }]);
  expect(postId).toBeGreaterThan(0);

  // karma_post = 5, so this first question is held for moderation.
  const [post] = await callKw(admin, 'forum.post', 'read', [[postId], ['state']]);
  expect(post.state, 'first question from a new account should be pending').toBe('pending');
});

test('past the karma_post threshold, questions publish immediately', async () => {
  const ctx = await newSession();
  await login(ctx, FORUM_USER, FORUM_PASS);
  await setKarma(5);
  const postId: number = await callKw(ctx, 'forum.post', 'create', [{
    forum_id: forum.id,
    name: 'Which backend should I use for stochastic integration?',
    content: '<p>Comparing the available integrators — which backend supports additive noise out of the box?</p>',
  }]);
  const [post] = await callKw(admin, 'forum.post', 'read', [[postId], ['state']]);
  expect(post.state).toBe('active');
});

// -------------------------------------------------------------- screenshots

// Captured signed-out on purpose: that is what a first-time visitor sees.
test('capture: the forum index', async ({ page }) => {
  await page.goto(`${BASE}/forum`, { waitUntil: 'load' });
  await settle();
  await shot(page, 'forum-index.webp');
});

test('capture: writing a post', async ({ page }) => {
  await setKarma(5);
  // The karma-gate test leaves a post awaiting moderation, and Odoo replaces the
  // whole form with "you already have a pending post" while one exists.
  const pending: number[] = await callKw(
    admin, 'forum.post', 'search', [[['create_uid', '=', userId], ['state', '=', 'pending']]]);
  if (pending.length) await callKw(admin, 'forum.post', 'unlink', [pending]);
  expect(await signIn(page, FORUM_USER, FORUM_PASS)).toBeTruthy();
  await page.goto(`${BASE}/forum/${forum.slug}/ask`, { waitUntil: 'load' });
  await settle();
  await shot(page, 'forum-ask.webp');
});

test('capture: a question thread', async ({ page }) => {
  const ids: number[] = await callKw(
    admin, 'forum.post', 'search',
    [[['forum_id', '=', forum.id], ['parent_id', '=', false], ['state', '=', 'active'],
      ['topic_type', '=', 'question']]],
    { limit: 1 },
  );
  test.skip(!ids.length, 'no published question to capture');
  await page.goto(`${BASE}/forum/${forum.slug}/${ids[0]}`, { waitUntil: 'load' });
  await settle();
  await shot(page, 'forum-question.webp');
});
