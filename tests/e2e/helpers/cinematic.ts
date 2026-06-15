/**
 * Cinematic helpers for screencast-style e2e demos.
 *
 * Adds a red-circle cursor that follows the (real) Playwright mouse, draws a
 * red-square highlight around each element before we interact with it, shows a
 * narration caption, and moves/types slowly so a viewer can follow along.
 *
 * Usage:
 *   const { context, page } = await openCinematicPage(browser, { storageState, videoDir });
 *   await caption(page, 'Browsing the Knowledge Graph');
 *   await click(page, '#someButton', { caption: 'Open in Experiment Builder' });
 *   await type(page, '#field', 'hello', { caption: 'Name the experiment' });
 *   await finish(context, page, '/abs/path/video.webm');
 */
import { Browser, BrowserContext, Page, Locator } from '@playwright/test';

export const VIEWPORT = { width: 1366, height: 900 };

/** Injected into every document: a red-circle cursor that tracks the mouse. */
/* eslint-disable */
function CURSOR_INIT() {
  const CID = '__cine_cursor__';
  // Idempotent per document: addInitScript runs this on every navigation and
  // ensureCursor() re-invokes it after each goto — without this guard each call
  // would stack another setInterval + document listeners (a per-page leak).
  if ((window as any).__cineInit) return;
  (window as any).__cineInit = true;
  function ensure() {
    if (!document.body && !document.documentElement) return;
    if (document.getElementById(CID)) return;
    const c = document.createElement('div');
    c.id = CID;
    const s = c.style as any;
    s.position = 'fixed';
    s.left = '50%';
    s.top = '50%';
    s.width = '24px';
    s.height = '24px';
    s.marginLeft = '-12px';
    s.marginTop = '-12px';
    s.borderRadius = '50%';
    s.border = '3px solid #ff2b2b';
    s.background = 'rgba(255,43,43,0.22)';
    s.boxShadow = '0 0 0 2px rgba(255,255,255,0.85), 0 0 14px rgba(255,43,43,0.7)';
    s.zIndex = '2147483647';
    s.pointerEvents = 'none';
    s.transition = 'transform 0.08s ease-out';
    s.willChange = 'left, top, transform';
    (document.body || document.documentElement).appendChild(c);
    document.addEventListener(
      'mousemove',
      (e) => {
        c.style.left = e.clientX + 'px';
        c.style.top = e.clientY + 'px';
      },
      true,
    );
    document.addEventListener('mousedown', () => (c.style.transform = 'scale(0.55)'), true);
    document.addEventListener('mouseup', () => (c.style.transform = 'scale(1)'), true);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensure);
  } else {
    ensure();
  }
  setInterval(ensure, 400);
}
/* eslint-enable */

/** Create a video-recording, logged-in (optional) page with the cursor installed. */
export async function openCinematicPage(
  browser: Browser,
  opts: { storageState?: any; videoDir: string },
): Promise<{ context: BrowserContext; page: Page }> {
  const context = await browser.newContext({
    viewport: VIEWPORT,
    storageState: opts.storageState,
    recordVideo: { dir: opts.videoDir, size: VIEWPORT },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.addInitScript(CURSOR_INIT);
  return { context, page };
}

/** Ensure the cursor exists on the current document (after a navigation). */
export async function ensureCursor(page: Page): Promise<void> {
  await page.evaluate(CURSOR_INIT).catch(() => {});
}

/** Show / update the narration caption banner. */
export async function caption(page: Page, text: string): Promise<void> {
  await page
    .evaluate((t) => {
      const ID = '__cine_caption__';
      let el = document.getElementById(ID);
      if (!el) {
        el = document.createElement('div');
        el.id = ID;
        const s = el.style as any;
        s.position = 'fixed';
        s.left = '50%';
        s.bottom = '30px';
        s.transform = 'translateX(-50%)';
        s.maxWidth = '82%';
        s.padding = '13px 24px';
        s.background = 'rgba(17,18,28,0.93)';
        s.color = '#fff';
        s.font = '600 19px/1.45 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif';
        s.borderRadius = '12px';
        s.zIndex = '2147483646';
        s.pointerEvents = 'none';
        s.boxShadow = '0 8px 28px rgba(0,0,0,0.45)';
        s.border = '1px solid rgba(255,255,255,0.16)';
        s.textAlign = 'center';
        (document.body || document.documentElement).appendChild(el);
      }
      el.textContent = t;
      (el.style as any).opacity = '1';
    }, text)
    .catch(() => {});
}

/** Draw a red-square highlight around a locator's current bounding box. */
export async function highlight(page: Page, loc: Locator, holdMs = 900): Promise<void> {
  const box = await loc.boundingBox().catch(() => null);
  if (!box) return;
  await page
    .evaluate(
      ({ b, hold }) => {
        const ID = '__cine_hl__';
        let el = document.getElementById(ID);
        if (!el) {
          el = document.createElement('div');
          el.id = ID;
          (document.body || document.documentElement).appendChild(el);
        }
        const s = el.style as any;
        s.position = 'fixed';
        s.left = b.x - 6 + 'px';
        s.top = b.y - 6 + 'px';
        s.width = b.width + 12 + 'px';
        s.height = b.height + 12 + 'px';
        s.border = '3px solid #ff2b2b';
        s.borderRadius = '7px';
        s.boxShadow = '0 0 0 3px rgba(255,43,43,0.22), 0 0 0 9999px rgba(10,10,15,0.06)';
        s.background = 'rgba(255,43,43,0.06)';
        s.zIndex = '2147483645';
        s.pointerEvents = 'none';
        s.transition = 'all 0.18s ease';
        s.opacity = '1';
        const w = window as any;
        clearTimeout(w.__cineHl);
        w.__cineHl = setTimeout(() => ((el as HTMLElement).style.opacity = '0'), hold);
      },
      { b: box, hold: holdMs },
    )
    .catch(() => {});
}

const pause = (page: Page, ms: number) => page.waitForTimeout(ms);

/** Scroll an element into view via JS — no actionability/stability wait (the
 *  builder's live 3D graph keeps the page "unstable", which makes Playwright's
 *  scrollIntoViewIfNeeded() block for the full action timeout). */
async function scrollTo(loc: Locator): Promise<void> {
  await loc.evaluate((el) => (el as HTMLElement).scrollIntoView({ block: 'center', inline: 'center' })).catch(() => {});
}

/** Animate the (real) mouse to the centre of a locator, so the cursor follows. */
export async function moveTo(page: Page, loc: Locator): Promise<void> {
  await scrollTo(loc);
  const box = await loc.boundingBox().catch(() => null);
  if (!box) return;
  // Few steps: each mouse.move step dispatches a mousemove the page must hit-test;
  // on heavy DOMs (loaded experiment + editors) many steps crawl.
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 6 });
}

