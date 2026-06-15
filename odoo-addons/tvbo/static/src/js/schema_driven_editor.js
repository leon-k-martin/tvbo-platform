/* TVBO Schema-Driven Editor
 * ---------------------------------------------------------------
 * Generic, building-block style editor for any LinkML-defined class
 * in the tvbo schema. Mounts into divs that carry these attributes:
 *
 *   data-sde-class="<ClassName>"   e.g. "Function", "Event"
 *   data-sde-slot="<slotName>"     e.g. "functions" (slot on SimulationExperiment)
 *   data-sde-multivalued="true|false"
 *
 * State is held in window.SchemaEditor.state[slot] and pushed into
 * the live YAML preview / download via the new /experiment/dump_yaml
 * endpoint.
 * ---------------------------------------------------------------
 */
(function () {
  'use strict';

  const SDE = {
    schema: null,                  // fetched LinkML JSON
    state: {},                     // slot -> single value or array
    instanceCache: {},             // class -> [{id,name,label,...}]
    detailCache: {},               // `${class}/${id}` -> deep record
    mounts: [],                    // [{el, cls, slot, multivalued}]
    previewTimer: null,
    onChange: null,                // callback wired in init
  };

  // ----------------- Schema bootstrap -----------------------------
  async function loadSchema(force) {
    if (SDE.schema && !force) return SDE.schema;
    const r = await fetch('/tvbo/api/configurator/schema' + (force ? '?refresh=1' : ''));
    const j = await r.json();
    if (!j.success) throw new Error(j.error || 'schema load failed');
    SDE.schema = j.data;
    return SDE.schema;
  }

  async function listInstances(cls, q) {
    const key = cls + '|' + (q || '');
    if (SDE.instanceCache[key]) return SDE.instanceCache[key];
    const url = '/tvbo/api/configurator/instances/' + encodeURIComponent(cls)
      + (q ? '?q=' + encodeURIComponent(q) : '');
    const r = await fetch(url);
    const j = await r.json();
    if (!j.success) return [];
    SDE.instanceCache[key] = j.data || [];
    return SDE.instanceCache[key];
  }

  async function getInstance(cls, id) {
    const key = cls + '/' + id;
    if (SDE.detailCache[key]) return SDE.detailCache[key];
    const r = await fetch('/tvbo/api/configurator/instances/' + encodeURIComponent(cls) + '/' + id + '?depth=6');
    const j = await r.json();
    if (!j.success) throw new Error(j.error);
    SDE.detailCache[key] = cleanRecord(j.data);
    return SDE.detailCache[key];
  }

  // Strip Odoo metadata + empty placeholders (mirrors backend _clean).
  const META_KEYS = new Set(['id','display_name','create_uid','create_date','write_uid','write_date','__last_update','record_id']);
  function cleanRecord(v) {
    if (v === false || v === null || v === undefined) return undefined;
    if (Array.isArray(v)) {
      const c = v.map(cleanRecord).filter(x => x !== undefined && x !== null && !(Array.isArray(x) && x.length===0));
      return c;
    }
    if (typeof v === 'object') {
      const out = {};
      for (const k of Object.keys(v)) {
        if (META_KEYS.has(k)) continue;
        const cv = cleanRecord(v[k]);
        if (cv === undefined || cv === null) continue;
        if (Array.isArray(cv) && cv.length === 0) continue;
        if (typeof cv === 'object' && !Array.isArray(cv) && Object.keys(cv).length === 0) continue;
        out[k] = cv;
      }
      return out;
    }
    return v;
  }

  // ----------------- DOM helpers ----------------------------------
  function el(tag, attrs, ...children) {
    const e = document.createElement(tag);
    if (attrs) for (const k of Object.keys(attrs)) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'style') e.style.cssText = attrs[k];
      else if (k.startsWith('on') && typeof attrs[k] === 'function') e.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
      else if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    }
    for (const c of children) {
      if (c === null || c === undefined || c === false) continue;
      if (typeof c === 'string' || typeof c === 'number') e.appendChild(document.createTextNode(String(c)));
      else e.appendChild(c);
    }
    return e;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function notifyChange() {
    if (SDE.previewTimer) clearTimeout(SDE.previewTimer);
    SDE.previewTimer = setTimeout(() => { if (typeof SDE.onChange === 'function') SDE.onChange(); }, 350);
  }

  // ----------------- Field renderers ------------------------------
  // Returns DOM and uses `bind(value)` for read-back.
  function isEnum(rangeName) {
    return SDE.schema && SDE.schema.enums && rangeName in SDE.schema.enums;
  }

  function fieldEditor(slot, value, onUpdate) {
    const range = slot.range || 'string';

    // Enum -> select
    if (isEnum(range)) {
      const enumDef = SDE.schema.enums[range];
      const sel = el('select', { class: 'form-select form-select-sm' });
      sel.appendChild(el('option', { value: '' }, '— select —'));
      for (const pv of Object.keys(enumDef.permissible_values)) {
        const opt = el('option', { value: pv }, pv);
        if (value === pv) opt.selected = true;
        sel.appendChild(opt);
      }
      sel.addEventListener('change', () => onUpdate(sel.value || undefined));
      return sel;
    }

    // Boolean
    if (range === 'boolean') {
      const cb = el('input', { type: 'checkbox', class: 'form-check-input' });
      cb.checked = !!value;
      cb.addEventListener('change', () => onUpdate(cb.checked));
      return cb;
    }

    // Number
    if (range === 'integer' || range === 'float' || range === 'double' || range === 'decimal') {
      const inp = el('input', { type: 'number', class: 'form-control form-control-sm', step: range === 'integer' ? '1' : 'any' });
      if (value !== undefined && value !== null && value !== false) inp.value = value;
      inp.addEventListener('input', () => {
        const v = inp.value === '' ? undefined : (range === 'integer' ? parseInt(inp.value, 10) : parseFloat(inp.value));
        onUpdate(Number.isNaN(v) ? undefined : v);
      });
      return inp;
    }

    // Long text heuristic
    if (slot.name === 'description' || slot.name === 'equation' || slot.name === 'expression' ||
        slot.name === 'source' || (slot.name && slot.name.endsWith('_code'))) {
      const ta = el('textarea', { class: 'form-control form-control-sm', rows: 3 });
      if (value && typeof value === 'string') ta.value = value;
      ta.addEventListener('input', () => onUpdate(ta.value || undefined));
      return ta;
    }

    // Default: string
    const inp = el('input', { type: 'text', class: 'form-control form-control-sm' });
    if (value !== undefined && value !== null && value !== false) inp.value = value;
    inp.addEventListener('input', () => onUpdate(inp.value || undefined));
    return inp;
  }

  // List of primitive strings (for `references`, etc.)
  function stringListEditor(values, onUpdate) {
    const wrap = el('div', { class: 'sde-string-list' });
    const arr = Array.isArray(values) ? [...values] : [];
    function render() {
      clear(wrap);
      arr.forEach((v, idx) => {
        const row = el('div', { class: 'input-group input-group-sm mb-1' },
          (function () {
            const ta = el('textarea', { class: 'form-control', rows: 2 });
            ta.value = v || '';
            ta.addEventListener('input', () => { arr[idx] = ta.value; onUpdate([...arr]); });
            return ta;
          })(),
          el('button', { class: 'btn btn-outline-danger', type: 'button',
            onClick: () => { arr.splice(idx, 1); render(); onUpdate([...arr]); } }, '×')
        );
        wrap.appendChild(row);
      });
      wrap.appendChild(el('button', { class: 'btn btn-sm btn-outline-secondary', type: 'button',
        onClick: () => { arr.push(''); render(); onUpdate([...arr]); } }, '+ Add'));
    }
    render();
    return wrap;
  }

  // Bound on nested class-editor recursion. The tvbo schema has cycles
  // (e.g. Network -> nodes -> Node -> subnetwork -> Network), and rendering
  // nested editors eagerly would recurse until the call stack overflows.
  const MAX_NEST_DEPTH = 6;
  function nestedPlaceholder(rangeClass, multi, reason) {
    return el('details', { class: 'sde-nested border rounded p-2' },
      el('summary', { class: 'small text-muted' },
        `${rangeClass}${multi ? ' list' : ''} — nested (${reason}); edit in its own building-block view`));
  }

  // ----------------- Class editor ---------------------------------
  // Renders all slots of a class. `value` may be undefined (blank).
  function classEditor(className, value, onUpdate, opts) {
    opts = opts || {};
    const depth = opts.depth || 0;
    const path = opts.path || [];
    const cls = SDE.schema.classes[className];
    const wrap = el('div', { class: 'sde-class-editor' });

    if (!cls) {
      wrap.appendChild(el('div', { class: 'text-danger small' }, `Unknown class ${className}`));
      return wrap;
    }

    const data = (value && typeof value === 'object' && !Array.isArray(value)) ? { ...value } : {};

    // Optional ClassPicker at the top.
    if (opts.picker !== false && cls.pickable) {
      wrap.appendChild(classPicker(className, async (rec) => {
        // Replace data with picked record
        Object.keys(data).forEach(k => delete data[k]);
        Object.assign(data, rec || {});
        rerender();
        onUpdate({ ...data });
      }));
    }

    const body = el('div', { class: 'row g-2 mt-2' });
    wrap.appendChild(body);

    function rerender() {
      clear(body);
      const slotNames = Object.keys(cls.slots);
      // Surface common identification fields first.
      const order = ['name', 'label', 'description'];
      slotNames.sort((a, b) => {
        const ai = order.indexOf(a), bi = order.indexOf(b);
        if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
        return a.localeCompare(b);
      });
      for (const slotName of slotNames) {
        const slot = cls.slots[slotName];
        if (slot.deprecated) continue;
        body.appendChild(slotField(slot, data[slotName], (newVal) => {
          if (newVal === undefined || newVal === null || newVal === '' ||
              (Array.isArray(newVal) && newVal.length === 0)) {
            delete data[slotName];
          } else {
            data[slotName] = newVal;
          }
          onUpdate({ ...data });
        }));
      }
    }

    function slotField(slot, val, onU) {
      const colCls = slot.multivalued ||
                     (SDE.schema.classes[slot.range]) ||
                     (slot.name === 'description' || slot.name === 'equation' || slot.name === 'source')
                     ? 'col-12' : 'col-md-6';
      const col = el('div', { class: colCls });
      const labelTxt = (slot.name || slot.alias || '').replace(/_/g, ' ');
      const lbl = el('label', { class: 'form-label small fw-semibold mb-1' }, labelTxt);
      if (slot.required) lbl.appendChild(el('span', { class: 'text-danger ms-1' }, '*'));
      col.appendChild(lbl);
      if (slot.description) {
        col.appendChild(el('div', { class: 'form-text small text-muted mb-1', style: 'font-size:11px' }, slot.description));
      }

      const childPath = [...path, className];
      const guard = SDE.schema.classes[slot.range] &&
        (depth >= MAX_NEST_DEPTH || childPath.includes(slot.range));
      // Multivalued
      if (slot.multivalued) {
        if (SDE.schema.classes[slot.range]) {
          if (guard) {
            col.appendChild(nestedPlaceholder(slot.range, true, depth >= MAX_NEST_DEPTH ? 'max depth' : 'cycle'));
          } else {
            col.appendChild(multiValueClassList(slot.range, val, onU, depth + 1, childPath));
          }
        } else {
          col.appendChild(stringListEditor(val, onU));
        }
        return col;
      }
      // Single-valued nested class
      if (SDE.schema.classes[slot.range]) {
        if (guard) {
          col.appendChild(nestedPlaceholder(slot.range, false, depth >= MAX_NEST_DEPTH ? 'max depth' : 'cycle'));
          return col;
        }
        const nested = classEditor(slot.range, val, onU,
          { picker: !!SDE.schema.classes[slot.range].pickable, depth: depth + 1, path: childPath });
        const collapse = el('details', { class: 'sde-nested border rounded p-2' },
          el('summary', { class: 'small text-muted' }, slot.range + (val && val.name ? ` — ${val.name}` : '')),
          nested);
        if (val && Object.keys(val).length) collapse.open = true;
        col.appendChild(collapse);
        return col;
      }
      // Primitive
      col.appendChild(fieldEditor(slot, val, onU));
      return col;
    }

    rerender();
    return wrap;
  }

  // ----------------- ClassPicker ----------------------------------
  function classPicker(className, onPick) {
    const wrap = el('div', { class: 'input-group input-group-sm mb-1' });
    const input = el('input', { type: 'text', class: 'form-control', placeholder: `Pick existing ${className}…` });
    const list = el('div', {
      class: 'list-group position-absolute bg-white shadow-sm',
      style: 'z-index:1050; max-height:240px; overflow:auto; min-width:280px; display:none;'
    });

    let timer = null;
    async function refresh(q) {
      const items = await listInstances(className, q);
      clear(list);
      if (!items.length) {
        list.appendChild(el('div', { class: 'list-group-item small text-muted' }, 'No matches'));
      }
      items.slice(0, 50).forEach(it => {
        const item = el('button', { type: 'button', class: 'list-group-item list-group-item-action small' },
          el('strong', null, it.label || it.name || `#${it.id}`),
          it.description ? el('div', { class: 'text-muted', style: 'font-size:11px' }, it.description) : null);
        item.addEventListener('mousedown', async (ev) => {
          ev.preventDefault();
          list.style.display = 'none';
          input.value = it.label || it.name || `#${it.id}`;
          try {
            const rec = await getInstance(className, it.id);
            onPick(rec);
          } catch (e) { console.error(e); alert('Load failed: ' + e.message); }
        });
        list.appendChild(item);
      });
      list.style.display = 'block';
    }

    input.addEventListener('focus', () => refresh(input.value));
    input.addEventListener('input', () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => refresh(input.value), 200);
    });
    input.addEventListener('blur', () => setTimeout(() => { list.style.display = 'none'; }, 200));

    const newBtn = el('button', { type: 'button', class: 'btn btn-outline-primary',
      onClick: () => { input.value = ''; onPick({}); } }, '+ New');

    wrap.appendChild(input);
    wrap.appendChild(newBtn);
    const positioned = el('div', { class: 'position-relative' }, wrap, list);
    return positioned;
  }

  // ----------------- MultiValue list (of class instances) ---------
  function multiValueClassList(className, values, onUpdate, depth, path) {
    const items = Array.isArray(values) ? [...values] : [];
    const wrap = el('div', { class: 'sde-multi border rounded p-2 bg-light' });

    function emit() { onUpdate(items.length ? [...items] : undefined); }

    function render() {
      clear(wrap);
      items.forEach((it, idx) => {
        const card = el('div', { class: 'card mb-2' });
        const header = el('div', { class: 'card-header d-flex justify-content-between align-items-center py-1 px-2' },
          el('span', { class: 'small' },
            el('strong', null, `${className} #${idx + 1}`),
            it && it.name ? ` — ${it.name}` : (it && it.label ? ` — ${it.label}` : '')),
          el('div', null,
            el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary me-1',
              onClick: () => { if (idx > 0) { [items[idx-1], items[idx]] = [items[idx], items[idx-1]]; render(); emit(); } } }, '↑'),
            el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary me-1',
              onClick: () => { if (idx < items.length - 1) { [items[idx+1], items[idx]] = [items[idx], items[idx+1]]; render(); emit(); } } }, '↓'),
            el('button', { type: 'button', class: 'btn btn-sm btn-outline-danger',
              onClick: () => { items.splice(idx, 1); render(); emit(); } }, 'Remove')
          )
        );
        const body = el('div', { class: 'card-body py-2 px-2' });
        const editor = classEditor(className, it, (newVal) => {
          items[idx] = newVal;
          emit();
        }, { picker: !!(SDE.schema.classes[className] && SDE.schema.classes[className].pickable),
             depth: depth || 0, path: path || [] });
        body.appendChild(editor);
        card.appendChild(header);
        card.appendChild(body);
        wrap.appendChild(card);
      });
      wrap.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-primary',
        onClick: () => { items.push({}); render(); emit(); } }, `+ Add ${className}`));
    }

    render();
    return wrap;
  }

  // ----------------- Section mounting -----------------------------
  function mountSection(rootEl) {
    const cls = rootEl.getAttribute('data-sde-class');
    const slot = rootEl.getAttribute('data-sde-slot');
    const multi = rootEl.getAttribute('data-sde-multivalued') === 'true';
    if (!cls || !slot) return;
    SDE.mounts.push({ el: rootEl, cls, slot, multivalued: multi });

    clear(rootEl);
    const header = el('div', { class: 'd-flex justify-content-between align-items-baseline mb-2' },
      el('h5', { class: 'mb-0' }, slot.replace(/_/g, ' ')),
      el('small', { class: 'text-muted' }, `${cls}${multi ? ' (multivalued)' : ''}`));
    rootEl.appendChild(header);

    const cur = SDE.state[slot];
    let editor;
    if (multi) {
      editor = multiValueClassList(cls, cur, (newVal) => {
        SDE.state[slot] = newVal;
        notifyChange();
      });
    } else if (slot === 'references' && cls === 'string') {
      editor = stringListEditor(cur, (newVal) => { SDE.state[slot] = newVal; notifyChange(); });
    } else {
      editor = classEditor(cls, cur, (newVal) => {
        SDE.state[slot] = newVal;
        notifyChange();
      }, { picker: true });
    }
    rootEl.appendChild(editor);
  }

  function rerenderAll() {
    for (const m of SDE.mounts) {
      const placeholder = m.el;
      const tmp = el('div');
      tmp.setAttribute('data-sde-class', m.cls);
      tmp.setAttribute('data-sde-slot', m.slot);
      tmp.setAttribute('data-sde-multivalued', m.multivalued ? 'true' : 'false');
      mountInPlace(placeholder, m);
    }
  }

  function mountInPlace(rootEl, m) {
    clear(rootEl);
    const header = el('div', { class: 'd-flex justify-content-between align-items-baseline mb-2' },
      el('h5', { class: 'mb-0' }, m.slot.replace(/_/g, ' ')),
      el('small', { class: 'text-muted' }, `${m.cls}${m.multivalued ? ' (multivalued)' : ''}`));
    rootEl.appendChild(header);
    const cur = SDE.state[m.slot];
    let editor;
    if (m.multivalued) {
      editor = multiValueClassList(m.cls, cur, (newVal) => { SDE.state[m.slot] = newVal; notifyChange(); });
    } else if (m.slot === 'references' && m.cls === 'string') {
      editor = stringListEditor(cur, (newVal) => { SDE.state[m.slot] = newVal; notifyChange(); });
    } else {
      editor = classEditor(m.cls, cur, (newVal) => { SDE.state[m.slot] = newVal; notifyChange(); }, { picker: true });
    }
    rootEl.appendChild(editor);
  }

  // ----------------- Public API -----------------------------------
  async function init(opts) {
    opts = opts || {};
    SDE.onChange = opts.onChange || null;
    try {
      await loadSchema();
    } catch (e) {
      console.error('SchemaEditor: failed to load schema', e);
      return;
    }
    document.querySelectorAll('[data-sde-class]').forEach(mountSection);
  }

  // Hydrate state from a deep-loaded experiment record.
  function loadExperiment(exp) {
    if (!exp) return;
    const cleaned = cleanRecord(exp) || {};
    // Slots we manage:
    for (const m of SDE.mounts) {
      const v = cleaned[m.slot];
      SDE.state[m.slot] = v;
    }
    rerenderAll();
    notifyChange();
  }

  // Merge SDE state into an existing config dict (for download / preview).
  function mergeInto(experimentObj) {
    experimentObj = experimentObj || {};
    for (const m of SDE.mounts) {
      const v = SDE.state[m.slot];
      if (v === undefined || v === null) continue;
      if (Array.isArray(v) && v.length === 0) continue;
      if (typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length === 0) continue;
      experimentObj[m.slot] = v;
    }
    return experimentObj;
  }

  async function dumpYaml(experimentObj) {
    const r = await fetch('/tvbo/api/configurator/experiment/dump_yaml', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params: { experiment: experimentObj } }),
    });
    const j = await r.json();
    return (j && j.result && j.result.success) ? j.result.yaml : null;
  }

  window.SchemaEditor = {
    init, loadExperiment, mergeInto, dumpYaml,
    state: SDE.state,
    _internals: SDE,
  };
})();
