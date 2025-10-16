/**
 * ActivNet Application Detail Page
 * Holistic Network Segmentation and Threat Analysis
 */

let appData = null;
let appId = null;
let dependencyGraph = null;

// Zone security levels and expected behaviors
const ZONE_SECURITY = {
    'DATA_TIER': {
        level: 'critical',
        expectedDeps: [0, 3],
        allowedOutbound: ['APP_TIER'],
        color: '#10b981'
    },
    'APP_TIER': {
        level: 'high',
        expectedDeps: [5, 15],
        allowedOutbound: ['DATA_TIER', 'CACHE_TIER', 'MESSAGING_TIER'],
        color: '#3b82f6'
    },
    'WEB_TIER': {
        level: 'high',
        expectedDeps: [3, 10],
        allowedOutbound: ['APP_TIER', 'CACHE_TIER'],
        color: '#8b5cf6'
    },
    'CACHE_TIER': {
        level: 'medium',
        expectedDeps: [1, 5],
        allowedOutbound: ['DATA_TIER'],
        color: '#f59e0b'
    },
    'MESSAGING_TIER': {
        level: 'medium',
        expectedDeps: [2, 8],
        allowedOutbound: ['APP_TIER', 'DATA_TIER'],
        color: '#ec4899'
    },
    'MANAGEMENT_TIER': {
        level: 'high',
        expectedDeps: [10, 50],
        allowedOutbound: ['*'],
        color: '#6366f1'
    }
};

// ============================================================================
// Data Loading
// ============================================================================

async function loadApplicationData() {
    const params = new URLSearchParams(window.location.search);
    appId = params.get('id');

    if (!appId) {
        alert('No application ID provided');
        window.location.href = '/applications.html';
        return;
    }

    try {
        // Load application topology data
        const response = await fetch(`/api/applications/${appId}`);
        const result = await response.json();
        appData = result.data;

        // Load all applications for related apps
        const allAppsResponse = await fetch('/api/applications');
        const allAppsData = await allAppsResponse.json();
        appData.allApplications = allAppsData.applications;

        // Perform comprehensive analysis
        const analysis = analyzeApplication(appData);

        // Render all sections
        renderHeader(appData, analysis);
        renderMetrics(appData, analysis);
        renderThreatAssessment(analysis);
        renderSegmentationAnalysis(appData, analysis);
        renderDependencyGraph(appData);
        renderDNSValidation(appData);
        renderSecurityPosture(analysis);
        renderRelatedApplications(appData);
        renderActivityTimeline(appData);
        renderRecommendations(analysis);

    } catch (error) {
        console.error('Error loading application:', error);
        alert('Failed to load application data');
    }
}

// ============================================================================
// Comprehensive Security Analysis
// ============================================================================