/** Slow, narrated click: caption → highlight → move cursor → click. Uses a
 *  forced click (skips actionability/stability waits that the 3D graph breaks). */
export async function click(
  page: Page,
  selector: string | Locator,
  opts: { caption?: string; hold?: number } = {},
): Promise<void> {
  const loc = typeof selector === 'string' ? page.locator(selector).first() : selector;
  await loc.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  await scrollTo(loc);
  if (opts.caption) await caption(page, opts.caption);
  await highlight(page, loc, 700);
  await moveTo(page, loc); // the cursor travel IS the pacing — no dead pause
  await loc.click({ force: true, timeout: 6000 }).catch(() => {});
  await pause(page, opts.hold ?? 280);
}

/** Slow, narrated typing into a field. Sets the value via evaluate() (no
 *  actionability / stability wait) so it never hangs when the page re-renders
 *  (the live 3D graph / YAML preview cause continuous reflow that stalls
 *  fill()/pressSequentially). Keeps a typed-on feel via incremental substrings. */
export async function type(
  page: Page,
  selector: string,
  text: string,
  opts: { caption?: string } = {},
): Promise<void> {
  const loc = page.locator(selector).first();
  await loc.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  await scrollTo(loc);
  if (opts.caption) await caption(page, opts.caption);
  await highlight(page, loc);
  await moveTo(page, loc);
  const set = (v: string, change = false) =>
    loc
      .evaluate(
        (el, args) => {
          const e = el as HTMLInputElement | HTMLTextAreaElement;
          e.focus();
          e.value = args.v;
          e.dispatchEvent(new Event('input', { bubbles: true }));
          if (args.change) e.dispatchEvent(new Event('change', { bubbles: true }));
        },
        { v, change },
      )
      .catch(() => {});
  const steps = Math.min(text.length, 9);
  for (let i = 1; i <= steps; i++) {
    await set(text.slice(0, Math.max(1, Math.round((text.length * i) / steps))));
    await pause(page, 45);
  }
  await set(text, true);
  await pause(page, 200);
}

/** Smoothly scroll the window by a delta (so panning reads as deliberate). */
export async function scrollBy(page: Page, dy: number): Promise<void> {
  await page.mouse.wheel(0, dy);
  await pause(page, 600);
}

/** Finalise: close the page+context (flushes the video) and produce an MP4
 *  (converts the recorded .webm via ffmpeg; falls back to .webm if ffmpeg
 *  is unavailable). `trimStart` (seconds) drops the leading portion — used to
 *  cut a slow initial page-load that can't be sped up. Pass a destPath .mp4. */
export async function finish(
  context: BrowserContext,
  page: Page,
  destPath: string,
  trimStart = 0,
): Promise<string> {
  const video = page.video();
  await page.close();
  await context.close();
  const fs = await import('node:fs');
  const path = await import('node:path');
  const { execFileSync } = await import('node:child_process');
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  if (!video) return '';
  const src = await video.path();
  for (let i = 0; i < 30; i++) {
    if (fs.existsSync(src) && fs.statSync(src).size > 2048) break;
    await new Promise((r) => setTimeout(r, 200));
  }
  if (destPath.endsWith('.mp4')) {
    try {
      const ss = trimStart > 0.2 ? ['-ss', trimStart.toFixed(2)] : [];
      execFileSync(
        'ffmpeg',
        ['-y', ...ss, '-i', src, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-crf', '22', destPath],
        { stdio: 'ignore' },
      );
      return destPath;
    } catch {
      const webm = destPath.replace(/\.mp4$/, '.webm');
      fs.copyFileSync(src, webm);
      return webm;
    }
  }
  fs.copyFileSync(src, destPath);
  return destPath;
}
