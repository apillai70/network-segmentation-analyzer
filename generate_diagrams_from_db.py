"""
Post-Processing Diagram Generator from PostgreSQL
===================================================
Generates enhanced network diagrams AFTER all batch processing completes.
Reads complete data from PostgreSQL database and creates:
- Grouped diagrams by server naming conventions
- Color-coded unknown connections
- Visual boxes around server groups
- Load balancer identification
- Multi-format output (MMD, HTML, PNG, SVG)

Usage:
    python generate_diagrams_from_db.py                    # All applications
    python generate_diagrams_from_db.py --apps BLZE BM BO  # Specific apps
    python generate_diagrams_from_db.py --format svg       # Only SVG output
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass
import re

import pandas as pd

from src.config import get_config
from src.database.flow_repository import FlowRepository
from src.server_classifier import ServerClassifier
from src.source_component_analyzer import SourceComponentAnalyzer
from src.diagram_format_generator import DiagramFormatGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServerGroup:
    """Represents a group of servers with naming convention"""
    name: str
    pattern: str
    servers: List[str]
    server_type: Optional[str] = None
    tier: Optional[str] = None


class DiagramGeneratorFromDB:
    """
    Generate enhanced diagrams from PostgreSQL database
    Runs AFTER all batch processing completes
    """

    def __init__(self, config=None):
        """Initialize diagram generator"""
        self.config = config or get_config()
        self.flow_repo = FlowRepository(self.config)
        self.server_classifier = ServerClassifier()
        self.source_analyzer = SourceComponentAnalyzer()
        self.format_generator = DiagramFormatGenerator()

        # Output directories
        self.output_dir = Path('outputs_final/diagrams_enhanced')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"✓ Diagram generator initialized")
        logger.info(f"  Output: {self.output_dir}")

    def generate_all_applications(self, app_codes: Optional[List[str]] = None):
        """
        Generate diagrams for all applications (or specified subset)

        Args:
            app_codes: Optional list of specific application codes
        """
        if not self.flow_repo.connection_pool:
            logger.error("Database not available. Cannot generate diagrams from DB.")
            return

        # Get list of applications from database
        if app_codes:
            apps_to_process = app_codes
        else:
            apps_to_process = self._get_all_app_codes()

        logger.info(f"Generating diagrams for {len(apps_to_process)} applications")

        success_count = 0
        for app_code in apps_to_process:
            try:
                logger.info(f"Processing {app_code}...")
                self.generate_application_diagram(app_code)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to generate diagram for {app_code}: {e}", exc_info=True)

        logger.info(f"✓ Successfully generated {success_count}/{len(apps_to_process)} diagrams")

    def _get_all_app_codes(self) -> List[str]:
        """Get all unique application codes from database"""
        with self.flow_repo.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT DISTINCT source_app_code
                    FROM {self.flow_repo.schema}.enriched_flows
                    WHERE source_app_code IS NOT NULL
                    ORDER BY source_app_code
                """)
                result = cur.fetchall()
                return [row[0] for row in result]

    def generate_application_diagram(self, app_code: str):
        """
        Generate enhanced diagram for a single application

        Args:
            app_code: Application code (e.g., 'BLZE', 'BM')
        """
        logger.info(f"📊 Generating diagram for {app_code}")

        # 1. Load flows from database
        flows_df = self._load_flows_from_db(app_code)

        if flows_df.empty:
            logger.warning(f"No flows found for {app_code}")
            return

        logger.info(f"  Loaded {len(flows_df)} flows from database")

        # 2. Identify server groups by naming convention
        target_groups = self._identify_server_groups(flows_df)
        logger.info(f"  Identified {len(target_groups)} server groups")

        # 3. Identify load balancers
        load_balancers = self._identify_load_balancers(flows_df)
        if load_balancers:
            logger.info(f"  Found {len(load_balancers)} load balancers")

        # 4. Generate Mermaid diagram with grouping
        mermaid_code = self._generate_enhanced_mermaid(
            app_code,
            flows_df,
            target_groups,
            load_balancers
        )

        # 5. Save all formats (MMD, HTML, PNG, SVG)
        self._save_all_formats(app_code, mermaid_code, target_groups, load_balancers)

        logger.info(f"✓ Generated diagram for {app_code}")

    def _load_flows_from_db(self, app_code: str) -> pd.DataFrame:
        """
        Load enriched flows from PostgreSQL for specific application

        Args:
            app_code: Application code

        Returns:
            DataFrame with flow data including server classification
        """
        with self.flow_repo.get_connection() as conn:
            query = f"""
                SELECT
                    source_app_code,
                    source_ip,
                    source_hostname,
                    source_device_type,
                    source_server_type,
                    source_server_tier,
                    source_server_category,
                    dest_ip,
                    dest_hostname,
                    dest_device_type,
                    dest_app_code,
                    dest_server_type,
                    dest_server_tier,
                    dest_server_category,
                    protocol,
                    port,
                    bytes_in,
                    bytes_out,
                    flow_direction,
                    flow_count
                FROM {self.flow_repo.schema}.enriched_flows
                WHERE source_app_code = %s
                ORDER BY dest_hostname, dest_ip
            """
            df = pd.read_sql_query(query, conn, params=(app_code,))
            return df

    def _identify_server_groups(self, flows_df: pd.DataFrame) -> List[ServerGroup]:
        """
        Identify server groups based on naming conventions

        Common patterns:
        - AODSVY1WEB01, AODSVY2WEB01, AODSVY3WEB01 -> Group: AODSVY-WEB
        - AODSVY1APP01, AODSVY1APP02 -> Group: AODSVY-APP
        - AODSVY1DB01 -> Group: AODSVY-DB
        - Suffix numbers (01, 02, 03) indicate cluster/HA

        Args:
            flows_df: DataFrame with flow data

        Returns:
            List of ServerGroup objects
        """
        groups = defaultdict(lambda: {'servers': set(), 'type': None, 'tier': None})

        # Regex patterns to extract base name and server type
        patterns = [
            # Pattern: AODSVY1WEB01 -> AODSVY-WEB
            (r'^([A-Z]+\d?)([A-Z]{2,4})\d+$', lambda m: f"{m.group(1)}-{m.group(2)}"),
            # Pattern: server-web-01 -> server-web
            (r'^([a-z\-]+\d?)-([a-z]+)-\d+$', lambda m: f"{m.group(1)}-{m.group(2)}"),
            # Pattern: SRV01WEB, SRV02WEB -> SRV-WEB
            (r'^([A-Z]+\d+)([A-Z]{3})$', lambda m: f"{m.group(1)[:3]}-{m.group(2)}"),
        ]

        for _, row in flows_df.iterrows():
            hostname = row.get('dest_hostname', '') or ''

            if not hostname or hostname == 'Unknown':
                continue

            # Try to match patterns
            group_name = None
            for pattern, name_func in patterns:
                match = re.match(pattern, hostname.upper())
                if match:
                    group_name = name_func(match)
                    break

            # If no pattern matched, use server type as group
            if not group_name:
                server_type = row.get('dest_server_type', 'Unknown')
                if server_type and server_type != 'Unknown':
                    group_name = f"GROUP-{server_type.upper()}"
                else:
                    group_name = "UNGROUPED"

            # Add to group
            groups[group_name]['servers'].add(hostname)

            # Record server type and tier
            if not groups[group_name]['type']:
                groups[group_name]['type'] = row.get('dest_server_type')
            if not groups[group_name]['tier']:
                groups[group_name]['tier'] = row.get('dest_server_tier')

        # Convert to ServerGroup objects
        server_groups = [
            ServerGroup(
                name=name,
                pattern=name,
                servers=sorted(list(info['servers'])),
                server_type=info['type'],
                tier=info['tier']
            )
            for name, info in groups.items()
            if info['servers']  # Only groups with servers
        ]

        # Sort by group name
        server_groups.sort(key=lambda g: g.name)

        return server_groups

    def _identify_load_balancers(self, flows_df: pd.DataFrame) -> List[Dict]:
        """
        Identify load balancers from flow data

        Args:
            flows_df: DataFrame with flow data

        Returns:
            List of load balancer information dicts
        """
        load_balancers = []

        for _, row in flows_df.iterrows():
            dest_type = row.get('dest_server_type', '')

            # Check if destination is a load balancer
            if dest_type in ['F5', 'Azure Traffic Manager', 'Load Balancer']:
                lb_info = {
                    'hostname': row.get('dest_hostname', 'Unknown'),
                    'ip': str(row.get('dest_ip', '')),
                    'type': dest_type,
                    'port': row.get('port')
                }

                # Avoid duplicates
                if not any(lb['hostname'] == lb_info['hostname'] and lb['ip'] == lb_info['ip']
                          for lb in load_balancers):
                    load_balancers.append(lb_info)

        return load_balancers

    def _generate_enhanced_mermaid(
        self,
        app_code: str,
        flows_df: pd.DataFrame,
        target_groups: List[ServerGroup],
        load_balancers: List[Dict]
    ) -> str:
        """
        Generate enhanced Mermaid diagram with:
        - Server grouping (subgraphs)
        - Color-coded unknown connections (red/gray)
        - Load balancer identification
        - Server type shapes

        Args:
            app_code: Application code
            flows_df: DataFrame with flow data
            target_groups: List of server groups
            load_balancers: List of load balancers

        Returns:
            Mermaid diagram code as string
        """
        lines = []
        lines.append("graph TB")
        lines.append("")
        lines.append(f"    %% Application: {app_code}")
        lines.append(f"    %% Generated from PostgreSQL database")
        lines.append("")

        # Define source node
        lines.append(f"    {app_code}[[\"{app_code}<br/>Application\"]]")
        lines.append(f"    style {app_code} fill:#E8F5E9,stroke:#4CAF50,stroke-width:3px")
        lines.append("")

        # Create subgraphs for each server group
        group_members = {}  # Track which servers are in which groups

        for idx, group in enumerate(target_groups):
            if len(group.servers) > 1:  # Only create subgraph if multiple servers
                lines.append(f"    subgraph GROUP_{idx} [\"{group.name}\"]")
                lines.append(f"        direction TB")

                for server in group.servers:
                    node_id = self._sanitize_node_id(server)
                    group_members[server] = node_id

                    # Get server type for shape selection
                    server_rows = flows_df[flows_df['dest_hostname'] == server]
                    if not server_rows.empty:
                        server_type = server_rows.iloc[0].get('dest_server_type', 'Unknown')
                        shape_open, shape_close = self._get_shape_for_server_type(server_type)

                        # Color by tier
                        tier = server_rows.iloc[0].get('dest_server_tier', 'Unknown')
                        color = self._get_color_for_tier(tier)

                        lines.append(f"        {node_id}{shape_open}\"{server}<br/>{server_type}\"{shape_close}")
                        lines.append(f"        style {node_id} fill:{color}")
                    else:
                        lines.append(f"        {node_id}[\"{server}\"]")

                lines.append(f"    end")
                lines.append("")

        # Add load balancers (outside groups, with special styling)
        if load_balancers:
            lines.append(f"    subgraph LOAD_BALANCERS [\"Load Balancers\"]")
            for lb in load_balancers:
                node_id = self._sanitize_node_id(lb['hostname'])
                lines.append(f"        {node_id}{{{{\"⚖️ {lb['hostname']}<br/>{lb['type']}\"}}}}")
                lines.append(f"        style {node_id} fill:#FFF3E0,stroke:#FF9800,stroke-width:2px")
            lines.append(f"    end")
            lines.append("")

        # Add ungrouped servers
        grouped_servers = set()
        for group in target_groups:
            grouped_servers.update(group.servers)

        ungrouped = []
        for _, row in flows_df.iterrows():
            hostname = row.get('dest_hostname', '')
            if hostname and hostname != 'Unknown' and hostname not in grouped_servers:
                if hostname not in ungrouped:
                    ungrouped.append(hostname)

        if ungrouped:
            lines.append(f"    subgraph UNGROUPED [\"Other Servers\"]")
            for server in ungrouped:
                node_id = self._sanitize_node_id(server)
                group_members[server] = node_id

                server_rows = flows_df[flows_df['dest_hostname'] == server]
                if not server_rows.empty:
                    server_type = server_rows.iloc[0].get('dest_server_type', 'Unknown')
                    shape_open, shape_close = self._get_shape_for_server_type(server_type)
                    tier = server_rows.iloc[0].get('dest_server_tier', 'Unknown')
                    color = self._get_color_for_tier(tier)

                    lines.append(f"        {node_id}{shape_open}\"{server}<br/>{server_type}\"{shape_close}")
                    lines.append(f"        style {node_id} fill:{color}")
                else:
                    lines.append(f"        {node_id}[\"{server}\"]")
            lines.append(f"    end")
            lines.append("")

        # Add connections with color coding for unknowns
        lines.append(f"    %% Connections")
        connections_added = set()

        for _, row in flows_df.iterrows():
            hostname = row.get('dest_hostname', '')
            port = row.get('port', '')
            protocol = row.get('protocol', '')

            if not hostname:
                continue

            # Create connection label
            label = f"{protocol}/{port}" if protocol and port else ""

            # Determine if unknown connection
            is_unknown = (
                hostname == 'Unknown' or
                row.get('dest_server_type') == 'Unknown' or
                not row.get('dest_server_type')
            )

            # Get target node ID
            if hostname in group_members:
                target_id = group_members[hostname]
            else:
                target_id = self._sanitize_node_id(hostname)

            # Create unique connection key
            conn_key = f"{app_code}-->{target_id}:{label}"
            if conn_key in connections_added:
                continue
            connections_added.add(conn_key)

            # Add connection with appropriate color
            if is_unknown:
                # Red for unknown connections
                lines.append(f"    {app_code} -->|{label}| {target_id}")
                lines.append(f"    linkStyle {len([l for l in lines if '-->' in l])-1} stroke:#f44336,stroke-width:2px")
            else:
                lines.append(f"    {app_code} -->|{label}| {target_id}")

        return "\n".join(lines)

    def _sanitize_node_id(self, name: str) -> str:
        """Convert hostname to valid Mermaid node ID"""
        return re.sub(r'[^A-Za-z0-9_]', '_', name)

    def _get_shape_for_server_type(self, server_type: str) -> Tuple[str, str]:
        """Get Mermaid shape for server type"""
        shape_map = {
            'DNS': ('{{', '}}'),           # Hexagon
            'LDAP': ('{{', '}}'),          # Hexagon
            'F5': ('{{', '}}'),            # Hexagon
            'Load Balancer': ('{{', '}}'),  # Hexagon
            'Database': ('[(', ')]'),       # Cylinder
            'Web Server': ('[/', '\\]'),    # Trapezoid
            'App Server': ('[', ']'),       # Rectangle
            'Mail Server': ('[/', '\\]'),   # Trapezoid
        }
        return shape_map.get(server_type, ('[', ']'))  # Default rectangle

    def _get_color_for_tier(self, tier: str) -> str:
        """Get color for server tier"""
        color_map = {
            'Infrastructure': '#E0F2F1',  # Mint
            'Security': '#FFCCBC',        # Coral
            'Cloud': '#E1BEE7',           # Purple
            'Database': '#FFE0B2',        # Orange
            'Presentation': '#C8E6C9',    # Light Green
        }
        return color_map.get(tier, '#EEEEEE')  # Default gray

    def _save_all_formats(
        self,
        app_code: str,
        mermaid_code: str,
        target_groups: List[ServerGroup],
        load_balancers: List[Dict]
    ):
        """
        Save diagram in all formats (MMD, HTML, PNG, SVG)

        Args:
            app_code: Application code
            mermaid_code: Mermaid diagram code
            target_groups: Server groups
            load_balancers: Load balancers
        """
        base_filename = f"{app_code}_enhanced_diagram"

        # 1. Save MMD
        mmd_file = self.output_dir / f"{base_filename}.mmd"
        mmd_file.write_text(mermaid_code, encoding='utf-8')
        logger.info(f"  ✓ Saved: {mmd_file.name}")

        # 2. Generate and save HTML
        html_file = self.output_dir / f"{base_filename}.html"
        html_content = self.format_generator.generate_html(
            mermaid_code=mermaid_code,
            title=f"{app_code} Network Diagram (Enhanced)",
            app_code=app_code
        )
        html_file.write_text(html_content, encoding='utf-8')
        logger.info(f"  ✓ Saved: {html_file.name}")

        # 3. Generate PNG (via Mermaid.ink API)
        png_file = self.output_dir / f"{base_filename}.png"
        png_success = self.format_generator.generate_png_mermaidink(
            mermaid_code=mermaid_code,
            output_file=str(png_file),
            width=4800
        )
        if png_success:
            logger.info(f"  ✓ Saved: {png_file.name}")
        else:
            logger.warning(f"  ⚠ Failed to generate PNG for {app_code}")

        # 4. Generate SVG (via Mermaid.ink API)
        svg_file = self.output_dir / f"{base_filename}.svg"
        svg_success = self.format_generator.generate_svg_mermaidink(
            mermaid_code=mermaid_code,
            output_file=str(svg_file)
        )
        if svg_success:
            logger.info(f"  ✓ Saved: {svg_file.name}")
        else:
            logger.warning(f"  ⚠ Failed to generate SVG for {app_code}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate enhanced diagrams from PostgreSQL database'
    )
    parser.add_argument(
        '--apps',
        nargs='+',
        help='Specific application codes to process (default: all)'
    )
    parser.add_argument(
        '--format',
        choices=['all', 'mmd', 'html', 'png', 'svg'],
        default='all',
        help='Output format (default: all)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Post-Processing Diagram Generator")
    logger.info("=" * 80)

    generator = DiagramGeneratorFromDB()
    generator.generate_all_applications(app_codes=args.apps)

    logger.info("=" * 80)
    logger.info("✓ Diagram generation complete")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