function analyzeApplication(data) {
    const analysis = {
        riskScore: 0,
        riskLevel: 'low',
        riskFactors: [],
        threats: [],
        segmentationViolations: [],
        recommendations: [],
        securityPosture: {}
    };

    const zone = data.security_zone;
    const zoneConfig = ZONE_SECURITY[zone] || {};
    const depCount = data.dependencies?.length || 0;
    const dnsValidation = data.dns_validation || {};

    // Calculate Risk Score (0-100)
    let riskScore = 0;

    // Factor 1: DNS Issues (0-30 points)
    const dnsIssues = (dnsValidation.mismatch || 0) + (dnsValidation.nxdomain || 0) + (dnsValidation.failed || 0);
    if (dnsIssues > 0) {
        const dnsRisk = Math.min(30, dnsIssues * 5);
        riskScore += dnsRisk;
        analysis.riskFactors.push(`DNS Issues: +${dnsRisk} points`);

        if (dnsIssues > 5) {
            analysis.threats.push({
                level: 'critical',
                category: 'DNS Health',
                title: 'Critical DNS Configuration Issues',
                description: `${dnsIssues} DNS validation failures detected. This could indicate misconfiguration, stale records, or potential DNS hijacking.`,
                impact: 'Service disruption, potential security breach',
                recommendation: 'Immediately review and correct DNS records. Verify with network team.'
            });
        } else if (dnsIssues > 0) {
            analysis.threats.push({
                level: 'high',
                category: 'DNS Health',
                title: 'DNS Validation Failures',
                description: `${dnsIssues} DNS issues detected.`,
                impact: 'Reduced reliability, potential connectivity issues',
                recommendation: 'Schedule DNS record cleanup and validation.'
            });
        }
    }

    // Factor 2: Dependency Complexity (0-25 points)
    const expectedRange = zoneConfig.expectedDeps || [0, 100];
    if (depCount > expectedRange[1]) {
        const depRisk = Math.min(25, (depCount - expectedRange[1]) * 2);
        riskScore += depRisk;
        analysis.riskFactors.push(`Excessive Dependencies: +${depRisk} points`);

        analysis.threats.push({
            level: depCount > expectedRange[1] * 2 ? 'high' : 'medium',
            category: 'Complexity',
            title: 'High Dependency Complexity',
            description: `Application has ${depCount} dependencies, exceeding expected range of ${expectedRange[1]} for ${zone}.`,
            impact: 'Increased attack surface, cascading failures, difficult maintenance',
            recommendation: 'Review and reduce dependencies. Consider microservice refactoring.'
        });
    }

    // Factor 3: Segmentation Violations (0-30 points)
    const violations = detectSegmentationViolations(data);
    if (violations.length > 0) {
        const segRisk = Math.min(30, violations.length * 10);
        riskScore += segRisk;
        analysis.riskFactors.push(`Segmentation Violations: +${segRisk} points`);
        analysis.segmentationViolations = violations;

        violations.forEach(violation => {
            analysis.threats.push({
                level: 'critical',
                category: 'Network Segmentation',
                title: 'Security Zone Violation',
                description: violation.description,
                impact: 'Breach of zero-trust architecture, lateral movement risk',
                recommendation: violation.recommendation
            });
        });
    }

    // Factor 4: Classification Confidence (0-15 points)
    const confidence = data.confidence || 0;
    if (confidence < 0.7) {
        const confRisk = Math.round((0.7 - confidence) * 50);
        riskScore += confRisk;
        analysis.riskFactors.push(`Low Classification Confidence: +${confRisk} points`);

        analysis.threats.push({
            level: 'medium',
            category: 'Classification',
            title: 'Uncertain Security Classification',
            description: `Classification confidence is only ${(confidence * 100).toFixed(0)}%. Application may be misplaced in current security zone.`,
            impact: 'Incorrect security controls, policy violations',
            recommendation: 'Review application behavior and reclassify if necessary.'
        });
    }

    // Factor 5: Critical Zone Exposure (0-10 points)
    if (zone === 'DATA_TIER' && depCount > 5) {
        riskScore += 10;
        analysis.riskFactors.push('Data Tier Overexposure: +10 points');

        analysis.threats.push({
            level: 'critical',
            category: 'Data Security',
            title: 'Excessive Data Tier Exposure',
            description: `Data tier application with ${depCount} dependencies violates principle of minimal exposure.`,
            impact: 'Direct risk to sensitive data, potential data breach',
            recommendation: 'Implement strict access controls. Consider data tier segmentation.'
        });
    }

    analysis.riskScore = Math.min(100, Math.round(riskScore));
    analysis.riskLevel = analysis.riskScore > 70 ? 'critical' :
                         analysis.riskScore > 50 ? 'high' :
                         analysis.riskScore > 30 ? 'medium' : 'low';

    // Security Posture Assessment
    analysis.securityPosture = {
        zoneCompliance: violations.length === 0 ? 100 : Math.max(0, 100 - (violations.length * 20)),
        dnsHealth: dnsIssues === 0 ? 100 : Math.max(0, 100 - (dnsIssues * 10)),
        complexityScore: depCount <= expectedRange[1] ? 100 : Math.max(0, 100 - ((depCount - expectedRange[1]) * 5)),
        confidenceScore: Math.round(confidence * 100)
    };

    // Generate Recommendations
    analysis.recommendations = generateRecommendations(data, analysis);

    return analysis;
}

