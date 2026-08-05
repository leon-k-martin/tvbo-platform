import { execFileSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { Page } from '@playwright/test';

/**
 * Write a documentation screenshot as lossless WebP.
 *
 * Playwright encodes PNG or JPEG only, and these are 2880x1800 retina captures:
 * ~1.1 MB each as PNG against ~160 KB as lossless WebP, bit-for-bit identical.
 * The docs pages were shipping 11 MB of screenshots, uncompressed, because the
 * platform ingress adds no compression (see tvbo/controllers/assets.py).
 *
 * Requires `cwebp` (libwebp) on PATH — the same media toolchain
 * process-docs-videos.sh already needs.
 */
let checked = false;

/** Fail once, with the fix, instead of ENOENT inside every screenshot test. */
function requireCwebp(): void {
  if (checked) return;
  try {
    execFileSync('cwebp', ['-version'], { stdio: 'ignore' });
  } catch {
    throw new Error('cwebp (libwebp) not found on PATH — install it (brew install webp)');
  }
  checked = true;
}

export async function writeShot(page: Page, dir: string, name: string): Promise<void> {
  if (!name.endsWith('.webp')) throw new Error(`screenshot must be .webp: ${name}`);
  requireCwebp();
  const tmp = path.join(os.tmpdir(), `docshot-${process.pid}-${name}.png`);
  await page.screenshot({ path: tmp });
  try {
    execFileSync('cwebp', ['-quiet', '-lossless', '-z', '9', tmp, '-o', path.join(dir, name)]);
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}
