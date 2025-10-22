#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Threat Surface HTML Visualization - Professional White Theme
======================================================================
Reads threat_surface_analysis.json and generates clean white HTML

Usage:
    python generate_threat_html.py
"""

import json
from pathlib import Path


def generate_threat_html():
    """Generate professional white-themed HTML from threat analysis JSON"""

    # Read threat analysis results
    json_path = Path('outputs/threat_analysis/threat_surface_analysis.json')

    if not json_path.exists():
        print(f"ERROR: {json_path} not found")
        print("Run 'python run_threat_analysis.py' first")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    attack_paths = data.get('attack_paths', [])[:10]  # Top 10
    exposure = data.get('exposure_analysis', {})
    chokepoints = data.get('critical_chokepoints', [])[:5]  # Top 5
    mitigations = data.get('mitigation_recommendations', [])

    # Get high exposure nodes
    high_exposure = [(ip, info) for ip, info in exposure.items()
                     if info.get('exposure_level') in ['CRITICAL', 'HIGH']]
    high_exposure.sort(key=lambda x: x[1].get('exposure_score', 0), reverse=True)
    high_exposure = high_exposure[:10]  # Top 10

    # Generate HTML with professional white theme
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Threat Surface Analysis - Network Security Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        h1 {{
            text-align: center;
            font-size: 2em;
            margin-bottom: 5px;
            color: #1a1a1a;
            font-weight: 600;
        }}

        .subtitle {{
            text-align: center;
            font-size: 0.95em;
            color: #666;
            margin-bottom: 25px;
        }}

        .alert {{
            background: #fff5f5;
            border: 1px solid #fc8181;
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 25px;
        }}

        .alert-title {{
            font-size: 1.05em;
            font-weight: 600;
            color: #c53030;
            margin-bottom: 5px;
        }}

        .alert-text {{
            color: #666;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 18px;
            border-radius: 8px;
            text-align: center;
            color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
        }}

        .metric-card.critical {{
            background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
        }}

        .metric-card.warning {{
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        }}

        .metric-card.success {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }}

        .metric-value {{
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .metric-label {{
            font-size: 0.9em;
            opacity: 0.95;
        }}

        .section {{
            margin: 35px 0;
        }}

        .section-title {{
            font-size: 1.5em;
            margin-bottom: 18px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            color: #1a1a1a;
            font-weight: 600;
        }}

        .path-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 16px;
            margin: 12px 0;
            border-radius: 6px;
            border-left: 4px solid #e53e3e;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}

        .path-card.high {{
            border-left-color: #ed8936;
        }}

        .path-card.medium {{
            border-left-color: #ecc94b;
        }}

        .path-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .path-title {{
            font-size: 1.05em;
            font-weight: 600;
            color: #2c3e50;
        }}

        .risk-badge {{
            background: #e53e3e;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .risk-badge.high {{
            background: #ed8936;
        }}

        .risk-badge.medium {{
            background: #ecc94b;
            color: #2d3748;
        }}

        .path-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }}

        .detail-item {{
            background: #f7fafc;
            padding: 10px 12px;
            border-radius: 5px;
            border-left: 2px solid #667eea;
        }}

        .detail-label {{
            font-size: 0.75em;
            color: #718096;
            margin-bottom: 3px;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}

        .detail-value {{
            font-size: 0.95em;
            font-weight: 600;
            color: #2d3748;
        }}

        .node-list {{
            background: #f7fafc;
            padding: 16px;
            border-radius: 6px;
            margin: 10px 0;
        }}

        .node-item {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 3px solid #48bb78;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }}

        .node-ip {{
            font-size: 1em;
            font-weight: 600;
            margin-bottom: 10px;
            color: #2c3e50;
        }}

        .node-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}

        .mitigation-card {{
            background: #f0fff4;
            border: 1px solid #68d391;
            border-radius: 6px;
            padding: 14px;
            margin: 12px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}

        .mitigation-priority {{
            display: inline-block;
            background: #48bb78;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.75em;
            text-transform: uppercase;
        }}

        .mitigation-priority.critical {{
            background: #e53e3e;
        }}

        .mitigation-priority.high {{
            background: #ed8936;
        }}

        .mitigation-title {{
            font-size: 1.05em;
            font-weight: 600;
            margin-bottom: 10px;
            color: #2c3e50;
        }}

        .mitigation-description {{
            margin: 8px 0;
            color: #4a5568;
            line-height: 1.6;
            font-size: 0.9em;
        }}

        .mitigation-description strong {{
            color: #2d3748;
        }}

        .footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
        }}

        .footer p {{
            margin: 5px 0;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Threat Surface Analysis</h1>
        <div class="subtitle">Network Security Assessment Report</div>

        <div class="alert">
            <div class="alert-title">Security Alert</div>
            <div class="alert-text">This report identifies critical vulnerabilities in your network infrastructure.
            Immediate action is recommended for CRITICAL and HIGH priority items.</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card critical">
                <div class="metric-value">{summary.get('total_attack_paths', 0)}</div>
                <div class="metric-label">Total Attack Paths</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-value">{summary.get('exposed_nodes', 0)}</div>
                <div class="metric-label">High-Exposure Nodes</div>
            </div>
            <div class="metric-card critical">
                <div class="metric-value">{summary.get('critical_assets_at_risk', 0)}</div>
                <div class="metric-label">Critical Assets at Risk</div>
            </div>
            <div class="metric-card success">
                <div class="metric-value">{summary.get('avg_attack_distance', 0):.1f}</div>
                <div class="metric-label">Avg Attack Distance (hops)</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Top Attack Paths</div>
"""

    # Add attack paths
    for i, path in enumerate(attack_paths, 1):
        risk_class = path.get('risk_level', 'MEDIUM').lower()
        html += f"""
            <div class="path-card {risk_class}">
                <div class="path-header">
                    <div class="path-title">{i}. {path.get('source_tier', 'UNKNOWN')} → {path.get('target_tier', 'UNKNOWN')}</div>
                    <div class="risk-badge {risk_class}">{path.get('risk_level', 'MEDIUM')}</div>
                </div>
                <div class="path-details">
                    <div class="detail-item">
                        <div class="detail-label">Source IP</div>
                        <div class="detail-value">{path.get('source', 'N/A')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Target IP</div>
                        <div class="detail-value">{path.get('target', 'N/A')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Path Length</div>
                        <div class="detail-value">{path.get('path_length', 0)} hops</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Attack Vector</div>
                        <div class="detail-value">{path.get('attack_vector', 'N/A')}</div>
                    </div>
                </div>
            </div>
"""

    html += """
        </div>

        <div class="section">
            <div class="section-title">High-Exposure Nodes</div>
            <div class="node-list">
"""

    # Add high exposure nodes
    for i, (ip, info) in enumerate(high_exposure, 1):
        html += f"""
                <div class="node-item">
                    <div class="node-ip">{i}. {ip}</div>
                    <div class="node-info">
                        <div class="detail-item">
                            <div class="detail-label">Tier</div>
                            <div class="detail-value">{info.get('tier', 'UNKNOWN')}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Exposure Level</div>
                            <div class="detail-value">{info.get('exposure_level', 'UNKNOWN')}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Exposure Score</div>
                            <div class="detail-value">{info.get('exposure_score', 0):.1f}/10</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">External Access</div>
                            <div class="detail-value">{'Yes' if info.get('has_external_access') else 'No'}</div>
                        </div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>

        <div class="section">
            <div class="section-title">Mitigation Recommendations</div>
"""

    # Add mitigations
    for i, mitigation in enumerate(mitigations[:10], 1):
        priority = mitigation.get('priority', 'MEDIUM').lower()
        html += f"""
            <div class="mitigation-card">
                <div class="mitigation-priority {priority}">{mitigation.get('priority', 'MEDIUM')}</div>
                <div class="mitigation-title">{i}. {mitigation.get('title', 'Mitigation Recommendation')}</div>
                <div class="mitigation-description">
                    <strong>Category:</strong> {mitigation.get('category', 'N/A')}<br>
                    <strong>Description:</strong> {mitigation.get('description', 'N/A')}<br>
                    <strong>Implementation:</strong> {mitigation.get('implementation', 'N/A')}<br>
                    <strong>Impact:</strong> {mitigation.get('impact', 'N/A')}
                </div>
            </div>
"""

    html += """
        </div>

        <div class="footer">
            <p><strong>Network Segmentation Analyzer</strong> - Threat Surface Analysis</p>
            <p>Report generated from real network flow data</p>
        </div>
    </div>
</body>
</html>
"""

    # Save HTML
    output_path = Path('outputs/visualizations/threat_surface.html')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML visualization generated: {output_path}")
    return output_path


if __name__ == '__main__':
    output_path = generate_threat_html()

    if output_path:
        print(f"\nOpen in browser:")
        print(f"  start {output_path}  (Windows)")
        print(f"  open {output_path}   (macOS)")
        print(f"  xdg-open {output_path}  (Linux)")
