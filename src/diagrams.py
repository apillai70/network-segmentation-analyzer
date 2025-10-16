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

    # Zone colors (Mermaid-compatible) - Rainbow spectrum for diverse components
    ZONE_COLORS = {
        'EXTERNAL': '#f44336',           # Red - External/High Risk
        'DMZ': '#ff9800',                # Orange - DMZ
        'WEB_TIER': '#4caf50',           # Green - Web Tier
        'APP_TIER': '#2196f3',           # Blue - Application Tier
        'DATA_TIER': '#ff5722',          # Deep Orange - Data Tier
        'MESSAGING_TIER': '#9c27b0',     # Purple - Message queues
        'CACHE_TIER': '#00bcd4',         # Cyan - Cache services
        'MANAGEMENT_TIER': '#ffc107',    # Amber - Management/infrastructure
        'INFRASTRUCTURE': '#795548',     # Brown - Infrastructure
        'INTERNAL': '#4caf50',           # Green - Internal/Low Risk
        'API_GATEWAY': '#8bc34a',        # Light Green - API Gateway
        'LOAD_BALANCER': '#e91e63',      # Pink - Load Balancers
        'STORAGE_TIER': '#673ab7',       # Deep Purple - Storage services
        'MONITORING': '#ff9800',         # Orange - Monitoring/Logging
        'SECURITY': '#f44336',           # Red - Security services
        'NETWORK': '#009688',            # Teal - Network services
        'COMPUTE': '#03a9f4',            # Light Blue - Compute/VMs
        'CONTAINER': '#9c27b0',          # Purple - Containers
        'SERVERLESS': '#00bcd4',         # Cyan - Serverless/Functions
        'ANALYTICS': '#ffeb3b',          # Yellow - Analytics
        'ML_SERVICE': '#8bc34a',         # Light Green - ML Services
        'UNKNOWN': '#9e9e9e',            # Gray - Unknown/Unclassified
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

        # Save as .mmd file with markdown fencing for better compatibility
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            # Wrap in markdown code fence for Mermaid.ink API compatibility
            f.write('```mermaid\n')
            f.write(mermaid_content)
            f.write('\n```')

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

        # Start building Mermaid diagram - TOP TO BOTTOM layout (VERTICAL)
        lines = []
        lines.append("graph TB")
        lines.append(f"    %% Application: {app_name} - Tier-based Architecture View")
        lines.append("")

        # Define styles for vertical tier-based layout
        lines.append("    %% Component Styles")
        lines.append("    classDef webTier fill:#ffcccc,stroke:#cc0000,stroke-width:3px,color:#000")  # Red - High Risk
        lines.append("    classDef appTier fill:#cce5ff,stroke:#0066cc,stroke-width:3px,color:#000")  # Blue - Application Tier
        lines.append("    classDef dataTier fill:#ff9966,stroke:#cc6600,stroke-width:3px,color:#000")  # Orange - Data Tier
        lines.append("    classDef cacheTier fill:#ffcc99,stroke:#ff9933,stroke-width:3px,color:#000")  # Light Orange - Cache
        lines.append("    classDef msgTier fill:#cc99ff,stroke:#9933ff,stroke-width:3px,color:#000")  # Purple - Messaging
        lines.append("    classDef mgmtTier fill:#ffff99,stroke:#cccc00,stroke-width:3px,color:#000")  # Yellow - Management
        lines.append("    classDef database fill:#ff9966,stroke:#cc6600,stroke-width:3px,color:#000")  # Orange - Databases
        lines.append("    classDef cache fill:#ffcc99,stroke:#ff9933,stroke-width:2px,color:#000")  # Light Orange - Cache
        lines.append("    classDef queue fill:#cc99ff,stroke:#9933ff,stroke-width:2px,color:#000")  # Purple - Queues
        lines.append("    classDef downstream fill:#cce5ff,stroke:#0066cc,stroke-width:2px,color:#000")  # Blue - Downstream Apps
        lines.append("    classDef lowRisk fill:#ccffcc,stroke:#009900,stroke-width:2px,color:#000")  # Green - Low Risk/Internal
        lines.append("")

        # Group application components by tier (LEFT SIDE)
        app_components_by_tier = defaultdict(list)

        for comp_ip in application_components:
            tier = None
            # Try to find tier from zone membership first
            for zone_name, zone_obj in self.zones.items():
                if hasattr(zone_obj, 'members') and comp_ip in zone_obj.members:
                    tier = zone_name
                    break

            # If not in a zone, infer from IP address pattern
            if not tier:
                tier = self._infer_tier_from_ip(comp_ip)

            hostname, display_label = self.hostname_resolver.resolve_with_display(comp_ip, tier)

            app_components_by_tier[tier].append({
                'ip': comp_ip,
                'safe_name': self._safe_name(comp_ip),
                'display_label': display_label
            })

        # Define tier order (top to bottom)
        tier_order = ['WEB_TIER', 'APP_TIER', 'DATA_TIER', 'CACHE_TIER',
                     'MESSAGING_TIER', 'MANAGEMENT_TIER', 'INFRASTRUCTURE_TIER', 'UNKNOWN']

        # Map tiers to class names
        tier_classes = {
            'WEB_TIER': 'webTier',
            'APP_TIER': 'appTier',
            'DATA_TIER': 'dataTier',
            'CACHE_TIER': 'cacheTier',
            'MESSAGING_TIER': 'msgTier',
            'MANAGEMENT_TIER': 'mgmtTier',
            'INFRASTRUCTURE_TIER': 'mgmtTier',
            'UNKNOWN': 'mgmtTier'
        }

        # Add application tiers as SEPARATE subgraphs (LEFT SIDE - stacked vertically)
        lines.append(f"    %% Application Tiers (Vertical Stack)")
        for tier in tier_order:
            if tier not in app_components_by_tier:
                continue

            tier_label = tier.replace('_TIER', '').replace('_', ' ').title()
            tier_id = self._safe_name(f"{app_name}_{tier}")
            tier_class = tier_classes.get(tier, 'mgmtTier')
            server_count = len(app_components_by_tier[tier])

            lines.append(f"    subgraph {tier_id}[\"{tier_label}<br/>{server_count} server(s)\"]")
            lines.append("        direction LR")

            # Show servers in this tier (limit to 10 for readability)
            for comp_info in sorted(app_components_by_tier[tier], key=lambda x: x['ip'])[:10]:
                safe_name = comp_info['safe_name']
                display_label = self._sanitize_label(comp_info['display_label'])
                lines.append(f"        {safe_name}[\"{display_label}\"]:::{tier_class}")

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
            'queue': 'Queues',
            'cache': 'Caches',
            'database': 'Databases',
            'downstream_app': 'Downstream Applications'
        }

        lines.append(f"    %% Infrastructure & External Dependencies (Right Side)")
        for dep_type in ['queue', 'cache', 'database', 'downstream_app']:
            if dep_type not in deps_by_type:
                continue

            type_label = type_labels[dep_type]
            type_id = self._safe_name(f"{dep_type}_infra")

            lines.append(f"    subgraph {type_id}[\"{type_label}\"]")
            lines.append("        direction LR")

            for dep_info in sorted(deps_by_type[dep_type], key=lambda x: x['ip'])[:10]:  # Limit to 10 per type for clarity
                safe_name = dep_info['safe_name']
                display_label = self._sanitize_label(dep_info['display_label'])

                # Use different shapes for different service types
                if dep_type == 'database':
                    # Cylinder shape for databases
                    lines.append(f"        {safe_name}[(\"{display_label}\")]:::database")
                elif dep_type == 'downstream_app':
                    # Circle shape for downstream applications
                    lines.append(f"        {safe_name}((\"{display_label}\")):::downstream")
                elif dep_type == 'queue':
                    # Rectangle for queues
                    lines.append(f"        {safe_name}[\"{display_label}\"]:::queue")
                else:
                    # Rectangle for caches
                    lines.append(f"        {safe_name}[\"{display_label}\"]:::cache")

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
        # IMPORTANT: Must match EXACT sorting/filtering used when rendering!
        displayed_app_components = set()
        for tier_comps in app_components_by_tier.values():
            # Match line 304: sorted by IP, first 10
            for comp in sorted(tier_comps, key=lambda x: x['ip'])[:10]:
                displayed_app_components.add(comp['ip'])

        displayed_dependencies = set()
        for dep_type_list in deps_by_type.values():
            # Match line 344: sorted by IP, first 10
            for dep in sorted(dep_type_list, key=lambda x: x['ip'])[:10]:
                displayed_dependencies.add(dep['ip'])

        flows_added = set()
        # Sort flows by count to show most important connections first
        for (src, dst), stats in sorted(flow_summary.items(), key=lambda x: x[1]['count'], reverse=True):
            if src is None or dst is None:
                continue

            # Only show flows where BOTH source and destination are displayed nodes
            if src not in displayed_app_components or dst not in displayed_dependencies:
                continue

            # Limit total flows displayed to avoid clutter
            if len(flows_added) >= 50:
                break

            src_safe = self._safe_name(src)
            dst_safe = self._safe_name(dst)
            dep_type = dependency_types.get(dst, 'downstream_app')
            edge_label = edge_labels.get(dep_type, 'app calls')

            # Use straight arrows with labels (vertical layout works better with simple arrows)
            lines.append(f"    {src_safe} -->|{edge_label}| {dst_safe}")
            flows_added.add((src, dst))

        mermaid_content = '\n'.join(lines)

        # Save as .mmd file with markdown fencing for better compatibility
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            # Wrap in markdown code fence for Mermaid.ink API compatibility
            f.write('```mermaid\n')
            f.write(mermaid_content)
            f.write('\n```')

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

        # Save as .mmd file with markdown fencing for better compatibility
        mmd_file = Path(output_path)
        mmd_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mmd_file, 'w', encoding='utf-8') as f:
            # Wrap in markdown code fence for Mermaid.ink API compatibility
            f.write('```mermaid\n')
            f.write(mermaid_content)
            f.write('\n```')

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

    def _infer_tier_from_ip(self, ip: str) -> str:
        """Infer network tier from IP address pattern"""
        if not ip or not isinstance(ip, str):
            return 'UNKNOWN'

        # Standard tier IP ranges
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
        else:
            return 'UNKNOWN'

    def _safe_name(self, name: str) -> str:
        """Convert name to Mermaid-safe identifier"""
        if name is None:
            return 'unknown_host'
        return str(name).replace('.', '_').replace('-', '_').replace(':', '_').replace(' ', '_').replace('(', '_').replace(')', '_')

    def _sanitize_label(self, label: str) -> str:
        """Sanitize label text for Mermaid display (remove parentheses that break syntax)"""
        if not label:
            return 'unknown'
        # Replace parentheses with hyphens for readability
        # Example: "10.164.41.47(hostname.com)" -> "10.164.41.47 - hostname.com"
        if '(' in label and ')' in label:
            label = label.replace('(', ' - ').replace(')', '')
        return label

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
                <div class="legend-title">Traffic Volume Indicators</div>
                <span><strong>=====></strong> High volume (>100 flows) - Thick solid lines<br>
                <strong>-----></strong> Medium volume (10-100 flows) - Solid lines<br>
                <strong>-.-.-></strong> Low volume (<10 flows) - Dotted/dashed lines</span>
            </div>
            <div class="legend-item">
                <div class="legend-title">Security Zone Colors</div>
                <span>
                <span style="color: #f44336;">■</span> External/High Risk<br>
                <span style="color: #ff9800;">■</span> DMZ/Medium Risk<br>
                <span style="color: #4caf50;">■</span> Internal/Low Risk<br>
                <span style="color: #2196f3;">■</span> Application Tier<br>
                <span style="color: #ff5722;">■</span> Data Tier<br>
                <span style="color: #00bcd4;">■</span> Cache Tier<br>
                <span style="color: #9c27b0;">■</span> Messaging Tier<br>
                <span style="color: #ffc107;">■</span> Management Tier
                </span>
            </div>
            <div class="legend-item">
                <div class="legend-title">Data Source Attribution</div>
                <span>
                <strong>⬛ Black solid</strong> = Observed from network flows (ExtraHop)<br>
                <strong>🔵 Blue dashed</strong> = ML inference/predictions<br>
                <strong>⬜ Gray dashed</strong> = Unknown/unclassified
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
    from parser import parse_network_logs
    from analysis import analyze_traffic

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
