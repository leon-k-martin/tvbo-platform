/**
 * TVB-O Knowledge Graph UI Components
 * Modular, reusable UI elements shared across views
 * MVP: Clean, markdown-focused display
 */

// ============================================================
// COMPONENT REGISTRY
// ============================================================
window.KGComponents = window.KGComponents || {};

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

        // Basic metadata
        if (data.source) md.push(`**Source:** ${data.source}`);
        if (data.year) md.push(`**Year:** ${data.year}`);
        if (data.doi) md.push(`**DOI:** [${data.doi}](https://doi.org/${data.doi})`);
        if (data.journal) md.push(`**Journal:** ${data.journal}`);

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

        // Ontology relationships
        if (data.relationships) {
            const rels = data.relationships;
            if (rels.links && rels.links.length > 0) {
                md.push('');
                md.push('### Relationships');
                md.push('');
                for (const link of rels.links) {
                    const relLabel = (link.relation || link.type || 'related to').replace(/_/g, ' ');
                    const targetLabel = link.target_label || link.target_name || link.target || '';
                    if (targetLabel) {
                        md.push(`- **${relLabel}:** ${targetLabel}`);
                    }
                }
                md.push('');
            }
        }

        // Experiment components
        if (data.dynamics && typeof data.dynamics === 'object') {
            md.push('');
            md.push(`**Dynamics Model:** ${data.dynamics.name || data.dynamics.label || ''}`);
        }
        if (data.integration && typeof data.integration === 'object') {
            md.push(`**Integration:** ${data.integration.method || ''}`);
        }
        if (data.connectivity && typeof data.connectivity === 'object') {
            md.push(`**Connectivity:** ${data.connectivity.label || ''}`);
        }
        if (data.parcellation && typeof data.parcellation === 'object') {
            md.push(`**Parcellation:** ${data.parcellation.label || ''}`);
        }

        // References
        if (data.references) {
            md.push('');
            md.push('### References');
            md.push('');
            md.push(data.references);
        }

        // Tags as simple list
        if (data.tags && data.tags.length > 0) {
            md.push('');
            md.push(`**Tags:** ${data.tags.join(', ')}`);
        }

        // Remaining fields not already displayed
        const displayedKeys = new Set([
            'id', 'storid', 'type', 'ontology_type', 'name', 'label', 'title',
            'description', 'definition', 'desc', 'summary', 'abstract',
            'iri', 'is_a', 'source', 'year', 'doi', 'journal',
            'parameters', 'state_variables', 'tags', 'references',
            'coupling_function', 'relationships', 'dynamics', 'integration',
            'connectivity', 'parcellation', 'symbol', 'system_type',
            'report_md', 'thumbnail', 'full_model'
        ]);
        const extraFields = Object.entries(data).filter(
            ([k, v]) => !displayedKeys.has(k) && v !== undefined && v !== null && v !== ''
                && !(Array.isArray(v) && v.length === 0)
        );
        if (extraFields.length > 0) {
            md.push('');
            md.push('### Details');
            md.push('');
            for (const [key, value] of extraFields) {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                if (Array.isArray(value)) {
                    md.push(`**${label}:** ${value.join(', ')}`);
                } else if (typeof value === 'object') {
                    md.push(`**${label}:**`);
                    md.push('');
                    md.push('```');
                    md.push(JSON.stringify(value, null, 2));
                    md.push('```');
                } else {
                    md.push(`**${label}:** ${value}`);
                }
            }
        }

        const markdown = md.join('\n');
        const thumbHtml = item.thumbnail
            ? `<div style="text-align:center; margin-bottom:16px;"><img src="${item.thumbnail}" alt="" style="max-width:100%; border-radius:6px; box-shadow:0 1px 3px rgba(0,0,0,0.15)" onerror="this.parentElement.style.display='none'"/></div>`
            : '';
        return `<div class="kg-detail-content">${thumbHtml}${this.renderMarkdown(markdown)}</div>`;
    }

    formatTypeLabel(data) {
        if (data.ontology_type) return data.ontology_type;
        if (data.type === 'ontology') return 'Ontology Class';
        if (data.type) return data.type.charAt(0).toUpperCase() + data.type.slice(1);
        return 'Item';
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
                    <h3 class="kg-modal-title"></h3>
                    <div class="kg-modal-actions">
                        <button class="kg-modal-action-btn" data-action="download" title="Download as YAML">
                            <svg viewBox="0 0 24 24" width="18" height="18">
                                <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                            </svg>
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
    open(title, content, data = null) {
        if (!this.element) this.create();

        this.currentData = data;
        this.element.querySelector('.kg-modal-title').textContent = title;
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
                <span class="kg-tooltip-title">${this.escapeHtml(title)}</span>
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
        if (type === 'ontology' || type === 'Class') return 'Ontology Class';
        return type.charAt(0).toUpperCase() + type.slice(1);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

console.log('🧩 KGComponents loaded');
