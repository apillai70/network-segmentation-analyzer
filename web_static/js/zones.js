/**
 * ActivNet Security Zones Analysis
 * Zone security posture, segmentation analysis, and recommendations
 */

let zoneData = null;
let charts = {};

// Zone configuration and security profiles
const ZONE_CONFIG = {
    'WEB_TIER': {
        color: '#8b5cf6',
        icon: 'fa-globe',
        description: 'Public-facing web applications and load balancers',
        security_level: 'high',
        expected_dependencies: 'Low to moderate (3-8)'
    },
    'APP_TIER': {
        color: '#3b82f6',
        icon: 'fa-cogs',
        description: 'Application servers and business logic',
        security_level: 'critical',
        expected_dependencies: 'Moderate to high (5-15)'
    },
    'DATA_TIER': {
        color: '#10b981',
        icon: 'fa-database',
        description: 'Databases and data storage systems',
        security_level: 'critical',
        expected_dependencies: 'Very low (0-3)'
    },
    'CACHE_TIER': {
        color: '#f59e0b',
        icon: 'fa-bolt',
        description: 'Caching layers (Redis, Memcached)',
        security_level: 'medium',
        expected_dependencies: 'Low (1-5)'
    },
    'MESSAGING_TIER': {
        color: '#ec4899',
        icon: 'fa-comments',
        description: 'Message queues and event streaming',
        security_level: 'medium',
        expected_dependencies: 'Low to moderate (2-8)'
    },
    'MANAGEMENT_TIER': {
        color: '#6366f1',
        icon: 'fa-tools',
        description: 'Management and monitoring systems',
        security_level: 'high',
        expected_dependencies: 'Very high (10+)'
    }
};

// ============================================================================
// Data Loading
// ============================================================================

async function loadZoneData() {
    try {
        const [zonesResponse, appsResponse] = await Promise.all([
            fetch('/api/security-zones'),
            fetch('/api/applications')
        ]);

        const zones = await zonesResponse.json();
        const apps = await appsResponse.json();

        zoneData = {
            zones: zones.zones || [],
            applications: apps.applications || [],
            totalZones: zones.total_zones || 0,
            totalApps: zones.total_apps || 0
        };

        // Calculate enhanced metrics
        const analytics = analyzeZones(zoneData);

        // Update UI
        updateStats(analytics);
        renderZoneCards(analytics);
        renderComparisonTable(analytics);
        renderRecommendations(analytics);
        renderCharts(analytics);

    } catch (error) {
        console.error('Error loading zone data:', error);
    }
}

// ============================================================================
// Zone Analysis
// ============================================================================

function analyzeZones(data) {
    const zones = data.zones;
    const apps = data.applications;

    // Calculate security scores for each zone
    const zoneAnalytics = zones.map(zone => {
        const zoneApps = apps.filter(app => app.security_zone === zone.name);
        const config = ZONE_CONFIG[zone.name] || {};

        // Calculate security score (0-100)
        const securityScore = calculateZoneSecurityScore(zone, zoneApps, config);

        // Determine risk level
        const riskLevel = determineRiskLevel(securityScore, zoneApps);

        // Generate recommendations
        const recommendations = generateZoneRecommendations(zone, zoneApps, config, securityScore);

        return {
            ...zone,
            config,
            security_score: securityScore,
            risk_level: riskLevel,
            recommendations,
            app_details: zoneApps
        };
    });

    // Calculate aggregate metrics
    const totalDependencies = zones.reduce((sum, z) => sum + z.total_dependencies, 0);
    const avgSecurityScore = zoneAnalytics.reduce((sum, z) => sum + z.security_score, 0) / zoneAnalytics.length || 0;

    return {
        zones: zoneAnalytics,
        totalZones: data.totalZones,
        totalApps: data.totalApps,
        totalDependencies,
        avgSecurityScore: Math.round(avgSecurityScore)
    };
}

