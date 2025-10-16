/**
 * ActivNet Network Topology Visualization
 * Interactive graph visualization using Cytoscape.js
 */

let cy = null;
let graphData = null;
let selectedNode = null;

// Zone color mapping
const ZONE_COLORS = {
    'WEB_TIER': '#8b5cf6',
    'APP_TIER': '#3b82f6',
    'DATA_TIER': '#10b981',
    'CACHE_TIER': '#f59e0b',
    'MESSAGING_TIER': '#ec4899',
    'MANAGEMENT_TIER': '#6366f1',
    'UNKNOWN': '#6b7280',
    'EXTERNAL': '#94a3b8'
};

// ============================================================================
// Data Loading
// ============================================================================

async function loadTopologyData() {
    try {
        const response = await fetch('/api/dependencies/graph');
        graphData = await response.json();

        // Also get application metadata for enrichment
        const appsResponse = await fetch('/api/applications');
        const appsData = await appsResponse.json();

        // Create app metadata map
        const appMetadata = {};
        appsData.applications.forEach(app => {
            appMetadata[app.app_id] = app;
        });

        // Enrich nodes with metadata
        graphData.nodes.forEach(node => {
            const metadata = appMetadata[node.id];
            if (metadata) {
                node.confidence = metadata.confidence;
                node.dependency_count = metadata.dependency_count;
                node.dns_issues = metadata.dns_issues;
                node.dns_validated = metadata.dns_validated;
            }
        });

        updateStatistics();
        initializeGraph();
    } catch (error) {
        console.error('Error loading topology data:', error);
    }
}

function updateStatistics() {
    const uniqueZones = new Set(graphData.nodes.map(n => n.zone)).size;
    const avgDeps = graphData.edges.length / graphData.nodes.filter(n => n.type === 'application').length || 0;

    document.getElementById('stat-nodes').textContent = graphData.nodes.filter(n => n.type === 'application').length;
    document.getElementById('stat-edges').textContent = graphData.edges.length;
    document.getElementById('stat-zones').textContent = uniqueZones;
    document.getElementById('stat-density').textContent = avgDeps.toFixed(1);
}

// ============================================================================
// Graph Initialization
// ============================================================================

function initializeGraph() {
    const container = document.getElementById('cy');

    // Convert data to Cytoscape format
    const elements = [
        // Nodes
        ...graphData.nodes
            .filter(node => node.type === 'application') // Only show applications initially
            .map(node => ({
                data: {
                    id: node.id,
                    label: node.id,
                    zone: node.zone,
                    type: node.type,
                    confidence: node.confidence || 0,
                    dependency_count: node.dependency_count || 0,
                    dns_issues: node.dns_issues || 0,
                    dns_validated: node.dns_validated || 0
                }
            })),
        // Edges between applications
        ...graphData.edges
            .filter(edge => {
                // Only show edges between applications we're displaying
                const sourceIsApp = graphData.nodes.find(n => n.id === edge.source && n.type === 'application');
                const targetIsApp = graphData.nodes.find(n => n.id === edge.target && n.type === 'application');
                return sourceIsApp && targetIsApp;
            })
            .map(edge => ({
                data: {
                    id: `${edge.source}-${edge.target}`,
                    source: edge.source,
                    target: edge.target,
                    type: edge.type
                }
            }))
    ];

    // Initialize Cytoscape
    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            // Node styles
            {
                selector: 'node',
                style: {
                    'background-color': function(ele) {
                        return ZONE_COLORS[ele.data('zone')] || ZONE_COLORS['UNKNOWN'];
                    },
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-outline-color': function(ele) {
                        return ZONE_COLORS[ele.data('zone')] || ZONE_COLORS['UNKNOWN'];
                    },
                    'text-outline-width': 2,
                    'font-size': '12px',
                    'font-weight': '600',
                    'width': function(ele) {
                        // Size by dependency count
                        const depCount = ele.data('dependency_count') || 0;
                        return Math.min(80, Math.max(30, 30 + depCount * 2));
                    },
                    'height': function(ele) {
                        const depCount = ele.data('dependency_count') || 0;
                        return Math.min(80, Math.max(30, 30 + depCount * 2));
                    },
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-margin-y': 5,
                    'border-width': function(ele) {
                        // Highlight if has DNS issues
                        return ele.data('dns_issues') > 0 ? 4 : 0;
                    },
                    'border-color': '#ef4444'
                }
            },
            // Edge styles
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#cbd5e1',
                    'target-arrow-color': '#cbd5e1',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.5,
                    'opacity': 0.6
                }
            },
            // Selected node
            {
                selector: 'node:selected',
                style: {
                    'border-width': 6,
                    'border-color': '#667eea',
                    'border-opacity': 1
                }
            },
            // Connected edges
            {
                selector: 'edge:selected',
                style: {
                    'line-color': '#667eea',
                    'target-arrow-color': '#667eea',
                    'width': 4,
                    'opacity': 1
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 1000,
            nodeRepulsion: 8000,
            idealEdgeLength: 100,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1000,
            randomize: false
        },
        minZoom: 0.1,
        maxZoom: 3,
        wheelSensitivity: 0.2
    });

    // Add event listeners
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        selectedNode = node.data();
        showNodeInfo(node.data());
    });

    cy.on('tap', function(evt) {
        if (evt.target === cy) {
            hideNodeInfo();
        }
    });

    // Double click to zoom to node
    cy.on('dbltap', 'node', function(evt) {
        const node = evt.target;
        cy.animate({
            zoom: 1.5,
            center: {
                eles: node
            }
        }, {
            duration: 500
        });
    });

    // Hover effects
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        node.style('opacity', 1);

        // Highlight connected edges
        node.connectedEdges().style({
            'line-color': '#667eea',
            'target-arrow-color': '#667eea',
            'opacity': 1,
            'width': 3
        });
    });

    cy.on('mouseout', 'node', function(evt) {
        const node = evt.target;
        node.style('opacity', 1);

        // Reset connected edges
        node.connectedEdges().style({
            'line-color': '#cbd5e1',
            'target-arrow-color': '#cbd5e1',
            'opacity': 0.6,
            'width': 2
        });
    });
}

