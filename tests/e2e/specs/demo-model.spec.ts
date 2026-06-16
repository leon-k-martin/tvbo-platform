import { test, expect } from '@playwright/test';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as ci from '../helpers/cinematic';

/**
 * VIDEO 3 — "specify a simple model", in the same dark IDE → IPython style as
 * the Python demo (Video 2):
 *   1. the model as YAML (left) + an empty editor (right)
 *   2. the same model TYPED in Python via the Dynamics class (char-by-char)
 *   3. the editor slides LEFT; an IPython "Out[]" window appears on the right
 *   4. execute: define → run → exp.run().plot(type="phase") (the Lorenz
 *      attractor) → a windowed state-variable timeseries
 *
 * Inputs (generated alongside this spec):
 *   demo-output/lorenz_model.yaml, demo_model.py, demo_model_phase.png,
 *   demo_model_ts.png
 */
const OUT = path.resolve(__dirname, '..', 'demo-output');
const VIDEO_DIR = path.join(OUT, 'video-raw-model');
const YAML_PATH = path.join(OUT, 'lorenz_model.yaml');
const PY_PATH = path.join(OUT, 'demo_model.py');
const PHASE_PATH = path.join(OUT, 'demo_model_phase.png');
const TS_PATH = path.join(OUT, 'demo_model_ts.png');
const HTML_PATH = path.join(OUT, 'model_demo.html');

