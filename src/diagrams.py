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

    def __init__(self, flow_records: List, zones: Dict, hostname_resolver=None):
        """
        Initialize diagram generator

        Args:
            flow_records: List of FlowRecord objects
            zones: Dictionary of NetworkZone objects
            hostname_resolver: HostnameResolver instance (optional)
                              If None, will create one in demo mode
        """
        self.records = flow_records
        self.zones = zones

        # Initialize hostname resolver
        if hostname_resolver is None:
            from utils.hostname_resolver import HostnameResolver
            self.hostname_resolver = HostnameResolver(demo_mode=True)
        else:
            self.hostname_resolver = hostname_resolver

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
        """Generate per-application diagram"""
        logger.info(f"Generating diagram for application: {app_name}")

        # Filter records for this app
        app_records = [r for r in self.records if r.app_name == app_name]

        if not app_records:
            logger.warning(f"No records found for application: {app_name}")
            return ""

        lines = []
        lines.append("graph LR")
        lines.append(f"    %% Application: {app_name}")
        lines.append("")

        # Define styles
        lines.append("    %% Component Styles")
        lines.append("    classDef internal fill:#4caf50,stroke:#388e3c,stroke-width:2px,color:#fff")
        lines.append("    classDef external fill:#f44336,stroke:#c62828,stroke-width:2px,color:#fff")
        lines.append("    classDef database fill:#ff5722,stroke:#d84315,stroke-width:2px,color:#fff")
        lines.append("    classDef cache fill:#00bcd4,stroke:#0097a7,stroke-width:2px,color:#fff")
        lines.append("    classDef messaging fill:#9c27b0,stroke:#7b1fa2,stroke-width:2px,color:#fff")
        lines.append("")

        # Collect unique hosts and their types
        hosts = set()
        host_types = {}

        for record in app_records:
            hosts.add(record.src_ip)
            hosts.add(record.dst_ip)

            # Classify host type based on ports
            if record.port:
                if record.port in [3306, 5432, 27017]:
                    host_types[record.dst_ip] = 'database'
                elif record.port == 6379:
                    host_types[record.dst_ip] = 'cache'
                elif record.port == 9092:
                    host_types[record.dst_ip] = 'messaging'

            # Check if external
            if not record.is_internal:
                if not self._is_internal_ip_check(record.src_ip):
                    host_types[record.src_ip] = 'external'
                if not self._is_internal_ip_check(record.dst_ip):
                    host_types[record.dst_ip] = 'external'

        # Add nodes
        lines.append("    %% Application Components")
        # Filter out None values before sorting
        valid_hosts = [h for h in hosts if h is not None]
        for host in sorted(valid_hosts):
            safe_name = self._safe_name(host)
            host_type = host_types.get(host, 'internal')

            # Resolve hostname using hostname resolver
            # Determine zone for better synthetic hostname generation
            zone = None
            for zone_name, zone_obj in self.zones.items():
                if hasattr(zone_obj, 'members') and host in zone_obj.members:
                    zone = zone_name
                    break

            hostname, display_label = self.hostname_resolver.resolve_with_display(host, zone)

            lines.append(f"    {safe_name}[\"{display_label}\"]:::{host_type}")

        lines.append("")

        # Add connections with protocol/port annotations
        lines.append("    %% Traffic Flows")
        flow_summary = defaultdict(lambda: {'count': 0, 'bytes': 0, 'protocols': set()})

        for record in app_records:
            key = (record.src_ip, record.dst_ip)
            flow_summary[key]['count'] += 1
            flow_summary[key]['bytes'] += record.bytes
            if record.port:
                flow_summary[key]['protocols'].add(f"{record.transport}:{record.port}")
            else:
                flow_summary[key]['protocols'].add(record.transport)

        # Sort by traffic volume
        sorted_flows = sorted(flow_summary.items(), key=lambda x: x[1]['bytes'], reverse=True)

        for (src, dst), stats in sorted_flows[:30]:  # Limit to top 30 to avoid clutter
            # Skip flows with None src or dst
            if src is None or dst is None:
                continue

            src_safe = self._safe_name(src)
            dst_safe = self._safe_name(dst)

            protocols = ', '.join(sorted(stats['protocols'])[:3])  # Show top 3 protocols
            bytes_mb = stats['bytes'] / (1024 * 1024)

            if bytes_mb > 1:
                label = f"{protocols}<br/>{bytes_mb:.1f}MB, {stats['count']} flows"
            else:
                label = f"{protocols}<br/>{stats['count']} flows"

            # Use different line styles based on traffic volume
            if bytes_mb > 10:
                lines.append(f"    {src_safe} ==>|{label}| {dst_safe}")
            elif bytes_mb > 1:
                lines.append(f"    {src_safe} -->|{label}| {dst_safe}")
            else:
                lines.append(f"    {src_safe} -.->|{label}| {dst_safe}")

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
        return name.replace('.', '_').replace('-', '_').replace(':', '_').replace(' ', '_')

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
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            color: #fff;
        }}
        h1 {{
            color: #6c7aff;
            text-align: center;
            margin-bottom: 30px;
        }}
        #diagram-container {{
            background: #1a1f3a;
            padding: 30px;
            border-radius: 12px;
            margin: 20px auto;
            max-width: 1600px;
            overflow-x: auto;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
        }}
        .info {{
            max-width: 1600px;
            margin: 20px auto;
            background: #1a1f3a;
            padding: 20px;
            border-radius: 8px;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .legend-item {{
            background: #2a2f4a;
            padding: 15px;
            border-radius: 8px;
        }}
        .legend-title {{
            font-weight: bold;
            color: #8a95ff;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <h1>🔒 {title}</h1>

    <div class="info">
        <h2>Network Segmentation Diagram</h2>
        <p>This diagram visualizes the network topology and traffic flows for security analysis and segmentation planning.</p>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-title">Line Types</div>
                <strong>=====></strong> High volume traffic<br>
                <strong>-----></strong> Medium volume traffic<br>
                <strong>-.-.-></strong> Low volume traffic
            </div>
            <div class="legend-item">
                <div class="legend-title">Colors</div>
                <span style="color: #f44336;">■</span> External/High Risk<br>
                <span style="color: #ff9800;">■</span> DMZ/Medium Risk<br>
                <span style="color: #4caf50;">■</span> Internal/Low Risk<br>
                <span style="color: #2196f3;">■</span> Application Tier<br>
                <span style="color: #ff5722;">■</span> Data Tier
            </div>
        </div>
    </div>

    <div id="diagram-container">
        <pre class="mermaid">
{mermaid_content}
        </pre>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            themeVariables: {{
                darkMode: true,
                background: '#1a1f3a',
                primaryColor: '#6c7aff',
                primaryTextColor: '#fff',
                primaryBorderColor: '#8a95ff',
                lineColor: '#8a95ff',
                secondaryColor: '#2a2f4a',
                tertiaryColor: '#3a3f5a'
            }}
        }});
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
