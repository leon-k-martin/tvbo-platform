/**
 * TVB-O Knowledge Graph UI Components
 * Modular, reusable UI elements shared across views
 * MVP: Clean, markdown-focused display
 */

// ============================================================
// COMPONENT REGISTRY
// ============================================================
window.KGComponents = window.KGComponents || {};

/** *text* safe to place in HTML, quotes included, so it can stand in an attribute too. */
KGComponents.escapeHtml = text => String(text ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** The name a card or detail view gives *item*. */
KGComponents.title = item => item.title || item.name || item.label || item.id || 'Untitled';

/** *href* when it is a web address or a path on this site, so data can never place a `javascript:` link. */
KGComponents.safeHref = href => (/^(https?:\/\/|\/)/.test(String(href)) ? href : null);

// ============================================================
// CARD COMPONENT
// ============================================================
/**
 * A result card, laid out from the item's KGTypes entry: the type, the title, the byline, a thumbnail or equation beside the description, the facts and the links. What a card shows is set in kg_types.js; how it looks, under `.kg-card` in kg_components.css.
 */
KGComponents.Card = {
    render(item, index) {
        const esc = KGComponents.escapeHtml;
        const entry = KGTypes.get(item.type);
        const isOntology = item.type === 'ontology';
        const title = KGComponents.title(item);
        const symbol = isOntology && item.symbol && item.symbol !== title ? `<span class="kg-card-symbol">${esc(item.symbol)}</span>` : '';
        const byline = entry.byline(item);
        const desc = [item.description, item.definition, item.ontology_instance?.description].find(text => text && text !== title) || '';
        const equation = entry.equation && item.equation_latex ? `<div class="kg-card-equation">$$${item.equation_latex}$$</div>` : '';
        const thumb = item.thumbnail ? `<img class="kg-card-thumb" src="${esc(item.thumbnail)}" alt="" loading="lazy" onerror="this.remove()">` : '';
        const facts = entry.facts.map(fact => fact(item)).filter(Boolean);
        const links = entry.links.map(link => link(item)).filter(link => link && KGComponents.safeHref(link.href));
        if (entry.builder && item.id != null) {
            links.push({ label: 'Open in Experiment Builder', href: `/tvbo/configurator?${entry.builder}=${encodeURIComponent(item.id)}`, local: true });
        }
        return `
            <article class="result-card kg-card" data-idx="${index}" tabindex="0" style="--kg-accent:${entry.color}">
                <p class="kg-card-type"><i class="${entry.icon}" aria-hidden="true"></i>${esc(isOntology ? item.ontology_type || entry.label : entry.label)}</p>
                <h3 class="kg-card-title">${esc(title)}${symbol}</h3>
                ${byline ? `<p class="kg-card-byline">${esc(byline)}</p>` : ''}
                ${thumb || equation || desc ? `<div class="kg-card-body">${thumb}<div class="kg-card-text">${equation}${desc ? `<p class="kg-card-desc">${esc(desc)}</p>` : ''}</div></div>` : ''}
                ${facts.length ? `<ul class="kg-card-facts">${facts.map(f => `<li title="${esc(f.value)}">${f.label ? `<span class="kg-fact-label">${esc(f.label)}</span>` : ''}${esc(f.value)}</li>`).join('')}</ul>` : ''}
                ${links.length ? `<p class="kg-card-links">${links.map(l => `<a class="${l.local ? 'kg-open-builder' : ''}" href="${esc(l.href)}"${l.local ? '' : ' target="_blank" rel="noopener"'} onclick="event.stopPropagation()">${esc(l.label)}</a>`).join('')}</p>` : ''}
            </article>`;
    },
};

// ============================================================
// METADATA COMPONENT
// ============================================================
/**
 * Everything the KG holds about an item, for the detail view: each field the view does not already show, then each link to other records and each record that links to this one, a KG record as a `/tvbo/kg?open=` link the browser opens in place. Labels and formats come from kg_types.js.
 */
KGComponents.Metadata = {
    /** Fields the detail view shows elsewhere, or that only the page itself uses. */
    hidden: new Set(['id', 'record_id', 'type', 'name', 'title', 'label', 'description', 'definition', 'thumbnail', 'report_url', 'equation_latex', 'related', 'used_by', 'copies', 'storid', 'tags', 'symbol', 'iri', 'is_a', 'requires', 'ontology_type']),

    render(item) {
        const esc = KGComponents.escapeHtml;
        const show = shown => {
            if (typeof shown !== 'object') return esc(shown);
            const href = KGComponents.safeHref(shown.href);
            return href ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(shown.text)}</a>` : esc(shown.text);
        };
        const linked = summary => summary.names.map((name, i) => (summary.type ? `<a href="/tvbo/kg?open=${summary.type}:${summary.ids[i]}">${esc(name)}</a>` : esc(name))).join(', ') + (summary.count > summary.names.length ? ` <span class="kg-metadata-more">and ${summary.count - summary.names.length} more</span>` : '');
        const rows = [];
        for (const [key, raw] of Object.entries(item)) {
            if (this.hidden.has(key) || key.startsWith('ontology_') || !KGTypes.filled(raw) || (typeof raw === 'object' && !Array.isArray(raw))) continue;
            const shown = KGTypes.format(key, raw);
            if (KGTypes.filled(shown)) rows.push([KGTypes.label(key), show(shown)]);
        }
        for (const [field, summary] of Object.entries(item.related || {})) {
            if (summary.names.length) rows.push([KGTypes.label(field), linked(summary) + esc(KGTypes.changes(summary))]);
        }
        for (const [type, summary] of Object.entries(item.used_by || {})) {
            if (summary.names.length) rows.push([`Linked from ${KGTypes.get(type).label.toLowerCase()}`, linked(summary)]);
        }
        for (const [label, node] of [['Ontology class', item.ontology_class], ['Ontology term', item.ontology_instance]]) {
            if (node?.storid) rows.push([label, linked({ names: [node.iri || node.label || node.name], ids: [node.storid], type: 'ontology', count: 1 })]);
        }
        if (!rows.length) return '';
        return `<section class="kg-metadata"><h4>Metadata</h4><dl>${rows.map(([label, html]) => `<dt>${esc(label)}</dt><dd>${html}</dd>`).join('')}</dl></section>`;
    },
};

// ============================================================
// DETAIL PANEL COMPONENT
// ============================================================
/**
 * Renders clean markdown-style detail content for any Knowledge Graph item
 * Uses renderMarkdownWithMath (from kg_browser.js) for proper LaTeX protection
 */
KGComponents.DetailPanel = class {
    constructor(options = {}) {
        this.options = { ...options };
    }

    /**
     * Render detail HTML for an item
     * @param {Object} item - The item data (can be ontology or database instance)
     * @param {Object} detailData - Optional additional detail data from API
     * @returns {string} HTML string
     */
    render(item, detailData = null) {
        const data = detailData || item;
        const isOntology = item.type === 'ontology';

        let md = [];

        // Type badge inline
        const typeLabel = this.formatTypeLabel(data);
        md.push(`**${typeLabel}**`);
        md.push('');

        // Description/Definition
        const desc = data.definition || data.description || data.desc || data.summary || data.abstract;
        if (desc) {
            md.push(desc);
            md.push('');
        }

        // IRI for ontology
        if (isOntology && data.iri) {
            md.push(`**IRI:** [${data.iri}](${data.iri})`);
            md.push('');
        }

        // Parent classes
        if (data.is_a && data.is_a.length > 0) {
            md.push(`**Parent Classes:** ${data.is_a.join(', ')}`);
            md.push('');
        }

        // Coupling function
        if (data.coupling_function) {
            md.push('');
            md.push('### Coupling Function');
            const cf = data.coupling_function;
            if (cf.label) md.push(`**${cf.label}**`);
            if (cf.definition) {
                md.push('');
                md.push(`$$${cf.definition}$$`);
            }
            md.push('');
        }

        // Parameters table
        if (data.parameters && data.parameters.length > 0) {
            md.push('');
            md.push('### Parameters');
            md.push('');
            md.push('| Name | Symbol | Default | Description |');
            md.push('|------|--------|---------|-------------|');
            for (const p of data.parameters) {
                const name = p.name || p.label || '';
                const symbol = p.symbol ? `$${p.symbol}$` : '';
                const value = p.value !== undefined && p.value !== null ? p.value : '';
                const pdesc = (p.description || '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
                md.push(`| ${name} | ${symbol} | ${value} | ${pdesc} |`);
            }
        }

        // State variables
        if (data.state_variables && data.state_variables.length > 0) {
            md.push('');
            md.push('### State Variables');
            md.push('');
            for (const sv of data.state_variables) {
                const label = sv.label || sv.name || '';
                const symbol = sv.symbol || '';
                const eq = sv.equation?.definition || sv.equation?.rhs || '';
                md.push(`**${label}**${symbol && symbol !== label ? ` ($${symbol}$)` : ''}`);
                if (sv.description) {
                    md.push('');
                    md.push(sv.description);
                }
                if (eq) {
                    md.push('');
                    md.push(`$$\\dot{${symbol || label}} = ${eq}$$`);
                }
                md.push('');
            }
        }

        // Ontology relationships, one line per relation and direction, each entity at the other end linked to its own detail
        if (data.relationships) {
            const rels = data.relationships;
            const centre = rels.center ? rels.center.storid : data.storid;
            const names = new Map((rels.nodes || []).map(n => [n.storid, n.label || n.name]));
            const groups = new Map();
            for (const link of rels.links || []) {
                const outgoing = link.source === centre;
                const other = outgoing ? link.target : link.source;
                if (other === centre || !names.has(other)) continue;
                const relation = (link.type || 'related to').split(/[/#:]/).pop().replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase();
                const heading = outgoing ? relation : `linked by ${relation} from`;
                if (!groups.has(heading)) groups.set(heading, new Set());
                groups.get(heading).add(`[${names.get(other)}](/tvbo/kg?open=ontology:${other})`);
            }
            if (groups.size) {
                md.push('', '### Relationships', '');
                groups.forEach((entries, heading) => md.push(`- **${heading}:** ${[...entries].join(', ')}`));
                md.push('');
            }
        }

        const markdown = md.join('\n');
        return `<div class="kg-detail-content">${this.renderMarkdown(markdown)}</div>`;
    }

    formatTypeLabel(data) {
        return data.ontology_type || KGTypes.get(data.type).label;
    }

    renderMarkdown(md) {
        // Use the global renderMarkdownWithMath (protects LaTeX from markdown parser)
        if (typeof renderMarkdownWithMath === 'function') {
            return renderMarkdownWithMath(md);
        }
        // Fallback if renderMarkdownWithMath not available yet
        if (typeof marked !== 'undefined' && marked.parse) {
            return marked.parse(md);
        }
        // Minimal fallback
        return md
            .replace(/^### (.+)$/gm, '<h4>$1</h4>')
            .replace(/^## (.+)$/gm, '<h3>$1</h3>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br/>');
    }

    /**
     * Trigger MathJax typesetting on a container
     */
    static typeset(container) {
        if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([container]).catch(() => {});
        }
    }
};

// ============================================================
// MODAL COMPONENT
// ============================================================
/**
 * Reusable modal dialog component
 */
KGComponents.Modal = class {
    constructor(options = {}) {
        this.id = options.id || 'kgModal';
        this.onClose = options.onClose || (() => {});
        this.onAction = options.onAction || (() => {});
        this.element = null;
        this.isOpen = false;
    }

    /**
     * Create the modal DOM element
     */
    create() {
        if (document.getElementById(this.id)) {
            this.element = document.getElementById(this.id);
            return this;
        }

        const modal = document.createElement('div');
        modal.id = this.id;
        modal.className = 'kg-modal hidden';
        modal.innerHTML = `
            <div class="kg-modal-backdrop"></div>
            <div class="kg-modal-dialog">
                <div class="kg-modal-header">
                    <div class="kg-modal-thumb-wrap"></div>
                    <h3 class="kg-modal-title"></h3>
                    <div class="kg-modal-actions">
                        <a class="kg-modal-builder-btn" href="#" title="Open in Experiment Builder" style="display:none;">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M14,3v2h3.59l-9.83,9.83l1.41,1.41L19,6.41V10h2V3M19,19H5V5h7V3H5C3.89,3,3,3.9,3,5v14a2,2 0 0,0 2,2h14a2,2 0 0,0 2-2v-7h-2V19Z"/>
                            </svg>
                            <span>Open in Builder</span>
                        </a>
                        <button class="kg-modal-action-btn labeled" data-action="download" title="Download as YAML — load it in Python with tvbo">
                            <svg viewBox="0 0 24 24" width="18" height="18">
                                <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                            </svg>
                            <span>Download for Python</span>
                        </button>
                        <button class="kg-modal-close" aria-label="Close">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="kg-modal-content"></div>
            </div>
        `;

        document.body.appendChild(modal);
        this.element = modal;
        this.bindEvents();

        return this;
    }

    bindEvents() {
        // Close on backdrop click
        this.element.querySelector('.kg-modal-backdrop').addEventListener('click', () => this.close());

        // Close on X button
        this.element.querySelector('.kg-modal-close').addEventListener('click', () => this.close());

        // Action buttons
        this.element.querySelectorAll('.kg-modal-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.onAction(action, this.currentData);
            });
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) this.close();
        });
    }

    /**
     * Open the modal with content
     * @param {string} title - Modal title
     * @param {string} content - HTML content
     * @param {Object} data - Original data object (for actions)
     */
    open(title, content, data = null, thumbnailUrl = null, typeInfo = null) {
        if (!this.element) this.create();

        this.currentData = data;
        this.element.querySelector('.kg-modal-title').textContent = title;

        // Builder deep-link: shown only when the caller supplies a builderUrl
        // (i.e. an entity type the Experiment Builder can load). Set here because
        // the modal DOM is created once and reused across entity types.
        const builderBtn = this.element.querySelector('.kg-modal-builder-btn');
        if (builderBtn) {
            const builderUrl = data && data.builderUrl;
            builderBtn.href = builderUrl || '#';
            builderBtn.style.display = builderUrl ? '' : 'none';
        }

        const thumbWrap = this.element.querySelector('.kg-modal-thumb-wrap');
        if (thumbnailUrl) {
            thumbWrap.innerHTML = `<img class="kg-modal-thumb" src="${thumbnailUrl}" alt="" onerror="this.parentElement.style.display='none'" />`;
            thumbWrap.style.display = '';
        } else if (typeInfo) {
            thumbWrap.innerHTML = `<span class="kg-modal-type-icon" style="background:${typeInfo.gradient}"><i class="${typeInfo.icon}"></i></span>`;
            thumbWrap.style.display = '';
        } else {
            thumbWrap.style.display = 'none';
        }
        this.element.querySelector('.kg-modal-content').innerHTML = content;

        this.element.classList.remove('hidden');
        this.element.classList.add('show');
        this.isOpen = true;

        // Typeset math
        KGComponents.DetailPanel.typeset(this.element.querySelector('.kg-modal-content'));

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    /**
     * Update modal content without closing/reopening
     * @param {string} content - New HTML content
     * @param {Object} data - Updated data object
     */
    updateContent(content, data = null) {
        if (!this.element || !this.isOpen) return;

        if (data) this.currentData = data;
        this.element.querySelector('.kg-modal-content').innerHTML = content;

        // Typeset math
        KGComponents.DetailPanel.typeset(this.element.querySelector('.kg-modal-content'));
    }

    close() {
        if (!this.element) return;

        this.element.classList.add('hidden');
        this.element.classList.remove('show');
        this.isOpen = false;
        this.currentData = null;

        document.body.style.overflow = '';
        this.onClose();
    }
};

// ============================================================
// TOOLTIP COMPONENT
// ============================================================
/**
 * Lightweight hover tooltip for graph nodes
 */
KGComponents.Tooltip = class {
    constructor() {
        this.element = null;
        this.visible = false;
    }

    create() {
        if (document.getElementById('kgTooltip')) {
            this.element = document.getElementById('kgTooltip');
            return this;
        }

        const tooltip = document.createElement('div');
        tooltip.id = 'kgTooltip';
        tooltip.className = 'kg-tooltip';
        document.body.appendChild(tooltip);
        this.element = tooltip;

        return this;
    }

    /**
     * Show tooltip at position
     * @param {Object} data - Node data
     * @param {number} x - Page X
     * @param {number} y - Page Y
     */
    show(data, x, y) {
        if (!this.element) this.create();

        const title = data.label || data.name || data.title || 'Unknown';
        const type = data.db_type || data.type || 'Class';
        const symbol = data.symbol;

        this.element.innerHTML = `
            <div class="kg-tooltip-header">
                <span class="kg-tooltip-title">${KGComponents.escapeHtml(title)}</span>
                ${symbol && symbol !== title ? `<span class="kg-tooltip-symbol">${symbol}</span>` : ''}
            </div>
            <span class="kg-tooltip-type">${this.formatType(type)}</span>
        `;

        // Position with viewport bounds check
        const rect = this.element.getBoundingClientRect();
        const padding = 10;
        let posX = x + padding;
        let posY = y - padding;

        if (posX + 200 > window.innerWidth) {
            posX = x - 200 - padding;
        }
        if (posY < 0) {
            posY = y + padding;
        }

        this.element.style.left = posX + 'px';
        this.element.style.top = posY + 'px';
        this.element.classList.add('visible');
        this.visible = true;
    }

    hide() {
        if (this.element) {
            this.element.classList.remove('visible');
            this.visible = false;
        }
    }

    formatType(type) {
        return KGTypes.get(type === 'Class' ? 'ontology' : type).label;
    }
};

console.log('🧩 KGComponents loaded');
