"""
Mermaid Network Diagram Generator
==================================
Generates Mermaid diagrams for network topology visualization.
Creates per-application diagrams and overall network architecture diagrams.

Author: Network Security Team
Version: 2.1 - With Hostname Resolution
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class MermaidDiagramGenerator:
    """Generates Mermaid diagrams for network visualization with hostname resolution"""

    # Zone colors (Mermaid-compatible)
    ZONE_COLORS = {
        'EXTERNAL': '#f44336',
        'DMZ': '#ff9800',
        'WEB_TIER': '#4caf50',
        'APP_TIER': '#2196f3',
        'DATA_TIER': '#ff5722',
        'MESSAGING_TIER': '#9c27b0',
        'CACHE_TIER': '#00bcd4',
        'MANAGEMENT_TIER': '#ffc107',
        'INFRASTRUCTURE': '#795548',
        'INTERNAL': '#4caf50'
    }

    def __init__(self, flow_records: List, zones: Dict, hostname_resolver=None, filter_nonexistent: bool = False):
        """
        Initialize diagram generator

        Args:
            flow_records: List of FlowRecord objects
            zones: Dictionary of NetworkZone objects
            hostname_resolver: HostnameResolver instance (optional)
                              If None, will create one in demo mode
            filter_nonexistent: If True, filter flows with both IPs non-existent (default: True)
        """
        # Initialize hostname resolver first
        if hostname_resolver is None:
            from utils.hostname_resolver import HostnameResolver
            self.hostname_resolver = HostnameResolver(
                demo_mode=True,
                filter_nonexistent=filter_nonexistent,
                mark_nonexistent=True
            )
        else:
            self.hostname_resolver = hostname_resolver

        # Apply filtering to flow records
        #if filter_nonexistent and self.hostname_resolver:
            #from utils.flow_filter import apply_filtering_to_records
            #flow_records = apply_filtering_to_records(
               # flow_records,
              #  self.hostname_resolver,
               # filter_enabled=True,
              #  log_stats=True
            #)

        self.records = flow_records
        self.zones = zones

        # Pre-load hostnames from flow records
        self._load_hostnames_from_records()

        logger.info(f"MermaidDiagramGenerator initialized with {len(flow_records)} records")
        logger.info(f"  Hostname resolution: {'Enabled' if self.hostname_resolver else 'Disabled'}")

    def _load_hostnames_from_records(self):
        """Load any existing hostnames from flow records into resolver"""
        for record in self.records:
            if hasattr(record, 'src_hostname') and record.src_hostname:
                self.hostname_resolver.add_known_hostname(record.src_ip, record.src_hostname)
            if hasattr(record, 'dst_hostname') and record.dst_hostname:
                self.hostname_resolver.add_known_hostname(record.dst_ip, record.dst_hostname)

    def generate_overall_network_diagram(self, output_path: str) -> str:
        """Generate overall network architecture diagram"""
        logger.info("Generating overall network diagram...")

        lines = []
        lines.append("graph TB")
        lines.append("    %% Overall Network Architecture")
        lines.append("")

        # Define styles
        lines.append("    %% Zone Styles")
        for zone_name, color in self.ZONE_COLORS.items():
            safe_name = zone_name.lower().replace('_', '').replace('-', '')
            lines.append(f"    classDef {safe_name} fill:{color},stroke:#333,stroke-width:2px,color:#fff")
        lines.append("")

        # Add macro zones
        lines.append("    %% Macro Zones")
        macro_zones = {name: zone for name, zone in self.zones.items()
                      if zone.zone_type == 'macro'}

        for zone_name, zone in macro_zones.items():
            safe_name = self._safe_name(zone_name)
            member_count = len(zone.members)
            security_level = zone.security_level
            class_name = zone_name.lower().replace('_', '').replace('-', '')

            lines.append(
                f"    {safe_name}[\"{zone_name}<br/>{zone.description}<br/>"
                f"{member_count} hosts | Security Level: {security_level}\"]:::{class_name}"
            )

        lines.append("")

        # Add micro zones
        lines.append("    %% Micro Zones (Application Tiers)")
        micro_zones = {name: zone for name, zone in self.zones.items()
                      if zone.zone_type == 'micro'}

        for zone_name, zone in micro_zones.items():
            safe_name = self._safe_name(zone_name)
            member_count = len(zone.members)
            class_name = zone_name.lower().replace('_', '').replace('-', '')

            lines.append(
                f"    {safe_name}[\"{zone_name}<br/>{member_count} hosts\"]:::{class_name}"
            )

        lines.append("")

        # Add zone relationships
        lines.append("    %% Zone Relationships")
        lines.append("    EXTERNAL -->|Filtered Traffic| DMZ")
        lines.append("    DMZ -->|Firewall| INTERNAL")

        # Add micro zone relationships based on traffic flows
        flow_summary = self._summarize_zone_flows()

        for (src_zone, dst_zone), flow_count in flow_summary.items():
            if src_zone and dst_zone and src_zone != dst_zone:
                src_safe = self._safe_name(src_zone)
                dst_safe = self._safe_name(dst_zone)

                # Determine line style based on flow count
                if flow_count > 100:
                    lines.append(f"    {src_safe} ==>|{flow_count} flows| {dst_safe}")
                elif flow_count > 10:
                    lines.append(f"    {src_safe} -->|{flow_count} flows| {dst_safe}")
                else:
                    lines.append(f"    {src_safe} -.->|{flow_count} flows| {dst_safe}")

        mermaid_content = '\n'.join(lines)

        # Save as .mmd file
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)

        logger.info(f"✓ Overall network diagram saved: {output_path}")

        # Also generate HTML version
        html_path = output_path.replace('.mmd', '.html')
        self._generate_html_diagram(mermaid_content, html_path, "Overall Network Architecture")

        return mermaid_content

    def generate_app_diagram(self, app_name: str, output_path: str) -> str:
        """Generate per-application diagram with upstream/downstream view"""
        logger.info(f"Generating upstream/downstream diagram for application: {app_name}")

        app_records = self.records
        if not app_records:
            logger.warning(f"No records found for application: {app_name}")
            return ""

        # KEY INSIGHT: All SOURCE IPs = Application Components, DESTINATION IPs = External Dependencies
        application_components = set()  # All source IPs
        external_dependencies = set()   # All destination IPs

        # Collect flow summary
        flow_summary = defaultdict(lambda: {'count': 0, 'bytes': 0, 'protocols': set(), 'ports': set()})

        for record in app_records:
            # Skip records with None IPs
            if record.src_ip is None or record.dst_ip is None:
                continue

            application_components.add(record.src_ip)
            external_dependencies.add(record.dst_ip)

            key = (record.src_ip, record.dst_ip)
            flow_summary[key]['count'] += 1
            flow_summary[key]['bytes'] += getattr(record, 'bytes', 0)

            if hasattr(record, 'port') and record.port:
                proto = getattr(record, 'protocol', 'TCP')
                flow_summary[key]['protocols'].add(f"{proto}:{record.port}")
                flow_summary[key]['ports'].add(record.port)
            else:
                flow_summary[key]['protocols'].add(getattr(record, 'protocol', 'TCP'))

        logger.info(f"  Application has {len(application_components)} internal components")
        logger.info(f"  Application depends on {len(external_dependencies)} external services")

        # Classify external dependencies by service type
        dependency_types = {}
        for dep_ip in external_dependencies:
            # Find ports used for this dependency
            ports_used = set()
            for (src, dst), stats in flow_summary.items():
                if dst == dep_ip:
                    ports_used.update(stats['ports'])

            # Classify by port
            if any(p in [3306, 5432, 27017, 1433, 1521] for p in ports_used):
                dependency_types[dep_ip] = 'database'
            elif 6379 in ports_used:
                dependency_types[dep_ip] = 'cache'
            elif any(p in [9092, 9093, 5672, 5671] for p in ports_used):
                dependency_types[dep_ip] = 'queue'
            else:
                dependency_types[dep_ip] = 'downstream_app'

        # Start building Mermaid diagram - LEFT TO RIGHT layout
        lines = []
        lines.append("graph LR")
        lines.append(f"    %% Application: {app_name} - Upstream/Downstream View")
        lines.append("")

        # Define styles matching the sample diagram
        lines.append("    %% Component Styles")
        lines.append("    classDef appComponent fill:#b3e5fc,stroke:#01579b,stroke-width:2px,color:#000")
        lines.append("    classDef database fill:#a5d6a7,stroke:#2e7d32,stroke-width:2px,color:#000")
        lines.append("    classDef cache fill:#b3e5fc,stroke:#01579b,stroke-width:2px,color:#000")
        lines.append("    classDef queue fill:#90caf9,stroke:#0277bd,stroke-width:2px,color:#000")
        lines.append("    classDef app fill:#ffe082,stroke:#f57c00,stroke-width:2px,color:#000")
        lines.append("")

        # Group application components by tier (LEFT SIDE)
        app_components_by_tier = defaultdict(list)

        for comp_ip in application_components:
            tier = None
            for zone_name, zone_obj in self.zones.items():
                if hasattr(zone_obj, 'members') and comp_ip in zone_obj.members:
                    tier = zone_name
                    break

            if not tier:
                tier = 'UNKNOWN'

            hostname, display_label = self.hostname_resolver.resolve_with_display(comp_ip, tier)

            app_components_by_tier[tier].append({
                'ip': comp_ip,
                'safe_name': self._safe_name(comp_ip),
                'display_label': display_label
            })

        # Define tier order
        tier_order = ['WEB_TIER', 'APP_TIER', 'DATA_TIER', 'CACHE_TIER',
                     'MESSAGING_TIER', 'MANAGEMENT_TIER', 'INFRASTRUCTURE_TIER', 'UNKNOWN']

        # Add application components subgraph (LEFT SIDE)
        lines.append(f"    subgraph app[\"{app_name} Application\"]")
        lines.append("        direction TB")

        for tier in tier_order:
            if tier not in app_components_by_tier:
                continue

            tier_label = tier.replace('_TIER', '').replace('_', ' ').title()
            tier_id = self._safe_name(f"{tier}_group")

            lines.append(f"        subgraph {tier_id}[\"{tier_label}<br/>{len(app_components_by_tier[tier])} server(s)\"]")

            for comp_info in sorted(app_components_by_tier[tier], key=lambda x: x['ip'])[:15]:  # Limit to 15 per tier
                safe_name = comp_info['safe_name']
                display_label = comp_info['display_label']
                lines.append(f"            {safe_name}[\"{display_label}\"]:::appComponent")

            lines.append("        end")

        lines.append("    end")
        lines.append("")

        # Group external dependencies by type (RIGHT SIDE)
        deps_by_type = defaultdict(list)

        for dep_ip in external_dependencies:
            dep_type = dependency_types.get(dep_ip, 'downstream_app')
            hostname, display_label = self.hostname_resolver.resolve_with_display(dep_ip, 'EXTERNAL')

            deps_by_type[dep_type].append({
                'ip': dep_ip,
                'safe_name': self._safe_name(dep_ip),
                'display_label': display_label
            })

        # Add external dependencies subgraphs (RIGHT SIDE)
        type_labels = {
            'database': 'Databases',
            'cache': 'Caches',
            'queue': 'Queues',
            'downstream_app': 'Downstream Applications'
        }

        for dep_type in ['queue', 'cache', 'database', 'downstream_app']:
            if dep_type not in deps_by_type:
                continue

            type_label = type_labels[dep_type]
            type_id = self._safe_name(dep_type)

            lines.append(f"    subgraph {type_id}[\"{type_label}\"]")
            lines.append("        direction TB")

            for dep_info in sorted(deps_by_type[dep_type], key=lambda x: x['ip'])[:20]:  # Limit to 20 per type
                safe_name = dep_info['safe_name']
                display_label = dep_info['display_label']
                # Use different shapes for different service types
                if dep_type == 'database':
                    # Cylinder shape for databases
                    lines.append(f"        {safe_name}[(\"{display_label}\")]:::database")
                elif dep_type == 'downstream_app':
                    # Circle shape for downstream applications
                    lines.append(f"        {safe_name}((\"{display_label}\")):::{dep_type.replace('downstream_', '')}")
                elif dep_type == 'queue':
                    # Hexagon for queues/messaging
                    lines.append(f"        {safe_name}{{{{\"{display_label}\"}}}}:::queue")
                else:
                    # Rectangle for caches
                    lines.append(f"        {safe_name}[\"{display_label}\"]:::{dep_type}")

            lines.append("    end")
            lines.append("")

        # Add traffic flows with meaningful labels
        lines.append("    %% Traffic Flows")

        # Determine edge labels based on dependency type
        edge_labels = {
            'database': 'data queries',
            'cache': 'cache operations',
            'queue': 'data flow',
            'downstream_app': 'app calls'
        }

        # Collect displayed node IPs (those that are actually rendered in the diagram)
        displayed_app_components = set()
        for tier_comps in app_components_by_tier.values():
            for comp in tier_comps[:15]:  # Match the limit used above
                displayed_app_components.add(comp['ip'])

        displayed_dependencies = set()
        for dep_type_list in deps_by_type.values():
            for dep in dep_type_list[:20]:  # Match the limit used above
                displayed_dependencies.add(dep['ip'])

        flows_added = set()
        for (src, dst), stats in sorted(flow_summary.items(), key=lambda x: x[1]['bytes'], reverse=True):
            if src is None or dst is None:
                continue

            # Only show flows where BOTH source and destination are displayed nodes
            if src not in displayed_app_components or dst not in displayed_dependencies:
                continue

            # Limit total flows displayed
            if len(flows_added) >= 100:
                break

            src_safe = self._safe_name(src)
            dst_safe = self._safe_name(dst)
            dep_type = dependency_types.get(dst, 'downstream_app')
            edge_label = edge_labels.get(dep_type, 'app calls')

            # Use simplified edge label with straight arrows
            lines.append(f"    {src_safe} -.->|{edge_label}| {dst_safe}")
            flows_added.add((src, dst))

        mermaid_content = '\n'.join(lines)

        # Save as .mmd file
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)

        logger.info(f"✓ Application diagram saved: {output_path}")

        # Also generate HTML version
        html_path = output_path.replace('.mmd', '.html')
        self._generate_html_diagram(mermaid_content, html_path, f"Application: {app_name}")

        return mermaid_content

    def generate_all_app_diagrams(self, output_dir: str) -> Dict[str, str]:
        """Generate diagrams for all applications"""
        logger.info("Generating diagrams for all applications...")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get unique apps
        apps = set(r.app_name for r in self.records)

        diagrams = {}
        for app_name in apps:
            output_file = output_path / f"{app_name}_diagram.mmd"
            content = self.generate_app_diagram(app_name, str(output_file))
            diagrams[app_name] = content

        logger.info(f"✓ Generated {len(diagrams)} application diagrams")
        return diagrams

    def generate_zone_flow_diagram(self, output_path: str) -> str:
        """Generate zone-to-zone traffic flow diagram"""
        logger.info("Generating zone flow diagram...")

        lines = []
        lines.append("graph TD")
        lines.append("    %% Zone Traffic Flow Analysis")
        lines.append("")

        # Define styles
        lines.append("    %% Styles")
        lines.append("    classDef high fill:#f44336,stroke:#c62828,stroke-width:3px,color:#fff")
        lines.append("    classDef medium fill:#ff9800,stroke:#f57c00,stroke-width:2px,color:#fff")
        lines.append("    classDef low fill:#4caf50,stroke:#388e3c,stroke-width:2px,color:#fff")
        lines.append("")

        # Get flow summary
        flow_summary = self._summarize_zone_flows()

        # Add zones as nodes
        zones_used = set()
        for (src, dst), _ in flow_summary.items():
            if src:
                zones_used.add(src)
            if dst:
                zones_used.add(dst)

        lines.append("    %% Zones")
        for zone in sorted(zones_used):
            safe_name = self._safe_name(zone)
            zone_obj = self.zones.get(zone)
            member_count = len(zone_obj.members) if zone_obj else 0
            lines.append(f"    {safe_name}[\"{zone}<br/>{member_count} hosts\"]")

        lines.append("")

        # Add flows
        lines.append("    %% Traffic Flows")
        for (src_zone, dst_zone), count in sorted(flow_summary.items(), key=lambda x: x[1], reverse=True):
            if src_zone and dst_zone and src_zone != dst_zone:
                src_safe = self._safe_name(src_zone)
                dst_safe = self._safe_name(dst_zone)

                # Classify flow volume
                if count > 100:
                    lines.append(f"    {src_safe} ==>|{count} flows<br/>HIGH| {dst_safe}")
                elif count > 10:
                    lines.append(f"    {src_safe} -->|{count} flows<br/>MEDIUM| {dst_safe}")
                else:
                    lines.append(f"    {src_safe} -.->|{count} flows<br/>LOW| {dst_safe}")

        mermaid_content = '\n'.join(lines)

        # Save as .mmd file
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)

        logger.info(f"✓ Zone flow diagram saved: {output_path}")

        # Also generate HTML version
        html_path = output_path.replace('.mmd', '.html')
        self._generate_html_diagram(mermaid_content, html_path, "Zone Traffic Flow Analysis")

        return mermaid_content

    def _summarize_zone_flows(self) -> Dict[Tuple[str, str], int]:
        """Summarize traffic flows between zones"""
        zone_flows = defaultdict(int)

        # Map IPs to zones
        ip_to_zone = {}
        for zone_name, zone in self.zones.items():
            for member in zone.members:
                ip_to_zone[member] = zone_name

        # Count flows between zones
        for record in self.records:
            src_zone = ip_to_zone.get(record.src_ip)
            dst_zone = ip_to_zone.get(record.dst_ip)

            # If not in a zone, classify as EXTERNAL or INTERNAL
            if not src_zone:
                src_zone = 'EXTERNAL' if not record.is_internal else 'INTERNAL'
            if not dst_zone:
                dst_zone = 'EXTERNAL' if not record.is_internal else 'INTERNAL'

            zone_flows[(src_zone, dst_zone)] += 1

        return dict(zone_flows)

    def _safe_name(self, name: str) -> str:
        """Convert name to Mermaid-safe identifier"""
        if name is None:
            return 'unknown_host'
        return str(name).replace('.', '_').replace('-', '_').replace(':', '_').replace(' ', '_')

    def _is_internal_ip_check(self, ip: str) -> bool:
        """Check if IP is internal"""
        try:
            import ipaddress
            ip_obj = ipaddress.IPv4Address(ip)
            return ip_obj.is_private
        except:
            return False

    def _generate_html_diagram(self, mermaid_content: str, output_path: str, title: str):
        """Generate standalone HTML file with Mermaid diagram"""
        html_template = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #ffffff;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        #diagram-wrapper {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px auto;
            max-width: 95%;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }}
        #diagram-container {{
            width: 100%;
            height: 1200px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: auto;
            position: relative;
            background: #ffffff;
        }}
        #diagram-container svg {{
            max-width: none !important;
            width: auto !important;
            height: auto !important;
            min-width: 100%;
        }}
        .mermaid {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }}
        .controls {{
            position: absolute;
            top: 30px;
            right: 30px;
            z-index: 1000;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            border: 1px solid #ddd;
        }}
        .controls button {{
            display: block;
            width: 100%;
            margin: 5px 0;
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }}
        .controls button:hover {{
            background: #2980b9;
        }}
        .controls button:active {{
            background: #21618c;
        }}
        .info {{
            max-width: 95%;
            margin: 20px auto;
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e0e0e0;
        }}
        .info h2 {{
            color: #2c3e50;
            font-size: 20px;
            margin-top: 0;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .legend-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .legend-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .legend-item span {{
            font-size: 13px;
            line-height: 1.6;
        }}
        .theme-toggle {{
            text-align: center;
            margin: 10px 0;
        }}
        .theme-toggle label {{
            margin-right: 10px;
            font-weight: 500;
        }}

        /* Dark theme styles */
        body.dark {{
            background: #2d2d2d;
            color: #e0e0e0;
        }}
        body.dark h1 {{
            color: #64b5f6;
        }}
        body.dark #diagram-wrapper {{
            background: #263238;
        }}
        body.dark #diagram-container {{
            background: #2d3436;
            border-color: #455a64;
        }}
        body.dark .info {{
            background: #263238;
        }}
        body.dark .info h2 {{
            color: #64b5f6;
        }}
        body.dark .legend-item {{
            background: #37474f;
            border-left-color: #64b5f6;
        }}
        body.dark .legend-title {{
            color: #90caf9;
        }}
        body.dark .controls {{
            background: #37474f;
            border-color: #455a64;
        }}
    </style>
</head>
<body>
    <h1>🔒 {title}</h1>

    <div class="info">
        <div class="theme-toggle">
            <label>Theme:</label>
            <button onclick="toggleTheme('light')" style="padding: 6px 12px; margin: 0 5px; cursor: pointer;">Light</button>
            <button onclick="toggleTheme('dark')" style="padding: 6px 12px; margin: 0 5px; cursor: pointer;">Dark</button>
        </div>
        <h2>Network Segmentation Diagram</h2>
        <p>This diagram visualizes the network topology and traffic flows for security analysis and segmentation planning.</p>
        <p><strong>Controls:</strong> Use mouse wheel to zoom, click and drag to pan. Use buttons on right for zoom controls.</p>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-title">Line Types</div>
                <span><strong>=====></strong> High volume traffic<br>
                <strong>-----></strong> Medium volume traffic<br>
                <strong>-.-.-></strong> Low volume traffic</span>
            </div>
            <div class="legend-item">
                <div class="legend-title">Node Colors</div>
                <span>
                <span style="color: #f44336;">■</span> External/High Risk<br>
                <span style="color: #ff9800;">■</span> DMZ/Medium Risk<br>
                <span style="color: #4caf50;">■</span> Internal/Low Risk<br>
                <span style="color: #2196f3;">■</span> Application Tier<br>
                <span style="color: #ff5722;">■</span> Data Tier
                </span>
            </div>
        </div>
    </div>

    <div id="diagram-wrapper">
        <div class="controls">
            <button onclick="zoomIn()">Zoom In (+)</button>
            <button onclick="zoomOut()">Zoom Out (-)</button>
            <button onclick="resetView()">Reset View</button>
            <button onclick="centerView()">Center</button>
            <button onclick="fitView()">Fit to Screen</button>
        </div>
        <div id="diagram-container">
            <div class="mermaid">
{mermaid_content}
            </div>
        </div>
    </div>

    <script>
        let panZoom;
        let currentZoom = 1;
        let currentPan = {{ x: 0, y: 0 }};

        mermaid.initialize({{
            startOnLoad: false,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'linear',
                padding: 15,
                nodeSpacing: 80,
                rankSpacing: 120,
                diagramPadding: 15
            }},
            themeVariables: {{
                primaryColor: '#fffde7',
                primaryTextColor: '#000',
                primaryBorderColor: '#f57c00',
                lineColor: '#000000',
                secondaryColor: '#fff9c4',
                tertiaryColor: '#fffde7',
                edgeLabelBackground: '#ffffff',
                clusterBkg: '#fffde7',
                clusterBorder: '#f57c00'
            }}
        }});

        // Initialize diagram on window load
        window.addEventListener('load', function() {{
            const mermaidDiv = document.querySelector('.mermaid');
            if (mermaidDiv) {{
                mermaid.run({{ nodes: [mermaidDiv] }}).then(() => {{
                    console.log('Mermaid rendered successfully');
                    initializePanZoom();
                }}).catch(err => {{
                    console.error('Mermaid rendering failed:', err);
                }});
            }}
        }});

        function initializePanZoom() {{
            setTimeout(() => {{
                const svg = document.querySelector('#diagram-container svg');
                console.log('SVG element:', svg);

                if (svg) {{
                    // Remove fixed dimensions
                    svg.removeAttribute('width');
                    svg.removeAttribute('height');
                    svg.style.width = '100%';
                    svg.style.height = 'auto';

                    // Initialize svg-pan-zoom
                    try {{
                        panZoom = svgPanZoom(svg, {{
                            zoomEnabled: true,
                            controlIconsEnabled: false,
                            fit: false,
                            center: false,
                            minZoom: 0.1,
                            maxZoom: 20,
                            zoomScaleSensitivity: 0.3,
                            onZoom: function(level) {{
                                currentZoom = level;
                                console.log('Zoomed to:', level);
                            }},
                            onPan: function(point) {{
                                currentPan = point;
                            }}
                        }});
                        console.log('Pan-zoom initialized successfully');
                    }} catch(err) {{
                        console.error('Pan-zoom initialization failed:', err);
                    }}
                }} else {{
                    console.error('SVG element not found');
                }}
            }}, 1000);
        }}

        // Manual zoom controls with fallback
        function zoomIn() {{
            if (panZoom) {{
                panZoom.zoomIn();
            }} else {{
                currentZoom *= 1.3;
                applyManualZoom();
            }}
        }}

        function zoomOut() {{
            if (panZoom) {{
                panZoom.zoomOut();
            }} else {{
                currentZoom *= 0.7;
                applyManualZoom();
            }}
        }}

        function resetView() {{
            if (panZoom) {{
                panZoom.reset();
            }} else {{
                currentZoom = 1;
                currentPan = {{ x: 0, y: 0 }};
                applyManualZoom();
            }}
        }}

        function centerView() {{
            if (panZoom) {{
                panZoom.center();
            }}
        }}

        function fitView() {{
            if (panZoom) {{
                panZoom.fit();
                panZoom.center();
            }}
        }}

        function applyManualZoom() {{
            const svg = document.querySelector('#diagram-container svg');
            if (svg) {{
                svg.style.transform = `scale(${{currentZoom}}) translate(${{currentPan.x}}px, ${{currentPan.y}}px)`;
                svg.style.transformOrigin = 'top left';
            }}
        }}

        // Theme toggle function
        function toggleTheme(theme) {{
            if (theme === 'dark') {{
                document.body.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }} else {{
                document.body.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }}
        }}

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {{
            document.body.classList.add('dark');
        }}
    </script>
</body>
</html>'''

        html_file = Path(output_path)
        html_file.parent.mkdir(parents=True, exist_ok=True)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"✓ HTML diagram saved: {output_path}")


# Convenience function
def generate_all_diagrams(flow_records: List, zones: Dict, output_dir: str = 'outputs/diagrams'):
    """
    Generate all network diagrams

    Args:
        flow_records: List of FlowRecord objects
        zones: Dictionary of NetworkZone objects
        output_dir: Output directory for diagrams

    Returns:
        MermaidDiagramGenerator instance
    """
    generator = MermaidDiagramGenerator(flow_records, zones)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate overall network diagram
    generator.generate_overall_network_diagram(str(output_path / 'overall_network.mmd'))

    # Generate zone flow diagram
    generator.generate_zone_flow_diagram(str(output_path / 'zone_flows.mmd'))

    # Generate per-app diagrams
    generator.generate_all_app_diagrams(str(output_path))

    logger.info("✅ All diagrams generated successfully")
    return generator


if __name__ == '__main__':
    # Example usage
    from src.parser import parse_network_logs
    from src.analysis import analyze_traffic

    print("="*60)
    print("Mermaid Diagram Generator - Test Run")
    print("="*60)

    # Parse and analyze
    parser = parse_network_logs('data/input')
    analyzer = analyze_traffic(parser.records, 'outputs')

    # Generate diagrams
    generator = generate_all_diagrams(
        parser.records,
        analyzer.zones,
        'outputs/diagrams'
    )

    print("\n✅ Diagram generation complete!")
