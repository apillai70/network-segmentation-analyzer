#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application-Level Data Flow Diagram Generator
==============================================
Generates diagrams following the Data Flow Diagram template format.

Visual Style:
- Circles: Services/APIs (color-coded by zone)
- Rectangles: Data stores, External systems
- Arrows: Application-level data flows (NO ports/protocols)
- Predictions: Dashed lines with different colors

Author: Enterprise Security Team
Version: 2.0 - Template-based Application Diagrams
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ApplicationDiagramGenerator:
    """Generates application-level data flow diagrams in Mermaid format"""

    # Color scheme following template
    ZONE_COLORS = {
        'WEB_TIER': '#ffcccc',           # Pink (frontend)
        'APP_TIER': '#ccffff',           # Cyan (backend services)
        'DATA_TIER': '#ccffcc',          # Light green (databases)
        'CACHE_TIER': '#ccffff',         # Cyan (cache services)
        'MESSAGING_TIER': '#ccffff',     # Cyan (message queues)
        'MANAGEMENT_TIER': '#ffffcc',    # Yellow (infrastructure)
        'EXTERNAL': '#e6ccff',           # Purple (external systems)
        'PREDICTED': '#aed6f1',          # ✅ LIGHT BLUE for predictions
    }

    # Shape types
    SHAPE_CIRCLE = '(({}))'              # Services/APIs
    SHAPE_RECTANGLE = '[{}]'             # Data stores
    SHAPE_ROUNDED_RECT = '({})' # External systems
    SHAPE_PREDICTED_CIRCLE = '(({}))' # Predicted services (dashed)

    def __init__(self, hostname_resolver=None):
        """Initialize diagram generator

        Args:
            hostname_resolver: Optional hostname resolver for IP→hostname mapping
        """
        self.hostname_resolver = hostname_resolver
        logger.info("ApplicationDiagramGenerator initialized")

    def _get_component_type(self, name: str, zone: str) -> str:
        """Determine component type from name and zone

        Returns:
            'service', 'database', 'cache', 'queue', 'external'
        """
        name_lower = name.lower()

        # Database indicators
        if any(db in name_lower for db in ['db', 'database', 'mysql', 'postgres', 'mongo', 'oracle', 'snowflake']):
            return 'database'

        # Cache indicators
        if any(cache in name_lower for cache in ['redis', 'memcache', 'cache']):
            return 'cache'

        # Message queue indicators
        if any(mq in name_lower for mq in ['kafka', 'rabbitmq', 'mq', 'queue', 'topic']):
            return 'queue'

        # External systems
        if zone == 'EXTERNAL':
            return 'external'

        # Default to service
        return 'service'

    def _get_node_shape(self, component_type: str, is_predicted: bool = False) -> tuple:
        """Get Mermaid shape for component type

        Returns:
            (shape_template, shape_description)
        """
        if is_predicted:
            return self.SHAPE_PREDICTED_CIRCLE, 'predicted_service'

        shapes = {
            'service': (self.SHAPE_CIRCLE, 'service'),
            'database': (self.SHAPE_RECTANGLE, 'datastore'),
            'cache': (self.SHAPE_RECTANGLE, 'datastore'),
            'queue': (self.SHAPE_RECTANGLE, 'datastore'),
            'external': (self.SHAPE_ROUNDED_RECT, 'external'),
        }

        return shapes.get(component_type, (self.SHAPE_CIRCLE, 'service'))

    def _get_flow_description(self, source: str, target: str, protocol: str = None) -> str:
        """Generate human-readable flow description (application-level only)

        NO ports or protocols - application semantics only
        """
        source_lower = source.lower()
        target_lower = target.lower()

        # Database flows
        if 'db' in target_lower or 'database' in target_lower:
            return 'data queries'

        # Cache flows
        if 'redis' in target_lower or 'cache' in target_lower:
            return 'cache operations'

        # Kafka/messaging flows
        if 'kafka' in target_lower or 'queue' in target_lower or 'topic' in target_lower:
            return 'event messages'

        # API flows
        if 'api' in target_lower:
            return 'API requests'

        # Service-to-service
        if 'service' in source_lower and 'service' in target_lower:
            return 'service calls'

        # Generic
        return 'data flow'

    def generate_application_diagram(
        self,
        app_name: str,
        flow_records: List,
        topology_data: Dict = None,
        predictions: Dict = None,
        output_path: str = None,
        max_nodes: int = 15,
        filter_nonexistent: bool = True
    ) -> str:
        """Generate application-level data flow diagram showing internal architecture

        Args:
            app_name: Application name
            flow_records: List of FlowRecord objects
            topology_data: Topology metadata (zone, dependencies)
            predictions: Markov chain predictions (optional)
            output_path: Output file path for .mmd file
            max_nodes: Maximum number of external connections to show (default: 15)
            filter_nonexistent: If True, filter flows with both IPs non-existent (default: True)

        Returns:
            Mermaid diagram content
        """
        logger.info(f"Generating application architecture diagram for: {app_name}")

        from collections import defaultdict

        # Apply filtering to flow records if hostname resolver available
        if filter_nonexistent and self.hostname_resolver:
            from utils.flow_filter import apply_filtering_to_records
            flow_records = apply_filtering_to_records(
                flow_records,
                self.hostname_resolver,
                filter_enabled=True,
                log_stats=False  # Don't log per-app (too verbose)
            )

        # Analyze SOURCE IPs to determine internal tiers
        internal_tiers = defaultdict(set)

        for record in flow_records:
            # ✅ FIX: Skip if src_ip is missing, invalid, or string 'nan'
            if not record.src_ip or not isinstance(record.src_ip, str) or record.src_ip == 'nan':
                continue

            # Classify source IP by subnet to determine tier
            src_zone = self._infer_zone_from_ip(record.src_ip)
            # Only track internal tiers (ignore external IPs)
            if src_zone != 'EXTERNAL':
                internal_tiers[src_zone].add(record.src_ip)

        logger.info(f"  Found internal tiers: {list(internal_tiers.keys())}")

        # Analyze destinations to separate applications from infrastructure
        dest_traffic = defaultdict(lambda: {
            'bytes': 0, 'count': 0, 'ips': set(), 'zone': None,
            'hostnames': set(), 'is_app': False, 'is_infrastructure': False
        })

        for record in flow_records:
            # ✅ FIX: Skip if dst_ip is missing, invalid, or string 'nan'
            if not record.dst_ip or not isinstance(record.dst_ip, str) or record.dst_ip == 'nan':
                continue

            target_name = self.hostname_resolver.resolve(record.dst_ip) if self.hostname_resolver else record.dst_ip
            dest_traffic[target_name]['bytes'] += getattr(record, 'bytes', 0)
            dest_traffic[target_name]['count'] += 1
            dest_traffic[target_name]['ips'].add(record.dst_ip)

            if dest_traffic[target_name]['zone'] is None:
                dest_traffic[target_name]['zone'] = self._infer_zone_from_ip(record.dst_ip)

            # Classify as application or infrastructure
            dest_zone = dest_traffic[target_name]['zone']
            dest_type = self._get_component_type(target_name, dest_zone)

            if dest_type in ['database', 'cache', 'queue']:
                dest_traffic[target_name]['is_infrastructure'] = True
            elif 'srv' in target_name.lower() or 'app' in target_name.lower():
                dest_traffic[target_name]['is_app'] = True

        # Separate applications from infrastructure
        downstream_apps = {}
        infrastructure = {}

        for dest_name, dest_data in dest_traffic.items():
            if dest_data['is_infrastructure']:
                infrastructure[dest_name] = dest_data
            elif dest_data['is_app'] or dest_data['zone'] in ['APP_TIER', 'WEB_TIER', 'MESSAGING_TIER']:
                downstream_apps[dest_name] = dest_data
            else:
                # Default: treat as infrastructure
                infrastructure[dest_name] = dest_data

        # Sort and limit
        top_apps = sorted(
            downstream_apps.items(),
            key=lambda x: (x[1]['bytes'], x[1]['count']),
            reverse=True
        )[:10]

        top_infrastructure = sorted(
            infrastructure.items(),
            key=lambda x: (x[1]['bytes'], x[1]['count']),
            reverse=True
        )[:10]

        logger.info(f"  Found {len(top_apps)} downstream applications, {len(top_infrastructure)} infrastructure dependencies")

        # Build diagram components
        components = {
            'internal_tiers': internal_tiers,
            'downstream_apps': {},
            'infrastructure': {}
        }

        flows = []

        # Add downstream applications
        for app_name_dest, app_data in top_apps:
            components['downstream_apps'][app_name_dest] = {
                'type': 'service',
                'zone': app_data['zone'],
                'is_predicted': False
            }

            flows.append({
                'source': app_name,
                'target': app_name_dest,
                'label': 'app calls',
                'is_predicted': False,
                'flow_type': 'app_to_app'
            })

        # Add infrastructure
        for infra_name, infra_data in top_infrastructure:
            components['infrastructure'][infra_name] = {
                'type': self._get_component_type(infra_name, infra_data['zone']),
                'zone': infra_data['zone'],
                'is_predicted': False
            }

            flow_desc = self._get_flow_description(app_name, infra_name, None)
            flows.append({
                'source': app_name,
                'target': infra_name,
                'label': flow_desc,
                'is_predicted': False,
                'flow_type': 'app_to_infra'
            })

        # Add predicted dependencies (Markov chain)
        if predictions:
            predicted_deps = predictions.get('predicted_dependencies', [])
            for pred in predicted_deps:
                pred_name = pred.get('name', 'Unknown')

                if pred_name not in components:
                    components[pred_name] = {
                        'type': pred.get('type', 'service'),
                        'zone': 'PREDICTED',
                        'is_predicted': True
                    }

                # Add predicted flow (dashed line)
                flows.append({
                    'source': app_name,
                    'target': pred_name,
                    'label': f"predicted: {pred.get('description', 'data flow')}",
                    'is_predicted': True
                })

        # Generate Mermaid diagram
        mermaid = self._build_mermaid_diagram(app_name, components, flows)

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(mermaid)

            logger.info(f"✓ Application diagram saved: {output_path}")

            # Also generate HTML version
            self._generate_html_diagram(mermaid, str(output_file.with_suffix('.html')))

            # Generate PNG using mmdc
            self._generate_png_diagram(str(output_file), str(output_file.with_suffix('.png')))

        return mermaid

    def _generate_png_diagram(self, mmd_path: str, png_path: str):
        """Generate PNG from Mermaid file using mmdc command"""
        import subprocess
        import tempfile

        try:
            # Create temporary file without markdown code fences (mmdc doesn't accept them)
            with open(mmd_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract only the graph content (between ```mermaid and ```, excluding legend)
            lines = content.split('\n')
            graph_lines = []
            in_graph = False

            for line in lines:
                if line.strip().startswith('```mermaid'):
                    in_graph = True
                    continue
                elif line.strip() == '```':
                    in_graph = False
                    break
                elif in_graph:
                    graph_lines.append(line)

            # Join only the graph content
            content = '\n'.join(graph_lines).strip()

            # Write raw mermaid to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Try mmdc with full path first (Windows)
            mmdc_paths = [
                r"C:\Users\AjayPillai\AppData\Roaming\npm\mmdc.cmd",
                'mmdc'
            ]

            success = False
            for mmdc_cmd in mmdc_paths:
                try:
                    result = subprocess.run(
                        [mmdc_cmd, '-i', tmp_path, '-o', png_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        logger.info(f"✓ PNG diagram generated: {Path(png_path).name}")
                        success = True
                        break
                    elif 'UnknownDiagramError' in result.stderr:
                        logger.warning(f"Mermaid syntax error in {Path(mmd_path).name}")
                        break
                except FileNotFoundError:
                    continue

            if not success and all(not Path(p).exists() for p in mmdc_paths if not p == 'mmdc'):
                logger.warning("mmdc not found - PNG generation skipped")

            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except:
                pass

        except subprocess.TimeoutExpired:
            logger.error(f"PNG generation timed out for {Path(mmd_path).name}")
        except Exception as e:
            logger.error(f"Failed to generate PNG: {e}")

    def _build_mermaid_diagram(self, app_name: str, components: Dict, flows: List) -> str:
        """Build Mermaid diagram showing internal architecture, downstream apps, and infrastructure"""

        lines = [
            "```mermaid",
            "graph LR",  # Left-to-right for application flow
            ""
        ]

        # Get components
        internal_tiers = components.get('internal_tiers', {})
        downstream_apps = components.get('downstream_apps', {})
        infrastructure = components.get('infrastructure', {})

        # Tier display order
        tier_order = ['WEB_TIER', 'APP_TIER', 'DATA_TIER', 'CACHE_TIER', 'MESSAGING_TIER', 'MANAGEMENT_TIER']
        tier_labels = {
            'WEB_TIER': 'Web Tier',
            'APP_TIER': 'App Tier',
            'DATA_TIER': 'Data Tier',
            'CACHE_TIER': 'Cache Tier',
            'MESSAGING_TIER': 'Messaging Tier',
            'MANAGEMENT_TIER': 'Management Tier'
        }

        # Create main application container with internal architecture
        lines.append(f"    subgraph app_container[\"{app_name} Application\"]")
        lines.append("        direction TB")
        lines.append("")

        # Render internal tiers
        tier_nodes = []
        for tier_name in tier_order:
            if tier_name not in internal_tiers or not internal_tiers[tier_name]:
                continue

            ip_count = len(internal_tiers[tier_name])
            tier_label = tier_labels.get(tier_name, tier_name)
            node_id = self._sanitize_id(f"{app_name}_{tier_name}")
            tier_nodes.append(node_id)

            color = self.ZONE_COLORS.get(tier_name, '#cccccc')
            lines.append(f"        {node_id}[\"{tier_label}<br/>{ip_count} server(s)\"]")
            lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")

        # Add tier connections
        lines.append("")
        for i in range(len(tier_nodes) - 1):
            lines.append(f"        {tier_nodes[i]} --> {tier_nodes[i+1]}")

        lines.append("    end")
        lines.append("")

        # Render downstream applications
        if downstream_apps:
            lines.append(f"    subgraph downstream_apps_group[\"Downstream Applications\"]")
            for app_name_dest, app_data in downstream_apps.items():
                node_id = self._sanitize_id(app_name_dest)
                color = self.ZONE_COLORS.get(app_data['zone'], '#cccccc')

                lines.append(f"        {node_id}(({app_name_dest}))")
                lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")

            lines.append("    end")
            lines.append("")

        # Render infrastructure grouped by type
        from collections import defaultdict
        by_type = defaultdict(list)

        for infra_name, infra_data in infrastructure.items():
            by_type[infra_data['type']].append((infra_name, infra_data))

        for comp_type in ['database', 'cache', 'queue']:
            if comp_type not in by_type or not by_type[comp_type]:
                continue

            type_label = comp_type.replace('_', ' ').title()
            lines.append(f"    subgraph {comp_type}_group[\"{type_label}s\"]")

            for comp_name, comp_data in by_type[comp_type]:
                shape_template, _ = self._get_node_shape(comp_data['type'], comp_data['is_predicted'])
                node_id = self._sanitize_id(comp_name)

                zone = comp_data['zone']
                color = self.ZONE_COLORS.get(zone, '#cccccc')

                lines.append(f"        {node_id}{shape_template.format(comp_name)}")

                # ✅ FIX: Blue stroke for predicted nodes
                if comp_data['is_predicted']:
                    lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
                else:
                    lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")

            lines.append("    end")
            lines.append("")

        # Define flows
        lines.append("")
        app_node = "app_container"

        flow_index = 0  # Track flow index for styling
        for flow in flows:
            target_id = self._sanitize_id(flow['target'])
            label = flow['label']
            flow_type = flow.get('flow_type', 'app_to_infra')

            if flow['is_predicted']:
                # ✅ FIX: Blue dashed line for predictions
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
                lines.append(f"    linkStyle {flow_index} stroke:#3498db,stroke-width:2px")
            else:
                # Use thicker arrows for app-to-app connections
                if flow_type == 'app_to_app':
                    lines.append(f"    {app_node} =={label}==> {target_id}")
                else:
                    lines.append(f"    {app_node} --{label}--> {target_id}")

            flow_index += 1

        lines.append("```")
        lines.append("")

        # Add legend
        lines.extend([
            "",
            "**Legend:**",
            "- **Application Box** = Internal architecture (web/app/db tiers)",
            "- **Downstream Apps** = Applications this app calls",
            "- **Infrastructure** = Databases, caches, queues",
            "- ⚪ Circles = Services/Applications",
            "- ▭ Rectangles = Data Stores",
            "- === Thick lines = App-to-app calls (observed)",
            "- ─── Solid lines = Infrastructure dependencies (observed)",
            "- ╌╌╌ Blue dashed lines = Predicted flows (Markov chain)",
            "- 🔵 Blue outline = Predicted components",
            "- 🎨 Colors indicate security zones",
            ""
        ])

        return '\n'.join(lines)

    def _generate_html_diagram(self, mermaid_content: str, html_path: str):
        """Generate interactive HTML version of diagram"""

        # Extract ONLY the graph portion (between backticks, excluding legend)
        # Split by lines and find the graph content
        lines = mermaid_content.split('\n')
        graph_lines = []
        in_graph = False

        for line in lines:
            if line.strip().startswith('```mermaid'):
                in_graph = True
                continue
            elif line.strip().startswith('```'):
                in_graph = False
                break
            elif in_graph:
                graph_lines.append(line)

        # Join only the graph content
        graph_content = '\n'.join(graph_lines).strip()

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Application Data Flow Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .diagram-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }}
        .legend h3 {{
            margin-top: 0;
        }}
        .legend ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="diagram-container">
        <h1>Application Data Flow Diagram</h1>
        <div class="mermaid">
{graph_content}
        </div>

        <div class="legend">
            <h3>Legend</h3>
            <ul>
                <li><strong>⚪ Circles</strong> = Services/APIs</li>
                <li><strong>▭ Rectangles</strong> = Data Stores (Database, Cache, Queue)</li>
                <li><strong>▢ Rounded Rectangles</strong> = External Systems</li>
                <li><strong>─── Solid lines</strong> = Observed flows (actual traffic data)</li>
                <li><strong>╌╌╌ Dashed lines</strong> = Predicted flows (Markov chain inference)</li>
                <li><strong>🎨 Colors</strong> indicate security zones</li>
            </ul>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                curve: 'basis',
                padding: 20
            }}
        }});
    </script>