function calculateZoneSecurityScore(zone, apps, config) {
    let score = 100;

    // Factor 1: Application count balance (0-20 points)
    const appCount = zone.app_count;
    if (appCount === 0) {
        score -= 10; // Empty zone
    } else if (appCount > 30) {
        score -= 15; // Overcrowded zone
    } else if (appCount < 3) {
        score -= 5; // Very few apps
    }

    // Factor 2: Average dependencies per app (0-25 points)
    const avgDeps = zone.total_dependencies / zone.app_count || 0;
    if (zone.name === 'DATA_TIER' && avgDeps > 3) {
        score -= 20; // Data tier should have minimal dependencies
    } else if (zone.name === 'WEB_TIER' && avgDeps > 10) {
        score -= 15; // Web tier should not have excessive dependencies
    } else if (avgDeps > 15) {
        score -= 10; // General complexity penalty
    }

    // Factor 3: DNS health per zone (0-25 points)
    const appsWithDnsIssues = apps.filter(app => app.dns_issues > 0).length;
    const dnsIssueRatio = appsWithDnsIssues / apps.length || 0;
    score -= Math.round(dnsIssueRatio * 25);

    // Factor 4: Classification confidence (0-20 points)
    const avgConfidence = apps.reduce((sum, app) => sum + app.confidence, 0) / apps.length || 1;
    score -= Math.round((1 - avgConfidence) * 20);

    // Factor 5: Security tier expectations (0-10 points)
    if (config.security_level === 'critical' && apps.some(app => app.dns_issues > 5)) {
        score -= 10; // Critical zones with DNS issues
    }

    return Math.max(0, Math.min(100, Math.round(score)));
}

function determineRiskLevel(securityScore, apps) {
    if (securityScore < 60) return 'critical';
    if (securityScore < 75) return 'high';
    if (securityScore < 85) return 'medium';
    return 'low';
}

function generateZoneRecommendations(zone, apps, config, securityScore) {
    const recommendations = [];

    // DNS health recommendations
    const appsWithDns = apps.filter(app => app.dns_issues > 0);
    if (appsWithDns.length > 0) {
        recommendations.push({
            priority: 'high',
            category: 'DNS Health',
            message: `${appsWithDns.length} applications have DNS issues`,
            action: 'Review and correct DNS mismatches'
        });
    }

    // Dependency recommendations
    const avgDeps = zone.total_dependencies / zone.app_count || 0;
    if (zone.name === 'DATA_TIER' && avgDeps > 3) {
        recommendations.push({
            priority: 'critical',
            category: 'Security',
            message: 'Data tier has excessive dependencies',
            action: 'Review and minimize data tier connections'
        });
    }

    // Overcrowding recommendations
    if (zone.app_count > 30) {
        recommendations.push({
            priority: 'medium',
            category: 'Architecture',
            message: 'Zone has high application density',
            action: 'Consider sub-segmentation or zone splitting'
        });
    }

    // Classification confidence
    const lowConfApps = apps.filter(app => app.confidence < 0.6);
    if (lowConfApps.length > 0) {
        recommendations.push({
            priority: 'medium',
            category: 'Classification',
            message: `${lowConfApps.length} applications have low confidence`,
            action: 'Review classification rules and dependencies'
        });
    }

    return recommendations;
}

// ============================================================================
// UI Updates
// ============================================================================

function updateStats(analytics) {
    document.getElementById('total-zones').textContent = analytics.totalZones;
    document.getElementById('total-apps-zones').textContent = analytics.totalApps;
    document.getElementById('total-dependencies').textContent = analytics.totalDependencies;
    document.getElementById('avg-security-score').textContent = analytics.avgSecurityScore;
}