function detectSegmentationViolations(data) {
    const violations = [];
    const zone = data.security_zone;
    const zoneConfig = ZONE_SECURITY[zone];

    if (!zoneConfig) return violations;

    // Analyze each dependency
    data.dependencies?.forEach(dep => {
        const depZone = inferDependencyZone(dep);

        if (depZone && !zoneConfig.allowedOutbound.includes(depZone) && !zoneConfig.allowedOutbound.includes('*')) {
            violations.push({
                type: 'Unauthorized Cross-Zone Communication',
                description: `${zone} should not communicate with ${depZone}. Dependency: ${dep.name}`,
                severity: zoneConfig.level === 'critical' ? 'critical' : 'high',
                recommendation: `Review firewall rules. Block ${zone} → ${depZone} communication or reclassify application.`
            });
        }
    });

    // Check for reverse dependencies (applications depending on this one)
    if (zone === 'DATA_TIER') {
        const directDataAccess = data.dependencies?.filter(dep =>
            dep.type === 'database' && !dep.name.includes('api')
        ).length || 0;

        if (directDataAccess > 0) {
            violations.push({
                type: 'Direct Database Access',
                description: `${directDataAccess} direct database connections detected. Data tier should be accessed through APIs only.`,
                severity: 'critical',
                recommendation: 'Implement API gateway pattern. Remove direct database access.'
            });
        }
    }

    return violations;
}

function inferDependencyZone(dep) {
    const name = dep.name.toLowerCase();
    const type = dep.type.toLowerCase();

    if (type === 'database' || name.includes('db') || name.includes('sql')) return 'DATA_TIER';
    if (type === 'cache' || name.includes('redis') || name.includes('memcached')) return 'CACHE_TIER';
    if (type === 'message_queue' || name.includes('kafka') || name.includes('rabbitmq')) return 'MESSAGING_TIER';
    if (type === 'api' || name.includes('api') || name.includes('service')) return 'APP_TIER';
    if (type === 'web' || name.includes('web') || name.includes('http')) return 'WEB_TIER';

    return null;
}

function generateRecommendations(data, analysis) {
    const recommendations = [];

    // Critical recommendations first
    if (analysis.riskScore > 70) {
        recommendations.push({
            priority: 'critical',
            title: 'Immediate Security Review Required',
            description: `Risk score of ${analysis.riskScore}/100 indicates critical security concerns. Immediate action required.`,
            actions: [
                'Conduct comprehensive security audit',
                'Review and restrict network access',
                'Implement enhanced monitoring',
                'Schedule emergency review with security team'
            ]
        });
    }

    // DNS-specific recommendations
    const dnsIssues = (data.dns_validation?.mismatch || 0) + (data.dns_validation?.nxdomain || 0);
    if (dnsIssues > 0) {
        recommendations.push({
            priority: dnsIssues > 5 ? 'critical' : 'high',
            title: 'DNS Configuration Remediation',
            description: `${dnsIssues} DNS issues require immediate attention to ensure service reliability.`,
            actions: [
                'Audit all DNS records for accuracy',
                'Update PTR records to match A records',
                'Verify DNS server synchronization',
                'Implement DNS monitoring and alerts'
            ]
        });
    }

    // Segmentation recommendations
    if (analysis.segmentationViolations.length > 0) {
        recommendations.push({
            priority: 'critical',
            title: 'Network Segmentation Enforcement',
            description: `${analysis.segmentationViolations.length} zone violations detected. Network segmentation is compromised.`,
            actions: [
                'Review firewall rules for all violations',
                'Implement micro-segmentation where possible',
                'Update security group policies',
                'Consider application reclassification'
            ]
        });
    }

    // Complexity recommendations
    const depCount = data.dependencies?.length || 0;
    if (depCount > 20) {
        recommendations.push({
            priority: 'medium',
            title: 'Reduce Application Complexity',
            description: `${depCount} dependencies create high complexity and maintenance burden.`,
            actions: [
                'Identify and remove unnecessary dependencies',
                'Consolidate similar services',
                'Consider microservice refactoring',
                'Document critical vs non-critical dependencies'
            ]
        });
    }

    // Confidence recommendations
    if (data.confidence < 0.7) {
        recommendations.push({
            priority: 'high',
            title: 'Verify Security Classification',
            description: `Low confidence (${(data.confidence * 100).toFixed(0)}%) suggests incorrect zone placement.`,
            actions: [
                'Review application purpose and data handling',
                'Analyze actual communication patterns',
                'Consult with application owners',
                'Reclassify if necessary and update firewall rules'
            ]
        });
    }

    return recommendations;
}

