/**
 * Network Topology Visualization
 * ===============================
 * Interactive D3.js force-directed graph for network topology visualization
 *
 * Features:
 * - Force-directed layout
 * - Zoom and pan
 * - Node dragging
 * - Interactive tooltips
 * - Color-coded security zones
 * - Edge labels
 *
 * 100% LOCAL - NO EXTERNAL APIs
 *
 * Author: Enterprise Security Team
 * Version: 3.0
 */

// Global variables
let svg, g, simulation;
let nodes = [], links = [];
let nodeElements, linkElements, linkLabelElements, labelElements;
let zoom;
let showLabels = true;
let showEdgeLabels = false;

// Zone colors
const zoneColors = {
    'WEB_TIER': '#3498db',
    'APP_TIER': '#2ecc71',
    'DATA_TIER': '#e74c3c',
    'MESSAGING_TIER': '#f39c12',
    'CACHE_TIER': '#9b59b6',
    'MANAGEMENT_TIER': '#1abc9c',
    'UNKNOWN': '#95a5a6'
};

/**
 * Initialize SVG and simulation
 */
function initSvg() {
    const container = d3.select('#topology-svg');
    const width = container.node().getBoundingClientRect().width;
    const height = 600;

    // Clear existing
    container.selectAll('*').remove();

    // Create SVG
    svg = container
        .attr('width', width)
        .attr('height', height);

    // Add zoom behavior
    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Create container group
    g = svg.append('g');

    // Add arrow markers for directed edges
    svg.append('defs').selectAll('marker')
        .data(['arrow'])
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#999');

    return { width, height };
}

/**
 * Create force simulation
 */
function createSimulation(width, height) {
    simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40))
        .on('tick', ticked);

    return simulation;
}

/**
 * Render topology graph
 */
function renderTopology(graph) {
    // Initialize
    const { width, height } = initSvg();

    // Process data
    nodes = graph.nodes.map(d => ({...d}));
    links = graph.edges.map(d => ({
        source: d.source,
        target: d.target,
        type: d.type,
        confidence: d.confidence
    }));

    // Create links
    linkElements = g.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('class', 'link')
        .attr('marker-end', 'url(#arrow)')
        .attr('stroke-width', d => Math.max(1, d.confidence * 3));

    // Create link labels
    linkLabelElements = g.append('g')
        .selectAll('text')
        .data(links)
        .enter().append('text')
        .attr('class', 'link-label')
        .attr('dy', -5)
        .style('display', showEdgeLabels ? 'block' : 'none')
        .text(d => d.type || '');

    // Create nodes
    nodeElements = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded))
        .on('click', (event, d) => {
            event.stopPropagation();
            showNodeDetails(d);
        })
        .on('mouseover', (event, d) => showTooltip(event, d))
        .on('mouseout', hideTooltip);

    // Add circles to nodes
    nodeElements.append('circle')
        .attr('r', 15)
        .attr('class', d => `zone-${d.zone || 'UNKNOWN'}`)
        .attr('fill', d => zoneColors[d.zone] || zoneColors['UNKNOWN']);

    // Add labels to nodes
    labelElements = nodeElements.append('text')
        .attr('dy', 25)
        .attr('text-anchor', 'middle')
        .style('font-size', '11px')
        .style('fill', '#333')
        .style('display', showLabels ? 'block' : 'none')
        .text(d => truncateLabel(d.label, 15));

    // Create simulation
    createSimulation(width, height);

    // Add slight delay for better animation
    simulation.alpha(1).restart();

    console.log(`Rendered topology: ${nodes.length} nodes, ${links.length} links`);
}

/**
 * Update positions on simulation tick
 */
function ticked() {
    // Update link positions
    linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

    // Update link label positions
    linkLabelElements
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2);

    // Update node positions
    nodeElements
        .attr('transform', d => `translate(${d.x},${d.y})`);
}

/**
 * Drag event handlers
 */
function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

/**
 * Show tooltip
 */
function showTooltip(event, d) {
    const tooltip = d3.select('#tooltip');

    let html = `<strong>${d.label}</strong><br/>`;
    html += `Zone: ${d.zone || 'Unknown'}<br/>`;

    if (d.characteristics && d.characteristics.length > 0) {
        html += `Characteristics: ${d.characteristics.join(', ')}`;
    }

    tooltip
        .style('opacity', 1)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
        .html(html);
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    d3.select('#tooltip').style('opacity', 0);
}

/**
 * Reset zoom to initial state
 */
function resetZoom() {
    svg.transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity);
}

/**
 * Center graph
 */
