/**
 * TVB-O Knowledge Graph Browser
 * API-powered faceted search interface
 */

// Render Markdown while protecting LaTeX math
function renderMarkdownWithMath(md) {
    if (!md || typeof md !== 'string') return '';

    const codePlaceholders = [];
    let codeIdx = 0;
    const protectCode = (text) => {
        text = text.replace(/```[\s\S]*?```/g, (m) => {
            const key = `@@CODE_BLOCK_${codeIdx++}@@`;
            codePlaceholders.push({ key, val: m });
            return key;
        });
        text = text.replace(/`[^`]*`/g, (m) => {
            const key = `@@CODE_INLINE_${codeIdx++}@@`;
            codePlaceholders.push({ key, val: m });
            return key;
        });
        return text;
    };

    const restoreCode = (html) => {
        codePlaceholders.forEach(({ key, val }) => {
            html = html.split(key).join(val);
        });
        return html;
    };

    const mathPlaceholders = [];
    let mathIdx = 0;
    const protectMath = (text) => {
        text = text.replace(/\$\$[\s\S]*?\$\$/g, (m) => {
            const key = `@@MATH_BLOCK_${mathIdx++}@@`;
            mathPlaceholders.push({ key, val: m });
            return key;
        });
        let out = '';
        for (let i = 0; i < text.length; i++) {
            if (text[i] === '$') {
                if (text[i + 1] === '$') {
                    out += '$$';
                    i += 1;
                    continue;
                }
                let j = i + 1;
                let found = -1;
                while (j < text.length) {
                    if (text[j] === '$' && text[j - 1] !== '\\') { found = j; break; }
                    j++;
                }
                if (found !== -1) {
                    const segment = text.slice(i, found + 1);
                    const key = `@@MATH_INLINE_${mathIdx++}@@`;
                    mathPlaceholders.push({ key, val: segment });
                    out += key;
                    i = found;
                } else {
                    out += text[i];
                }
            } else {
                out += text[i];
            }
        }
        return out;
    };

    let safe = protectCode(md);
    safe = protectMath(safe);

    let html = (window.marked && window.marked.parse)
        ? window.marked.parse(safe)
        : safe
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br/>');

    mathPlaceholders.forEach(({ key, val }) => {
        html = html.split(key).join(val);
    });
    html = restoreCode(html);

    return html;
}

// Ensure KGComponents is available
if (typeof window.KGComponents === 'undefined') {
    console.error('KGComponents not loaded! Make sure kg_components.js is loaded before kg_browser.js');
    window.KGComponents = {};
}

class KnowledgeGraphBrowser {
    constructor() {
        console.log('🏗️ KnowledgeGraphBrowser constructor called');
        this.originalData = [];
        this.schema = null;
        this.classSchemas = null; // Class schemas from Pydantic models
        this.currentFilters = {};
        this.currentQuery = '';
        this.collapsedFacets = new Set();
        this.lastResultIndices = [];
        this.currentSort = 'relevance';
        this.currentModalItem = null;
        this.searchIndex = new Map();
        this.facetIndex = {};
        this.currentView = 'list'; // 'list' or 'graph'
        this.graphViz = null;
        this._previousSelectedTypes = []; // Track type selection changes

        // Initialize modular components (with fallbacks)
        if (window.KGComponents.DetailPanel) {
            this.detailPanel = new KGComponents.DetailPanel();
        }
        if (window.KGComponents.Modal) {
            this.modal = new KGComponents.Modal({
                id: 'kgDetailModal',
                onAction: (action, data) => this.handleModalAction(action, data)
            });
            this.modal.create();
        }

        this.init();
    }

    async init() {
        try {
            console.log('📡 Fetching data from API...');
            await this.loadData();
            console.log('📚 Building search index...');
            this.searchIndex = this.buildSearchIndex();
            console.log('✅ Search index built:', this.searchIndex.size, 'tokens');
            console.log('🏷️ Building facet index...');
            this.facetIndex = this.buildFacetIndex();
            console.log('✅ Facet index built');
            console.log('🎧 Setting up event listeners...');
            this.setupEventListeners();

            // Check for search query in URL (from header search)
            const urlParams = new URLSearchParams(window.location.search);
            const queryFromUrl = urlParams.get('q');
            if (queryFromUrl) {
                console.log('🔗 Found search query in URL:', queryFromUrl);
                const searchBox = document.getElementById('searchBox');
                if (searchBox) {
                    searchBox.value = queryFromUrl;
                }
                this.currentQuery = queryFromUrl;
            }

            console.log('🔍 Performing initial search...');
            this.search();

            // Check URL hash for view state
            this.initViewFromHash();

            console.log('✅ Browser initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing browser:', error);
            this.showError('Failed to load data. Please try refreshing the page.');
        }
    }

    async loadData() {
        // Fetch schema, class schemas, and data in parallel
        const [schemaResponse, classSchemaResponse, dataResponse] = await Promise.all([
            fetch('/tvbo/api/kg/schema'),
            fetch('/tvbo/api/kg/schema/classes'),
            fetch('/tvbo/api/kg/data'),
        ]);

        if (!schemaResponse.ok) throw new Error('Failed to fetch schema');
        this.schema = await schemaResponse.json();
        console.log('📊 Schema loaded:', this.schema);

        if (classSchemaResponse.ok) {
            this.classSchemas = await classSchemaResponse.json();
            console.log('🏛️ Class schemas loaded:', Object.keys(this.classSchemas));
        } else {
            console.warn('⚠️ Class schemas not available, property filters disabled');
            this.classSchemas = {};
        }

        if (!dataResponse.ok) throw new Error('Failed to fetch data');
        this.originalData = await dataResponse.json();
        console.log('📦 Data loaded:', this.originalData.length, 'items');

        if (this.originalData.length === 0) {
            console.warn('⚠️ No data returned from API');
        }
    }

    showError(message) {
        const resultsGrid = document.getElementById('resultsGrid');
        if (resultsGrid) {
            resultsGrid.innerHTML = `
                <div class="no-results">
                    <div style="font-size: 4rem; margin-bottom: 20px;">⚠️</div>
                    <h3>Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
        const perfInfo = document.getElementById('performanceInfo');
        if (perfInfo) {
            perfInfo.textContent = 'Error loading data';
        }
    }

    buildSearchIndex() {
        console.log('Building search index for', this.originalData.length, 'items');
        const index = new Map();
        this.originalData.forEach((item, idx) => {
            const searchText = this.schema.searchableFields
                .map(field => {
                    const value = item[field];
                    if (value === undefined || value === null) {
                        return '';
                    }
                    if (Array.isArray(value)) {
                        return value.join(' ');
                    }
                    return String(value);
                })
                .join(' ')
                .toLowerCase();
            const tokens = searchText.split(/\s+/).filter(token => token.length > 0);
            tokens.forEach(token => {
                if (!index.has(token)) {
                    index.set(token, new Set());
                }
                index.get(token).add(idx);
            });
        });
        console.log('Search index created with', index.size, 'unique tokens');
        return index;
    }

    buildFacetIndex() {
        // Index all schema-defined facets AND all properties from class schemas
        const fieldsToIndex = new Map(); // field -> type ('string' or 'array')

        // Schema-defined facets
        this.schema.facets.forEach(facet => {
            fieldsToIndex.set(facet.field, facet.type);
        });

        // All property fields from class schemas
        if (this.classSchemas) {
            for (const schema of Object.values(this.classSchemas)) {
                for (const fieldName of Object.keys(schema.properties)) {
                    if (!fieldsToIndex.has(fieldName)) {
                        fieldsToIndex.set(fieldName, 'string');
                    }
                }
            }
        }

        console.log('Building facet index for fields:', [...fieldsToIndex.keys()]);
        const index = {};
        fieldsToIndex.forEach((type, field) => {
            index[field] = new Map();
            this.originalData.forEach((item, idx) => {
                const value = item[field];
                if (value === undefined || value === null || value === '') return;

                if (type === 'array' || Array.isArray(value)) {
                    const arr = Array.isArray(value) ? value : [value];
                    arr.forEach(val => {
                        if (val !== undefined && val !== null && val !== '') {
                            const key = String(val);
                            if (!index[field].has(key)) index[field].set(key, new Set());
                            index[field].get(key).add(idx);
                        }
                    });
                } else {
                    const key = String(value);
                    if (!index[field].has(key)) index[field].set(key, new Set());
                    index[field].get(key).add(idx);
                }
            });
            if (index[field].size > 0) {
                console.log(`Facet ${field} indexed with`, index[field].size, 'unique values');
            }
        });
        return index;
    }

    setupEventListeners() {
        let searchTimeout;
        const searchBox = document.getElementById('searchBox');
        const searchForm = document.getElementById('globalSearchForm');

        // Prevent form submission on KG browser page - use live search instead
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                if (searchBox) {
                    this.currentQuery = searchBox.value;
                    this.search();
                }
            });
        }

        if (searchBox) {
            searchBox.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentQuery = e.target.value;
                    this.search();
                }, 150);
            });
        }

        document.addEventListener('click', (e) => {
            if (e.target.closest('.facet-item')) {
                this.handleFacetClick(e.target.closest('.facet-item'));
            } else if (e.target.closest('.facet-header')) {
                this.handleFacetToggle(e.target.closest('.facet-header'));
            } else if (e.target.closest('.result-card')) {
                const card = e.target.closest('.result-card');
                const idxRaw = card?.dataset?.idx;
                const idx = parseInt(idxRaw);
                if (!isNaN(idx)) {
                    const item = this.originalData[idx];
                    this.openModal(item);
                }
            }
        });

        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        const sortSel = document.getElementById('sortSelect');
        if (sortSel) {
            sortSel.addEventListener('change', () => {
                this.currentSort = sortSel.value || 'relevance';
                const items = this.lastResultIndices.map(idx => this.originalData[idx]);
                this.renderResults(items);
            });
        }

        // Note: Modal events are handled by KGComponents.Modal

        // View toggle handlers
        const listViewBtn = document.getElementById('listViewBtn');
        const graphViewBtn = document.getElementById('graphViewBtn');

        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => this.switchView('list'));
        }
        if (graphViewBtn) {
            graphViewBtn.addEventListener('click', () => this.switchView('graph'));
        }

        // Listen for hash changes (browser back/forward)
        window.addEventListener('hashchange', () => this.initViewFromHash());
    }

    /**
     * Initialize view based on URL hash
     */
    initViewFromHash() {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'graph') {
            this.switchView('graph', false); // false = don't update hash again
        } else if (hash === 'list' || !hash) {
            this.switchView('list', false);
        }
    }

    async switchView(view, updateHash = true) {
        this.currentView = view;

        // Update URL hash for bookmarkability
        if (updateHash) {
            history.replaceState(null, '', `#${view}`);
        }

        const resultsGrid = document.getElementById('resultsGrid');
        const graphContainer = document.getElementById('graphContainer');
        const listViewBtn = document.getElementById('listViewBtn');
        const graphViewBtn = document.getElementById('graphViewBtn');

        if (view === 'list') {
            resultsGrid?.classList.remove('hidden');
            graphContainer?.classList.add('hidden');
            listViewBtn?.classList.add('active');
            graphViewBtn?.classList.remove('active');

            // Cleanup graph
            if (this.graphViz) {
                this.graphViz.destroy();
                this.graphViz = null;
            }
        } else {
            resultsGrid?.classList.add('hidden');
            graphContainer?.classList.remove('hidden');
            listViewBtn?.classList.remove('active');
            graphViewBtn?.classList.add('active');

            // Initialize graph visualization with current filters
            if (window.KnowledgeGraphVisualization) {
                this.graphViz = new window.KnowledgeGraphVisualization();
                // Pass filtered item IDs to the graph (null = show all)
                const hasActiveFilters = this.currentQuery || Object.keys(this.currentFilters).length > 0;
                this.graphViz.setFilteredItems(hasActiveFilters ? this.getFilteredItemIds() : null);
                await this.graphViz.init();
            }
        }
    }

    /**
     * Get the IDs of currently filtered items (for graph filtering)
     */
    getFilteredItemIds() {
        return this.lastResultIndices.map(idx => {
            const item = this.originalData[idx];
            return {
                id: item.id,
                type: item.type,
                storid: item.storid
            };
        });
    }

    handleFacetClick(facetItem) {
        const filterKey = facetItem.dataset.filter;
        const value = facetItem.dataset.value;

        if (!this.currentFilters[filterKey]) {
            this.currentFilters[filterKey] = [];
        }

        const index = this.currentFilters[filterKey].indexOf(value);
        if (index > -1) {
            this.currentFilters[filterKey].splice(index, 1);
            if (this.currentFilters[filterKey].length === 0) {
                delete this.currentFilters[filterKey];
            }
        } else {
            this.currentFilters[filterKey].push(value);
        }

        // When the type filter changes, clear property filters that no longer apply
        if (filterKey === 'type') {
            this._cleanupPropertyFilters();
        }

        this.search();
    }

    /**
     * Remove property filters that don't belong to any currently selected type.
     */
    _cleanupPropertyFilters() {
        const selectedTypes = this.currentFilters['type'] || [];
        if (selectedTypes.length === 0) {
            // No types selected — remove all property filters
            this._removeAllPropertyFilters();
            return;
        }
        // Collect all valid property field names for selected types
        const validFields = new Set();
        selectedTypes.forEach(type => {
            const schema = this.classSchemas?.[type];
            if (schema) {
                Object.keys(schema.properties).forEach(f => validFields.add(f));
            }
        });
        // Remove filters for fields not in any selected type
        Object.keys(this.currentFilters).forEach(key => {
            if (key !== 'type' && key !== 'tags' && !this.schema.facets.some(f => f.field === key) && !validFields.has(key)) {
                delete this.currentFilters[key];
            }
        });
    }

    /**
     * Remove all property-level filters (keep only schema-defined facets).
     */
    _removeAllPropertyFilters() {
        const schemaFields = new Set(this.schema.facets.map(f => f.field));
        Object.keys(this.currentFilters).forEach(key => {
            if (!schemaFields.has(key)) {
                delete this.currentFilters[key];
            }
        });
    }

    handleFacetToggle(header) {
        const group = header.parentElement;
        const field = group.dataset.field;
        if (this.collapsedFacets.has(field)) {
            this.collapsedFacets.delete(field);
            group.classList.remove('collapsed');
        } else {
            this.collapsedFacets.add(field);
            group.classList.add('collapsed');
        }
    }

    clearAllFilters() {
        this.currentFilters = {};
        this.currentQuery = '';
        const searchBox = document.getElementById('searchBox');
        if (searchBox) {
            searchBox.value = '';
        }
        this.search();
    }

    search() {
        const startTime = performance.now();
        let results = new Set();

        // Text search
        if (this.currentQuery && this.currentQuery.length > 0) {
            const query = this.currentQuery.toLowerCase();
            const tokens = query.split(/\s+/).filter(token => token.length > 0);

            if (tokens.length === 0) {
                results = new Set(this.originalData.map((_, idx) => idx));
            } else {
                tokens.forEach((token, tokenIdx) => {
                    const matching = new Set();
                    this.searchIndex.forEach((indices, indexToken) => {
                        if (indexToken.includes(token)) {
                            indices.forEach(idx => matching.add(idx));
                        }
                    });

                    if (tokenIdx === 0) {
                        results = matching;
                    } else {
                        results = new Set([...results].filter(idx => matching.has(idx)));
                    }
                });
            }
        } else {
            results = new Set(this.originalData.map((_, idx) => idx));
        }

        // Apply filters
        Object.entries(this.currentFilters).forEach(([field, values]) => {
            if (values && values.length > 0) {
                const matchingIndices = new Set();
                values.forEach(value => {
                    const indices = this.facetIndex[field]?.get(value);
                    if (indices) {
                        indices.forEach(idx => matchingIndices.add(idx));
                    }
                });
                results = new Set([...results].filter(idx => matchingIndices.has(idx)));
            }
        });

        const resultItems = [...results].map(idx => this.originalData[idx]);
        this.lastResultIndices = [...results];

        const endTime = performance.now();
        const searchTime = (endTime - startTime).toFixed(2);

        this.renderFacets(results);
        this.renderResults(resultItems);

        // Update graph if it's currently visible
        if (this.currentView === 'graph' && this.graphViz) {
            const hasActiveFilters = this.currentQuery || Object.keys(this.currentFilters).length > 0;
            if (hasActiveFilters) {
                this.graphViz.setFilteredItems(this.getFilteredItemIds());
            } else {
                this.graphViz.setFilteredItems(null); // Show all
            }
            this.graphViz.applyFilters();
        }

        const perfInfo = document.getElementById('performanceInfo');
        if (perfInfo) {
            perfInfo.textContent = `Found ${resultItems.length} results in ${searchTime}ms`;
        }
    }

    renderFacets(currentResults) {
        const facetsSidebar = document.getElementById('facetsSidebar');
        if (!facetsSidebar) return;
        facetsSidebar.innerHTML = '';

        // Render standard schema-defined facets (Class, Tags, etc.)
        this.schema.facets.forEach(facet => {
            const group = this._buildFacetGroup(facet, currentResults, this.originalData);
            if (group) facetsSidebar.appendChild(group);
        });

        // Render dynamic property facets based on selected types
        const selectedTypes = this.currentFilters['type'] || [];
        if (selectedTypes.length > 0 && this.classSchemas) {
            // Collect ALL items of the selected types (for facet value counting)
            const allTypeItems = this.originalData.filter(item => selectedTypes.includes(item.type));
            // Collect indices of filtered items matching selected types
            const typeItemIndices = [];
            currentResults.forEach(idx => {
                const item = this.originalData[idx];
                if (selectedTypes.includes(item.type)) {
                    typeItemIndices.push(idx);
                }
            });

            // For each selected type, build property facets
            selectedTypes.forEach(typeKey => {
                const classSchema = this.classSchemas[typeKey];
                if (!classSchema) return;

                const propsWithValues = this._getFilterableProperties(typeKey, classSchema, typeItemIndices);
                if (propsWithValues.length === 0) return;

                // Section header for this class
                const sectionHeader = document.createElement('div');
                sectionHeader.className = 'property-section-header';
                const classLabel = this.formatClassName(classSchema.label || classSchema.class_name);
                sectionHeader.innerHTML = `<span class="material-icons" style="font-size:16px;">tune</span> ${this.escapeHtml(classLabel)}`;
                facetsSidebar.appendChild(sectionHeader);

                propsWithValues.forEach(({ fieldName, propSchema, values }) => {
                    const facetDef = {
                        field: fieldName,
                        label: propSchema.label,
                        type: 'string',
                    };
                    // Pass only items of selected types for property facet counting
                    const group = this._buildFacetGroup(facetDef, currentResults, allTypeItems);
                    if (group) {
                        group.classList.add('property-facet');
                        facetsSidebar.appendChild(group);
                    }
                });
            });
        }
    }

    /**
     * Determine which properties of a class are worth showing as facets.
     * A property is filterable if it has 2+ unique values across items of this type,
     * and at most 30 unique values (otherwise it's too unique to be useful).
     */
    _getFilterableProperties(typeKey, classSchema, typeItemIndices) {
        const result = [];
        // Fields already handled as top-level facets
        const skipFields = new Set(this.schema.facets.map(f => f.field));
        // Also skip fields that are identity-like
        skipFields.add('id');
        skipFields.add('title');
        skipFields.add('thumbnail');
        skipFields.add('ontology_class');
        skipFields.add('ontology_instance');

        for (const [fieldName, propSchema] of Object.entries(classSchema.properties)) {
            if (skipFields.has(fieldName)) continue;
            // Skip text-heavy fields (name, description, label, iri)
            if (['name', 'description', 'label', 'iri', 'has_reference', 'abstract', 'doi', 'key', 'definition'].includes(fieldName)) continue;

            // Count unique values
            const uniqueValues = new Set();
            typeItemIndices.forEach(idx => {
                const item = this.originalData[idx];
                const val = item[fieldName];
                if (val !== undefined && val !== null && val !== '') {
                    if (propSchema.type === 'boolean') {
                        uniqueValues.add(String(val));
                    } else {
                        uniqueValues.add(String(val));
                    }
                }
            });

            // Show as facet if 1+ values exist (shows what data has) and not too many unique values
            if (uniqueValues.size >= 1 && uniqueValues.size <= 30) {
                result.push({ fieldName, propSchema, values: uniqueValues });
            }
        }
        return result;
    }

    /**
     * Build a single facet group element.
     */
    _buildFacetGroup(facet, currentResults, allData) {
        // Get all possible values from the full dataset
        const allFacetValues = new Map();
        allData.forEach((item) => {
            const value = item[facet.field];
            if (facet.type === 'array' && Array.isArray(value)) {
                value.forEach(val => {
                    if (val) {
                        const key = String(val);
                        if (!allFacetValues.has(key)) allFacetValues.set(key, 0);
                    }
                });
            } else if (value !== undefined && value !== null && value !== '') {
                const key = String(value);
                if (!allFacetValues.has(key)) allFacetValues.set(key, 0);
            }
        });

        // Count matches in current results
        currentResults.forEach(idx => {
            const item = this.originalData[idx];
            const value = item[facet.field];

            if (facet.type === 'array' && Array.isArray(value)) {
                value.forEach(val => {
                    if (val) {
                        const key = String(val);
                        allFacetValues.set(key, (allFacetValues.get(key) || 0) + 1);
                    }
                });
            } else if (value !== undefined && value !== null && value !== '') {
                const key = String(value);
                allFacetValues.set(key, (allFacetValues.get(key) || 0) + 1);
            }
        });

        if (allFacetValues.size === 0) return null;

        // For the type facet, use class labels from schema
        const labelMap = {};
        if (facet.field === 'type' && this.classSchemas) {
            for (const [typeKey, schema] of Object.entries(this.classSchemas)) {
                const raw = schema.label || schema.class_name || typeKey;
                labelMap[typeKey] = this.formatClassName(raw);
            }
        }

        const facetGroup = document.createElement('div');
        facetGroup.className = 'facet-group';
        facetGroup.dataset.field = facet.field;
        if (this.collapsedFacets.has(facet.field)) {
            facetGroup.classList.add('collapsed');
        }

        const header = document.createElement('div');
        header.className = 'facet-header';
        header.innerHTML = `<span class="facet-title">${facet.label}</span>`;
        facetGroup.appendChild(header);

        const content = document.createElement('div');
        content.className = 'facet-content';

        // Sort by total count from full dataset (stable order regardless of current filters)
        const totalCounts = new Map();
        allData.forEach((item) => {
            const value = item[facet.field];
            if (facet.type === 'array' && Array.isArray(value)) {
                value.forEach(val => {
                    if (val) { const key = String(val); totalCounts.set(key, (totalCounts.get(key) || 0) + 1); }
                });
            } else if (value !== undefined && value !== null && value !== '') {
                const key = String(value);
                totalCounts.set(key, (totalCounts.get(key) || 0) + 1);
            }
        });
        const sortedValues = [...allFacetValues.entries()].sort((a, b) => (totalCounts.get(b[0]) || 0) - (totalCounts.get(a[0]) || 0));

        sortedValues.forEach(([value, count]) => {
            const facetItem = document.createElement('div');
            facetItem.className = 'facet-item';
            facetItem.dataset.filter = facet.field;
            facetItem.dataset.value = value;

            const isActive = this.currentFilters[facet.field] &&
                            this.currentFilters[facet.field].includes(value);
            if (isActive) facetItem.classList.add('active');
            if (count === 0 && !isActive) facetItem.classList.add('dimmed');

            const displayLabel = labelMap[value] || value;

            facetItem.innerHTML = `
                <input type="checkbox" class="facet-checkbox" ${isActive ? 'checked' : ''}>
                <span class="facet-label">${this.escapeHtml(displayLabel)}</span>
                <span class="facet-count">${count}</span>
            `;

            content.appendChild(facetItem);
        });

        facetGroup.appendChild(content);
        return facetGroup;
    }

    renderResults(items) {
        const resultsGrid = document.getElementById('resultsGrid');
        const resultsCount = document.getElementById('resultsCount');

        if (resultsCount) {
            resultsCount.textContent = `${items.length} result${items.length !== 1 ? 's' : ''}`;
        }

        if (!resultsGrid) return;

        if (items.length === 0) {
            resultsGrid.innerHTML = `
                <div class="no-results">
                    <div style="font-size: 4rem; margin-bottom: 20px;">🔍</div>
                    <h3>No items found</h3>
                    <p>Try adjusting your filters or search terms</p>
                </div>
            `;
            return;
        }

        let sortedItems = items;
        if (this.currentSort === 'az' || this.currentSort === 'za') {
            sortedItems = [...items]
                .map((it, i) => ({ it, idx: this.lastResultIndices[i] }))
                .sort((a, b) => {
                    const ta = String(this.getItemTitle(a.it) || '').toLowerCase();
                    const tb = String(this.getItemTitle(b.it) || '').toLowerCase();
                    const cmp = ta.localeCompare(tb);
                    return this.currentSort === 'az' ? cmp : -cmp;
                })
                .map(x => x.it);
        }

        resultsGrid.innerHTML = sortedItems.map((item, i) => {
            const originalIdx = this.lastResultIndices[i];
            const title = this.getItemTitle(item);
            const desc = this.truncateText(this.getItemDescription(item), 150);
            const type = (item.type || '').toLowerCase();
            const isOntology = type === 'ontology';
            const ontologyType = item.ontology_type || '';

            // Determine icon and styling from TVBO icon registry
            const typeInfo = KnowledgeGraphBrowser.TYPE_ICONS[type] || KnowledgeGraphBrowser.TYPE_ICONS._default;
            const typeLabel = isOntology ? (ontologyType || 'Ontology') : (item.type || '');

            const typeBadge = typeLabel
                ? `<span class="badge type-badge" style="background:${typeInfo.gradient};"><i class="${typeInfo.icon}"></i>${typeLabel}</span>`
                : '';
            const studyMeta = (item.type === 'study') ? this.getStudyMeta(item) : '';

            // Show symbol for ontology items
            const symbolDisplay = isOntology && item.symbol && item.symbol !== title
                ? `<span class="ontology-symbol">${item.symbol}</span>` : '';

            // Thumbnail
            const thumb = item.thumbnail
                ? `<img class="card-thumb" src="${item.thumbnail}" alt="" onerror="this.style.display='none'">`
                : '';

            const header = `
                <div class="field-display" style="margin-bottom:6px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    <span class="field-value" style="font-weight:700; color:#2d3748; font-size:1.05rem;">${this.escapeHtml(title)}</span>
                    ${symbolDisplay}
                    ${typeBadge}
                </div>`;
            // Show equation for coupling items
            const eqDisplay = item.equation
                ? `<div class="card-equation">${this.escapeHtml(item.equation)}</div>`
                : '';

            const body = desc || thumb || eqDisplay ? `
                <div class="card-body">
                    ${thumb}
                    <div class="card-desc">${eqDisplay}<span class="field-value" style="color:#4a5568;">${this.escapeHtml(desc)}</span></div>
                </div>` : '';

            // Show tags if available
            const tags = item.tags && item.tags.length > 0
                ? `<div class="card-tags">${item.tags.map(t => `<span class="tag-pill">${this.escapeHtml(t)}</span>`).join('')}</div>`
                : '';

            return `
                <div class="result-card" data-idx="${originalIdx}">
                    ${header}
                    ${studyMeta}
                    ${body}
                    ${tags}
                </div>
            `;
        }).join('');
    }

    getStudyMeta(item) {
        const parts = [];
        if (item.year) parts.push(String(item.year));
        if (item.journal) parts.push(item.journal);
        if (item.doi) {
            const doiUrl = item.doi.startsWith('http') ? item.doi : `https://doi.org/${item.doi}`;
            parts.push(`<a href="${doiUrl}" target="_blank" onclick="event.stopPropagation()">doi</a>`);
        }
        if (parts.length === 0) return '';
        return `<div class="field-display"><span class="field-value" style="color:#718096; font-size: 0.9rem;">${parts.join(' · ')}</span></div>`;
    }

    getItemTitle(item) {
        return item.title || item.name || item.label || item.id || 'Untitled';
    }

    truncateText(text, maxLen = 200) {
        if (!text) return '';
        const clean = String(text).replace(/\s+/g, ' ').trim();
        if (clean.length <= maxLen) return clean;
        const cutoff = clean.lastIndexOf(' ', maxLen);
        if (cutoff > Math.floor(maxLen * 0.6)) {
            return clean.slice(0, cutoff).trimEnd() + '…';
        }
        return clean.slice(0, maxLen).trimEnd() + '…';
    }

    getItemDescription(item) {
        return item.description || item.desc || item.summary || item.abstract || '';
    }

    async openModal(item) {
        this.currentModalItem = item;
        const title = this.getItemTitle(item);

        // Show modal IMMEDIATELY with loading placeholder
        const type = (item.type || '').toLowerCase();
        const typeInfo = KnowledgeGraphBrowser.TYPE_ICONS[type] || KnowledgeGraphBrowser.TYPE_ICONS._default;
        if (this.modal) {
            this.modal.open(title, `<div class="kg-detail-content"><p style="color:#a0aec0">Loading report...</p></div>`, { item, detailData: null }, item.thumbnail || null, typeInfo);
        }

        // Strategy: try pre-rendered report first, fall back to detail API
        if (item.report_url) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                const resp = await fetch(item.report_url, { signal: controller.signal });
                clearTimeout(timeoutId);

                if (resp.ok && this.currentModalItem === item) {
                    const reportMd = await resp.text();
                    const reportHtml = typeof renderMarkdownWithMath === 'function'
                        ? renderMarkdownWithMath(reportMd)
                        : (typeof marked !== 'undefined' ? marked.parse(reportMd) : reportMd);
                    const content = `<div class="kg-detail-content"><div class="model-report">${reportHtml}</div></div>`;
                    if (this.modal && this.modal.isOpen) {
                        this.modal.updateContent(content, { item });
                        // Typeset math
                        const el = document.getElementById('modalContent') || document.querySelector('.modal-content');
                        if (el && window.MathJax && window.MathJax.typesetPromise) {
                            window.MathJax.typesetPromise([el]).catch(() => {});
                        }
                    }
                    return;
                }
            } catch (e) {
                // Fall through to detail API
            }
        }

        // Fall back to detail API
        const isOntology = item.type === 'ontology';
        try {
            let url = null;
            if (isOntology && item.storid) {
                url = `/tvbo/api/kg/ontology/node/${item.storid}`;
            } else if (item.id) {
                const typeRoutes = {
                    'model': 'dynamics', 'dynamics': 'dynamics',
                    'network': 'network', 'coupling': 'coupling',
                    'integrator': 'integrator', 'experiment': 'experiment',
                    'study': 'study'
                };
                const route = typeRoutes[item.type];
                if (route) {
                    url = `/tvbo/api/kg/${route}/${item.id}`;
                }
            }

            if (url) {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 3000);
                const resp = await fetch(url, { signal: controller.signal });
                clearTimeout(timeoutId);

                if (resp.ok && this.currentModalItem === item) {
                    const detailData = await resp.json();
                    const fullContent = this.detailPanel ? this.detailPanel.render(item, detailData) : '';
                    if (this.modal && this.modal.isOpen) {
                        this.modal.updateContent(fullContent, { item, detailData });
                    }
                }
            }
        } catch (e) {
            // Silently ignore - modal already shows basic data
        }
    }

    handleModalAction(action, data) {
        if (action === 'download' && data) {
            this.downloadItem(data.item);
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.close();
        }
        this.currentModalItem = null;
    }

    downloadItem(item) {
        if (!item) return;
        const yaml = this.objectToYAML(item);
        const filename = (item.title || item.name || 'item').replace(/\s+/g, '_') + '.yaml';
        const blob = new Blob([yaml], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    objectToYAML(obj, indent = 0) {
        const pad = '  '.repeat(indent);
        let yaml = '';

        Object.entries(obj).forEach(([key, value]) => {
            if (value === undefined || value === null) return;

            yaml += `${pad}${key}:`;

            if (Array.isArray(value)) {
                yaml += '\n';
                value.forEach(item => {
                    if (typeof item === 'object') {
                        yaml += `${pad}- ${this.objectToYAML(item, indent + 1).trim()}\n`;
                    } else {
                        yaml += `${pad}- ${item}\n`;
                    }
                });
            } else if (typeof value === 'object') {
                yaml += '\n' + this.objectToYAML(value, indent + 1);
            } else {
                yaml += ` ${value}\n`;
            }
        });

        return yaml;
    }

    formatLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Split CamelCase into readable words: "SimulationExperiment" → "Simulation Experiment"
     */
    formatClassName(name) {
        return name.replace(/([a-z])([A-Z])/g, '$1 $2');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Icon & gradient registry — mirrors TVBO_ICONS from docs
KnowledgeGraphBrowser.TYPE_ICONS = {
    dynamics:    { icon: 'fa-solid fa-wave-square',          gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#667eea' },
    model:       { icon: 'fa-solid fa-wave-square',          gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#667eea' },
    network:     { icon: 'fa-solid fa-diagram-project',      gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: '#43e97b' },
    coupling:    { icon: 'fa-solid fa-arrow-right-arrow-left', gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)', color: '#a18cd1' },
    integrator:  { icon: 'fa-solid fa-gears',                gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: '#4facfe' },
    experiment:  { icon: 'fa-solid fa-flask',                 gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: '#fa709a' },
    study:       { icon: 'fa-solid fa-book-open',             gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)', color: '#f7971e' },
    ontology:    { icon: 'fa-solid fa-share-nodes',           gradient: 'linear-gradient(135deg, #c471f5 0%, #fa71cd 100%)', color: '#c471f5' },
    _default:    { icon: 'fa-solid fa-tag',                   gradient: 'linear-gradient(135deg, #a0aec0 0%, #718096 100%)', color: '#a0aec0' },
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 DOM ready, initializing Knowledge Graph Browser...');
    window.kgBrowser = new KnowledgeGraphBrowser();
});