// ============================================================================
// UI Rendering Functions
// ============================================================================

function renderHeader(data, analysis) {
    document.getElementById('app-title').textContent = data.app_id;

    const zone = data.security_zone;
    const zoneConfig = ZONE_SECURITY[zone] || {};

    const badges = `
        <div class="app-badge" style="background: ${zoneConfig.color};">
            <i class="fas fa-shield-alt"></i>
            ${zone}
        </div>
        <div class="app-badge">
            <i class="fas fa-project-diagram"></i>
            ${data.dependencies?.length || 0} Dependencies
        </div>
        <div class="app-badge">
            <i class="fas fa-percentage"></i>
            ${(data.confidence * 100).toFixed(0)}% Confidence
        </div>
    `;

    document.getElementById('app-badges').innerHTML = badges;

    // Risk Score
    const riskElement = document.getElementById('risk-score');
    riskElement.textContent = analysis.riskScore;
    riskElement.className = `threat-score-value risk-${analysis.riskLevel}`;
}

function renderMetrics(data, analysis) {
    document.getElementById('metric-dependencies').textContent = data.dependencies?.length || 0;
    document.getElementById('metric-confidence').textContent = `${(data.confidence * 100).toFixed(0)}%`;

    const dnsIssues = (data.dns_validation?.mismatch || 0) + (data.dns_validation?.nxdomain || 0);
    document.getElementById('metric-dns-issues').textContent = dnsIssues;

    // Calculate unique zones this app connects to
    const connectedZones = new Set();
    data.dependencies?.forEach(dep => {
        const zone = inferDependencyZone(dep);
        if (zone) connectedZones.add(zone);
    });
    document.getElementById('metric-zone-connections').textContent = connectedZones.size;
}

function renderThreatAssessment(analysis) {
    const container = document.getElementById('threat-indicators');

    if (analysis.threats.length === 0) {
        container.innerHTML = `
            <div class="threat-indicator threat-low">
                <div class="threat-icon" style="color: #10b981;">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="threat-content">
                    <h4>No Critical Threats Detected</h4>
                    <p>Application security posture is good. Continue regular monitoring.</p>
                </div>
            </div>
        `;
        return;
    }

    // Sort by severity
    const sortedThreats = analysis.threats.sort((a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 };
        return order[a.level] - order[b.level];
    });

    container.innerHTML = sortedThreats.map(threat => `
        <div class="threat-indicator threat-${threat.level}">
            <div class="threat-icon" style="color: ${
                threat.level === 'critical' ? '#ef4444' :
                threat.level === 'high' ? '#f59e0b' :
                threat.level === 'medium' ? '#3b82f6' : '#10b981'
            };">
                <i class="fas fa-${
                    threat.level === 'critical' ? 'exclamation-circle' :
                    threat.level === 'high' ? 'exclamation-triangle' :
                    threat.level === 'medium' ? 'info-circle' : 'check-circle'
                }"></i>
            </div>
            <div class="threat-content">
                <h4>${threat.title}</h4>
                <p><strong>Impact:</strong> ${threat.impact}</p>
                <p><strong>Recommendation:</strong> ${threat.recommendation}</p>
            </div>
        </div>
    `).join('');
}

