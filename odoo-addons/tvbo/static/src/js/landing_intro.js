/* Landing scope: plays back a real 2-D parameter sweep of one tvbo experiment.
 *
 * Nothing here simulates anything. Every frame comes from
 * scripts/landing_experiment.yaml run through exp.run("tvboptim") by
 * scripts/bake_landing_scope.py — 20 cells over the SupHopf bifurcation
 * parameter against global coupling.
 *
 * The brain follows tvbase_viewer's BrainModel: an *opaque* fsaverage5
 * midthickness cortex with `vertexColors` on a MeshStandardMaterial, grey where a
 * region is quiet and hot where it is active, under one ambient and two
 * directional lights. The activity paints the surface itself rather than floating
 * inside a transparent shell.
 *
 * WebGL is optional: without it the spec, the sweep readouts and the generated
 * code all still work, so a missing three.js costs the brain and nothing else.
 */
(function () {
  'use strict';

  var S = window.TVBO_SCOPE;
  var host = document.querySelector('[data-tvbo-scope]');
  if (!S || !host) return;

  var sec = host.closest('section') || document;
  var netCv = host.querySelector('[data-scope-net]');
  var trCv = host.querySelector('[data-scope-trace]');
  var slA = sec.querySelector('[data-scope-slider-a]');
  var slG = sec.querySelector('[data-scope-slider-g]');
  var rBar = sec.querySelector('[data-scope-rbar]');
  var tabsEl = sec.querySelector('[data-scope-tabs]');
  var codeEl = sec.querySelector('[data-scope-code]');
  var readA = sec.querySelectorAll('[data-scope-a]');
  var readG = sec.querySelectorAll('[data-scope-g]');
  var readFC = sec.querySelector('[data-scope-fc]');
  if (!netCv || !trCv) return;

  var THREE = window.THREE;
  var N = S.labels.length;
  var NA = S.sweepA.length, NG = S.sweepG.length;
  var BS = S.brainSamples, TS = S.traceSamples;
  var NL = S.traceLanes.length;
  var cell = S.sweepA.indexOf(0.01) * NG + S.sweepG.indexOf(0.05);
  if (cell < 0) cell = 0;

  function bytes(b64) {
    var s = atob(b64), a = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
    return a;
  }

  var frames = null, laneGain = null;
  /** Brain sample: 4-bit, packed two per byte, high nibble first. */
  function brainAt(c, t, node) {
    var k = (c * BS + t) * N + node;
    var b = frames.brain[k >> 1];
    return ((k & 1) ? (b & 15) : (b >> 4)) / 15;
  }
  function traceAt(c, t, lane) {
    return frames.traces[(c * TS + t) * NL + lane] / 127.5 - 1;
  }
  function adoptFrames() {
    var F = window.TVBO_SCOPE_FRAMES;
    if (!F || frames) return;
    frames = { brain: bytes(F.brain), traces: bytes(F.traces) };
    /* per-cell, per-lane auto-range: the bake normalises by the 99.5th percentile
       across all 84 regions, so a single region fills only part of its lane */
    laneGain = new Float32Array(NA * NG * NL);
    for (var c = 0; c < NA * NG; c++) {
      for (var k = 0; k < NL; k++) {
        var m = 0;
        for (var t = 0; t < TS; t++) m = Math.max(m, Math.abs(traceAt(c, t, k)));
        laneGain[c * NL + k] = 0.94 / (m || 1);
      }
    }
  }

  /* -------------------------------------------------------------------- brain */
  var renderer, scene, camera, controls, grp, pivot;
  var shellMesh, matSurface, matGlass, netGroup, core, dummy, tint;
  var view = 'surface';
  var shellBuilt = false;
  var gl = !!THREE;
  if (gl) {
    try {
      renderer = new THREE.WebGLRenderer({ canvas: netCv, antialias: true, alpha: true });
    } catch (e) { gl = false; }
  }

  if (gl) {
    renderer.setPixelRatio(Math.min(1.75, window.devicePixelRatio || 1));
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(50, 1, 0.05, 40);

    grp = new THREE.Group();
    grp.rotation.x = -Math.PI / 2;   // anatomical superior -> scene up
    scene.add(grp);
    /* cortex and connectome share one pivot, shifted so the cortex centroid lands
       on the orbit target; the two layers must move together to stay registered */
    pivot = new THREE.Group();
    grp.add(pivot);

    // tvbase_viewer's lighting, verbatim
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    var d1 = new THREE.DirectionalLight(0xffffff, 0.8); d1.position.set(5, 5, 5); scene.add(d1);
    var d2 = new THREE.DirectionalLight(0xffffff, 0.3); d2.position.set(-5, -5, 5); scene.add(d2);

    if (THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, netCv);
      controls.enableZoom = false;   // never hijack page scroll
      controls.enablePan = false;
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.rotateSpeed = 0.45;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.45;
      controls.addEventListener('start', function () { controls.autoRotate = false; });
    }
  }

  /** The cortex ships as a delta-encoded binary, fetched and decoded once. */
  var vRegion = null, vColor = null, colorAttr = null;
  function buildShell() {
    if (!gl || shellBuilt || !S.mesh) return;
    shellBuilt = true;
    /* Versioned by the geometry it decodes to, not by hand: /tvbo/z/ caches for a
       week, and a re-bake that changes the counts would otherwise hit a stale
       buffer and throw on the first typed-array view. */
    fetch('/tvbo/z/src/img/landing_cortex.bin?v=' + S.mesh.verts + 'x' + S.mesh.faces)
      .then(function (r) { if (!r.ok) throw new Error('mesh'); return r.arrayBuffer(); })
      .then(function (buf) {
        var NV = S.mesh.verts, NF = S.mesh.faces;
        var lo = S.mesh.range[0], sp = (S.mesh.range[1] - lo) / 4095;
        var u8 = new Uint8Array(buf);
        /** Each delta stream ships as a low-byte plane followed by a high-byte one. */
        function plane(off, n) {
          var out = new Int16Array(n);
          for (var k = 0; k < n; k++) out[k] = (u8[off + k] | (u8[off + n + k] << 8)) << 16 >> 16;
          return out;
        }
        var dv = plane(0, NV * 3);
        var pos = new Float32Array(NV * 3);
        var ax = 0, ay = 0, az = 0, i;
        for (i = 0; i < NV; i++) {
          ax += dv[i * 3]; ay += dv[i * 3 + 1]; az += dv[i * 3 + 2];
          pos[i * 3] = lo + ax * sp - 0.5;
          pos[i * 3 + 1] = lo + ay * sp - 0.5;
          pos[i * 3 + 2] = lo + az * sp - 0.5;
        }
        var df = plane(NV * 6, NF * 3);
        var idx = new Uint16Array(NF * 3), a = 0;
        for (i = 0; i < NF; i++) {
          a += df[i * 3];
          idx[i * 3] = a; idx[i * 3 + 1] = a + df[i * 3 + 1]; idx[i * 3 + 2] = a + df[i * 3 + 2];
        }
        vRegion = new Uint8Array(buf, NV * 6 + NF * 6, NV);
        vColor = new Float32Array(NV * 3);
        for (i = 0; i < NV * 3; i++) vColor[i] = 0.66;   // tvbase's resting grey

        var geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        colorAttr = new THREE.BufferAttribute(vColor, 3);
        geo.setAttribute('color', colorAttr);
        geo.setIndex(new THREE.BufferAttribute(idx, 1));
        geo.computeVertexNormals();
        geo.computeBoundingBox();
        matSurface = new THREE.MeshStandardMaterial({
          vertexColors: true, flatShading: false, side: THREE.FrontSide,
          roughness: 0.92, metalness: 0.0
        });
        /* the same cortex, made translucent so the connectome inside reads */
        matGlass = new THREE.MeshStandardMaterial({
          color: 0x9dc9ea, flatShading: false, side: THREE.DoubleSide,
          roughness: 0.9, metalness: 0.0, transparent: true, opacity: 0.14, depthWrite: false
        });
        shellMesh = new THREE.Mesh(geo, view === 'surface' ? matSurface : matGlass);
        pivot.add(shellMesh);
        var c = geo.boundingBox.getCenter(new THREE.Vector3());
        pivot.position.set(-c.x, -c.y, -c.z);
        hull = pos;
        buildNetwork();
        applyView();
        frameCamera();
        frame();
      })
      .catch(function (err) {
        shellBuilt = false;
        if (window.console) console.warn('[tvbo] cortex mesh unavailable:', err);
      });
  }

  /* Fit the cortex to whatever aspect the pane currently has. Every vertex is
     projected onto the camera basis, not the bounding box: from an oblique angle a
     box corner sits far outside the actual silhouette, which is what left the brain
     small in a wide pane. Rotating the basis into mesh space keeps this to three
     dot products per vertex, cheap enough to redo on every resize. */
  var hull = null, CAM0 = null;
  function frameCamera() {
    if (!gl || !hull || !pivot) return;
    if (!CAM0) CAM0 = new THREE.Vector3(-2.55, 0.30, 0.55).normalize();
    var dir = camera.position.lengthSq() > 1e-6 ? camera.position.clone().normalize() : CAM0.clone();
    var right = new THREE.Vector3().crossVectors(dir, camera.up).normalize();
    if (right.lengthSq() < 1e-6) right.set(1, 0, 0);
    var up = new THREE.Vector3().crossVectors(right, dir).normalize();
    var inv = new THREE.Quaternion().copy(grp.quaternion).invert();
    var lr = right.clone().applyQuaternion(inv), lu = up.clone().applyQuaternion(inv),
        ld = dir.clone().applyQuaternion(inv), t = pivot.position;
    var hw = 0, hh = 0, depth = 0;
    for (var i = 0; i < hull.length; i += 3) {
      var x = hull[i] + t.x, y = hull[i + 1] + t.y, z = hull[i + 2] + t.z;
      var a = Math.abs(x * lr.x + y * lr.y + z * lr.z); if (a > hw) hw = a;
      var b = Math.abs(x * lu.x + y * lu.y + z * lu.z); if (b > hh) hh = b;
      var c = x * ld.x + y * ld.y + z * ld.z; if (c > depth) depth = c;
    }
    var tanY = Math.tan((camera.fov * Math.PI) / 360), tanX = tanY * camera.aspect;
    var d = depth + 1.03 * Math.max(hh / tanY, hw / tanX);
    camera.position.copy(dir).multiplyScalar(d);
    camera.near = Math.max(0.01, d - depth * 3);
    camera.far = d + depth * 4 + 1;
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    if (controls) controls.update();
  }

  /** Connectome layer: only shown in `network` view, where the cortex turns glass. */
  function buildNetwork() {
    netGroup = new THREE.Group();
    var ep = new Float32Array(S.edges.length * 6), ec = new Float32Array(S.edges.length * 6);
    for (var e = 0; e < S.edges.length; e++) {
      var ed = S.edges[e], w = 0.45 + 0.55 * ed[2];
      for (var q = 0; q < 2; q++) {
        var pp = S.pos[ed[q]];
        ep[e * 6 + q * 3] = pp[0] - 0.5;
        ep[e * 6 + q * 3 + 1] = pp[1] - 0.5;
        ep[e * 6 + q * 3 + 2] = pp[2] - 0.5;
        ec[e * 6 + q * 3] = 0.16 * w; ec[e * 6 + q * 3 + 1] = 0.68 * w; ec[e * 6 + q * 3 + 2] = w;
      }
    }
    var eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.BufferAttribute(ep, 3));
    eg.setAttribute('color', new THREE.BufferAttribute(ec, 3));
    netGroup.add(new THREE.LineSegments(eg, new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.95,
      blending: THREE.AdditiveBlending, depthWrite: false
    })));
    dummy = new THREE.Object3D();
    tint = new THREE.Color();
    core = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 12, 10),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.95, depthWrite: false }), N);
    core.renderOrder = 4;
    netGroup.add(core);
    pivot.add(netGroup);
  }

  function applyView() {
    if (shellMesh) shellMesh.material = view === 'surface' ? matSurface : matGlass;
    if (netGroup) netGroup.visible = view === 'network';
    var btns = sec.querySelectorAll('[data-scope-view] button');
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute('aria-pressed', btns[i].getAttribute('data-view') === view ? 'true' : 'false');
    }
  }

  (function () {
    var btns = sec.querySelectorAll('[data-scope-view] button');
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener('click', function () {
        view = this.getAttribute('data-view');
        applyView();
        redraw();
      });
    }
  })();

  /* tvbase_viewer's `hot` ramp, but blended out of its resting grey: quiet cortex
     stays neutral and only genuinely active regions take colour, which is what
     makes an activation map readable rather than uniformly red. */
  var regC = new Float32Array(N * 3);
  function recolour(t0, t1, f) {
    if (!vRegion || !frames) return;
    var i, GY = 0.66;
    for (i = 0; i < N; i++) {
      var v = brainAt(cell, t0, i) * (1 - f) + brainAt(cell, t1, i) * f;
      var m = v < 0.30 ? 0 : (v > 0.80 ? 1 : (v - 0.30) / 0.50);
      m = m * m * (3 - 2 * m);
      regC[i * 3] = GY + (Math.min(1, v * 2.5) - GY) * m;
      regC[i * 3 + 1] = GY + (Math.max(0, Math.min(1, (v - 0.4) * 2.5)) - GY) * m;
      regC[i * 3 + 2] = GY + (Math.max(0, 0.3 - v * 0.6) - GY) * m;
    }
    if (view === 'surface') {
      for (i = 0; i < vRegion.length; i++) {
        var k = vRegion[i] * 3;
        vColor[i * 3] = regC[k]; vColor[i * 3 + 1] = regC[k + 1]; vColor[i * 3 + 2] = regC[k + 2];
      }
      colorAttr.needsUpdate = true;
    } else if (core) {
      for (i = 0; i < N; i++) {
        var act = brainAt(cell, t0, i) * (1 - f) + brainAt(cell, t1, i) * f;
        var pp = S.pos[i];
        dummy.position.set(pp[0] - 0.5, pp[1] - 0.5, pp[2] - 0.5);
        dummy.scale.setScalar(0.006 + 0.011 * act);
        dummy.updateMatrix();
        core.setMatrixAt(i, dummy.matrix);
        tint.setRGB(regC[i * 3], regC[i * 3 + 1], regC[i * 3 + 2]);
        core.setColorAt(i, tint);
      }
      core.instanceMatrix.needsUpdate = true;
      if (core.instanceColor) core.instanceColor.needsUpdate = true;
    }
  }

  function drawBrain(t0, t1, f) {
    if (!gl) return;
    recolour(t0, t1, f);
    if (controls) controls.update();
    renderer.render(scene, camera);
  }

  /* ------------------------------------------------------------------- traces */
  var tctx = trCv.getContext('2d');
  var trW = 0, trH = 0, dpr = 1;

  function fit() {
    dpr = Math.min(2, window.devicePixelRatio || 1);
    var nb = netCv.getBoundingClientRect(), tb = trCv.getBoundingClientRect();
    if (gl) {
      camera.aspect = Math.max(0.2, nb.width / Math.max(1, nb.height));
      camera.updateProjectionMatrix();
      renderer.setSize(Math.max(1, Math.round(nb.width)), Math.max(1, Math.round(nb.height)), false);
      frameCamera();
    }
    trW = Math.max(1, Math.round(tb.width)); trH = Math.max(1, Math.round(tb.height));
    trCv.width = trW * dpr; trCv.height = trH * dpr;
    tctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawTraces(head) {
    tctx.clearRect(0, 0, trW, trH);
    if (!frames) return;
    var laneH = trH / NL, padL = 48, w = trW - padL - 6;
    var span = Math.min(TS, 130);
    tctx.font = '9px ui-monospace, SFMono-Regular, Menlo, monospace';
    tctx.textBaseline = 'middle';
    for (var k = 0; k < NL; k++) {
      var cy = laneH * (k + 0.5);
      tctx.fillStyle = 'rgba(150,183,204,0.62)';
      tctx.fillText(S.traceLanes[k], 5, cy);
      tctx.strokeStyle = 'rgba(136,198,244,' + (0.95 - k * 0.05).toFixed(2) + ')';
      tctx.lineWidth = 1.2;
      tctx.beginPath();
      for (var s = 0; s < span; s++) {
        var t = (head - span + s + TS * 2) % TS;
        var sx = padL + (w * s) / (span - 1);
        var sy = cy - traceAt(cell, t, k) * laneGain[cell * NL + k] * laneH * 0.44;
        if (s === 0) tctx.moveTo(sx, sy); else tctx.lineTo(sx, sy);
      }
      tctx.stroke();
    }
  }

  var head = 0, SPEED = 0.28;
  function frame() {
    head = (head + SPEED) % BS;
    var t0 = Math.floor(head), t1 = (t0 + 1) % BS;
    drawBrain(t0, t1, head - t0);
    drawTraces(Math.floor((head / BS) * TS));
  }
  /** Repaint once when nothing is animating, so the sliders and the view toggle
      still respond under prefers-reduced-motion or off-screen. */
  function redraw() { if (!raf) frame(); }

  /* ------------------------------------------------------------ sweep sliders */
  var FCLO = Math.min.apply(null, S.sync), FCHI = Math.max.apply(null, S.sync);

  function select(idx) {
    cell = idx;
    var ai = Math.floor(idx / NG), gi = idx % NG, i;
    for (i = 0; i < readA.length; i++) readA[i].textContent = S.sweepA[ai].toFixed(2);
    for (i = 0; i < readG.length; i++) readG[i].textContent = S.sweepG[gi].toFixed(3);
    if (readFC) readFC.textContent = (S.sync[idx] >= 0 ? '+' : '') + S.sync[idx].toFixed(3);
    if (rBar) rBar.style.width = Math.round(Math.max(0, (S.sync[idx] - FCLO) / (FCHI - FCLO || 1)) * 100) + '%';
    redraw();
  }
  function fromSliders() { select((+slA.value) * NG + (+slG.value)); }

  if (slA && slG) {
    slA.max = NA - 1; slA.value = Math.floor(cell / NG);
    slG.max = NG - 1; slG.value = cell % NG;
    slA.addEventListener('input', fromSliders);
    slG.addEventListener('input', fromSliders);
  }
  select(cell);

  /* ------------------------------------------------------------------ code tabs */
  /* Ordered token grammar, one pass per line. The first alternative that matches at
     a position wins, so comments and strings precede the patterns whose characters
     they contain. Every group is non-capturing: the outer wrapper owns the indices. */
  var NUM = '\\b\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?\\b';
  var CALL = '[A-Za-z_]\\w*(?=\\s*\\()';
  var OPS = '[=+\\-*/%<>!&|^~,:;.()\\[\\]{}]';
  var GRAMMAR = {
    py: [
      ['c', '#.*'],
      ['s', '"(?:\\\\.|[^"\\\\])*"|\'(?:\\\\.|[^\'\\\\])*\''],
      ['at', '@[A-Za-z_][\\w.]*'],
      ['k', '\\b(?:def|class|return|import|from|as|if|elif|else|for|while|in|is|not|and|or|None|True|False|lambda|with|try|except|finally|raise|yield|pass|break|continue|global|nonlocal|assert|del|async|await)\\b'],
      ['b', '\\b(?:self|np|jnp|numpy|jax|scipy|print|len|range|dict|list|tuple|set|int|float|str|bool)\\b'],
      ['n', NUM],
      ['f', CALL],
      ['o', OPS]
    ],
    jl: [
      ['c', '#.*'],
      ['s', '"(?:\\\\.|[^"\\\\])*"'],
      ['at', '@[A-Za-z_][\\w.]*'],
      ['k', '\\b(?:function|end|using|import|module|export|return|nothing|const|struct|mutable|let|for|while|in|if|elseif|else|begin|do|try|catch|finally|global|local|abstract|where|true|false)\\b'],
      ['b', '\\b(?:Float64|Int|Vector|Matrix|Array|Tuple|println|length|zeros|ones|similar)\\b'],
      ['n', NUM],
      ['f', CALL],
      ['o', OPS]
    ],
    xml: [
      ['c', '<!--[\\s\\S]*?-->'],
      ['t', '</?[A-Za-z][\\w:.-]*|/?>'],
      ['a', '[A-Za-z_][\\w:.-]*(?=\\s*=)'],
      ['s', '"[^"]*"|\'[^\']*\''],
      ['n', NUM]
    ]
  };

  var RE_CACHE = {};
  function grammarRe(lang) {
    if (!RE_CACHE[lang]) {
      RE_CACHE[lang] = new RegExp(GRAMMAR[lang].map(function (t) {
        return '(' + t[1] + ')';
      }).join('|'), 'g');
    }
    return RE_CACHE[lang];
  }

  /* Docstrings and XML comments open on one line and close on another, so a purely
     per-line pass paints their bodies as code. These three carry across lines. */
  var BLOCK = {
    py: [['s', '"""', '"""'], ['s', ", "]],
    jl: [['s', '"""', '"""']],
    xml: [['c', '<!--', '-->']]
  };

  function mkSpan(cls, text) {
    var sp = document.createElement('span');
    sp.className = cls;
    sp.textContent = text;
    return sp;
  }

  /** Leftmost block opener, ignoring one quoted inside a line comment. */
  function findOpen(text, lang) {
    var defs = BLOCK[lang] || [], best = null;
    var hash = lang === 'xml' ? -1 : text.indexOf('#');
    for (var i = 0; i < defs.length; i++) {
      var at = text.indexOf(defs[i][1]);
      if (at < 0 || (hash >= 0 && at > hash)) continue;
      if (!best || at < best.at) {
        best = { at: at, cls: defs[i][0], open: defs[i][1], close: defs[i][2] };
      }
    }
    return best;
  }

  function tokenize(frag, text, lang) {
    var spec = GRAMMAR[lang], re = grammarRe(lang);
    var last = 0, m;
    re.lastIndex = 0;
    while ((m = re.exec(text))) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      var cls = '';
      for (var gi = 1; gi <= spec.length; gi++) {
        if (m[gi] !== undefined) { cls = spec[gi - 1][0]; break; }
      }
      frag.appendChild(mkSpan(cls, m[0]));
      last = m.index + m[0].length;
      if (re.lastIndex === m.index) re.lastIndex++;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
  }

  /** `st` carries an unterminated block in from the previous line; one per file. */
  function highlight(line, lang, st) {
    var g = GRAMMAR[lang] ? lang : 'py';
    var frag = document.createDocumentFragment();
    var rest = line;
    if (st.close) {
      var e = rest.indexOf(st.close);
      if (e < 0) { frag.appendChild(mkSpan(st.cls, rest)); return frag; }
      frag.appendChild(mkSpan(st.cls, rest.slice(0, e + st.close.length)));
      rest = rest.slice(e + st.close.length);
      st.close = null;
    }
    for (;;) {
      var op = findOpen(rest, g);
      if (!op) break;
      tokenize(frag, rest.slice(0, op.at), g);
      var ci = rest.slice(op.at + op.open.length).indexOf(op.close);
      if (ci < 0) {
        frag.appendChild(mkSpan(op.cls, rest.slice(op.at)));
        st.close = op.close;
        st.cls = op.cls;
        return frag;
      }
      var end = op.at + op.open.length + ci + op.close.length;
      frag.appendChild(mkSpan(op.cls, rest.slice(op.at, end)));
      rest = rest.slice(end);
    }
    tokenize(frag, rest, g);
    return frag;
  }

  function showCode(i, focus) {
    var b = S.code[i];
    codeEl.textContent = '';
    var st = {};
    for (var n = 0; n < b.lines.length; n++) {
      var d = document.createElement('div');
      d.className = 'cl';
      d.appendChild(highlight(b.lines[n], b.lang, st));
      codeEl.appendChild(d);
    }
    codeEl.scrollTop = 0;
    codeEl.setAttribute('aria-label', b.label + ' — ' + b.file + ', ' + b.lines.length + ' lines generated from experiment.yaml');
    var tabs = tabsEl.querySelectorAll('button');
    for (n = 0; n < tabs.length; n++) {
      tabs[n].setAttribute('aria-selected', n === i ? 'true' : 'false');
      tabs[n].tabIndex = n === i ? 0 : -1;   // one tab stop for the whole strip
    }
    if (focus) { tabs[i].focus(); tabs[i].scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
    var fn = sec.querySelector('[data-scope-file]');
    if (fn) fn.textContent = b.file;
  }

  // .length, not truthiness: an all-failed bake emits [] and showCode(0) would throw
  if (tabsEl && codeEl && S.code && S.code.length) {
    tabsEl.setAttribute('role', 'tablist');
    tabsEl.setAttribute('aria-label', 'Backend');
    codeEl.setAttribute('role', 'tabpanel');
    codeEl.tabIndex = 0;   // it scrolls, so it must be reachable by keyboard
    S.code.forEach(function (b, i) {
      var t = document.createElement('button');
      t.type = 'button';
      t.id = 'tvbo-scope-tab-' + b.key;
      t.setAttribute('role', 'tab');
      t.setAttribute('aria-controls', codeEl.id);
      t.textContent = b.label;
      t.addEventListener('click', function () { showCode(i); });
      tabsEl.appendChild(t);
    });
    tabsEl.addEventListener('keydown', function (ev) {
      var d = ev.key === 'ArrowRight' ? 1 : (ev.key === 'ArrowLeft' ? -1 : 0);
      var cur = [].indexOf.call(tabsEl.querySelectorAll('button'), document.activeElement);
      if (cur < 0) return;
      var to = d ? (cur + d + S.code.length) % S.code.length
        : (ev.key === 'Home' ? 0 : (ev.key === 'End' ? S.code.length - 1 : -1));
      if (to < 0) return;
      ev.preventDefault();
      showCode(to, true);
    });
    showCode(0);
    var markScroll = function () {
      tabsEl.classList.toggle('more', tabsEl.scrollWidth > tabsEl.clientWidth + 2);
    };
    markScroll();
    window.addEventListener('resize', markScroll);
  }

  /* ----------------------------------------------------------------- lifecycle */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var raf = 0, visible = false;
  function loop() { raf = window.requestAnimationFrame(loop); frame(); }
  function start() { if (!raf && !reduce) loop(); }
  function stop() { if (raf) { window.cancelAnimationFrame(raf); raf = 0; } }

  if (reduce && controls) controls.autoRotate = false;
  adoptFrames();
  buildShell();
  fit();
  frame();
  window.addEventListener('tvbo-scope-frames', function () {
    adoptFrames(); frame(); if (visible) start();
  });

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () { fit(); frame(); }, 150);
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      visible = es[0].isIntersecting;
      if (visible) start(); else stop();
    }, { threshold: 0.05 }).observe(host);
  } else { start(); }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stop(); else if (visible) start();
  });
})();

/* First-look affordance. Every control pulses once, staggered, as it first scrolls
 * into view — above the fold that means on load — so the sliders, backend tabs, view
 * toggle and scrollable code pane announce themselves as operable before anything is
 * touched. One shot per element: it hints, it does not decorate.
 */
(function () {
  'use strict';

  var root = document.querySelector('.tvbo-landing');
  if (!root) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var SEL = '.btn, .scope-tabs button, .scope-bar .seg button, .scope-ctl input[type=range], [data-scope-code]';
  var els = [].slice.call(root.querySelectorAll(SEL));
  if (!els.length) return;

  var LEAD = 320;   // clears the .reveal fade so the pulse lands on a visible control
  var seen = 0;

  function pulse(el) {
    var wait = LEAD + (seen++ % 8) * 90;
    window.setTimeout(function () {
      el.classList.add('aff');
      window.setTimeout(function () { el.classList.remove('aff'); }, 1700);
    }, wait);
  }

  if (!('IntersectionObserver' in window)) {
    els.forEach(pulse);
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      pulse(e.target);
    });
  }, { threshold: 0.4 });
  els.forEach(function (el) { io.observe(el); });
})();
