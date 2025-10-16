/**
 * ActivNet Advanced Analytics
 * Combines multiple APIs for deep network insights
 */

// Global state
let analyticsData = {
    applications: [],
    zones: [],
    dnsData: null,
    enterpriseData: null
};

let charts = {};

// ============================================================================
// Main Data Loading
// ============================================================================

async function loadAllAnalytics() {
    try {
        // Fetch all data in parallel
        const [appsData, zonesData, dnsData, enterpriseData] = await Promise.all([
            fetch('/api/applications').then(r => r.json()),
            fetch('/api/security-zones').then(r => r.json()),
            fetch('/api/dns-validation/summary').then(r => r.json()),
            fetch('/api/enterprise/summary').then(r => r.json())
        ]);

        // Store data
        analyticsData.applications = appsData.applications || [];
        analyticsData.zones = zonesData.zones || [];
        analyticsData.dnsData = dnsData;
        analyticsData.enterpriseData = enterpriseData;

        // Perform analytics
        const analytics = performAnalytics(analyticsData);

        // Update UI
        updateHealthScore(analytics);
        updateAlerts(analytics);
        updateAnomalies(analytics);
        updateRiskScores(analytics);
        renderCharts(analytics);
        updateRecommendations(analytics);

    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// ============================================================================
// Analytics Engine
// ============================================================================

function performAnalytics(data) {
    const apps = data.applications;
    const zones = data.zones;
    const dnsStats = data.dnsData?.statistics || {};

    // Calculate dependency statistics
    const dependencyStats = apps.map(app => app.dependency_count);
    const avgDeps = dependencyStats.reduce((a, b) => a + b, 0) / apps.length || 0;
    const maxDeps = Math.max(...dependencyStats, 0);
    const stdDev = calculateStdDev(dependencyStats, avgDeps);

    // Detect anomalies
    const anomalies = detectAnomalies(apps, avgDeps, stdDev);

    // Calculate risk scores
    const riskScores = calculateRiskScores(apps, dnsStats);

    // Calculate health score
    const healthScore = calculateHealthScore(apps, zones, dnsStats);

    // Generate alerts
    const alerts = generateAlerts(apps, zones, dnsStats, anomalies);

    // Generate recommendations
    const recommendations = generateRecommendations(apps, zones, dnsStats, anomalies, riskScores);

    return {
        apps,
        zones,
        dnsStats,
        avgDeps,
        maxDeps,
        stdDev,
        anomalies,
        riskScores,
        healthScore,
        alerts,
        recommendations
    };
}

// ============================================================================
// Anomaly Detection
// ============================================================================

function detectAnomalies(apps, avgDeps, stdDev) {
    const anomalies = [];

    apps.forEach(app => {
        // Excessive dependencies (> 2 std dev from mean)
        if (app.dependency_count > (avgDeps + 2 * stdDev) && app.dependency_count > 5) {
            anomalies.push({
                app_id: app.app_id,
                type: 'Excessive Dependencies',
                severity: 'high',
                details: `${app.dependency_count} dependencies (avg: ${avgDeps.toFixed(1)})`,
                impact: 'Increased complexity and potential attack surface'
            });
        }

        // High DNS issues
        if (app.dns_issues > 5) {
            anomalies.push({
                app_id: app.app_id,
                type: 'DNS Health Critical',
                severity: 'critical',
                details: `${app.dns_issues} DNS issues detected`,
                impact: 'Service disruption and security risks'
            });
        }

        // Low confidence classification
        if (app.confidence < 0.5 && app.dependency_count > 0) {
            anomalies.push({
                app_id: app.app_id,
                type: 'Low Confidence Classification',
                severity: 'medium',
                details: `Confidence: ${(app.confidence * 100).toFixed(0)}%`,
                impact: 'May be misclassified in security zone'
            });
        }

        // Orphaned applications (no dependencies)
        if (app.dependency_count === 0 && app.dns_validated === 0) {
            anomalies.push({
                app_id: app.app_id,
                type: 'Orphaned Application',
                severity: 'low',
                details: 'No dependencies or DNS validation',
                impact: 'May be outdated or unused'
            });
        }
    });

    return anomalies;
}

// ============================================================================
// Risk Scoring
// ============================================================================

function calculateRiskScores(apps, dnsStats) {
    return apps.map(app => {
        let risk = 0;
        const factors = [];

        // DNS issues (0-30 points)
        if (app.dns_issues > 0) {
            const dnsRisk = Math.min(30, app.dns_issues * 5);
            risk += dnsRisk;
            factors.push(`DNS issues (+${dnsRisk})`);
        }

        // High dependency count (0-25 points)
        if (app.dependency_count > 10) {
            const depRisk = Math.min(25, (app.dependency_count - 10) * 2);
            risk += depRisk;
            factors.push(`High dependencies (+${depRisk})`);
        }

        // Low confidence (0-20 points)
        if (app.confidence < 0.7) {
            const confRisk = Math.round((0.7 - app.confidence) * 100);
            risk += confRisk;
            factors.push(`Low confidence (+${confRisk})`);
        }

        // No DNS validation (15 points)
        if (app.dns_validated === 0 && app.dependency_count > 0) {
            risk += 15;
            factors.push('No DNS validation (+15)');
        }

        // Security zone considerations (0-10 points)
        if (app.security_zone === 'WEB_TIER' && app.dependency_count > 5) {
            risk += 10;
            factors.push('Exposed tier (+10)');
        }

        return {
            app_id: app.app_id,
            risk_score: Math.min(100, risk),
            risk_level: risk > 60 ? 'critical' : risk > 40 ? 'high' : risk > 20 ? 'medium' : 'low',
            factors: factors,
            dependency_count: app.dependency_count,
            dns_issues: app.dns_issues,
            security_zone: app.security_zone
        };
    }).sort((a, b) => b.risk_score - a.risk_score);
}

// ============================================================================
// Health Score Calculation
// ============================================================================

function calculateHealthScore(apps, zones, dnsStats) {
    let score = 100;
    const indicators = [];

    // DNS Health (0-30 points deduction)
    const totalDns = dnsStats.total_validated || 1;
    const dnsIssues = (dnsStats.total_mismatches || 0) + (dnsStats.total_nxdomain || 0);
    const dnsHealthPercent = ((totalDns - dnsIssues) / totalDns) * 100;
    const dnsDeduction = Math.round((100 - dnsHealthPercent) * 0.3);
    score -= dnsDeduction;
    indicators.push({
        name: 'DNS Health',
        score: Math.round(dnsHealthPercent),
        status: dnsHealthPercent > 90 ? 'good' : dnsHealthPercent > 70 ? 'warning' : 'critical'
    });

    // Application Classification Confidence (0-25 points deduction)
    const avgConfidence = apps.reduce((sum, app) => sum + app.confidence, 0) / apps.length || 0;
    const confDeduction = Math.round((1 - avgConfidence) * 25);
    score -= confDeduction;
    indicators.push({
        name: 'Classification Confidence',
        score: Math.round(avgConfidence * 100),
        status: avgConfidence > 0.8 ? 'good' : avgConfidence > 0.6 ? 'warning' : 'critical'
    });

    // Security Zone Distribution (0-20 points deduction)
    const zoneBalance = calculateZoneBalance(zones);
    const zoneDeduction = Math.round((1 - zoneBalance) * 20);
    score -= zoneDeduction;
    indicators.push({
        name: 'Zone Balance',
        score: Math.round(zoneBalance * 100),
        status: zoneBalance > 0.7 ? 'good' : zoneBalance > 0.5 ? 'warning' : 'critical'
    });

    // Dependency Complexity (0-25 points deduction)
    const complexApps = apps.filter(app => app.dependency_count > 15).length;
    const complexityRatio = complexApps / apps.length;
    const complexityDeduction = Math.round(complexityRatio * 25);
    score -= complexityDeduction;
    indicators.push({
        name: 'Dependency Complexity',
        score: Math.round((1 - complexityRatio) * 100),
        status: complexityRatio < 0.1 ? 'good' : complexityRatio < 0.3 ? 'warning' : 'critical'
    });

    return {
        overall: Math.max(0, Math.round(score)),
        indicators,
        grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F'
    };
}

function calculateZoneBalance(zones) {
    if (zones.length === 0) return 1;
    const totalApps = zones.reduce((sum, z) => sum + z.app_count, 0);
    const expectedPerZone = totalApps / zones.length;
    const variance = zones.reduce((sum, z) => {
        const diff = z.app_count - expectedPerZone;
        return sum + (diff * diff);
    }, 0) / zones.length;
    const stdDev = Math.sqrt(variance);
    return Math.max(0, 1 - (stdDev / expectedPerZone));
}

// ============================================================================
// Alert Generation
// ============================================================================

function generateAlerts(apps, zones, dnsStats, anomalies) {
    const alerts = [];

    // Critical DNS issues
    const criticalDns = (dnsStats.total_mismatches || 0) + (dnsStats.total_nxdomain || 0);
    if (criticalDns > 10) {
        alerts.push({
            severity: 'critical',
            title: 'Critical DNS Configuration Issues',
            message: `${criticalDns} DNS issues detected that require immediate attention`,
            action: 'Review DNS validation dashboard and correct mismatches'
        });
    }

    // High risk applications
    const highRiskApps = apps.filter(app =>
        app.dns_issues > 5 || app.dependency_count > 20
    );
    if (highRiskApps.length > 5) {
        alerts.push({
            severity: 'high',
            title: 'Multiple High-Risk Applications',
            message: `${highRiskApps.length} applications with elevated security risk`,
            action: 'Review risk scoring and implement mitigation strategies'
        });
    }

    // Anomalies detected
    const criticalAnomalies = anomalies.filter(a => a.severity === 'critical');
    if (criticalAnomalies.length > 0) {
        alerts.push({
            severity: 'critical',
            title: 'Critical Anomalies Detected',
            message: `${criticalAnomalies.length} critical anomalies require investigation`,
            action: 'Review anomalies table and investigate root causes'
        });
    }

    return alerts;
}

// ============================================================================
// Recommendations Generation
// ============================================================================

function generateRecommendations(apps, zones, dnsStats, anomalies, riskScores) {
    const recommendations = [];

    // DNS recommendations
    const dnsIssues = (dnsStats.total_mismatches || 0) + (dnsStats.total_nxdomain || 0);
    if (dnsIssues > 0) {
        recommendations.push({
            priority: 'high',
            category: 'DNS Health',
            title: 'Resolve DNS Configuration Issues',
            description: `${dnsIssues} DNS issues detected. Ensure PTR records match A records and synchronize DNS servers.`,
            benefit: 'Improved service reliability and reduced security vulnerabilities'
        });
    }

    // High-risk apps
    const criticalRisk = riskScores.filter(r => r.risk_level === 'critical').length;
    if (criticalRisk > 0) {
        recommendations.push({
            priority: 'critical',
            category: 'Security',
            title: 'Mitigate High-Risk Applications',
            description: `${criticalRisk} applications have critical risk scores. Review dependencies and implement controls.`,
            benefit: 'Reduced attack surface and improved security posture'
        });
    }

    // Complexity reduction
    const complexApps = apps.filter(app => app.dependency_count > 15).length;
    if (complexApps > 10) {
        recommendations.push({
            priority: 'medium',
            category: 'Architecture',
            title: 'Reduce Dependency Complexity',
            description: `${complexApps} applications have high dependency counts. Consider microservices refactoring.`,
            benefit: 'Improved maintainability and reduced failure cascades'
        });
    }

    // Zone segregation
    const webTierApps = apps.filter(app => app.security_zone === 'WEB_TIER' && app.dependency_count > 8);
    if (webTierApps.length > 5) {
        recommendations.push({
            priority: 'medium',
            category: 'Network Segmentation',
            title: 'Review WEB_TIER Dependencies',
            description: `${webTierApps.length} web tier applications have excessive dependencies. Verify firewall rules.`,
            benefit: 'Enhanced security through proper network segmentation'
        });
    }

    return recommendations;
}

// ============================================================================
// UI Updates
// ============================================================================

function updateHealthScore(analytics) {
    const healthScore = analytics.healthScore;

    // Update overall score
    document.getElementById('health-score').textContent = healthScore.overall;

    // Update indicators
    const indicatorsHtml = healthScore.indicators.map(ind => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: ${
            ind.status === 'good' ? 'rgba(16, 185, 129, 0.1)' :
            ind.status === 'warning' ? 'rgba(245, 158, 11, 0.1)' :
            'rgba(239, 68, 68, 0.1)'
        }; border-radius: 8px;">
            <span style="font-weight: 600;">${ind.name}</span>
            <span style="font-weight: 700; color: ${
                ind.status === 'good' ? '#10b981' :
                ind.status === 'warning' ? '#f59e0b' :
                '#ef4444'
            };">${ind.score}%</span>
        </div>
    `).join('');

    document.getElementById('health-indicators').innerHTML = indicatorsHtml;

    // Update stats
    document.getElementById('anomalies-count').textContent = analytics.anomalies.length;
    document.getElementById('high-risk-count').textContent =
        analytics.riskScores.filter(r => r.risk_level === 'high' || r.risk_level === 'critical').length;
    document.getElementById('complex-apps-count').textContent =
        analytics.apps.filter(app => app.dependency_count > 15).length;

    const dnsHealthPercent = ((analytics.dnsStats.total_validated || 1) -
        ((analytics.dnsStats.total_mismatches || 0) + (analytics.dnsStats.total_nxdomain || 0))) /
        (analytics.dnsStats.total_validated || 1) * 100;
    document.getElementById('dns-health-score').textContent = Math.round(dnsHealthPercent);
}

function updateAlerts(analytics) {
    const alertsSection = document.getElementById('alerts-section');
    const alertsContent = document.getElementById('alerts-content');
    const alertCount = document.getElementById('alert-count');

    if (analytics.alerts.length === 0) {
        alertsSection.style.display = 'none';
        return;
    }

    alertsSection.style.display = 'block';
    alertCount.textContent = analytics.alerts.length;

    const alertsHtml = analytics.alerts.map(alert => `
        <div class="${alert.severity === 'critical' ? 'error' : 'error'}" style="border-left: 4px solid ${
            alert.severity === 'critical' ? '#ef4444' : '#f59e0b'
        };">
            <div style="display: flex; align-items: start; gap: 1rem;">
                <i class="fas fa-exclamation-triangle" style="font-size: 1.5rem; color: ${
                    alert.severity === 'critical' ? '#ef4444' : '#f59e0b'
                };"></i>
                <div style="flex: 1;">
                    <strong>${alert.title}</strong>
                    <p style="margin: 0.5rem 0;">${alert.message}</p>
                    <p style="margin: 0; font-size: 0.875rem;"><strong>Action:</strong> ${alert.action}</p>
                </div>
            </div>
        </div>
    `).join('');

    alertsContent.innerHTML = alertsHtml;
}

function updateAnomalies(analytics) {
    const tbody = document.getElementById('anomalies-tbody');

    if (analytics.anomalies.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="5" class="text-center success">
                <i class="fas fa-check-circle"></i> No anomalies detected - network configuration is healthy
            </td></tr>
        `;
        return;
    }

    tbody.innerHTML = analytics.anomalies.map(anomaly => `
        <tr>
            <td><strong>${anomaly.app_id}</strong></td>
            <td>${anomaly.type}</td>
            <td>
                <span class="badge badge-${
                    anomaly.severity === 'critical' ? 'danger' :
                    anomaly.severity === 'high' ? 'warning' :
                    anomaly.severity === 'medium' ? 'info' : 'success'
                }">${anomaly.severity.toUpperCase()}</span>
            </td>
            <td>${anomaly.details}</td>
            <td>${anomaly.impact}</td>
        </tr>
    `).join('');
}

