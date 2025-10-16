/**
 * Network Segmentation Analyzer - Main JavaScript
 * Handles API calls, data fetching, and chart rendering
 */

// Global state
const state = {
    applications: [],
    zones: [],
    dnsData: null,
    charts: {}
};

// API Base URL
const API_BASE = '/api';

// ============================================================================
// API Functions
// ============================================================================

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

async function getApplications(zone = null) {
    const url = zone ? `/applications?zone=${zone}` : '/applications';
    return await fetchAPI(url);
}

async function getSecurityZones() {
    return await fetchAPI('/security-zones');
}

async function getDNSValidationSummary() {
    return await fetchAPI('/dns-validation/summary');
}

async function getZoneDistribution() {
    return await fetchAPI('/analytics/zone-distribution');
}

async function getDNSHealth() {
    return await fetchAPI('/analytics/dns-health');
}

async function getEnterpriseSummary() {
    return await fetchAPI('/enterprise/summary');
}

// ============================================================================
// Data Loading
// ============================================================================

async function loadData() {
    try {
        // Show loading state
        updateLastUpdated('Loading...');

        // Fetch all data in parallel
        const [
            appsData,
            zonesData,
            dnsData,
            zoneDistribution,
            dnsHealth,
            enterpriseData
        ] = await Promise.all([
            getApplications(),
            getSecurityZones(),
            getDNSValidationSummary(),
            getZoneDistribution(),
            getDNSHealth(),
            getEnterpriseSummary()
        ]);

        // Update state
        state.applications = appsData.applications || [];
        state.zones = zonesData.zones || [];
        state.dnsData = dnsData;

        // Update UI
        updateStats(appsData, zonesData, enterpriseData, dnsData);
        updateRecentApplications(state.applications.slice(0, 10));
        renderZoneChart(zoneDistribution);
        renderDNSChart(dnsHealth);

        // Update timestamp
        updateLastUpdated();

    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load dashboard data. Please refresh the page.');
    }
}

// ============================================================================
// UI Updates
// ============================================================================

function updateStats(appsData, zonesData, enterpriseData, dnsData) {
    // Total applications
    document.getElementById('total-apps').textContent =
        appsData.total || 0;

    // Total zones
    document.getElementById('total-zones').textContent =
        zonesData.total_zones || 0;

    // Total dependencies
    document.getElementById('total-dependencies').textContent =
        formatNumber(enterpriseData.statistics?.total_dependencies || 0);

    // DNS issues
    const dnsIssues = (dnsData.total_mismatches || 0) +
                     (dnsData.total_nxdomain || 0);
    document.getElementById('dns-issues').textContent = dnsIssues;

    // Update badge color based on DNS issues
    const dnsCard = document.getElementById('dns-issues').closest('.stat-card');
    if (dnsIssues === 0) {
        dnsCard.querySelector('.stat-icon').classList.remove('orange');
        dnsCard.querySelector('.stat-icon').classList.add('green');
    }
}

function updateRecentApplications(applications) {
    const tbody = document.getElementById('recent-apps');

    if (applications.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No applications found</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = applications.map(app => `
        <tr>
            <td>
                <strong>${app.app_id}</strong>
            </td>
            <td>
                <span class="zone-badge zone-${app.security_zone}">
                    ${app.security_zone}
                </span>
            </td>
            <td>${app.dependency_count}</td>
            <td>
                ${getDNSStatusBadge(app)}
            </td>
            <td>
                <a href="/application.html?id=${app.app_id}" class="btn-link">
                    View Details →
                </a>
            </td>
        </tr>
    `).join('');
}

function getDNSStatusBadge(app) {
    if (!app.dns_validated) {
        return '<span class="badge badge-info">Not Validated</span>';
    }

    if (app.dns_issues === 0) {
        return '<span class="badge badge-success">✓ Healthy</span>';
    } else if (app.dns_issues <= 3) {
        return `<span class="badge badge-warning">⚠ ${app.dns_issues} Issues</span>`;
    } else {
        return `<span class="badge badge-danger">✗ ${app.dns_issues} Issues</span>`;
    }
}

function updateLastUpdated(text = null) {
    const element = document.getElementById('last-updated');
    if (text) {
        element.textContent = text;
    } else {
        const now = new Date();
        element.textContent = now.toLocaleString();
    }
}

// ============================================================================
// Charts
// ============================================================================

function renderZoneChart(data) {
    const ctx = document.getElementById('zoneChart');
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.zoneChart) {
        state.charts.zoneChart.destroy();
    }

    // Zone colors
    const zoneColors = {
        'WEB_TIER': '#8b5cf6',
        'APP_TIER': '#3b82f6',
        'DATA_TIER': '#10b981',
        'CACHE_TIER': '#f59e0b',
        'MESSAGING_TIER': '#ec4899',
        'MANAGEMENT_TIER': '#6366f1',
        'UNKNOWN': '#9ca3af'
    };

    const colors = data.labels.map(label => zoneColors[label] || '#64748b');

    state.charts.zoneChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Applications',
                data: data.values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderDNSChart(data) {
    const ctx = document.getElementById('dnsChart');
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.dnsChart) {
        state.charts.dnsChart.destroy();
    }

    const colors = [
        '#10b981', // Valid - green
        '#3b82f6', // Multiple IPs - blue
        '#f59e0b', // Mismatches - orange
        '#ef4444', // NXDOMAIN - red
        '#6b7280'  // Failed - gray
    ];

    state.charts.dnsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'DNS Records',
                data: data.values,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = data.total_validated || 0;
                            const value = context.parsed.y || 0;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function showError(message) {
    console.error(message);
    // Could show toast notification here
}

function showSuccess(message) {
    console.log(message);
    // Could show toast notification here
}

// ============================================================================
// Initialization
// ============================================================================

// Make loadData available globally for refresh buttons
window.loadData = loadData;

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Network Segmentation Analyzer - Dashboard Loaded');
    loadData();
});
