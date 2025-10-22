"""
Interactive Path Visualization Generator
=========================================
Generates beautiful HTML visualizations for network paths,
gap analysis, and policy violations.

Uses only pip-installable libraries (no Graph DB required)

Author: Network Security Team
Version: 1.0
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PathVisualizer:
    """
    Generate interactive HTML visualizations for network path analysis
    """

    def __init__(self, graph_analyzer):
        """
        Initialize with GraphAnalyzer instance

        Args:
            graph_analyzer: GraphAnalyzer instance with network data
        """
        self.analyzer = graph_analyzer
        self.output_dir = Path('outputs/visualizations')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_shortest_path(self, source_ip: str, target_ip: str,
                               output_filename: str = 'shortest_path.html') -> Optional[str]:
        """
        Create interactive visualization of shortest path

        Args:
            source_ip: Source IP address
            target_ip: Target IP address
            output_filename: Output HTML filename

        Returns:
            Path to generated HTML file or None if no path found
        """
        logger.info(f"Generating path visualization: {source_ip} → {target_ip}")

        # Find path
        path_result = self.analyzer.find_shortest_path(source_ip, target_ip)

        if not path_result:
            logger.warning("No path found - cannot generate visualization")
            return None

        # Generate HTML
        html_content = self._generate_path_html(path_result, source_ip, target_ip)

        # Save
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"  ✓ Path visualization saved: {output_path}")
        return str(output_path)

    def visualize_all_paths(self, source_ip: str, target_ip: str,
                           max_paths: int = 10,
                           output_filename: str = 'all_paths.html') -> Optional[str]:
        """
        Visualize all paths between two IPs

        Args:
            source_ip: Source IP address
            target_ip: Target IP address
            max_paths: Maximum number of paths to show
            output_filename: Output HTML filename

        Returns:
            Path to generated HTML file
        """
        logger.info(f"Finding all paths: {source_ip} → {target_ip}")

        paths = self.analyzer.find_all_paths(source_ip, target_ip, max_depth=6)

        if not paths:
            logger.warning("No paths found")
            return None

        # Limit number of paths shown
        paths_to_show = paths[:max_paths]

        html_content = self._generate_multi_path_html(
            paths_to_show, source_ip, target_ip, len(paths)
        )

        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"  ✓ Multi-path visualization saved: {output_path}")
        return str(output_path)

    def visualize_gaps(self, gaps: List[Dict],
                      output_filename: str = 'gap_analysis.html') -> str:
        """
        Visualize topology gaps

        Args:
            gaps: List of gap dictionaries from analyzer.analyze_gaps()
            output_filename: Output HTML filename

        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating gap visualization for {len(gaps)} gaps")

        html_content = self._generate_gaps_html(gaps)

        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"  ✓ Gap analysis visualization saved: {output_path}")
        return str(output_path)

    def _generate_path_html(self, path_result: Dict, source: str, target: str) -> str:
        """Generate HTML for single shortest path"""
        path = path_result['path']
        hops = path_result['hops']

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Shortest Path: {source} → {target}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: #fff;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            opacity: 0.9;
            margin-bottom: 30px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            opacity: 0.8;
            font-size: 0.9em;
        }}
        .path-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .path-node {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 25px;
            border-radius: 10px;
            margin: 10px 0;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}
        .path-arrow {{
            display: inline-block;
            margin: 0 15px;
            font-size: 2em;
            opacity: 0.7;
        }}
        .hop-details {{
            margin-top: 30px;
        }}
        .hop-card {{
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .hop-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .hop-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        .info-item {{
            background: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
        }}
        .info-label {{
            font-size: 0.8em;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        .info-value {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Shortest Path Analysis</h1>
        <div class="subtitle">
            Network path from <strong>{source}</strong> to <strong>{target}</strong>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{path_result['path_length']}</div>
                <div class="metric-label">Hops</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{path_result['total_flows']:,}</div>
                <div class="metric-label">Total Flows</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{path_result['total_bytes'] / 1024 / 1024:.1f} MB</div>
                <div class="metric-label">Total Bytes</div>
            </div>
        </div>

        <div class="path-container">
            <h2 style="margin-top: 0;">Path Visualization</h2>
            <div style="text-align: center; padding: 20px; overflow-x: auto; white-space: nowrap;">
'''

        # Add path nodes
        for i, node in enumerate(path):
            hostname = self.analyzer.node_metadata.get(node, {}).get('hostname', '')
            display_name = f"{node}<br/><small>{hostname}</small>" if hostname else node

            html += f'                <div class="path-node">{display_name}</div>\n'
            if i < len(path) - 1:
                html += '                <span class="path-arrow">→</span>\n'

        html += '''            </div>
        </div>

        <div class="hop-details">
            <h2>Hop-by-Hop Details</h2>
'''

        # Add hop details
        for i, hop in enumerate(hops, 1):
            protocols_str = ', '.join(hop['protocols']) if hop['protocols'] else 'N/A'
            ports_str = ', '.join(map(str, hop['ports'])) if hop['ports'] else 'N/A'

            html += f'''
            <div class="hop-card">
                <div class="hop-title">Hop {i}: {hop['from']} → {hop['to']}</div>
                <div class="hop-info">
                    <div class="info-item">
                        <div class="info-label">Source</div>
                        <div class="info-value">{hop['from']}</div>
                        <div class="info-label" style="margin-top: 5px;">{hop['from_hostname'] or 'No hostname'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Destination</div>
                        <div class="info-value">{hop['to']}</div>
                        <div class="info-label" style="margin-top: 5px;">{hop['to_hostname'] or 'No hostname'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Flows</div>
                        <div class="info-value">{hop['flows']:,}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Bytes</div>
                        <div class="info-value">{hop['bytes'] / 1024:.1f} KB</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Protocols</div>
                        <div class="info-value">{protocols_str}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Ports</div>
                        <div class="info-value">{ports_str}</div>
                    </div>
                </div>
            </div>
'''

        html += '''
        </div>
    </div>
</body>
</html>'''

        return html

    def _generate_multi_path_html(self, paths: List[List[str]],
                                  source: str, target: str,
                                  total_paths: int) -> str:
        """Generate HTML for multiple paths"""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>All Paths: {source} → {target}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            margin: 0;
            padding: 20px;
            color: #fff;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            opacity: 0.9;
            margin-bottom: 30px;
        }}
        .path-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }}
        .path-card {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.2s;
        }}
        .path-card:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.2);
        }}
        .path-header {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }}
        .path-node {{
            background: rgba(0, 0, 0, 0.2);
            padding: 8px 15px;
            border-radius: 5px;
            margin: 5px 0;
            display: inline-block;
        }}
        .path-arrow {{
            display: inline-block;
            margin: 0 10px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 All Network Paths</h1>
        <div class="subtitle">
            Found <strong>{total_paths}</strong> paths from <strong>{source}</strong> to <strong>{target}</strong>
            <br/>
            (Showing first {len(paths)} paths)
        </div>

        <div class="path-grid">
'''

        for i, path in enumerate(paths, 1):
            html += f'''
            <div class="path-card">
                <div class="path-header">Path {i} ({len(path)-1} hops)</div>
                <div style="line-height: 2.5;">
'''
            for j, node in enumerate(path):
                html += f'                    <div class="path-node">{node}</div>'
                if j < len(path) - 1:
                    html += '<span class="path-arrow">→</span>'
                html += '\n'

            html += '''                </div>
            </div>
'''

        html += '''
        </div>
    </div>
</body>
</html>'''

        return html

    def _generate_gaps_html(self, gaps: List[Dict]) -> str:
        """Generate HTML for gap analysis"""
        # Group gaps by type
        gaps_by_type = {}
        for gap in gaps:
            gap_type = gap['gap_type']
            if gap_type not in gaps_by_type:
                gaps_by_type[gap_type] = []
            gaps_by_type[gap_type].append(gap)

        # Severity colors
        severity_colors = {
            'CRITICAL': '#ff4444',
            'HIGH': '#ff8800',
            'MEDIUM': '#ffbb33',
            'LOW': '#00C851'
        }

        html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Topology Gap Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            margin: 0;
            padding: 20px;
            color: #fff;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            opacity: 0.9;
            margin-bottom: 30px;
            font-size: 1.2em;
        }}
        .gap-section {{
            margin-bottom: 30px;
        }}
        .section-header {{
            background: rgba(0, 0, 0, 0.3);
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .gap-table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }}
        .gap-table th {{
            background: rgba(0, 0, 0, 0.4);
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        .gap-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .gap-table tr:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        .severity-badge {{
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
            display: inline-block;
        }}
        .recommendation {{
            font-size: 0.9em;
            opacity: 0.9;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚠️ Network Topology Gap Analysis</h1>
        <div class="subtitle">
            Found <strong>{gap_count}</strong> gaps in expected network topology
        </div>
'''

        html = html_template.format(gap_count=len(gaps))

        for gap_type, type_gaps in sorted(gaps_by_type.items()):
            html += f'''
        <div class="gap-section">
            <div class="section-header">
                {gap_type.replace('_', ' → ')} ({len(type_gaps)} gaps)
            </div>
            <table class="gap-table">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Destination</th>
                        <th>Severity</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
'''

            for gap in type_gaps:
                severity_color = severity_colors.get(gap['severity'], '#999')
                src_display = f"{gap['source_ip']}<br/><small>{gap['source_hostname'] or gap['source_app']}</small>"
                dst_display = f"{gap['destination_ip']}<br/><small>{gap['destination_hostname'] or gap['destination_app']}</small>"

                html += f'''
                    <tr>
                        <td>{src_display}</td>
                        <td>{dst_display}</td>
                        <td>
                            <span class="severity-badge" style="background: {severity_color};">
                                {gap['severity']}
                            </span>
                        </td>
                        <td class="recommendation">{gap['recommendation']}</td>
                    </tr>
'''

            html += '''
                </tbody>
            </table>
        </div>
'''

        html += '''
    </div>
</body>
</html>'''

        return html


if __name__ == '__main__':
    print("Path Visualizer - Use from main pipeline")
