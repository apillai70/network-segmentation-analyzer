#!/usr/bin/env python3
"""
Generate Enhanced Diagrams from JSON Enriched Flows
===================================================

This script reads enriched flow data from JSON files and generates enhanced
diagrams with server grouping, load balancer detection, and color-coding.

This is a fallback when PostgreSQL is not available.

Usage:
    # Generate diagrams for all applications
    python generate_diagrams_from_json.py

    # Generate for specific applications
    python generate_diagrams_from_json.py --apps AODSVY APSE ACDA

    # Specify custom output directory
    python generate_diagrams_from_json.py --output outputs/diagrams_from_json
"""

import sys
from pathlib import Path
import json
import pandas as pd
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import re
from collections import defaultdict
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import get_config
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServerGroup:
    """Represents a group of servers with same naming pattern"""
    pattern: str  # e.g., "AODSVY-WEB", "server-db"
    server_names: List[str]
    server_type: str  # e.g., "WEB_SERVER", "DATABASE_SERVER"
    count: int


class DiagramGeneratorFromJSON:
    """
    Generates enhanced diagrams from JSON enriched flows

    Features:
    - Groups servers by naming conventions
    - Detects load balancers
    - Color-codes unknown connections
    - Creates visual boxes around groups
    """

    def __init__(self, json_dir: str = "outputs_final/enriched_flows", output_dir: str = "outputs/diagrams_from_json"):
        """
        Initialize diagram generator

        Args:
            json_dir: Directory containing enriched_flows JSON files
            output_dir: Output directory for diagrams
        """
        self.json_dir = Path(json_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Color scheme for unknown connections
        self.UNKNOWN_COLOR = "#ff4444"  # Red
        self.KNOWN_COLOR = "#4CAF50"    # Green
        self.LB_COLOR = "#FF9800"        # Orange

    def load_enriched_flows(self, app_code: Optional[str] = None) -> pd.DataFrame:
        """
        Load enriched flows from JSON

        Args:
            app_code: Optional app code to filter by

        Returns:
            DataFrame with enriched flows
        """
        all_records = []

        if app_code:
            # Load specific app file
            json_file = self.json_dir / f"{app_code}_enriched_flows.json"
            if json_file.exists():
                with open(json_file, 'r') as f:
                    records = json.load(f)
                    all_records.extend(records)
            else:
                logger.warning(f"File not found: {json_file}")
        else:
            # Load consolidated file
            consolidated_file = self.json_dir / "enriched_flows_all.json"
            if consolidated_file.exists():
                with open(consolidated_file, 'r') as f:
                    all_records = json.load(f)
            else:
                # Load all individual files
                for json_file in self.json_dir.glob("*_enriched_flows.json"):
                    with open(json_file, 'r') as f:
                        records = json.load(f)
                        all_records.extend(records)

        if not all_records:
            logger.warning("No enriched flow records found")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        logger.info(f"Loaded {len(df)} enriched flow records")

        return df

    def get_available_apps(self) -> List[str]:
        """Get list of available applications"""
        apps = set()

        # Check consolidated file
        consolidated_file = self.json_dir / "enriched_flows_all.json"
        if consolidated_file.exists():
            with open(consolidated_file, 'r') as f:
                records = json.load(f)
                apps.update([r['source_app_code'] for r in records if 'source_app_code' in r])
        else:
            # Check individual files
            for json_file in self.json_dir.glob("*_enriched_flows.json"):
                app_code = json_file.stem.replace('_enriched_flows', '')
                apps.add(app_code)

        return sorted(list(apps))

    def _identify_server_groups(self, flows_df: pd.DataFrame) -> List[ServerGroup]:
        """
        Identify server groups based on naming conventions

        Patterns:
        - AODSVY1WEB01, AODSVY2WEB01 -> AODSVY-WEB
        - server-web-01, server-web-02 -> server-web
        - db-master-01, db-master-02 -> db-master

        Args:
            flows_df: Enriched flows DataFrame

        Returns:
            List of ServerGroup objects
        """
        # Collect all unique destination hostnames
        dest_hostnames = flows_df['dest_hostname'].unique()

        # Group by pattern
        pattern_groups = defaultdict(lambda: {'servers': set(), 'type': 'Unknown'})

        for hostname in dest_hostnames:
            if pd.isna(hostname) or not hostname:
                continue

            hostname = str(hostname)

            # Pattern 1: AODSVY1WEB01 -> AODSVY-WEB
            # Pattern: PREFIX + number + TYPE + number
            match = re.match(r'([A-Z]+)\d+([A-Z]+)\d+', hostname, re.IGNORECASE)
            if match:
                prefix = match.group(1)
                type_name = match.group(2)
                pattern = f"{prefix}-{type_name}"
                pattern_groups[pattern]['servers'].add(hostname)

                # Try to get server type from flows_df
                server_type_rows = flows_df[flows_df['dest_hostname'] == hostname]['dest_server_type']
                if not server_type_rows.empty:
                    pattern_groups[pattern]['type'] = server_type_rows.iloc[0]

                continue

            # Pattern 2: server-web-01 -> server-web
            # Pattern: word-word-number
            match = re.match(r'([\w-]+?)-(\d+)$', hostname)
            if match:
                pattern = match.group(1)
                pattern_groups[pattern]['servers'].add(hostname)

                # Get server type
                server_type_rows = flows_df[flows_df['dest_hostname'] == hostname]['dest_server_type']
                if not server_type_rows.empty:
                    pattern_groups[pattern]['type'] = server_type_rows.iloc[0]

                continue

            # No pattern matched - treat as individual server
            pattern_groups[hostname]['servers'].add(hostname)
            server_type_rows = flows_df[flows_df['dest_hostname'] == hostname]['dest_server_type']
            if not server_type_rows.empty:
                pattern_groups[hostname]['type'] = server_type_rows.iloc[0]

        # Convert to ServerGroup objects
        groups = []
        for pattern, data in pattern_groups.items():
            if len(data['servers']) >= 2:  # Only create groups for 2+ servers
                groups.append(ServerGroup(
                    pattern=pattern,
                    server_names=sorted(list(data['servers'])),
                    server_type=data['type'],
                    count=len(data['servers'])
                ))

        return groups

    def _identify_load_balancers(self, flows_df: pd.DataFrame) -> List[str]:
        """
        Identify potential load balancers

        Criteria:
        - Server type is F5_LOAD_BALANCER or LOAD_BALANCER
        - Or hostname contains 'lb', 'f5', 'balancer'

        Args:
            flows_df: Enriched flows DataFrame

        Returns:
            List of load balancer hostnames
        """
        load_balancers = set()

        # Method 1: By server type
        lb_types = flows_df[flows_df['dest_server_type'].isin(['F5_LOAD_BALANCER', 'LOAD_BALANCER'])]
        load_balancers.update(lb_types['dest_hostname'].unique())

        # Method 2: By hostname pattern
        for hostname in flows_df['dest_hostname'].unique():
            if pd.isna(hostname):
                continue
            hostname_lower = str(hostname).lower()
            if any(pattern in hostname_lower for pattern in ['lb', 'f5', 'balancer', 'loadbalancer']):
                load_balancers.add(hostname)

        return sorted(list(load_balancers))

    def _generate_enhanced_mermaid(self, app_code: str, flows_df: pd.DataFrame,
                                    target_groups: List[ServerGroup],
                                    load_balancers: List[str]) -> str:
        """
        Generate Mermaid diagram with enhancements

        Args:
            app_code: Application code
            flows_df: Enriched flows for this app
            target_groups: Server groups
            load_balancers: Load balancer hostnames

        Returns:
            Mermaid diagram code
        """
        lines = ["graph TD"]

        # Add source application node
        lines.append(f"    {app_code}[{app_code}]")
        lines.append(f"    style {app_code} fill:#4CAF50,stroke:#333,stroke-width:2px")
        lines.append("")

        # Create subgraphs for server groups
        for idx, group in enumerate(target_groups):
            subgraph_id = f"group_{idx}"
            lines.append(f"    subgraph {subgraph_id}[\"{group.pattern} ({group.count} servers)\"]")

            for server in group.server_names:
                safe_id = server.replace('.', '_').replace('-', '_')
                lines.append(f"        {safe_id}[\"{server}\\n{group.server_type}\"]")
                lines.append(f"        style {safe_id} fill:#E3F2FD,stroke:#333")

            lines.append("    end")
            lines.append("")

        # Add individual servers not in groups
        grouped_servers = set()
        for group in target_groups:
            grouped_servers.update(group.server_names)

        for hostname in flows_df['dest_hostname'].unique():
            if pd.isna(hostname) or hostname in grouped_servers:
                continue

            safe_id = str(hostname).replace('.', '_').replace('-', '_')

            # Get server type
            server_type_rows = flows_df[flows_df['dest_hostname'] == hostname]['dest_server_type']
            server_type = server_type_rows.iloc[0] if not server_type_rows.empty else 'Unknown'

            # Style based on server type and load balancer status
            if hostname in load_balancers:
                lines.append(f"    {safe_id}[\"{hostname}\\n{server_type}\\n(Load Balancer)\"]")
                lines.append(f"    style {safe_id} fill:{self.LB_COLOR},stroke:#333,stroke-width:3px")
            elif server_type == 'Unknown':
                lines.append(f"    {safe_id}[\"{hostname}\\n{server_type}\"]")
                lines.append(f"    style {safe_id} fill:#FFEBEE,stroke:{self.UNKNOWN_COLOR},stroke-width:2px")
            else:
                lines.append(f"    {safe_id}[\"{hostname}\\n{server_type}\"]")
                lines.append(f"    style {safe_id} fill:#E8F5E9,stroke:#333")

        lines.append("")

        # Add connections
        lines.append("    %% Connections")
        for _, flow in flows_df.iterrows():
            dest_hostname = flow['dest_hostname']
            if pd.isna(dest_hostname):
                continue

            safe_dest = str(dest_hostname).replace('.', '_').replace('-', '_')
            dest_type = flow.get('dest_server_type', 'Unknown')

            # Color-code connection based on whether destination is known
            if dest_type == 'Unknown':
                lines.append(f"    {app_code} -->|{flow.get('protocol', '')}:{flow.get('port', '')}| {safe_dest}")
                lines.append(f"    linkStyle {len([l for l in lines if '  -->' in l]) - 1} stroke:{self.UNKNOWN_COLOR},stroke-width:2px")
            else:
                lines.append(f"    {app_code} -->|{flow.get('protocol', '')}:{flow.get('port', '')}| {safe_dest}")

        return "\n".join(lines)

    def generate_for_application(self, app_code: str):
        """
        Generate enhanced diagrams for a single application

        Args:
            app_code: Application code
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Generating enhanced diagrams for: {app_code}")
        logger.info(f"{'='*80}")

        # Load flows for this app
        all_flows = self.load_enriched_flows()
        flows_df = all_flows[all_flows['source_app_code'] == app_code]

        if flows_df.empty:
            logger.warning(f"No flows found for {app_code}")
            return

        logger.info(f"Found {len(flows_df)} flows for {app_code}")

        # Identify server groups
        target_groups = self._identify_server_groups(flows_df)
        logger.info(f"Identified {len(target_groups)} server groups:")
        for group in target_groups:
            logger.info(f"  - {group.pattern}: {group.count} servers ({group.server_type})")

        # Identify load balancers
        load_balancers = self._identify_load_balancers(flows_df)
        logger.info(f"Identified {len(load_balancers)} load balancers: {load_balancers}")

        # Generate Mermaid diagram
        mermaid_code = self._generate_enhanced_mermaid(app_code, flows_df, target_groups, load_balancers)

        # Save Mermaid file
        mmd_file = self.output_dir / f"{app_code}_enhanced.mmd"
        with open(mmd_file, 'w') as f:
            f.write(mermaid_code)
        logger.info(f"✓ Saved Mermaid: {mmd_file}")

        # Generate HTML with Mermaid.js
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{app_code} Enhanced Network Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'default'}});</script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .diagram-container {{ margin: 20px 0; }}
        .legend {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .legend-item {{ margin: 5px 0; }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border: 1px solid #333;
        }}
    </style>
</head>
<body>
    <h1>{app_code} - Enhanced Network Diagram</h1>

    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.KNOWN_COLOR};"></span>
            Known Server (Classified)
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.UNKNOWN_COLOR};"></span>
            Unknown Server (Needs Classification)
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.LB_COLOR};"></span>
            Load Balancer
        </div>
    </div>

    <div class="diagram-container">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>

    <div style="margin-top: 30px;">
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Source:</strong> JSON enriched flows</p>
        <p><strong>Total Flows:</strong> {len(flows_df)}</p>
        <p><strong>Server Groups:</strong> {len(target_groups)}</p>
        <p><strong>Load Balancers:</strong> {len(load_balancers)}</p>
    </div>
</body>
</html>"""

        html_file = self.output_dir / f"{app_code}_enhanced.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        logger.info(f"✓ Saved HTML: {html_file}")

        # Summary
        logger.info(f"\n✅ Done! Generated enhanced diagrams for {app_code}")
        logger.info(f"   - Mermaid: {mmd_file}")
        logger.info(f"   - HTML: {html_file}")

    def generate_all_applications(self, app_codes: Optional[List[str]] = None):
        """
        Generate diagrams for all applications (or specified subset)

        Args:
            app_codes: Optional list of app codes to generate for
        """
        if app_codes:
            apps = app_codes
        else:
            apps = self.get_available_apps()

        logger.info(f"\n{'='*80}")
        logger.info(f"GENERATING ENHANCED DIAGRAMS FROM JSON")
        logger.info(f"{'='*80}")
        logger.info(f"Applications: {len(apps)}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"JSON directory: {self.json_dir}")
        logger.info("")

        for app_code in apps:
            try:
                self.generate_for_application(app_code)
            except Exception as e:
                logger.error(f"Failed to generate diagrams for {app_code}: {e}")
                import traceback
                traceback.print_exc()

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ ALL DONE!")
        logger.info(f"{'='*80}")
        logger.info(f"Generated diagrams for {len(apps)} applications")
        logger.info(f"Output directory: {self.output_dir}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate enhanced diagrams from JSON enriched flows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--apps',
        nargs='+',
        help="Specific application codes to generate for (default: all)"
    )

    parser.add_argument(
        '--json-dir',
        default="outputs_final/enriched_flows",
        help="Directory containing enriched_flows JSON files (default: outputs_final/enriched_flows)"
    )

    parser.add_argument(
        '--output',
        default="outputs/diagrams_from_json",
        help="Output directory for diagrams (default: outputs/diagrams_from_json)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    # Generate diagrams
    generator = DiagramGeneratorFromJSON(
        json_dir=args.json_dir,
        output_dir=args.output
    )

    generator.generate_all_applications(app_codes=args.apps)


if __name__ == '__main__':
    main()