function updateRiskScores(analytics) {
    const tbody = document.getElementById('high-risk-tbody');
    const highRiskBadge = document.getElementById('high-risk-badge');

    const highRisk = analytics.riskScores.filter(r =>
        r.risk_level === 'high' || r.risk_level === 'critical'
    );

    highRiskBadge.textContent = highRisk.length;

    if (highRisk.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6" class="text-center success">
                <i class="fas fa-shield-alt"></i> No high-risk applications detected
            </td></tr>
        `;
        return;
    }

    tbody.innerHTML = highRisk.slice(0, 20).map(risk => `
        <tr>
            <td><strong>${risk.app_id}</strong></td>
            <td>
                <span class="badge badge-${risk.risk_level === 'critical' ? 'danger' : 'warning'}"
                      style="font-size: 1rem; padding: 0.5rem 1rem;">
                    ${risk.risk_score}/100
                </span>
            </td>
            <td style="font-size: 0.875rem;">${risk.factors.join(', ')}</td>
            <td>${risk.dependency_count}</td>
            <td>
                ${risk.dns_issues > 0
                    ? `<span class="badge badge-warning">${risk.dns_issues}</span>`
                    : `<span class="badge badge-success">0</span>`
                }
            </td>
            <td>
                ${risk.risk_level === 'critical'
                    ? 'Immediate review required'
                    : 'Review and implement controls'
                }
            </td>
        </tr>
    `).join('');
}

function updateRecommendations(analytics) {
    const content = document.getElementById('recommendations-content');

    if (analytics.recommendations.length === 0) {
        content.innerHTML = `
            <div class="success">
                <i class="fas fa-check-circle"></i> <strong>Network is optimally configured</strong>
                <p>No critical recommendations at this time. Continue monitoring for changes.</p>
            </div>
        `;
        return;
    }

    const recHtml = analytics.recommendations.map(rec => `
        <div style="padding: 1.5rem; background: white; border-radius: 12px; border-left: 4px solid ${
            rec.priority === 'critical' ? '#ef4444' :
            rec.priority === 'high' ? '#f59e0b' :
            '#3b82f6'
        }; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 0.75rem;">
                <span class="badge badge-${
                    rec.priority === 'critical' ? 'danger' :
                    rec.priority === 'high' ? 'warning' : 'info'
                }">${rec.priority.toUpperCase()}</span>
                <span style="color: var(--gray-600); font-size: 0.875rem; font-weight: 600; text-transform: uppercase;">
                    ${rec.category}
                </span>
            </div>
            <h3 style="margin-bottom: 0.5rem; font-size: 1.125rem;">${rec.title}</h3>
            <p style="color: var(--gray-600); margin-bottom: 0.75rem;">${rec.description}</p>
            <div style="padding: 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px;">
                <strong style="color: #10b981;"><i class="fas fa-check-circle"></i> Benefit:</strong>
                <span style="color: var(--gray-700);"> ${rec.benefit}</span>
            </div>
        </div>
    `).join('');

    content.innerHTML = recHtml;
}

// ============================================================================
// Chart Rendering
// ============================================================================

function renderCharts(analytics) {
    renderRiskChart(analytics.riskScores);
    renderComplexityChart(analytics.apps);
}

function renderRiskChart(riskScores) {
    const ctx = document.getElementById('riskChart');
    if (!ctx) return;

    if (charts.riskChart) charts.riskChart.destroy();

    const riskDistribution = {
        critical: riskScores.filter(r => r.risk_level === 'critical').length,
        high: riskScores.filter(r => r.risk_level === 'high').length,
        medium: riskScores.filter(r => r.risk_level === 'medium').length,
        low: riskScores.filter(r => r.risk_level === 'low').length
    };

    charts.riskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
                data: [riskDistribution.critical, riskDistribution.high,
                       riskDistribution.medium, riskDistribution.low],
                backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderComplexityChart(apps) {
    const ctx = document.getElementById('complexityChart');
    if (!ctx) return;

    if (charts.complexityChart) charts.complexityChart.destroy();

    const complexity = {
        simple: apps.filter(app => app.dependency_count <= 5).length,
        moderate: apps.filter(app => app.dependency_count > 5 && app.dependency_count <= 10).length,
        complex: apps.filter(app => app.dependency_count > 10 && app.dependency_count <= 15).length,
        veryComplex: apps.filter(app => app.dependency_count > 15).length
    };

    charts.complexityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Simple (≤5)', 'Moderate (6-10)', 'Complex (11-15)', 'Very Complex (>15)'],
            datasets: [{
                label: 'Applications',
                data: [complexity.simple, complexity.moderate, complexity.complex, complexity.veryComplex],
                backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
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
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

function calculateStdDev(values, mean) {
    const squareDiffs = values.map(value => Math.pow(value - mean, 2));
    const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / values.length;
    return Math.sqrt(avgSquareDiff);
}

// ============================================================================
// Export Functionality
// ============================================================================

function exportAnalytics() {
    // Trigger JSON export download
    window.location.href = '/api/export/analytics?format=json';
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', loadAllAnalytics);
