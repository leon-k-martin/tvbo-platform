import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import * as path from 'node:path';

// tests/e2e/helpers -> repo root
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');
const PYTHON = process.env.TVBO_PYTHON || path.join(REPO_ROOT, '.venv', 'bin', 'python');
const HARNESS = path.join(REPO_ROOT, 'tests', 'validate_experiment.py');

export interface ValidationCheck {
  path: string;
  ok: boolean;
  error?: string;
  errors?: Array<{ loc: string; type: string; msg: string }>;
  advisory?: boolean;
  skipped?: boolean;
  id?: number | null;
}

export interface ValidationReport {
  source: string;
  target: string;
  valid: boolean;
  checks: ValidationCheck[];
}

/**
 * Validate YAML using the tvbo-native Python harness
 * (tests/validate_experiment.py). The Pydantic check is authoritative; the
 * optional runtime check is advisory and does not affect `valid`.
 */
export function validateYaml(
  yamlText: string,
  target = 'SimulationExperiment',
  { runtime = false }: { runtime?: boolean } = {},
): ValidationReport {
  const dir = mkdtempSync(path.join(tmpdir(), 'tvbo-yaml-'));
  const file = path.join(dir, 'experiment.yaml');
  writeFileSync(file, yamlText, 'utf-8');

  const args = [HARNESS, file, '--target', target];
  if (runtime) args.push('--runtime');

  let out: string;
  try {
    out = execFileSync(PYTHON, args, { encoding: 'utf-8' });
  } catch (e: any) {
    // Non-zero exit (invalid YAML) still prints the JSON report to stdout.
    out = (e.stdout && e.stdout.toString()) || '{}';
  }
  return JSON.parse(out) as ValidationReport;
}

/**
 * Validate many YAML strings in a single Python process. The tvbo import is the
 * expensive part, so paying it once for the whole batch is far faster than
 * spawning the harness per file. Returns one report per item, in order.
 */
export function validateYamls(
  items: Array<{ text: string; target?: string; label?: string }>,
  { runtime = false }: { runtime?: boolean } = {},
): ValidationReport[] {
  const args = [HARNESS, '--batch'];
  if (runtime) args.push('--runtime');
  const input = JSON.stringify(items);

  let out: string;
  try {
    out = execFileSync(PYTHON, args, {
      input,
      encoding: 'utf-8',
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch (e: any) {
    // Non-zero exit (some item invalid) still prints the JSON array to stdout.
    out = (e.stdout && e.stdout.toString()) || '[]';
  }
  return JSON.parse(out) as ValidationReport[];
}

/** Compact human-readable summary of failed checks, for assertion messages. */
export function summarize(report: ValidationReport): string {
  return report.checks
    .filter((c) => !c.ok && !c.advisory && !c.skipped)
    .map((c) => `${c.path}: ${c.error}${c.errors ? ' ' + JSON.stringify(c.errors) : ''}`)
    .join('; ');
}