const esc = (s: string) => (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function hlYaml(line: string): string {
  if (/^\s*#/.test(line)) return `<span class="cm">${esc(line)}</span>`;
  const m = line.match(/^(\s*)([\w.$-]+)(:)(.*)$/);
  if (m) {
    const val = esc(m[4]).replace(/(-?\d+(?:\.\d+)?)\s*$/, '<span class="ynum">$1</span>');
    return `${m[1]}<span class="yk">${esc(m[2])}</span><span class="yc">:</span>${val}`;
  }
  const li = line.match(/^(\s*)(-\s)(.*)$/);
  if (li) return `${li[1]}<span class="yc">- </span>${esc(li[3])}`;
  return esc(line);
}

function buildHtml(yaml: string, code: string, phaseB64: string, tsB64: string): string {
  const yamlLines = yaml.replace(/\s+$/, '').split('\n');
  const yamlPreview = yamlLines.slice(0, 40).map(hlYaml).join('\n') + (yamlLines.length > 40 ? '\n  …' : '');
  return `<!doctype html><html><head><meta charset="utf-8"><title>Specify a model</title>
<style>
  *{box-sizing:border-box} html,body{margin:0;height:100%;background:#0d1117;color:#c9d1d9;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
  .wrap{display:flex;flex-direction:column;height:100vh;padding:24px 30px;gap:16px}
  h1{margin:0;font-size:23px;font-weight:700;color:#fff}
  h1 .sub{font-weight:500;font-size:15px;color:#8b949e;margin-left:10px}
  .cols{display:flex;gap:20px;flex:1;min-height:0}
  .panel{background:#161b22;border:1px solid #30363d;border-radius:12px;display:flex;flex-direction:column;
    min-height:0;min-width:0;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,.35);
    transition:flex-grow .9s cubic-bezier(.4,0,.2,1),opacity .6s ease}
  #yamlPanel{flex:1} #codePanel{flex:1} #outPanel{flex:0;opacity:0;border-color:transparent}
  .bar{padding:10px 16px;background:#0d1117;border-bottom:1px solid #30363d;font-size:13px;color:#8b949e;
    display:flex;align-items:center;gap:8px}
  .dot{width:11px;height:11px;border-radius:50%;display:inline-block}.r{background:#ff5f56}.y{background:#ffbd2e}.g{background:#27c93f}
  .fname{margin-left:8px;color:#c9d1d9;font-weight:600}
  pre,.code{margin:0;padding:16px 18px;overflow:auto;flex:1;font-size:14px;line-height:1.65;
    font-family:"SF Mono",Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
  .kw{color:#ff7b72}.str{color:#a5d6ff}.cm{color:#8b949e;font-style:italic}.fn{color:#d2a8ff}.cls{color:#7ee787}
  .yk{color:#79c0ff}.yc{color:#8b949e}.ynum{color:#f0883e}
  .caret{color:#58a6ff;animation:blink 1s step-end infinite}@keyframes blink{50%{opacity:0}}
  .cl{border-radius:5px;padding:0 6px;transition:background .25s}
  .cl.active{background:rgba(255,43,43,.16);box-shadow:inset 3px 0 0 #ff2b2b}
  #outPanel .bar .fname::after{content:" — IPython";color:#8b949e;font-weight:400}
  #out{padding:14px 16px;overflow:auto;flex:1;background:#0d1117}
  .cell{display:flex;gap:12px;opacity:0;transform:translateY(8px);transition:all .45s ease;margin-bottom:16px}
  .cell.show{opacity:1;transform:none}
  .prompt{flex:0 0 64px;text-align:right;font-family:"SF Mono",Menlo,monospace;font-size:13px;padding-top:2px}
  .prompt.out{color:#d2456e}
  .cellbody{flex:1;min-width:0}
  .ok{color:#3fb950;font-family:"SF Mono",Menlo,monospace;font-size:13.5px}
  .outimg{max-width:100%;border-radius:8px;background:#fff;padding:8px;display:block;border:1px solid #21262d}
</style></head><body>
<div class="wrap">
  <h1>Specify a model in TVBO <span class="sub">— parameters + state variables + ODEs</span></h1>
  <div class="cols">
    <div class="panel" id="yamlPanel">
      <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
        <span class="fname">lorenz_model.yaml</span></div>
      <pre id="yaml">${yamlPreview}</pre>
    </div>
    <div class="panel" id="codePanel">
      <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
        <span class="fname">model.py</span></div>
      <div class="code" id="code"></div>
    </div>
    <div class="panel" id="outPanel">
      <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
        <span class="fname">output</span></div>
      <div id="out">
        <div class="cell" id="s-define"><span class="prompt out">Out[1]:</span>
          <div class="cellbody"><span class="ok">&#10003; Dynamics: LorenzAttractor — 3 state variables (X, Y, Z), 3 parameters</span></div></div>
        <div class="cell" id="s-phase"><span class="prompt out">Out[2]:</span>
          <div class="cellbody"><img class="outimg" id="phaseImg" src="data:image/png;base64,${phaseB64}"/></div></div>
        <div class="cell" id="s-ts"><span class="prompt out">Out[3]:</span>
          <div class="cellbody"><img class="outimg" id="tsImg" src="data:image/png;base64,${tsB64}"/></div></div>
      </div>
    </div>
  </div>
</div>
<script>
  const RAW = ${JSON.stringify(code.replace(/\s+$/, ''))};
  function hlLine(line){
    const E=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    if(line.trimStart().startsWith('#')) return '<span class="cm">'+E(line)+'</span>';
    const strs=[]; let s=line.replace(/("[^"]*"|'[^']*')/g,m=>{strs.push(m);return ' \\u0000'+(strs.length-1)+'\\u0000 ';});
    s=E(s);
    s=s.replace(/\\b(from|import|as|return|def|class|None|True|False|with|for|in|if|else)\\b/g,'<span class="kw">$1</span>');
    s=s.replace(/\\b([A-Z][A-Za-z0-9_]+)\\b/g,'<span class="cls">$1</span>');
    s=s.replace(/\\.([a-z_][A-Za-z0-9_]*)(\\s*\\()/g,'.<span class="fn">$1</span>$2');
    s=s.replace(/\\u0000(\\d+)\\u0000/g,(_m,i)=>'<span class="str">'+E(strs[+i])+'</span>');
    return s;
  }
  function hl(code){ return code.split('\\n').map(hlLine).join('\\n'); }
  function lineId(l){ return l.indexOf('Dynamics(')>=0?'ln-define':l.indexOf('type="phase"')>=0?'ln-phase':l.indexOf('.sel(time')>=0?'ln-ts':''; }
  function renderLines(code){ return code.split('\\n').map(function(l){ var id=lineId(l);
    return '<div class="cl"'+(id?' id="'+id+'"':'')+'>'+(l?hlLine(l):'&nbsp;')+'</div>'; }).join(''); }
  window.demo = {
    typeCode(speed){ const el=document.getElementById('code');
      return new Promise(res=>{ let i=0; const tick=()=>{ i++;
        el.innerHTML=hl(RAW.slice(0,i))+'<span class="caret">▋</span>';
        el.scrollTop=el.scrollHeight;
        if(i>=RAW.length){ el.innerHTML=renderLines(RAW); res(); return; }
        setTimeout(tick, RAW[i-1]==='\\n' ? speed*6 : speed);
      }; tick(); }); },
    activeLine(id){ document.querySelectorAll('.cl.active').forEach(e=>e.classList.remove('active'));
      const el=document.getElementById(id); if(el) el.classList.add('active'); },
    shift(){ const y=document.getElementById('yamlPanel'),o=document.getElementById('outPanel');
      y.style.flexGrow='0';y.style.opacity='0';o.style.flexGrow='1.35';o.style.opacity='1';o.style.borderColor='#30363d'; },
    reveal(id){ const el=document.getElementById(id); if(el) el.classList.add('show'); },
    scrollTo(id){ const el=document.getElementById(id); if(el) el.scrollIntoView({block:'center'}); }
  };
</script></body></html>`;
}

test('Model demo: specify a Dynamics → run → attractor + timeseries', async ({ browser }) => {
  test.setTimeout(180_000);
  for (const f of [YAML_PATH, PY_PATH, PHASE_PATH, TS_PATH]) {
    if (!fs.existsSync(f)) throw new Error(`missing input ${f}`);
  }
  const yaml = fs.readFileSync(YAML_PATH, 'utf8');
  const code = fs.readFileSync(PY_PATH, 'utf8');
  const phaseB64 = fs.readFileSync(PHASE_PATH).toString('base64');
  const tsB64 = fs.readFileSync(TS_PATH).toString('base64');
  fs.writeFileSync(HTML_PATH, buildHtml(yaml, code, phaseB64, tsB64));

  const { context, page } = await ci.openCinematicPage(browser, { videoDir: VIDEO_DIR });
  await page.goto('file://' + HTML_PATH, { waitUntil: 'domcontentloaded' });
  await ci.ensureCursor(page);
  const t0 = Date.now();
  const mark = (s: string) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${s}`);
  await page.waitForTimeout(700);

  // 1. the model as YAML
  await ci.caption(page, 'A model in TVBO: parameters, state variables and their ODEs');
  await ci.highlight(page, page.locator('#yamlPanel'), 2200);
  await page.mouse.move(360, 320, { steps: 22 });
  await page.waitForTimeout(1800);

  // 2. TYPE the same model in Python via the Dynamics class
  await ci.caption(page, 'Specify the same model in Python with the Dynamics class');
  await page.mouse.move(1000, 300, { steps: 22 });
  await page.evaluate(() => (window as any).demo.typeCode(24));
  mark('typed');
  await page.waitForTimeout(700);

  // 3. shift: editor → left, IPython output → right
  await ci.caption(page, 'Run it — the output appears in an IPython session');
  await page.evaluate(() => (window as any).demo.shift());
  await page.waitForTimeout(1200);

  // 4a. define
  await ci.caption(page, '1 — Dynamics(...): the model is now a first-class object');
  await page.evaluate(() => { (window as any).demo.activeLine('ln-define'); (window as any).demo.reveal('s-define'); });
  await page.waitForTimeout(1300);

  // 4b. phase portrait — run() then plot the attractor
  await ci.caption(page, '2 — run it and plot(type="phase"): the Lorenz attractor');
  await page.evaluate(() => { (window as any).demo.activeLine('ln-phase'); (window as any).demo.reveal('s-phase'); (window as any).demo.scrollTo('s-phase'); });
  await page.waitForTimeout(800);
  mark('phase');
  await ci.highlight(page, page.locator('#phaseImg'), 4000);
  await page.waitForTimeout(4400);

  // 4c. timeseries
  await ci.caption(page, '3 — the state variables X, Y, Z over time');
  await page.evaluate(() => { (window as any).demo.activeLine('ln-ts'); (window as any).demo.reveal('s-ts'); (window as any).demo.scrollTo('s-ts'); });
  await page.waitForTimeout(800);
  mark('timeseries');
  await ci.highlight(page, page.locator('#tsImg'), 3800);
  await page.waitForTimeout(4200);

  await ci.caption(page, 'A complete model — specified, simulated and plotted in a handful of lines');
  await page.waitForTimeout(1800);

  const videoPath = await ci.finish(context, page, path.join(OUT, 'tvbo-specify-a-model.mp4'));
  mark('done -> ' + videoPath);
  expect(fs.existsSync(HTML_PATH)).toBeTruthy();
  // eslint-disable-next-line no-console
  console.log('VIDEO3', videoPath);
});