// ============================================================================
// Node Information Panel
// ============================================================================

function showNodeInfo(data) {
    const panel = document.getElementById('node-info');

    document.getElementById('info-app-id').textContent = data.id;
    document.getElementById('info-zone').textContent = data.zone;
    document.getElementById('info-deps').textContent = data.dependency_count;
    document.getElementById('info-confidence').textContent = `${(data.confidence * 100).toFixed(0)}%`;
    document.getElementById('info-dns').textContent = data.dns_issues > 0
        ? `${data.dns_issues} issues`
        : 'No issues';

    // Color code DNS issues
    const dnsElement = document.getElementById('info-dns');
    if (data.dns_issues > 0) {
        dnsElement.style.color = '#ef4444';
        dnsElement.style.fontWeight = '700';
    } else {
        dnsElement.style.color = '#10b981';
        dnsElement.style.fontWeight = '500';
    }

    panel.classList.add('show');
}

function hideNodeInfo() {
    document.getElementById('node-info').classList.remove('show');
    selectedNode = null;
}

function viewAppDetails() {
    if (selectedNode) {
        window.location.href = `/application.html?id=${selectedNode.id}`;
    }
}

// ============================================================================
// Layout Control
// ============================================================================

function changeLayout(layoutName) {
    if (!cy) return;

    // Update button states
    document.querySelectorAll('.layout-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    const layoutConfig = {
        name: layoutName,
        animate: true,
        animationDuration: 1000
    };

    // Add specific configurations for each layout
    if (layoutName === 'cose') {
        Object.assign(layoutConfig, {
            nodeRepulsion: 8000,
            idealEdgeLength: 100,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1000,
            randomize: false
        });
    } else if (layoutName === 'concentric') {
        Object.assign(layoutConfig, {
            concentric: function(node) {
                return node.data('dependency_count') || 1;
            },
            levelWidth: function(nodes) {
                return 2;
            }
        });
    } else if (layoutName === 'circle') {
        Object.assign(layoutConfig, {
            radius: 300,
            startAngle: 0,
            sweep: 2 * Math.PI
        });
    } else if (layoutName === 'grid') {
        Object.assign(layoutConfig, {
            rows: undefined,
            cols: undefined
        });
    }

    cy.layout(layoutConfig).run();
}

function fitGraph() {
    if (cy) {
        cy.fit(null, 50);
        cy.center();
    }
}

// ============================================================================
// Filtering
// ============================================================================

document.getElementById('zone-filter').addEventListener('change', function(e) {
    const selectedZone = e.target.value;

    if (!cy) return;

    if (selectedZone === '') {
        // Show all nodes
        cy.nodes().style('display', 'element');
        cy.edges().style('display', 'element');
    } else {
        // Hide nodes not in selected zone
        cy.nodes().forEach(node => {
            if (node.data('zone') === selectedZone) {
                node.style('display', 'element');
            } else {
                node.style('display', 'none');
            }
        });

        // Show only edges between visible nodes
        cy.edges().forEach(edge => {
            const sourceZone = edge.source().data('zone');
            const targetZone = edge.target().data('zone');

            if (sourceZone === selectedZone || targetZone === selectedZone) {
                edge.style('display', 'element');
            } else {
                edge.style('display', 'none');
            }
        });
    }

    // Refit the graph
    cy.fit(cy.nodes(':visible'), 50);
});

// ============================================================================
// Export
// ============================================================================

function exportGraph() {
    if (!cy) return;

    // Export as PNG
    const png = cy.png({
        output: 'blob',
        bg: '#f9fafb',
        full: true,
        scale: 2
    });

    // Create download link
    const url = URL.createObjectURL(png);
    const link = document.createElement('a');
    link.href = url;
    link.download = `network_topology_${new Date().toISOString().split('T')[0]}.png`;
    link.click();
    URL.revokeObjectURL(url);
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', loadTopologyData);