function renderZoneCards(analytics) {
    const container = document.getElementById('zone-cards-container');

    const cardsHtml = analytics.zones.map(zone => {
        const config = zone.config || {};

        return `
            <div class="table-card" style="border-top: 4px solid ${config.color || '#6b7280'};">
                <div class="card-header" style="background: linear-gradient(135deg, ${config.color}10 0%, ${config.color}05 100%);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 50px; height: 50px; border-radius: 12px; background: ${config.color}; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
                            <i class="fas ${config.icon || 'fa-layer-group'}"></i>
                        </div>
                        <div style="flex: 1;">
                            <h2 style="margin-bottom: 0.25rem;">${zone.name}</h2>
                            <p style="margin: 0; font-size: 0.875rem; color: var(--gray-600);">${config.description || 'Security zone'}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 2rem; font-weight: 800; color: ${
                                zone.security_score >= 85 ? '#10b981' :
                                zone.security_score >= 75 ? '#3b82f6' :
                                zone.security_score >= 60 ? '#f59e0b' : '#ef4444'
                            };">
                                ${zone.security_score}
                            </div>
                            <div style="font-size: 0.75rem; color: var(--gray-600); font-weight: 600; text-transform: uppercase;">
                                Security Score
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;">
                        <div>
                            <div style="font-size: 0.875rem; color: var(--gray-600); margin-bottom: 0.25rem;">Applications</div>
                            <div style="font-size: 1.5rem; font-weight: 700;">${zone.app_count}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.875rem; color: var(--gray-600); margin-bottom: 0.25rem;">Dependencies</div>
                            <div style="font-size: 1.5rem; font-weight: 700;">${zone.total_dependencies}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.875rem; color: var(--gray-600); margin-bottom: 0.25rem;">Avg Deps/App</div>
                            <div style="font-size: 1.5rem; font-weight: 700;">${(zone.total_dependencies / zone.app_count || 0).toFixed(1)}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.875rem; color: var(--gray-600); margin-bottom: 0.25rem;">Risk Level</div>
                            <div>
                                <span class="badge badge-${
                                    zone.risk_level === 'critical' ? 'danger' :
                                    zone.risk_level === 'high' ? 'warning' :
                                    zone.risk_level === 'medium' ? 'info' : 'success'
                                }" style="font-size: 0.875rem; padding: 0.5rem 1rem;">
                                    ${zone.risk_level.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    </div>

                    ${zone.recommendations.length > 0 ? `
                        <div style="padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <strong style="color: #f59e0b;"><i class="fas fa-exclamation-triangle"></i> Recommendations:</strong>
                            <ul style="margin: 0.5rem 0 0 1.5rem; color: var(--gray-700);">
                                ${zone.recommendations.slice(0, 3).map(rec => `
                                    <li>${rec.message} - ${rec.action}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : `
                        <div style="padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 4px solid #10b981;">
                            <strong style="color: #10b981;"><i class="fas fa-check-circle"></i> Zone is optimally configured</strong>
                        </div>
                    `}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = cardsHtml;
}

function renderComparisonTable(analytics) {
    const tbody = document.getElementById('zone-comparison-tbody');

    const rowsHtml = analytics.zones.map(zone => `
        <tr>
            <td>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 30px; height: 30px; border-radius: 6px; background: ${zone.config.color}; display: flex; align-items: center; justify-content: center; color: white;">
                        <i class="fas ${zone.config.icon} fa-sm"></i>
                    </div>
                    <strong>${zone.name}</strong>
                </div>
            </td>
            <td>${zone.app_count}</td>
            <td>${zone.total_dependencies}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${zone.security_score}%; height: 100%; background: ${
                            zone.security_score >= 85 ? '#10b981' :
                            zone.security_score >= 75 ? '#3b82f6' :
                            zone.security_score >= 60 ? '#f59e0b' : '#ef4444'
                        };"></div>
                    </div>
                    <span style="font-weight: 700; min-width: 40px;">${zone.security_score}</span>
                </div>
            </td>
            <td>
                <span class="badge badge-${
                    zone.risk_level === 'critical' ? 'danger' :
                    zone.risk_level === 'high' ? 'warning' :
                    zone.risk_level === 'medium' ? 'info' : 'success'
                }">
                    ${zone.risk_level.toUpperCase()}
                </span>
            </td>
            <td>${zone.recommendations.length} items</td>
        </tr>
    `).join('');

    tbody.innerHTML = rowsHtml;
}

function renderRecommendations(analytics) {
    const container = document.getElementById('zone-recommendations');

    // Aggregate all recommendations
    const allRecommendations = analytics.zones.flatMap(zone =>
        zone.recommendations.map(rec => ({ ...rec, zone: zone.name }))
    );

    // Sort by priority
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    allRecommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    if (allRecommendations.length === 0) {
        container.innerHTML = `
            <div class="success">
                <i class="fas fa-shield-alt"></i> <strong>All zones are properly configured</strong>
                <p>No critical segmentation issues detected. Continue monitoring for changes.</p>
            </div>
        `;
        return;
    }

    const recHtml = allRecommendations.map(rec => `
        <div style="padding: 1.25rem; background: white; border-radius: 12px; border-left: 4px solid ${
            rec.priority === 'critical' ? '#ef4444' :
            rec.priority === 'high' ? '#f59e0b' : '#3b82f6'
        }; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                <div style="display: flex; gap: 0.75rem; align-items: center;">
                    <span class="badge badge-${
                        rec.priority === 'critical' ? 'danger' :
                        rec.priority === 'high' ? 'warning' : 'info'
                    }">${rec.priority.toUpperCase()}</span>
                    <span class="zone-badge zone-${rec.zone}">${rec.zone}</span>
                </div>
                <span style="font-size: 0.875rem; font-weight: 600; color: var(--gray-600); text-transform: uppercase;">
                    ${rec.category}
                </span>
            </div>
            <div style="font-weight: 600; color: var(--gray-900); margin-bottom: 0.5rem;">
                ${rec.message}
            </div>
            <div style="padding: 0.75rem; background: rgba(59, 130, 246, 0.1); border-radius: 6px;">
                <strong style="color: #3b82f6;"><i class="fas fa-arrow-right"></i> Action:</strong>
                <span style="color: var(--gray-700);"> ${rec.action}</span>
            </div>
        </div>
    `).join('');

    container.innerHTML = recHtml;
}

// ============================================================================
// Charts
// ============================================================================

function renderCharts(analytics) {
    renderDistributionChart(analytics);
    renderSecurityPostureChart(analytics);
}

function renderDistributionChart(analytics) {
    const ctx = document.getElementById('zoneDistributionChart');
    if (!ctx) return;

    if (charts.distribution) charts.distribution.destroy();

    const data = {
        labels: analytics.zones.map(z => z.name),
        datasets: [{
            data: analytics.zones.map(z => z.app_count),
            backgroundColor: analytics.zones.map(z => z.config.color || '#6b7280'),
            borderWidth: 0
        }]
    };

    charts.distribution = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} apps (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderSecurityPostureChart(analytics) {
    const ctx = document.getElementById('securityPostureChart');
    if (!ctx) return;

    if (charts.posture) charts.posture.destroy();

    charts.posture = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: analytics.zones.map(z => z.name),
            datasets: [{
                label: 'Security Score',
                data: analytics.zones.map(z => z.security_score),
                backgroundColor: analytics.zones.map(z =>
                    z.security_score >= 85 ? '#10b981' :
                    z.security_score >= 75 ? '#3b82f6' :
                    z.security_score >= 60 ? '#f59e0b' : '#ef4444'
                )
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================================
// Export Functionality
// ============================================================================

function toggleExportDropdown(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('export-dropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

function exportZones(format) {
    window.location.href = `/api/export/zones?format=${format}`;
    document.getElementById('export-dropdown').style.display = 'none';
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    const dropdown = document.getElementById('export-dropdown');
    if (dropdown) dropdown.style.display = 'none';
});

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', loadZoneData);