function renderSegmentationAnalysis(data, analysis) {
    const container = document.getElementById('segmentation-flows');
    const zone = data.security_zone;
    const zoneConfig = ZONE_SECURITY[zone] || {};

    // Count dependencies by inferred zone
    const zoneFlows = {};
    data.dependencies?.forEach(dep => {
        const depZone = inferDependencyZone(dep) || 'EXTERNAL';
        zoneFlows[depZone] = (zoneFlows[depZone] || 0) + 1;
    });

    if (Object.keys(zoneFlows).length === 0) {
        container.innerHTML = '<p style="color: var(--gray-600);">No dependencies detected</p>';
        return;
    }

    container.innerHTML = Object.entries(zoneFlows).map(([targetZone, count]) => {
        const isViolation = !zoneConfig.allowedOutbound?.includes(targetZone) &&
                           !zoneConfig.allowedOutbound?.includes('*');
        const targetConfig = ZONE_SECURITY[targetZone] || { color: '#6b7280' };

        return `
            <div class="segmentation-flow" style="${isViolation ? 'border: 2px solid #ef4444;' : ''}">
                <div class="flow-zone" style="background: ${zoneConfig.color}; color: white;">
                    ${zone}
                </div>
                <div class="flow-arrow">
                    <i class="fas fa-arrow-right"></i>
                </div>
                <div class="flow-zone" style="background: ${targetConfig.color}; color: white;">
                    ${targetZone}
                </div>
                <div class="flow-count">
                    ${count} connection${count > 1 ? 's' : ''}
                    ${isViolation ? '<span style="color: #ef4444; margin-left: 0.5rem;"><i class="fas fa-exclamation-triangle"></i> Violation</span>' : ''}
                </div>
            </div>
        `;
    }).join('');
}

