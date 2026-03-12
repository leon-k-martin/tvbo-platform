/**
 * TVB-O Knowledge Graph Visualization
 * D3.js force-directed graph for ontology + database items
 */

class KnowledgeGraphVisualization {
    constructor() {
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.allNodes = [];  // All nodes before filtering
        this.allLinks = [];  // All links before filtering
        this.filteredItemIds = null;  // Set of filtered item IDs (null = show all)
        this.width = 0;
        this.height = 0;
        this.zoom = null;
        this.g = null;
        this.selectedNode = null;
        this.limit = 500; // Default limit - must be high enough to include core ontology classes

        // Color scheme for node types — matches KnowledgeGraphBrowser.TYPE_ICONS
        this.colors = {
            'Class': '#667eea',
            'instance': '#48bb78',
            'dynamics': '#667eea',
            'network': '#43e97b',
            'integrator': '#4facfe',
            'experiment': '#fa709a',
            'study': '#f7971e',
            'coupling': '#a18cd1',
            'ontology': '#c471f5',
        };
    }

    /**
     * Set filtered items from the browser's search/filter results
     * @param {Array} items - Array of {id, type, storid} objects
     */
    setFilteredItems(items) {
        if (!items || items.length === 0) {
            this.filteredItemIds = null; // Show all
            return;
        }

        // Create a Set of node IDs that should be visible
        this.filteredItemIds = new Set();
        items.forEach(item => {
            // Database items have format: db_<type>_<id>
            if (item.type && item.type !== 'ontology') {
                this.filteredItemIds.add(`db_${item.type}_${item.id}`);
            }
            // Ontology items have format: onto_<storid>
            if (item.storid) {
                this.filteredItemIds.add(`onto_${item.storid}`);
            }
        });
    }

    async init() {
        const container = document.getElementById('graphContainer');
        const svgEl = document.getElementById('graphSvg');
        if (!container || !svgEl) return;

        this.width = container.clientWidth;
        this.height = container.clientHeight || 600;

        this.svg = d3.select('#graphSvg')
            .attr('width', this.width)
            .attr('height', this.height);

        // Clear previous content
        this.svg.selectAll('*').remove();

        // Add zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // Create main group for zooming
        this.g = this.svg.append('g');

        // Add arrow marker for directed edges
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('path')
            .attr('d', 'M 0,-5 L 10,0 L 0,5')
            .attr('fill', '#999');

        // Setup controls
        this.setupControls();

        // Load and render graph
        await this.loadGraph();
    }

    setupControls() {
        document.getElementById('graphZoomIn')?.addEventListener('click', () => {
            this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.3);
        });

        document.getElementById('graphZoomOut')?.addEventListener('click', () => {
            this.svg.transition().duration(300).call(this.zoom.scaleBy, 0.7);
        });

