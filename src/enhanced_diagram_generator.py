#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Application Diagram Generator
=======================================
Generates diagrams with server classification and layered architecture.

Features:
- Server type classification (DNS, LDAP, F5, CDN, etc.)
- Layered architecture visualization (web → app → db)
- Grouped rectangles for applications
- Server names with protocols
- Multi-format output (mmd, png, svg, docx)

Author: Enterprise Security Team
Version: 3.0 - Enhanced with Server Classification
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from src.server_classifier import ServerClassifier

logger = logging.getLogger(__name__)


class EnhancedDiagramGenerator:
    """Enhanced diagram generator with server classification and layered architecture"""

    # Color scheme matching application_diagram_generator.py
    SERVER_TYPE_COLORS = {
        # Infrastructure servers
        'DNS': '#99ffcc',                    # Mint - Network services
        'LDAP Server': '#99ffcc',            # Mint - Network services
        'Active Directory': '#99ffcc',       # Mint - Network services
        'Traffic Manager': '#ffb3d9',        # Pink - Load Balancers
        'F5 Load Balancer': '#ffb3d9',       # Pink - Load Balancers
        'CDN': '#99ffcc',                    # Mint - Network services

        # Monitoring/Security servers
        'Splunk': '#ffe6cc',                 # Peach - Monitoring/Logging
        'Rapid7': '#ff9999',                 # Coral - Security services
        'DB Auditor': '#ff9999',             # Coral - Security services
        'CyberArk': '#ff9999',               # Coral - Security services
        'Azure Key Vault': '#ff9999',        # Coral - Security services

        # Application servers
        'ServiceNow': '#cce5ff',             # Blue - Application Tier
        'CIFS Server': '#cce5ff',            # Blue - Application Tier
        'Mail Server': '#cce5ff',            # Blue - Application Tier
        'SSRS': '#cce5ff',                   # Blue - Application Tier

        # Database servers
        'MySQL/Oracle': '#ff9966',           # Orange - Data Tier

        # Cloud services
        'AWS': '#e6ccff',                    # Light Purple - External systems
        'Azure Traffic Manager': '#e6ccff',  # Light Purple - External systems

        # Tier colors (for fallback)
        'web': '#ffcccc',                    # Red - Web Tier (frontend)
        'app': '#cce5ff',                    # Blue - Application Tier
        'database': '#ff9966',               # Orange - Data Tier
        'infrastructure': '#99ffcc',         # Mint - Network services
        'security': '#ff9999',               # Coral - Security services
        'cloud': '#e6ccff',                  # Light Purple - External
        'unknown': '#e0e0e0'                 # Gray - Unknown/Unclassified
    }

    def __init__(self, hostname_resolver=None):
        """Initialize enhanced diagram generator

        Args:
            hostname_resolver: Optional hostname resolver for IP→hostname mapping
        """
        self.hostname_resolver = hostname_resolver
        self.classifier = ServerClassifier()
        logger.info("EnhancedDiagramGenerator initialized with ServerClassifier")

    def generate_enhanced_diagram(
        self,
        app_name: str,
        flow_records: List,
        output_dir: str = 'outputs/diagrams',
        output_formats: List[str] = None
    ) -> Dict[str, str]:
        """Generate enhanced diagram with server classification

        Args:
            app_name: Application name
            flow_records: List of FlowRecord objects
            output_dir: Output directory path
            output_formats: List of formats to generate ['mmd', 'png', 'svg', 'docx']

        Returns:
            Dict of format → output path
        """
        logger.info(f"Generating enhanced diagram for: {app_name}")

        output_formats = output_formats or ['mmd', 'html']
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Analyze flow records and classify servers
        classified_servers = self._analyze_and_classify(app_name, flow_records)

        # Build Mermaid diagram
        mermaid_content = self._build_enhanced_mermaid(app_name, classified_servers)

        # Save outputs
        output_paths = {}

        # Save .mmd file
        if 'mmd' in output_formats:
            mmd_path = output_dir / f"{app_name}_enhanced.mmd"
            with open(mmd_path, 'w', encoding='utf-8') as f:
                f.write(mermaid_content)
            output_paths['mmd'] = str(mmd_path)
            logger.info(f"  [OK] Saved Mermaid diagram: {mmd_path.name}")

        # Save HTML file
        if 'html' in output_formats:
            html_path = output_dir / f"{app_name}_enhanced.html"
            self._generate_html(mermaid_content, str(html_path))
            output_paths['html'] = str(html_path)
            logger.info(f"  [OK] Saved HTML diagram: {html_path.name}")

        # PNG and SVG generation will be added later
        # DOCX generation will be added later

        return output_paths

    def _analyze_and_classify(self, app_name: str, flow_records: List) -> Dict:
        """Analyze flow records and classify all servers

        Args:
            app_name: Application name
            flow_records: List of FlowRecord objects

        Returns:
            Dict with classified servers grouped by tier and type
        """
        # Track all destination servers with protocols and ports
        dest_servers = defaultdict(lambda: {
            'ips': set(),
            'protocols': set(),
            'ports': set(),
            'bytes': 0,
            'count': 0
        })

        for record in flow_records:
            # Skip invalid records
            if not record.dst_ip or not isinstance(record.dst_ip, str) or record.dst_ip == 'nan':
                continue

            # Resolve hostname
            hostname = self.hostname_resolver.resolve(record.dst_ip) if self.hostname_resolver else record.dst_ip

            # Collect information
            dest_servers[hostname]['ips'].add(record.dst_ip)
            if hasattr(record, 'protocol') and record.protocol:
                dest_servers[hostname]['protocols'].add(record.protocol)
            if hasattr(record, 'dst_port') and record.dst_port:
                try:
                    dest_servers[hostname]['ports'].add(int(record.dst_port))
                except:
                    pass
            dest_servers[hostname]['bytes'] += getattr(record, 'bytes', 0)
            dest_servers[hostname]['count'] += 1

        # Classify each server
        classified = {
            'web': [],
            'app': [],
            'database': [],
            'infrastructure': [],
            'security': [],
            'cloud': [],
            'unknown': []
        }

        for hostname, data in dest_servers.items():
            protocols = list(data['protocols'])
            ports = list(data['ports'])

            # Classify server
            classification = self.classifier.classify_server(hostname, protocols, ports)

            server_info = {
                'hostname': hostname,
                'ips': list(data['ips']),
                'protocols': protocols,
                'ports': ports,
                'bytes': data['bytes'],
                'count': data['count'],
                'server_type': classification['type'],
                'tier': classification['tier'],
                'category': classification['category']
            }

            # Add to appropriate tier
            tier = classification['tier'] or 'unknown'
            if tier in classified:
                classified[tier].append(server_info)
            else:
                classified['unknown'].append(server_info)

        # Sort by traffic volume
        for tier in classified:
            classified[tier].sort(key=lambda x: (x['bytes'], x['count']), reverse=True)

        logger.info(f"  Classified {sum(len(v) for v in classified.values())} servers:")
        for tier, servers in classified.items():
            if servers:
                logger.info(f"    {tier}: {len(servers)} servers")

        return classified

    def _build_enhanced_mermaid(self, app_name: str, classified_servers: Dict) -> str:
        """Build enhanced Mermaid diagram with server classification

        Args:
            app_name: Application name
            classified_servers: Dict of tier → list of server info

        Returns:
            Mermaid diagram content
        """
        lines = [
            "```mermaid",
            "graph TB",
            ""
        ]

        # Main application node
        app_node = self._sanitize_id(app_name)
        lines.append(f"    {app_node}[\"{app_name}<br/>Application\"]")
        lines.append(f"    style {app_node} fill:#3498db,stroke:#333,stroke-width:3px,color:#fff")
        lines.append("")

        # Counter for link styling
        link_index = 0

        # Render each tier
        for tier, servers in classified_servers.items():
            if not servers:
                continue

            tier_label = tier.replace('_', ' ').title()
            tier_color = self.SERVER_TYPE_COLORS.get(tier, '#e0e0e0')

            # Group servers by server type within tier
            by_type = defaultdict(list)
            for server in servers:
                server_type = server['server_type'] or 'Unknown'
                by_type[server_type].append(server)

            # Create subgraph for tier
            tier_id = self._sanitize_id(f"{app_name}_{tier}_group")
            lines.append(f"    subgraph {tier_id}[\"{tier_label}\"]")
            lines.append("        direction TB")

            # Render servers grouped by type
            for server_type, type_servers in by_type.items():
                type_color = self.SERVER_TYPE_COLORS.get(server_type, tier_color)

                for server in type_servers[:10]:  # Limit to top 10 per type
                    node_id = self._sanitize_id(server['hostname'])

                    # Build label with server name, type, and protocols
                    protocols_str = ', '.join(sorted(server['protocols']))[:50] if server['protocols'] else 'N/A'
                    label_lines = [
                        f"{server['hostname'][:40]}",
                        f"Type: {server_type}",
                        f"Protocols: {protocols_str}"
                    ]
                    label = '<br/>'.join(label_lines)

                    # Determine shape based on tier
                    if server['tier'] == 'database':
                        shape = f"[{label}]"  # Rectangle for databases
                    else:
                        shape = f"({label})"  # Rounded rectangle for others

                    lines.append(f"        {node_id}{shape}")
                    lines.append(f"        style {node_id} fill:{type_color},stroke:#333,stroke-width:2px")

            lines.append("    end")
            lines.append("")

            # Add flows from app to servers in this tier
            for server_type, type_servers in by_type.items():
                for server in type_servers[:10]:  # Match limit
                    node_id = self._sanitize_id(server['hostname'])

                    # Flow label
                    flow_label = self._get_flow_label(server)

                    # Add flow
                    lines.append(f"    {app_node} --{flow_label}--> {node_id}")
                    lines.append(f"    linkStyle {link_index} stroke:#333,stroke-width:2px")
                    link_index += 1

        lines.append("```")
        lines.append("")

        # Add legend
        lines.extend(self._build_legend())

        return '\n'.join(lines)

    def _get_flow_label(self, server: Dict) -> str:
        """Generate flow label based on server info

        Args:
            server: Server info dict

        Returns:
            Flow label string
        """
        server_type = server['server_type']
        tier = server['tier']
        protocols = server['protocols']

        # Special labels for known types
        if server_type == 'MySQL/Oracle':
            return 'DB queries'
        elif server_type == 'LDAP Server' or server_type == 'Active Directory':
            return 'Auth/Directory'
        elif server_type == 'F5 Load Balancer':
            return 'Load Balanced'
        elif server_type == 'CDN':
            return 'CDN requests'
        elif server_type == 'Mail Server':
            return 'Email'
        elif server_type == 'Azure Key Vault':
            return 'Secrets/Keys'
        elif tier == 'database':
            return 'Data queries'
        elif tier == 'web':
            return 'HTTP/S'
        elif protocols:
            # Use first protocol
            return list(protocols)[0][:20]
        else:
            return 'data flow'

    def _build_legend(self) -> List[str]:
        """Build legend for diagram

        Returns:
            List of legend lines
        """
        return [
            "",
            "**Legend:**",
            "",
            "**Shapes:**",
            "- **Application Node** = Source application (blue)",
            "- **Rounded Rectangles** = Services/Servers",
            "- **Rectangles** = Databases",
            "",
            "**Server Types:**",
            "- DNS, LDAP, Active Directory, CDN = Network Services (Mint)",
            "- F5 Load Balancer, Traffic Manager = Load Balancers (Pink)",
            "- Splunk = Monitoring/Logging (Peach)",
            "- CyberArk, Azure Key Vault, Rapid7, DB Auditor = Security Services (Coral)",
            "- ServiceNow, CIFS, Mail, SSRS = Application Services (Blue)",
            "- MySQL/Oracle = Database Tier (Orange)",
            "- AWS, Azure Traffic Manager = Cloud/External (Light Purple)",
            "",
            "**Colors (matching application_diagram_generator.py):**",
            "- Red (#ffcccc) = Web Tier (frontend)",
            "- Blue (#cce5ff) = Application Tier",
            "- Orange (#ff9966) = Data Tier (databases)",
            "- Mint (#99ffcc) = Network Services",
            "- Pink (#ffb3d9) = Load Balancers",
            "- Peach (#ffe6cc) = Monitoring/Logging",
            "- Coral (#ff9999) = Security Services",
            "- Light Purple (#e6ccff) = External Systems",
            "- Gray (#e0e0e0) = Unknown",
            ""
        ]

    def _generate_html(self, mermaid_content: str, output_path: str):
        """Generate interactive HTML diagram

        Args:
            mermaid_content: Mermaid diagram content
            output_path: Output HTML file path
        """
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Application Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .diagram-container {{
            margin: 20px 0;
            overflow-x: auto;
        }}
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        button {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Enhanced Application Diagram - Server Classification</h1>

        <div class="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetZoom()">Reset</button>
            <button onclick="window.print()">Print</button>
        </div>

        <div class="diagram-container" id="diagram">
            <pre class="mermaid">
{mermaid_content.replace('```mermaid', '').replace('```', '').strip()}
            </pre>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});

        let currentZoom = 1.0;

        function zoomIn() {{
            currentZoom += 0.1;
            document.getElementById('diagram').style.transform = `scale(${{currentZoom}})`;
            document.getElementById('diagram').style.transformOrigin = 'top left';
        }}

        function zoomOut() {{
            if (currentZoom > 0.3) {{
                currentZoom -= 0.1;
                document.getElementById('diagram').style.transform = `scale(${{currentZoom}})`;
                document.getElementById('diagram').style.transformOrigin = 'top left';
            }}
        }}

        function resetZoom() {{
            currentZoom = 1.0;
            document.getElementById('diagram').style.transform = 'scale(1)';
        }}
    </script>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

    def _sanitize_id(self, name: str) -> str:
        """Sanitize name for use as Mermaid node ID

        Args:
            name: Node name

        Returns:
            Sanitized ID
        """
        import re
        # Replace special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized or 'node'


# Convenience function
def generate_enhanced_diagram(app_name: str, flow_records: List,
                             hostname_resolver=None,
                             output_dir: str = 'outputs/diagrams',
                             output_formats: List[str] = None) -> Dict[str, str]:
    """
    Generate enhanced diagram with server classification

    Args:
        app_name: Application name
        flow_records: List of FlowRecord objects
        hostname_resolver: Optional hostname resolver
        output_dir: Output directory
        output_formats: List of formats ['mmd', 'html', 'png', 'svg', 'docx']

    Returns:
        Dict of format → output path
    """
    generator = EnhancedDiagramGenerator(hostname_resolver)
    return generator.generate_enhanced_diagram(
        app_name, flow_records, output_dir, output_formats
    )


if __name__ == '__main__':
    print("Enhanced Diagram Generator with Server Classification")
    print("=" * 80)
    print("Usage:")
    print("  from src.enhanced_diagram_generator import generate_enhanced_diagram")
    print("  generate_enhanced_diagram(app_name, flow_records, hostname_resolver)")