</body>
</html>
"""

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"✓ HTML diagram saved: {html_path}")

    def _infer_zone_from_ip(self, ip: str) -> str:
        """Infer security zone from IP address"""
        if not ip or not isinstance(ip, str):
            return 'EXTERNAL'

        if ip.startswith('10.100.160.'):
            return 'MANAGEMENT_TIER'
        elif ip.startswith('10.164.105.'):
            return 'WEB_TIER'
        elif ip.startswith('10.100.246.') or ip.startswith('10.165.116.'):
            return 'APP_TIER'
        elif ip.startswith('10.164.116.'):
            return 'DATA_TIER'
        elif ip.startswith('10.164.144.'):
            return 'CACHE_TIER'
        elif ip.startswith('10.164.145.'):
            return 'MESSAGING_TIER'
        elif ip.startswith('10.'):
            return 'APP_TIER'  # Internal default
        else:
            return 'EXTERNAL'

    def _sanitize_id(self, name: str) -> str:
        """Sanitize name for Mermaid node ID"""
        # Replace special characters
        sanitized = name.replace('.', '_').replace('-', '_').replace(':', '_')
        # Ensure starts with letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'node_' + sanitized
        return sanitized or 'unknown'


# Convenience function
def generate_application_diagram(
    app_name: str,
    flow_records: List,
    topology_data: Dict = None,
    predictions: Dict = None,
    output_path: str = None,
    hostname_resolver = None
) -> str:
    """
    Generate application-level data flow diagram

    Args:
        app_name: Application name
        flow_records: List of FlowRecord objects
        topology_data: Topology metadata
        predictions: Markov chain predictions
        output_path: Output file path
        hostname_resolver: Hostname resolver

    Returns:
        Mermaid diagram content
    """
    generator = ApplicationDiagramGenerator(hostname_resolver)
    return generator.generate_application_diagram(
        app_name, flow_records, topology_data, predictions, output_path
    )


if __name__ == '__main__':
    # Example usage
    print("Application Diagram Generator - Template-based")
    print("Generates diagrams following Data Flow Diagram template format")
