/* The knowledge-base band on the front page. It draws the whole knowledge graph from /tvbo/api/kg/graph/cloud as points joined by their links, lights up the records named in data-cloud-highlight with their real (non-taxonomic) links, and fills in the live counts. Hovering a point names it; clicking it opens its detail in the Knowledge Graph. */
(function () {
  var sec = document.querySelector('[data-tvbo-cloud]');
  if (!sec) return;
  var canvas = sec.querySelector('[data-cloud-canvas]');
  var tip = sec.querySelector('[data-cloud-tip]');
  var wait = sec.querySelector('[data-cloud-wait]');
  var ctx = canvas.getContext('2d');
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var GROUPS = [
    {name: 'Models', one: 'Model', color: '#63B3E8', kinds: ['dynamics']},
    {name: 'Networks and atlases', one: 'Network or atlas', color: '#4FD1C5', kinds: ['network', 'atlas']},
    {name: 'Studies', one: 'Study', color: '#F6C177', kinds: ['study']},
    {name: 'Experiments', one: 'Experiment', color: '#F78C6C', kinds: ['experiment']},
    {name: 'Simulation tools', one: 'Simulation tool', color: '#C3B4EA', kinds: ['software']},
    {name: 'Other building blocks', one: 'Building block', color: '#9FB3C8', kinds: ['integrator', 'coupling', 'observation', 'continuation', 'graph_generator']},
    {name: 'Ontology classes', one: 'Ontology class', color: '#4C6A80', kinds: ['ontology']}
  ];
  var COUNTS = [['dynamics', 'models'], ['network', 'networks'], ['study', 'studies'], ['experiment', 'experiments'], ['software', 'simulation tools'], ['ontology', 'ontology classes']];
  var HL = '#63B3E8';

  var graph, nodes, base, hot, hotLinks, seeds, view, hover = -1, progress = still ? 1 : 0;

  function groupOf(kind) {
    for (var i = 0; i < GROUPS.length; i++) if (GROUPS[i].kinds.indexOf(kind) !== -1) return GROUPS[i];
    return GROUPS[GROUPS.length - 1];
  }

  function el(tag, html) {
    var e = document.createElement(tag);
    e.innerHTML = html;
    return e;
  }

  function escape(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; });
  }

  /** Counts per kind over the drawn nodes, so they match the cloud below them. */
  function fillCounts() {
    var n = {};
    nodes.forEach(function (d) { n[d.kind] = (n[d.kind] || 0) + 1; });
    var box = sec.querySelector('[data-cloud-counts]');
    COUNTS.forEach(function (c) {
      if (n[c[0]]) box.appendChild(el('span', '<b>' + n[c[0]].toLocaleString('en') + '</b>' + c[1]));
    });
    var legend = sec.querySelector('[data-cloud-legend]');
    GROUPS.forEach(function (g) {
      if (nodes.some(function (d) { return g.kinds.indexOf(d.kind) !== -1; })) legend.appendChild(el('li', '<i style="background:' + g.color + '"></i>' + g.name));
    });
    if (seeds.length) legend.appendChild(el('li', '<i></i>The example above, with its links')).className = 'hl';
  }

  /** The seed records (kind:label pairs in data-cloud-highlight) and every node and non-taxonomic link that touches one. */
  function pickHighlight() {
    var wanted = (sec.getAttribute('data-cloud-highlight') || '').split('|');
    seeds = [];
    nodes.forEach(function (d, i) { if (wanted.indexOf(d.kind + ':' + d.label) !== -1) seeds.push(i); });
    hot = {};
    hotLinks = [];
    seeds.forEach(function (i) { hot[i] = true; });
    graph.links.forEach(function (l) {
      if (!l[2] && (seeds.indexOf(l[0]) !== -1 || seeds.indexOf(l[1]) !== -1)) {
        hotLinks.push(l);
        hot[l[0]] = hot[l[1]] = true;
      }
    });
  }

  /** Map layout coordinates into the canvas; the round layout may stretch up to STRETCH times along one axis so it fills a wide or tall band. */
  var STRETCH = 1.6;
  function fit() {
    var w = canvas.clientWidth, h = canvas.clientHeight, dpr = window.devicePixelRatio || 1, pad = 28;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    nodes.forEach(function (d) { x0 = Math.min(x0, d.x); y0 = Math.min(y0, d.y); x1 = Math.max(x1, d.x); y1 = Math.max(y1, d.y); });
    var sx = (w - 2 * pad) / Math.max(x1 - x0, 1), sy = (h - 2 * pad) / Math.max(y1 - y0, 1);
    sx = Math.min(sx, sy * STRETCH);
    sy = Math.min(sy, sx * STRETCH);
    view = {dpr: dpr};
    var ox = (w - sx * (x1 - x0)) / 2 - sx * x0, oy = (h - sy * (y1 - y0)) / 2 - sy * y0;
    var scale = Math.min(1, Math.max(0.5, w / 1100));   // points shrink with a narrow canvas so they do not merge
    nodes.forEach(function (d) { d.px = ox + sx * d.x; d.py = oy + sy * d.y; d.r = d.size * scale; });
    drawBase();
  }

  /** Every link and point, drawn once per size onto an offscreen canvas; a link takes the colour of its record end, fainter when it is taxonomic. */
  function drawBase() {
    base = document.createElement('canvas');
    base.width = canvas.width;
    base.height = canvas.height;
    var b = base.getContext('2d');
    b.scale(view.dpr, view.dpr);
    var strokes = {};
    graph.links.forEach(function (l) {
      var end = nodes[l[0]].kind === 'ontology' ? nodes[l[1]] : nodes[l[0]];
      var color = groupOf(end.kind).color + (l[2] ? '26' : '44');
      (strokes[color] = strokes[color] || []).push(l);
    });
    b.globalCompositeOperation = 'lighter';
    b.lineWidth = 0.7;
    Object.keys(strokes).forEach(function (color) {
      b.strokeStyle = color;
      b.beginPath();
      strokes[color].forEach(function (l) {
        b.moveTo(nodes[l[0]].px, nodes[l[0]].py);
        b.lineTo(nodes[l[1]].px, nodes[l[1]].py);
      });
      b.stroke();
    });
    nodes.forEach(function (d) {
      var color = groupOf(d.kind).color;
      if (d.kind !== 'ontology') {
        var halo = b.createRadialGradient(d.px, d.py, 0, d.px, d.py, d.r * 3.4);
        halo.addColorStop(0, color + '40');
        halo.addColorStop(1, color + '00');
        b.fillStyle = halo;
        b.beginPath();
        b.arc(d.px, d.py, d.r * 3.4, 0, 2 * Math.PI);
        b.fill();
      }
      b.globalAlpha = d.kind === 'ontology' ? 0.75 : 0.95;
      b.fillStyle = color;
      b.beginPath();
      b.arc(d.px, d.py, d.r, 0, 2 * Math.PI);
      b.fill();
      b.globalAlpha = 1;
    });
    b.globalCompositeOperation = 'source-over';
  }

  /** The hovered point with its own non-taxonomic links and neighbours, so its real connections can be read off. */
  function drawHover() {
    var h = nodes[hover];
    ctx.strokeStyle = 'rgba(255,255,255,0.75)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    h.links.forEach(function (j) {
      ctx.moveTo(h.px, h.py);
      ctx.lineTo(nodes[j].px, nodes[j].py);
    });
    ctx.stroke();
    ctx.fillStyle = '#fff';
    h.links.forEach(function (j) {
      ctx.beginPath();
      ctx.arc(nodes[j].px, nodes[j].py, 2.6, 0, 2 * Math.PI);
      ctx.fill();
    });
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(h.px, h.py, h.r + 4, 0, 2 * Math.PI);
    ctx.stroke();
  }

  /** Draw a name beside a point unless it would overlap one already drawn; long names are shortened. */
  function label(text, x, y, bold, boxes) {
    text = text.length > 34 ? text.slice(0, 32) + '…' : text;
    ctx.font = (bold ? '600 13px ' : '12px ') + getComputedStyle(sec).fontFamily;
    var w = ctx.measureText(text).width;
    var x0 = x + 14 + w > canvas.clientWidth - 4 ? Math.max(4, x - 14 - w) : x + 8;
    var box = [x0, y - 16, x0 + w + 6, y + 2];
    for (var i = 0; i < boxes.length; i++) {
      var o = boxes[i];
      if (box[0] < o[2] && o[0] < box[2] && box[1] < o[3] && o[1] < box[3]) return;
    }
    boxes.push(box);
    ctx.fillStyle = 'rgba(11,22,34,0.78)';
    ctx.fillRect(box[0] - 3, box[1], box[2] - box[0] + 2, box[3] - box[1] + 2);
    ctx.fillStyle = bold ? '#fff' : '#CFE0EC';
    ctx.fillText(text, box[0] + 2, y - 2);
  }

  function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(base, 0, 0);
    ctx.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
    var t = 1 - Math.pow(1 - progress, 3);
    ctx.strokeStyle = HL;
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.9;
    ctx.beginPath();
    hotLinks.forEach(function (l) {
      var a = nodes[seeds.indexOf(l[0]) !== -1 ? l[0] : l[1]], b = nodes[a === nodes[l[0]] ? l[1] : l[0]];
      ctx.moveTo(a.px, a.py);
      ctx.lineTo(a.px + (b.px - a.px) * t, a.py + (b.py - a.py) * t);
    });
    ctx.stroke();
    ctx.globalAlpha = t;
    Object.keys(hot).forEach(function (i) {
      if (seeds.indexOf(+i) !== -1) return;
      var d = nodes[i];
      ctx.fillStyle = groupOf(d.kind).color;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(d.px, d.py, 3.6, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
    seeds.forEach(function (i) {
      var d = nodes[i];
      ctx.shadowColor = HL;
      ctx.shadowBlur = 14;
      ctx.fillStyle = '#fff';
      ctx.beginPath();
      ctx.arc(d.px, d.py, 5.5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.shadowBlur = 0;
    });
    if (t > 0.6) {
      var boxes = [];
      seeds.forEach(function (i) { label(nodes[i].label, nodes[i].px, nodes[i].py, true, boxes); });
      Object.keys(hot).map(Number)
        .filter(function (i) { return seeds.indexOf(i) === -1; })
        .sort(function (a, b) { return (nodes[a].kind === 'ontology') - (nodes[b].kind === 'ontology'); })
        .forEach(function (i) { label(nodes[i].label, nodes[i].px, nodes[i].py, false, boxes); });
    }
    if (hover !== -1) drawHover();
  }

  /** The one orchestrated moment: the highlighted links grow out of their seeds once the band is on screen. */
  function reveal() {
    if (still) return draw();
    var start = null;
    (function step(now) {
      start = start || now;
      progress = Math.min((now - start) / 900, 1);
      draw();
      if (progress < 1) requestAnimationFrame(step);
    })(performance.now());
  }

  function nearest(ev) {
    var r = canvas.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top, best = -1, bestD = 144;
    nodes.forEach(function (d, i) {
      var dd = (d.px - x) * (d.px - x) + (d.py - y) * (d.py - y);
      if (dd < bestD) { bestD = dd; best = i; }
    });
    return best;
  }

  function onMove(ev) {
    var i = nearest(ev);
    if (i === hover) return;
    hover = i;
    canvas.style.cursor = i === -1 ? 'default' : 'pointer';
    if (i === -1) {
      tip.hidden = true;
    } else {
      var d = nodes[i];
      tip.innerHTML = escape(d.label) + '<span>' + groupOf(d.kind).one + (d.links.length ? ', ' + d.links.length + (d.links.length === 1 ? ' link' : ' links') : '') + '</span>';
      tip.style.left = d.px + 'px';
      tip.style.top = d.py + 'px';
      tip.hidden = false;
    }
    draw();
  }

  function onClick(ev) {
    var i = nearest(ev);
    if (i !== -1) window.location.href = '/tvbo/kg?open=' + encodeURIComponent(nodes[i].kind + ':' + nodes[i].id);
  }

  function start(data) {
    graph = data;
    nodes = data.nodes.map(function (n) { return {x: n[0], y: n[1], kind: data.kinds[n[2]], label: n[3], id: n[4], degree: 0, links: []}; });
    data.links.forEach(function (l) {
      nodes[l[0]].degree++;
      nodes[l[1]].degree++;
      if (!l[2]) {
        nodes[l[0]].links.push(l[1]);
        nodes[l[1]].links.push(l[0]);
      }
    });
    nodes.forEach(function (d) {
      d.size = d.kind === 'ontology' ? Math.min(1.1 + Math.sqrt(d.degree) * 0.3, 4) : Math.min(1.9 + Math.sqrt(d.degree) * 0.55, 6.5);
    });
    pickHighlight();
    fillCounts();
    wait.remove();
    fit();
    draw();
    new IntersectionObserver(function (entries, io) {
      if (entries[0].isIntersecting) { io.disconnect(); reveal(); }
    }, {threshold: 0.35}).observe(canvas);
    new ResizeObserver(function () { fit(); draw(); }).observe(canvas);
    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseleave', function () { hover = -1; tip.hidden = true; draw(); });
    canvas.addEventListener('click', onClick);
  }

  function load() {
    fetch(sec.getAttribute('data-tvbo-cloud'))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(start)
      .catch(function () { wait.textContent = 'The graph could not be loaded. Open the Knowledge Graph to browse it.'; });
  }

  new IntersectionObserver(function (entries, io) {
    if (entries[0].isIntersecting) { io.disconnect(); load(); }
  }, {rootMargin: '900px 0px'}).observe(sec);
})();