function centerGraph() {
    if (nodes.length === 0) return;

    const bounds = g.node().getBBox();
    const parent = svg.node().getBoundingClientRect();
    const fullWidth = parent.width;
    const fullHeight = parent.height;
    const width = bounds.width;
    const height = bounds.height;
    const midX = bounds.x + width / 2;
    const midY = bounds.y + height / 2;

    if (width === 0 || height === 0) return;

    const scale = 0.85 / Math.max(width / fullWidth, height / fullHeight);
    const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];

    svg.transition()
        .duration(750)
        .call(
            zoom.transform,
            d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        );
}

/**
 * Toggle node labels
 */
function toggleLabels() {
    showLabels = !showLabels;
    if (labelElements) {
        labelElements.style('display', showLabels ? 'block' : 'none');
    }
}

/**
 * Toggle edge labels
 */
function toggleEdgeLabels() {
    showEdgeLabels = !showEdgeLabels;
    if (linkLabelElements) {
        linkLabelElements.style('display', showEdgeLabels ? 'block' : 'none');
    }
}

/**
 * Truncate label to max length
 */
function truncateLabel(label, maxLength) {
    if (!label) return '';
    if (label.length <= maxLength) return label;
    return label.substring(0, maxLength - 3) + '...';
}

/**
 * Filter nodes by zone
 */
function filterByZone(zone) {
    if (!nodeElements) return;

    nodeElements.style('opacity', d => {
        if (zone === 'all') return 1;
        return d.zone === zone ? 1 : 0.2;
    });

    linkElements.style('opacity', d => {
        if (zone === 'all') return 0.6;
        return (d.source.zone === zone || d.target.zone === zone) ? 0.6 : 0.1;
    });
}

/**
 * Search nodes
 */
function searchNodes(query) {
    if (!nodeElements) return;

    const lowerQuery = query.toLowerCase();

    nodeElements.style('opacity', d => {
        if (!query) return 1;
        return d.label.toLowerCase().includes(lowerQuery) ? 1 : 0.2;
    });

    linkElements.style('opacity', d => {
        if (!query) return 0.6;
        const sourceMatch = d.source.label.toLowerCase().includes(lowerQuery);
        const targetMatch = d.target.label.toLowerCase().includes(lowerQuery);
        return (sourceMatch || targetMatch) ? 0.6 : 0.1;
    });
}

/**
 * Highlight node and its connections
 */
function highlightNode(nodeId) {
    if (!nodeElements) return;

    // Find connected nodes
    const connectedNodes = new Set([nodeId]);
    links.forEach(link => {
        if (link.source.id === nodeId) connectedNodes.add(link.target.id);
        if (link.target.id === nodeId) connectedNodes.add(link.source.id);
    });

    // Update opacity
    nodeElements.style('opacity', d => connectedNodes.has(d.id) ? 1 : 0.2);

    linkElements.style('opacity', d => {
        return (d.source.id === nodeId || d.target.id === nodeId) ? 0.8 : 0.1;
    });
}

/**
 * Clear all filters and highlights
 */
function clearFilters() {
    if (!nodeElements) return;

    nodeElements.style('opacity', 1);
    linkElements.style('opacity', 0.6);
}

/**
 * Export topology as image
 */
function exportTopologyAsImage() {
    const svgElement = document.getElementById('topology-svg');
    const svgString = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    canvas.width = svgElement.width.baseVal.value;
    canvas.height = svgElement.height.baseVal.value;

    img.onload = function() {
        ctx.drawImage(img, 0, 0);
        const pngFile = canvas.toDataURL('image/png');

        const downloadLink = document.createElement('a');
        downloadLink.download = 'network-topology.png';
        downloadLink.href = pngFile;
        downloadLink.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
}

/**
 * Calculate graph statistics
 */
function calculateGraphStats() {
    if (nodes.length === 0) return null;

    const stats = {
        nodeCount: nodes.length,
        edgeCount: links.length,
        avgDegree: (links.length * 2) / nodes.length,
        zones: {}
    };

    // Count nodes per zone
    nodes.forEach(node => {
        const zone = node.zone || 'UNKNOWN';
        stats.zones[zone] = (stats.zones[zone] || 0) + 1;
    });

    return stats;
}

/**
 * Get node by ID
 */
function getNodeById(nodeId) {
    return nodes.find(n => n.id === nodeId);
}

/**
 * Get links for node
 */
function getNodeLinks(nodeId) {
    return links.filter(l => l.source.id === nodeId || l.target.id === nodeId);
}

// Export functions for use in HTML
window.renderTopology = renderTopology;
window.resetZoom = resetZoom;
window.centerGraph = centerGraph;
window.toggleLabels = toggleLabels;
window.toggleEdgeLabels = toggleEdgeLabels;
window.filterByZone = filterByZone;
window.searchNodes = searchNodes;
window.highlightNode = highlightNode;
window.clearFilters = clearFilters;
window.exportTopologyAsImage = exportTopologyAsImage;
window.calculateGraphStats = calculateGraphStats;
window.getNodeById = getNodeById;
window.getNodeLinks = getNodeLinks;

console.log('✓ Topology visualization module loaded');