function renderDependencyGraph(data) {
    // Simplified dependency graph visualization
    const container = document.getElementById('dependency-graph');

    // Implementation would use Cytoscape.js here similar to topology.js
    // For now, show a message
    container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--gray-600);">
            <div style="text-align: center;">
                <i class="fas fa-project-diagram" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>Dependency graph visualization</p>
                <p style="font-size: 0.875rem;">${data.dependencies?.length || 0} dependencies detected</p>
            </div>
        </div>
    `;
}

function renderDNSValidation(data) {
    const tbody = document.getElementById('dns-validation-tbody');
    const dnsData = data.dns_validation;

    if (!dnsData || (!dnsData.valid && !dnsData.mismatches && !dnsData.nxdomain)) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No DNS validation data available</td></tr>';
        return;
    }

    const rows = [];

    // Add valid entries
    if (dnsData.valid) {
        dnsData.valid.forEach(entry => {
            rows.push(`
                <tr>
                    <td><code>${entry.ip || 'N/A'}</code></td>
                    <td>${entry.reverse_hostname || 'N/A'}</td>
                    <td><code>${entry.forward_ip || 'N/A'}</code></td>
                    <td><span class="badge badge-success">Valid</span></td>
                </tr>
            `);
        });
    }

    // Add mismatches
    if (dnsData.mismatches) {
        dnsData.mismatches.forEach(entry => {
            rows.push(`
                <tr style="background: rgba(239, 68, 68, 0.05);">
                    <td><code>${entry.ip || 'N/A'}</code></td>
                    <td>${entry.reverse_hostname || 'N/A'}</td>
                    <td><code>${entry.forward_ip || 'N/A'}</code></td>
                    <td><span class="badge badge-danger">Mismatch</span></td>
                </tr>
            `);
        });
    }

    // Add NXDOMAIN
    if (dnsData.nxdomain) {
        dnsData.nxdomain.forEach(entry => {
            rows.push(`
                <tr style="background: rgba(239, 68, 68, 0.05);">
                    <td><code>${entry.ip || 'N/A'}</code></td>
                    <td colspan="2">NXDOMAIN - DNS record not found</td>
                    <td><span class="badge badge-danger">NXDOMAIN</span></td>
                </tr>
            `);
        });
    }

    tbody.innerHTML = rows.join('') || '<tr><td colspan="4" class="text-center">No DNS records</td></tr>';
}

function renderSecurityPosture(analysis) {
    const ctx = document.getElementById('posture-chart');
    const posture = analysis.securityPosture;

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Zone Compliance', 'DNS Health', 'Complexity', 'Confidence'],
            datasets: [{
                label: 'Security Posture',
                data: [
                    posture.zoneCompliance,
                    posture.dnsHealth,
                    posture.complexityScore,
                    posture.confidenceScore
                ],
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(102, 126, 234, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Summary
    const avgScore = (posture.zoneCompliance + posture.dnsHealth + posture.complexityScore + posture.confidenceScore) / 4;
    document.getElementById('posture-summary').innerHTML = `
        <div style="text-align: center; padding: 1rem; background: ${
            avgScore > 80 ? 'rgba(16, 185, 129, 0.1)' :
            avgScore > 60 ? 'rgba(59, 130, 246, 0.1)' :
            avgScore > 40 ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 68, 68, 0.1)'
        }; border-radius: 8px;">
            <div style="font-size: 2rem; font-weight: 800; color: ${
                avgScore > 80 ? '#10b981' :
                avgScore > 60 ? '#3b82f6' :
                avgScore > 40 ? '#f59e0b' : '#ef4444'
            };">${Math.round(avgScore)}%</div>
            <div style="font-size: 0.875rem; color: var(--gray-600); font-weight: 600;">Overall Posture</div>
        </div>
    `;
}

function renderRelatedApplications(data) {
    const container = document.getElementById('related-apps');
    const sameZoneApps = data.allApplications
        ?.filter(app => app.security_zone === data.security_zone && app.app_id !== data.app_id)
        .slice(0, 5) || [];

    if (sameZoneApps.length === 0) {
        container.innerHTML = '<p style="font-size: 0.875rem; color: var(--gray-600);">No related applications found</p>';
        return;
    }

    container.innerHTML = sameZoneApps.map(app => `
        <a href="/application.html?id=${app.app_id}" style="display: block; padding: 0.75rem; background: #f9fafb; border-radius: 8px; margin-bottom: 0.5rem; text-decoration: none; color: var(--gray-900); border: 1px solid #e5e7eb; transition: all 0.2s;">
            <div style="font-weight: 600; margin-bottom: 0.25rem;">${app.app_id}</div>
            <div style="font-size: 0.75rem; color: var(--gray-600);">
                ${app.dependency_count} dependencies • ${(app.confidence * 100).toFixed(0)}% confidence
            </div>
        </a>
    `).join('');
}

function renderActivityTimeline(data) {
    const container = document.getElementById('activity-timeline');

    // Mock timeline data
    const timeline = [
        {
            date: new Date(data.timestamp || Date.now()).toLocaleDateString(),
            event: 'Application Discovered',
            details: 'Initial topology scan completed'
        },
        {
            date: new Date(data.timestamp || Date.now()).toLocaleDateString(),
            event: 'Security Classification',
            details: `Classified as ${data.security_zone} with ${(data.confidence * 100).toFixed(0)}% confidence`
        },
        {
            date: new Date(data.timestamp || Date.now()).toLocaleDateString(),
            event: 'DNS Validation',
            details: `${data.dns_validation?.total_validated || 0} IPs validated`
        }
    ];

    container.innerHTML = timeline.map(item => `
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-date">${item.date}</div>
                <div style="font-weight: 600; margin-bottom: 0.25rem;">${item.event}</div>
                <div style="font-size: 0.875rem; color: var(--gray-600);">${item.details}</div>
            </div>
        </div>
    `).join('');
}

function renderRecommendations(analysis) {
    const container = document.getElementById('recommendations-section');

    if (analysis.recommendations.length === 0) {
        container.innerHTML = `
            <div class="success">
                <i class="fas fa-check-circle"></i> <strong>No critical recommendations</strong>
                <p>Application security posture is acceptable. Continue monitoring.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = analysis.recommendations.map(rec => `
        <div class="recommendation-card rec-priority-${rec.priority}">
            <div class="rec-header">
                <h3 class="rec-title">${rec.title}</h3>
                <span class="badge badge-${
                    rec.priority === 'critical' ? 'danger' :
                    rec.priority === 'high' ? 'warning' : 'info'
                }">${rec.priority.toUpperCase()}</span>
            </div>
            <p style="color: var(--gray-700); margin-bottom: 1rem;">${rec.description}</p>
            <div style="padding: 1rem; background: #f9fafb; border-radius: 8px;">
                <strong style="font-size: 0.875rem; color: var(--gray-700);">Action Items:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; font-size: 0.875rem;">
                    ${rec.actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// Quick Actions
// ============================================================================

function exportApplication() {
    window.location.href = `/api/export/application/${appId}?format=json`;
}

function viewInTopology() {
    window.location.href = `/topology.html?highlight=${appId}`;
}

function generateReport() {
    alert('Report generation feature coming soon!');
}

function refreshDependencyGraph() {
    loadApplicationData();
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', loadApplicationData);
