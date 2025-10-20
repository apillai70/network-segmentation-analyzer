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

    # Color scheme following template - Rainbow spectrum for diverse components
    ZONE_COLORS = {
        'WEB_TIER': '#ffcccc',           # Red - High Risk (frontend)
        'APP_TIER': '#cce5ff',           # Blue - Application Tier (backend services)
        'DATA_TIER': '#ff9966',          # Orange - Data Tier (databases)
        'CACHE_TIER': '#ffcc99',         # Light Orange - Cache services
        'MESSAGING_TIER': '#cc99ff',     # Purple - Message queues
        'MANAGEMENT_TIER': '#ffff99',    # Yellow - Management/infrastructure
        'EXTERNAL': '#e6ccff',           # Light Purple - External systems
        'PREDICTED': '#aed6f1',          # Light Blue - Predictions
        'API_GATEWAY': '#b3e6b3',        # Green - API Gateway
        'LOAD_BALANCER': '#ffb3d9',      # Pink - Load Balancers
        'STORAGE_TIER': '#d9b3ff',       # Lavender - Storage services
        'MONITORING': '#ffe6cc',         # Peach - Monitoring/Logging
        'SECURITY': '#ff9999',           # Coral - Security services
        'NETWORK': '#99ffcc',            # Mint - Network services
        'COMPUTE': '#cce6ff',            # Sky Blue - Compute/VMs
        'CONTAINER': '#e6ccff',          # Lilac - Containers
        'SERVERLESS': '#ccffff',         # Cyan - Serverless/Functions
        'ANALYTICS': '#ffffcc',          # Pale Yellow - Analytics
        'ML_SERVICE': '#d9f2d9',         # Pale Green - ML Services
        'UNKNOWN': '#e0e0e0',            # Gray - Unknown/Unclassified
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
            # [SUCCESS] FIX: Skip if src_ip is missing, invalid, or string 'nan'
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
            # [SUCCESS] FIX: Skip if dst_ip is missing, invalid, or string 'nan'
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

        # [SUCCESS] NEW: Add dependencies from topology data with source-based styling
        if topology_data:
            topology_deps = topology_data.get('predicted_dependencies', [])
            for dep in topology_deps:
                dep_name = dep.get('name', 'Unknown*')
                dep_type = dep.get('type', 'service')
                dep_source = dep.get('source', 'unknown')  # network_observation, type_inference, or unknown

                # Skip if already added from flow analysis
                if dep_name in components['infrastructure'] or dep_name in components['downstream_apps']:
                    continue

                # Determine if this is ML-inferred or observed
                is_ml_inferred = (dep_source == 'type_inference')
                is_unknown = (dep_source not in ['network_observation', 'type_inference'])

                # Add to infrastructure
                components['infrastructure'][dep_name] = {
                    'type': dep_type,
                    'zone': 'PREDICTED' if (is_ml_inferred or is_unknown) else 'EXTERNAL',
                    'is_predicted': is_ml_inferred or is_unknown,
                    'source': dep_source  # Track source for flow styling
                }

                # Add flow with appropriate styling
                flow_label = dep.get('purpose', 'data flow')
                flows.append({
                    'source': app_name,
                    'target': dep_name,
                    'label': flow_label,
                    'is_predicted': is_ml_inferred or is_unknown,
                    'source': dep_source,  # Pass source for color coding
                    'flow_type': 'topology_dep'
                })

        # Add predicted dependencies from Markov chain (if available)
        if predictions:
            predicted_deps = predictions.get('predicted_dependencies', [])
            for pred in predicted_deps:
                pred_name = pred.get('name', 'Unknown*')
                pred_type = pred.get('type', 'service')

                # Add to infrastructure (since predictions are typically for backends/databases)
                if pred_name not in components['infrastructure']:
                    components['infrastructure'][pred_name] = {
                        'type': pred_type,
                        'zone': 'PREDICTED',
                        'is_predicted': True,
                        'source': 'markov_prediction'
                    }

                # Add predicted flow (dashed line)
                flows.append({
                    'source': app_name,
                    'target': pred_name,
                    'label': f"predicted: {pred.get('description', 'data flow')}",
                    'is_predicted': True,
                    'source': 'markov_prediction'
                })

        # Generate Mermaid diagram
        mermaid = self._build_mermaid_diagram(app_name, components, flows)

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(mermaid)

            logger.info(f"[OK] Application diagram saved: {output_path}")

            # Also generate HTML version
            self._generate_html_diagram(mermaid, str(output_file.with_suffix('.html')))

            # PNG generation now done by run_batch_processing.py using Python API (no Chrome!)
            # self._generate_png_diagram(str(output_file), str(output_file.with_suffix('.png')))

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

            # Try mmdc command
            success = False
            for mmdc_cmd in ['mmdc']:
                try:
                    result = subprocess.run(
                        [mmdc_cmd, '-i', tmp_path, '-o', png_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        logger.info(f"[OK] PNG diagram generated: {Path(png_path).name}")
                        success = True
                        break
                    elif 'UnknownDiagramError' in result.stderr:
                        logger.warning(f"Mermaid syntax error in {Path(mmd_path).name}")
                        break
                except FileNotFoundError:
                    continue

            if not success:
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
            "graph TB",  # Top-to-bottom for application flow (rotated 90° clockwise from LR)
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
                label = self._sanitize_label(app_name_dest)
                color = self.ZONE_COLORS.get(app_data['zone'], '#cccccc')

                lines.append(f"        {node_id}(({label}))")
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
                label = self._sanitize_label(comp_name)

                zone = comp_data['zone']
                color = self.ZONE_COLORS.get(zone, '#cccccc')
                comp_source = comp_data.get('source', 'unknown')

                lines.append(f"        {node_id}{shape_template.format(label)}")

                # [SUCCESS] Color-code stroke based on data source
                if comp_source == 'network_observation':
                    # Observed data: Black solid stroke (ExtraHop flows)
                    lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")
                elif comp_source == 'type_inference':
                    # ML inferred: Blue dashed stroke (ML predictions)
                    lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
                elif comp_source == 'markov_prediction':
                    # Markov prediction: Blue dashed stroke (usage pattern predictions)
                    lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
                else:
                    # Unknown: Gray dashed stroke
                    lines.append(f"        style {node_id} fill:{color},stroke:#95a5a6,stroke-width:3px,stroke-dasharray:5")

            lines.append("    end")
            lines.append("")

        # Render other infrastructure (services, external systems, etc.)
        other_types = [t for t in by_type.keys() if t not in ['database', 'cache', 'queue']]
        if other_types:
            lines.append(f"    subgraph other_deps_group[\"Other Dependencies\"]")
            for comp_type in other_types:
                for comp_name, comp_data in by_type[comp_type]:
                    shape_template, _ = self._get_node_shape(comp_data['type'], comp_data['is_predicted'])
                    node_id = self._sanitize_id(comp_name)
                    label = self._sanitize_label(comp_name)

                    zone = comp_data['zone']
                    color = self.ZONE_COLORS.get(zone, '#cccccc')
                    comp_source = comp_data.get('source', 'unknown')

                    lines.append(f"        {node_id}{shape_template.format(label)}")

                    # [SUCCESS] Color-code stroke based on data source
                    if comp_source == 'network_observation':
                        # Observed data: Black solid stroke (ExtraHop flows)
                        lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")
                    elif comp_source == 'type_inference':
                        # ML inferred: Blue dashed stroke (ML predictions)
                        lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
                    elif comp_source == 'markov_prediction':
                        # Markov prediction: Blue dashed stroke (usage pattern predictions)
                        lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
                    else:
                        # Unknown: Gray dashed stroke
                        lines.append(f"        style {node_id} fill:{color},stroke:#95a5a6,stroke-width:3px,stroke-dasharray:5")

            lines.append("    end")
            lines.append("")

        # Define flows with source-based color coding
        lines.append("")
        app_node = "app_container"

        flow_index = 0  # Track flow index for styling
        for flow in flows:
            target_id = self._sanitize_id(flow['target'])
            label = flow['label']
            flow_type = flow.get('flow_type', 'app_to_infra')
            flow_source = flow.get('source', 'unknown')

            # Color code based on data source
            if flow_source == 'network_observation':
                # [SUCCESS] OBSERVED DATA: Solid lines, standard style (black)
                if flow_type == 'app_to_app':
                    lines.append(f"    {app_node} =={label}==> {target_id}")
                    lines.append(f"    linkStyle {flow_index} stroke:#333,stroke-width:3px")
                else:
                    lines.append(f"    {app_node} --{label}--> {target_id}")
                    lines.append(f"    linkStyle {flow_index} stroke:#333,stroke-width:2px")

            elif flow_source == 'type_inference':
                # [SUCCESS] ML INFERRED: Blue dashed lines (ML predictions)
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
                lines.append(f"    linkStyle {flow_index} stroke:#3498db,stroke-width:2px,stroke-dasharray:5")

            elif flow_source == 'markov_prediction':
                # [SUCCESS] MARKOV PREDICTION: Blue dashed lines
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
                lines.append(f"    linkStyle {flow_index} stroke:#3498db,stroke-width:2px,stroke-dasharray:5")

            else:
                # [SUCCESS] UNKNOWN: Gray dashed lines
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
                lines.append(f"    linkStyle {flow_index} stroke:#95a5a6,stroke-width:2px,stroke-dasharray:5")

            flow_index += 1

        lines.append("```")
        lines.append("")

        # Add legend with source-based color coding
        lines.extend([
            "",
            "**Legend:**",
            "",
            "**Shapes:**",
            "- **Application Box** = Internal architecture (web/app/db tiers)",
            "- **Downstream Apps** = Applications this app calls",
            "- **Infrastructure** = Databases, caches, queues",
            "- [WHITE] Circles = Services/Applications",
            "- [RECT] Rectangles = Data Stores",
            "",
            "**Data Source Colors:**",
            "- [BLACK] Black solid = Observed from network flows (ExtraHop)",
            "- [BLUE] Blue dashed = ML type inference (predicted dependency type)",
            "- [BLUE] Blue dashed = Markov chain prediction (usage pattern predictions)",
            "- [WHITE] Gray dashed = Unknown/unclassified",
            "",
            "**Lines:**",
            "- === Thick solid lines = App-to-app calls (observed)",
            "- --- Solid lines = Infrastructure dependencies (observed)",
            "- --- Dashed lines = Predicted/inferred connections",
            "",
            "**Colors:** Background colors indicate security zones (Web, App, Data tiers)",
            "",
            "**\\* Unknown Connections - Detailed Explanation:**",
            "",
            "Unknown connections could not be definitively classified based on available ExtraHop network flow data.",
            "This may occur when:",
            "- (1) Destination endpoints do not have clear service type indicators in their network signatures",
            "- (2) Flow data lacks sufficient context to determine the application protocol",
            "- (3) Connections involve custom or proprietary services without standard port/protocol patterns",
            "",
            "**Recommendation:** Manual investigation and correlation with application configuration is recommended to properly classify these dependencies.",
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
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            color: #333;
            overflow: hidden;
            height: 100vh;
        }}
        h1 {{
            color: #2c3e50;
            margin: 0;
            padding: 15px 20px;
            font-size: 22px;
            background: white;
            border-bottom: 3px solid #3498db;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }}
        .instructions {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 12px 20px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }}
        .instructions strong {{
            font-size: 15px;
        }}
        .diagram-container {{
            background: #fafafa;
            padding: 0;
            margin: 0;
            height: calc(100vh - 100px);
            position: relative;
            overflow: hidden;
        }}
        .diagram-container .mermaid {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .diagram-container svg {{
            max-width: none !important;
            width: auto !important;
            height: auto !important;
        }}
        .controls {{
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 1001;
            background: rgba(255, 255, 255, 0.98);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            border: 2px solid #3498db;
            cursor: move;
        }}
        .controls h4 {{
            margin: 0 0 12px 0;
            font-size: 14px;
            color: #2c3e50;
            text-align: center;
            font-weight: 600;
            cursor: move;
            user-select: none;
        }}
        .controls button {{
            display: block;
            width: 140px;
            margin: 8px 0;
            padding: 10px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }}
        .controls button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.25);
        }}
        .controls button:active {{
            transform: translateY(0);
        }}
        /* Override hover for pan arrows - keep them centered */
        .pan-arrow.pan-up:hover {{
            transform: translateX(-50%) !important;
        }}
        .pan-arrow.pan-down:hover {{
            transform: translateX(-50%) !important;
        }}
        .pan-arrow.pan-left:hover {{
            transform: translateY(-50%) !important;
        }}
        .pan-arrow.pan-right:hover {{
            transform: translateY(-50%) !important;
        }}
        .pan-control {{
            width: 110px;
            height: 110px;
            margin: 15px auto;
            position: relative;
            background: radial-gradient(circle, #ecf0f1 0%, #bdc3c7 100%);
            border-radius: 50%;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.15);
        }}
        .pan-arrow {{
            position: absolute;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}
        .pan-arrow:hover {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }}
        .pan-up {{
            top: 10px;
            left: 50%;
            width: 20px;
            height: 10px;
            transform: translateX(-50%) !important;
        }}
        .pan-down {{
            bottom: 10px;
            left: 50%;
            width: 20px;
            height: 10px;
            transform: translateX(-50%) !important;
        }}
        .pan-left {{
            left: 10px;
            top: 50%;
            width: 10px;
            height: 20px;
            transform: translateY(-50%) !important;
        }}
        .pan-right {{
            right: 10px;
            top: 50%;
            width: 10px;
            height: 20px;
            transform: translateY(-50%) !important;
        }}
        .legend {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            max-width: 650px;
            width: auto;
            max-height: 320px;
            padding: 18px;
            background: rgba(255, 255, 255, 0.96);
            border: 2px solid #3498db;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            font-size: 13px;
            z-index: 1001;
            overflow-y: auto;
            position: relative;
            transition: opacity 0.3s, transform 0.3s;
        }}
        .legend.hidden {{
            opacity: 0;
            transform: translateY(20px);
            pointer-events: none;
        }}
        .legend-close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .legend-close-btn:hover {{
            background: #c0392b;
        }}
        .legend-toggle-btn {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            display: none;
        }}
        .legend-toggle-btn.show {{
            display: block;
        }}
        .legend h3 {{
            margin-top: 0;
            font-size: 14px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        .legend ul {{
            margin: 8px 0;
            padding-left: 18px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <h1>Application Data Flow Diagram</h1>

    <div class="instructions">
        <strong>Navigation:</strong>
        <span>Use 4-way arrows to pan • Mouse wheel to zoom • Use controls on right</span>
    </div>

    <div class="controls">
        <h4>Controls</h4>

        <div class="pan-control">
            <button class="pan-arrow pan-up" onclick="panDirection('up')" title="Pan Up">↑</button>
            <button class="pan-arrow pan-down" onclick="panDirection('down')" title="Pan Down">↓</button>
            <button class="pan-arrow pan-left" onclick="panDirection('left')" title="Pan Left">←</button>
            <button class="pan-arrow pan-right" onclick="panDirection('right')" title="Pan Right">→</button>
        </div>

        <button onclick="zoomIn()">Zoom In</button>
        <button onclick="zoomOut()">Zoom Out</button>
        <button onclick="resetView()">Reset View</button>
    </div>

    <div class="legend">
        <button class="legend-close-btn" onclick="toggleLegend()" title="Close Legend">×</button>
        <h3>Legend</h3>
        <ul>
            <li><strong>[WHITE] Circles</strong> = Services/APIs</li>
            <li><strong>[RECT] Rectangles</strong> = Data Stores</li>
            <li><strong>[BLACK] Black solid</strong> = Observed flows (ExtraHop)</li>
            <li><strong>[BLUE] Blue dashed</strong> = ML inference/predictions</li>
            <li><strong>[VISUAL] Colors</strong> = Security zones</li>
        </ul>
        <div style="margin-top: 15px; padding: 18px; background: rgba(158, 158, 158, 0.15); border-radius: 6px; border-left: 4px solid #9e9e9e;">
            <strong style="color: #2c3e50; font-size: 14px;">* Unknown Connections:</strong>
            <p style="margin: 8px 0 0 0; font-size: 13px; line-height: 1.7;">
                Unknown connections could not be definitively classified based on available ExtraHop network flow data.
                This may occur when: <br><br>
                <strong>(1)</strong> Destination endpoints do not have clear service type indicators,<br>
                <strong>(2)</strong> Flow data lacks sufficient context to determine the application protocol, or<br>
                <strong>(3)</strong> Connections involve custom or proprietary services without standard port/protocol patterns.
                <br><br>
                <strong>Recommendation:</strong> Manual investigation and correlation with application configuration is recommended.
            </p>
        </div>
    </div>

    <button class="legend-toggle-btn" id="legendToggle" onclick="toggleLegend()">Show Legend</button>

    <div class="diagram-container">
        <div class="mermaid">
{graph_content}
        </div>
    </div>

    <script>
        let translateX = 0;
        let translateY = 0;
        let scale = 1;
        const PAN_STEP = 100; // pixels to pan per arrow click

        // Make controls panel draggable
        let controlsIsDragging = false;
        let controlsStartX, controlsStartY, controlsInitialX, controlsInitialY;

        mermaid.initialize({{
            startOnLoad: false,
            theme: 'default',
            maxTextSize: 90000,
            flowchart: {{
                curve: 'basis',
                padding: 20,
                useMaxWidth: false,
                htmlLabels: true
            }},
            securityLevel: 'loose'
        }});

        // Initialize after Mermaid renders
        window.addEventListener('load', function() {{
            const mermaidDiv = document.querySelector('.mermaid');
            if (mermaidDiv) {{
                // Force render
                mermaid.run({{ nodes: [mermaidDiv] }}).then(() => {{
                    console.log('Mermaid rendered successfully');
                    initControls();
                }}).catch(err => {{
                    console.error('Mermaid rendering failed:', err);
                    // Show error message to user
                    mermaidDiv.innerHTML = '<div style="padding: 40px; text-align: center; color: #e74c3c;"><h2>Diagram Rendering Error</h2><p>' + err.message + '</p><p>Check browser console for details.</p></div>';
                }});
            }} else {{
                console.error('Mermaid div not found');
            }}
        }});

        function initControls() {{
            const container = document.querySelector('.diagram-container');
            const svg = document.querySelector('.diagram-container svg');

            if (!svg) return;

            // Mouse wheel to zoom
            container.addEventListener('wheel', zoom);

            // Make controls panel draggable
            const controls = document.querySelector('.controls');
            const controlsHeader = controls.querySelector('h4');

            controlsHeader.addEventListener('mousedown', startDragControls);
            document.addEventListener('mousemove', dragControls);
            document.addEventListener('mouseup', stopDragControls);

            // Initial fit
            setTimeout(() => {{
                fitView();
            }}, 500);
        }}

        function startDragControls(e) {{
            controlsIsDragging = true;
            const controls = document.querySelector('.controls');
            controlsStartX = e.clientX;
            controlsStartY = e.clientY;
            const rect = controls.getBoundingClientRect();
            controlsInitialX = rect.left;
            controlsInitialY = rect.top;
            e.preventDefault();
        }}

        function dragControls(e) {{
            if (!controlsIsDragging) return;

            const controls = document.querySelector('.controls');
            const dx = e.clientX - controlsStartX;
            const dy = e.clientY - controlsStartY;

            controls.style.left = (controlsInitialX + dx) + 'px';
            controls.style.top = (controlsInitialY + dy) + 'px';
            controls.style.right = 'auto';
        }}

        function stopDragControls() {{
            controlsIsDragging = false;
        }}

        function zoom(e) {{
            e.preventDefault();

            const svg = document.querySelector('.diagram-container svg');
            if (!svg) return;

            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale = Math.min(Math.max(0.1, scale * delta), 5);

            updateTransform();
        }}

        function panDirection(direction) {{
            requestAnimationFrame(() => {{
                switch(direction) {{
                    case 'up':
                        translateY += PAN_STEP;
                        break;
                    case 'down':
                        translateY -= PAN_STEP;
                        break;
                    case 'left':
                        translateX += PAN_STEP;
                        break;
                    case 'right':
                        translateX -= PAN_STEP;
                        break;
                }}
                updateTransform();
            }});
        }}

        function zoomIn() {{
            scale = Math.min(scale * 1.2, 5);
            updateTransform();
        }}

        function zoomOut() {{
            scale = Math.max(scale * 0.8, 0.1);
            updateTransform();
        }}

        function resetView() {{
            scale = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
            // Center the diagram after reset
            setTimeout(() => {{
                fitView();
            }}, 100);
        }}

        function fitView() {{
            const container = document.querySelector('.diagram-container');
            const svg = document.querySelector('.diagram-container svg');
            if (!svg || !container) {{
                console.log('SVG or container not found');
                return;
            }}

            // Reset transform first
            svg.style.transform = '';

            // Get natural dimensions
            setTimeout(() => {{
                const svgRect = svg.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();

                console.log('SVG:', svgRect.width, svgRect.height);
                console.log('Container:', containerRect.width, containerRect.height);

                const scaleX = containerRect.width / svgRect.width;
                const scaleY = containerRect.height / svgRect.height;
                scale = Math.min(scaleX, scaleY, 1) * 0.9;

                // Center the diagram
                translateX = (containerRect.width - svgRect.width * scale) / 2;
                translateY = (containerRect.height - svgRect.height * scale) / 2;

                console.log('Scale:', scale, 'Translate:', translateX, translateY);

                updateTransform();
            }}, 100);
        }}

        function updateTransform() {{
            const svg = document.querySelector('.diagram-container svg');
            if (svg) {{
                svg.style.transformOrigin = '0 0';
                svg.style.transition = 'transform 0.2s ease-out';
                svg.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
            }}
        }}

        function toggleLegend() {{
            const legend = document.querySelector('.legend');
            const toggleBtn = document.getElementById('legendToggle');

            if (legend.classList.contains('hidden')) {{
                legend.classList.remove('hidden');
                toggleBtn.classList.remove('show');
            }} else {{
                legend.classList.add('hidden');
                toggleBtn.classList.add('show');
            }}
            
            // Recenter diagram after legend toggle
            setTimeout(() => {{
                fitView();
            }}, 350);  // Wait for legend animation to complete
        }}
    </script>
</body>
</html>
"""

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"[OK] HTML diagram saved: {html_path}")

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
        sanitized = name.replace('.', '_').replace('-', '_').replace(':', '_').replace('(', '_').replace(')', '_')
        # Ensure starts with letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'node_' + sanitized
        return sanitized or 'unknown'

    def _sanitize_label(self, name: str) -> str:
        """Sanitize label text for Mermaid display (more readable than IDs)"""
        # Replace parentheses with hyphens for readability
        # Example: "10.164.41.47(hostname.com)" -> "10.164.41.47 - hostname.com"
        if '(' in name and ')' in name:
            name = name.replace('(', ' - ').replace(')', '')
        return name


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