        document.getElementById('graphReset')?.addEventListener('click', () => {
            this.resetToLargestCluster();
        });
    }

    /**
     * Center and zoom to fit all visible nodes
     */
    resetToLargestCluster() {
        if (!this.nodes || this.nodes.length === 0) {
            this.svg.transition().duration(300).call(
                this.zoom.transform,
                d3.zoomIdentity.translate(this.width / 2, this.height / 2).scale(0.5)
            );
            return;
        }

        // Calculate bounding box of all visible nodes
        let cx = 0, cy = 0;
        this.nodes.forEach(n => {
            cx += n.x || 0;
            cy += n.y || 0;
        });
        cx /= this.nodes.length;
        cy /= this.nodes.length;

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        this.nodes.forEach(n => {
            minX = Math.min(minX, n.x || 0);
            maxX = Math.max(maxX, n.x || 0);
            minY = Math.min(minY, n.y || 0);
            maxY = Math.max(maxY, n.y || 0);
        });

        const clusterWidth = maxX - minX + 100;
        const clusterHeight = maxY - minY + 100;
        const scaleX = this.width / clusterWidth;
        const scaleY = this.height / clusterHeight;
        const scale = Math.min(scaleX, scaleY, 1.5) * 0.9;

        // Transform to center on cluster
        this.svg.transition().duration(300).call(
            this.zoom.transform,
            d3.zoomIdentity
                .translate(this.width / 2, this.height / 2)
                .scale(scale)
                .translate(-cx, -cy)
        );
    }

    async loadGraph() {
        try {
            this.showLoading();

            // Use limit parameter for better performance
            const url = `/tvbo/api/kg/graph?limit=${this.limit}`;
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();

            // Store all nodes and links for filtering
            this.allNodes = data.nodes || [];
            this.allLinks = data.links || [];

            if (this.allNodes.length === 0) {
                this.showError('No graph data available');
                return;
            }

            // Apply current filters
            this.applyFiltersInternal();

            this.render();
            this.renderLegend(data.stats || {});
        } catch (error) {
            console.error('Failed to load graph:', error);
            this.showError(`Failed to load graph: ${error.message}`);
        }
    }

    /**
     * Apply filters from the browser sidebar to the graph
     * Called when filters change while graph is visible
     */
    applyFilters() {
        if (this.allNodes.length === 0) return; // Not loaded yet

        // Stop old simulation before re-rendering
        if (this.simulation) {
            this.simulation.stop();
            this.simulation = null;
        }

        this.applyFiltersInternal();

        // Re-render with filtered data
        if (this.g) {
            this.g.selectAll('*').remove();
        }
        this.render();

        // Update legend with filtered counts
        this.renderLegend({
            ontology_classes: this.nodes.filter(n => n.type === 'Class' || !n.db_type).length,
            database_items: this.nodes.filter(n => n.db_type).length,
            total_links: this.links.length
        });
    }

    /**
     * Internal method to apply filter logic.
     * When filters are active, only shows matching DB items plus
     * the ontology nodes they connect to (and their hierarchy ancestors).
     */
    applyFiltersInternal() {
        if (!this.filteredItemIds) {
            // No filter - show all
            this.nodes = [...this.allNodes];
            this.links = [...this.allLinks];
            return;
        }

        // Build lookup of all links by source/target storid for fast traversal
        // Links use storid values (int for ontology, string for DB items)
        const getLinkId = (end) => typeof end === 'object' ? (end.storid ?? end.id) : end;

        // Step 1: Find matching DB nodes and directly matched ontology nodes
        const matchedDbStorids = new Set();
        const connectedOntoStorids = new Set();
        this.allNodes.forEach(node => {
            if (node.id.startsWith('onto_')) {
                // Ontology item explicitly in filter results (e.g. type=ontology facet)
                if (this.filteredItemIds.has(node.id)) {
                    connectedOntoStorids.add(node.storid);
                    connectedOntoStorids.add(node.id);
                }
            } else if (this.filteredItemIds.has(node.id)) {
                matchedDbStorids.add(node.storid);
                matchedDbStorids.add(node.id);
            }
        });

        // Step 2: Find ontology nodes directly linked to matched DB items
        this.allLinks.forEach(link => {
            const srcId = getLinkId(link.source);
            const tgtId = getLinkId(link.target);
            if (matchedDbStorids.has(srcId)) connectedOntoStorids.add(tgtId);
            if (matchedDbStorids.has(tgtId)) connectedOntoStorids.add(srcId);
        });

        // Step 3: Walk up is_a hierarchy to include ancestor ontology classes
        let changed = true;
        while (changed) {
            changed = false;
            this.allLinks.forEach(link => {
                if (link.type !== 'is_a') return;
                const srcId = getLinkId(link.source);
                const tgtId = getLinkId(link.target);
                // is_a: source → target means source is subclass of target
                if (connectedOntoStorids.has(srcId) && !connectedOntoStorids.has(tgtId)) {
                    connectedOntoStorids.add(tgtId);
                    changed = true;
                }
            });
        }

        // Step 4: Filter nodes — keep matched DB items + connected ontology nodes
        const visibleNodeIds = new Set();
        this.nodes = this.allNodes.filter(node => {
            if (node.id.startsWith('onto_')) {
                if (connectedOntoStorids.has(node.storid) || connectedOntoStorids.has(node.id)) {
                    visibleNodeIds.add(node.id);
                    visibleNodeIds.add(node.storid);
                    return true;
                }
                return false;
            }
            if (this.filteredItemIds.has(node.id)) {
                visibleNodeIds.add(node.id);
                visibleNodeIds.add(node.storid);
                return true;
            }
            return false;
        });

        // Step 5: Filter links to only include visible nodes
        this.links = this.allLinks.filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
        });
    }

    showLoading() {
        const container = document.getElementById('graphContainer');
        if (container) {
            // Clear any existing error messages but keep SVG structure
            const existing = container.querySelector('.graph-loading');
            if (!existing) {
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'graph-loading';
                loadingDiv.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; text-align: center;';
                loadingDiv.innerHTML = `
                    <div style="font-size: 2rem;">⏳</div>
                    <p>Loading knowledge graph...</p>
                `;
                container.style.position = 'relative';
                container.appendChild(loadingDiv);
            }
        }
    }

    hideLoading() {
        const loading = document.querySelector('.graph-loading');
        if (loading) loading.remove();
    }

    showError(message) {
        const container = document.getElementById('graphContainer');
        if (container) {
            container.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #e53e3e;">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem;">⚠️</div>
                        <p>${message}</p>
                        <button onclick="window.kgBrowser?.graphViz?.init()" style="margin-top: 10px; padding: 8px 16px; cursor: pointer;">Retry</button>
                    </div>
                </div>
            `;
        }
    }

    render() {
        this.hideLoading();

        // Create link elements
        const link = this.g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', d => d.type === 'instance_of' ? '#48bb78' : '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => d.type === 'instance_of' ? 2 : 1)
            .attr('marker-end', 'url(#arrowhead)');

        // Create node elements
        const node = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(this.nodes)
            .join('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)));

        // Add circles to nodes
        // Ontology classes: filled with color, white stroke
        // DB instances: hollow (white fill), colored stroke
        node.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => d.db_type ? '#fff' : this.getNodeColor(d))
            .attr('stroke', d => d.db_type ? this.getNodeColor(d) : '#fff')
            .attr('stroke-width', d => d.db_type ? 2.5 : 2);

        // Add labels
        node.append('text')
            .text(d => this.truncateLabel(d.label || d.name || ''))
            .attr('x', 0)
            .attr('y', d => this.getNodeRadius(d) + 12)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('fill', '#4a5568');

        // Add tooltip on hover
        node.on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip())
            .on('click', (event, d) => this.handleNodeClick(event, d));

        // Pre-position isolated nodes (no links) in a row below the center
        // so they stay near the main cluster instead of flying off
        const connectedNodeIds = new Set();
        this.links.forEach(l => {
            const srcId = typeof l.source === 'object' ? (l.source.storid || l.source.id) : l.source;
            const tgtId = typeof l.target === 'object' ? (l.target.storid || l.target.id) : l.target;
            connectedNodeIds.add(srcId);
            connectedNodeIds.add(tgtId);
        });
        const isolatedNodes = this.nodes.filter(n => {
            const nid = n.storid || n.id;
            return !connectedNodeIds.has(nid);
        });
        if (isolatedNodes.length > 0) {
            const cols = Math.ceil(Math.sqrt(isolatedNodes.length));
            const spacing = 50;
            const startX = this.width / 2 - ((cols - 1) * spacing) / 2;
            const startY = this.height / 2 + 150; // Below center
            isolatedNodes.forEach((n, i) => {
                const col = i % cols;
                const row = Math.floor(i / cols);
                n.fx = startX + col * spacing;
                n.fy = startY + row * spacing;
            });
        }

        // Create force simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links)
                .id(d => d.storid || d.id)
                .distance(80))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 5))
            .alphaDecay(0.05);  // Settle faster (~60 ticks instead of ~300)

        // Update positions on tick
        let tickCount = 0;
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);

            // Zoom to fit once layout has roughly stabilized
            tickCount++;
            if (tickCount === 30) {
                // Release isolated node pins so they can be dragged
                isolatedNodes.forEach(n => { n.fx = null; n.fy = null; });
                this.resetToLargestCluster();
            }
        });
    }

    getNodeRadius(node) {
        if (node.type === 'instance') return 6;
        if (node.db_type) return 8;
        return 10; // Ontology classes
    }

    getNodeColor(node) {
        if (node.db_type) return this.colors[node.db_type] || this.colors.instance;
        if (node.type === 'instance') return this.colors.instance;
        return this.colors[node.type] || this.colors.Class;
    }

    truncateLabel(text, maxLen = 15) {
        if (text.length <= maxLen) return text;
        return text.slice(0, maxLen - 1) + '…';
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    showTooltip(event, node) {
        // Use modular tooltip component
        if (!this.tooltip) {
            this.tooltip = new KGComponents.Tooltip();
        }
        this.tooltip.show(node, event.pageX, event.pageY);
    }

    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.hide();
        }
    }

    handleNodeClick(event, node) {
        event.stopPropagation();

        // Highlight connected nodes
        const connectedIds = new Set();
        this.links.forEach(l => {
            const sourceId = l.source.storid || l.source.id || l.source;
            const targetId = l.target.storid || l.target.id || l.target;
            const nodeId = node.storid || node.id;

            if (sourceId === nodeId) connectedIds.add(targetId);
            if (targetId === nodeId) connectedIds.add(sourceId);
        });

        this.g.selectAll('.node circle')
            .attr('opacity', d => {
                const dId = d.storid || d.id;
                const nodeId = node.storid || node.id;
                return dId === nodeId || connectedIds.has(dId) ? 1 : 0.2;
            });

        this.g.selectAll('.links line')
            .attr('opacity', l => {
                const sourceId = l.source.storid || l.source.id || l.source;
                const targetId = l.target.storid || l.target.id || l.target;
                const nodeId = node.storid || node.id;
                return sourceId === nodeId || targetId === nodeId ? 1 : 0.1;
            });

        // Open modal with details
        if (window.kgBrowser && node.db_type) {
            const dbItem = window.kgBrowser.originalData.find(item =>
                item.id === node.id?.replace(`db_${node.db_type}_`, '') ||
                `db_${item.type}_${item.id}` === node.id
            );
            if (dbItem) window.kgBrowser.openModal(dbItem);
        }
    }

    resetHighlight() {
        this.g.selectAll('.node circle').attr('opacity', 1);
        this.g.selectAll('.links line').attr('opacity', 0.6);
    }

    renderLegend(stats) {
        const legend = document.getElementById('graphLegend');
        if (!legend) return;

        const instanceTypes = [
            { label: 'Dynamics', color: this.colors.dynamics },
            { label: 'Network', color: this.colors.network },
            { label: 'Integrator', color: this.colors.integrator },
            { label: 'Experiment', color: this.colors.experiment },
            { label: 'Study', color: this.colors.study },
            { label: 'Coupling', color: this.colors.coupling },
        ];

        legend.innerHTML = `
            <div class="legend-title">Legend</div>
            <div class="legend-item">
                <span class="legend-color" style="background:${this.colors.Class}"></span>
                <span class="legend-label">Ontology Class</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background:#fff;border:2.5px solid #718096"></span>
                <span class="legend-label">Instance</span>
            </div>
            ${instanceTypes.map(t => `
                <div class="legend-item" style="padding-left:18px">
                    <span class="legend-color" style="background:#fff;border:2.5px solid ${t.color}"></span>
                    <span class="legend-label">${t.label}</span>
                </div>
            `).join('')}
            <div class="legend-stats">
                <div>Classes: ${stats.ontology_classes}</div>
                <div>Instances: ${stats.database_items}</div>
                <div>Links: ${stats.total_links}</div>
            </div>
        `;
    }

    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        this.svg?.selectAll('*').remove();
    }
}

// Export for use in kg_browser.js
window.KnowledgeGraphVisualization = KnowledgeGraphVisualization;
