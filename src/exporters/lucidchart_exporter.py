# -*- coding: utf-8 -*-
"""
Lucidchart Exporter
===================
Exports network topology to Lucidchart-compatible CSV format

Features:
- Node export with properties
- Edge/connection export
- Zone-based styling
- Hierarchical layout hints

Author: Enterprise Security Team
Version: 3.0
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LucidchartExporter:
    """
    Export network topology to Lucidchart CSV format

    Lucidchart CSV Import Format:
    - Nodes: ID, Label, Type, Shape, Color, etc.
    - Edges: Source, Target, Label, Style, etc.
    """

    # Zone color mapping (compatible with Lucidchart)
    ZONE_COLORS = {
        'WEB_TIER': '#4CAF50',          # Green
        'APP_TIER': '#2196F3',          # Blue
        'DATA_TIER': '#FF9800',         # Orange
        'MESSAGING_TIER': '#9C27B0',    # Purple
        'CACHE_TIER': '#00BCD4',        # Cyan
        'MANAGEMENT_TIER': '#FFEB3B',   # Yellow
        'INFRASTRUCTURE': '#F44336',     # Red
        'EXTERNAL': '#607D8B',          # Grey
        'DMZ': '#FF5722',               # Deep Orange
        'UNKNOWN': '#9E9E9E'            # Grey
    }

    # Shape mapping by app type
    SHAPE_MAPPING = {
        'web': 'Process',
        'api': 'Process',
        'database': 'DataStore',
        'datamart': 'DataStore',
        'cache': 'DataStore',
        'messaging': 'Queue',
        'management': 'Cloud',
        'payment': 'Shield',
        'default': 'Rectangle'
    }

    def __init__(self, persistence_manager=None, output_dir='./visualizations'):
        """
        Initialize Lucidchart exporter

        Args:
            persistence_manager: Optional database connection
            output_dir: Directory for output files
        """
        self.pm = persistence_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_from_topology_json(self, topology_json_path: str, output_path: Optional[str] = None) -> str:
        """
        Export from incremental_topology.json file

        Args:
            topology_json_path: Path to topology JSON file
            output_path: Optional output path (auto-generated if None)

        Returns:
            Path to generated CSV file
        """
        logger.info(f"[LUCID] Exporting from {topology_json_path}...")

        # Load topology data
        with open(topology_json_path, 'r') as f:
            topology_data = json.load(f)

        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f'lucidchart_export_{timestamp}.csv'
        else:
            output_path = Path(output_path)

        # Extract nodes and edges
        nodes = []
        edges = []

        for app_id, app_data in topology_data.get('topology', {}).items():
            # Create node
            node = {
                'Id': app_id,
                'Name': app_id,
                'Type': app_data.get('app_type', 'application'),
                'Zone': app_data.get('security_zone', 'UNKNOWN'),
                'Shape': self._get_shape(app_data.get('app_type', 'default')),
                'Color': self.ZONE_COLORS.get(app_data.get('security_zone', 'UNKNOWN'), '#9E9E9E'),
                'Confidence': f"{app_data.get('confidence', 0.0):.2f}",
                'RiskLevel': app_data.get('risk_level', 'UNKNOWN'),
                'Protocols': ', '.join(app_data.get('typical_protocols', [])),
                'Ports': ', '.join(map(str, app_data.get('typical_ports', [])))
            }
            nodes.append(node)

            # Create edges from dependencies
            for dep in app_data.get('predicted_dependencies', []):
                edge = {
                    'Source': app_id,
                    'Target': dep,
                    'Label': 'depends on',
                    'Style': 'solid',
                    'Direction': 'forward',
                    'Color': '#999999'
                }
                edges.append(edge)

        # Write to CSV
        self._write_lucidchart_csv(nodes, edges, output_path)

        logger.info(f"[OK] Lucidchart export saved: {output_path}")
        return str(output_path)

    def export_from_database(self, output_path: Optional[str] = None) -> str:
        """
        Export directly from database

        Args:
            output_path: Optional output path (auto-generated if None)

        Returns:
            Path to generated CSV file
        """
        if self.pm is None:
            raise ValueError("PersistenceManager required for database export")

        logger.info("[LUCID] Exporting from database...")

        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f'lucidchart_export_{timestamp}.csv'
        else:
            output_path = Path(output_path)

        # Get nodes from database
        nodes_df = self.pm.get_all_nodes()
        flows_df = self.pm.get_all_flows()

        # Build nodes list
        nodes = []
        for _, node_row in nodes_df.iterrows():
            node = {
                'Id': node_row['ip_address'],
                'Name': node_row['hostname'] or node_row['ip_address'],
                'Type': node_row['infrastructure_type'] or 'server',
                'Zone': node_row['micro_segment'] or 'UNKNOWN',
                'Shape': self._get_shape(node_row['infrastructure_type'] or 'default'),
                'Color': self.ZONE_COLORS.get(node_row['micro_segment'], '#9E9E9E'),
                'Role': node_row['role'] or '',
                'Cluster': str(node_row['cluster_id']) if node_row['cluster_id'] else ''
            }
            nodes.append(node)

        # Build edges from flows
        edges = []
        edge_counts = flows_df.groupby(['source_ip', 'destination_ip']).size().reset_index(name='count')

        for _, edge_row in edge_counts.iterrows():
            edge = {
                'Source': edge_row['source_ip'],
                'Target': edge_row['destination_ip'],
                'Label': f"{edge_row['count']} flows",
                'Style': 'solid',
                'Direction': 'forward',
                'Color': '#999999',
                'Weight': str(edge_row['count'])
            }
            edges.append(edge)

        # Write to CSV
        self._write_lucidchart_csv(nodes, edges, output_path)

        logger.info(f"[OK] Lucidchart export saved: {output_path}")
        return str(output_path)

    def _get_shape(self, app_type: str) -> str:
        """Get Lucidchart shape for app type"""
        return self.SHAPE_MAPPING.get(app_type.lower(), self.SHAPE_MAPPING['default'])

    def _write_lucidchart_csv(self, nodes: List[Dict], edges: List[Dict], output_path: Path):
        """
        Write nodes and edges to Lucidchart-compatible CSV

        Format:
        - Section 1: Nodes with properties
        - Section 2: Edges with properties
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header comment
            writer.writerow(['# Network Segmentation Analyzer - Lucidchart Import'])
            writer.writerow(['# Generated:', datetime.now().isoformat()])
            writer.writerow(['# Format: Nodes first, then Edges'])
            writer.writerow([])

            # Write nodes section
            writer.writerow(['# NODES'])
            if nodes:
                # Node headers
                node_headers = list(nodes[0].keys())
                writer.writerow(node_headers)

                # Node data
                for node in nodes:
                    writer.writerow([node.get(h, '') for h in node_headers])

            writer.writerow([])

            # Write edges section
            writer.writerow(['# EDGES'])
            if edges:
                # Edge headers
                edge_headers = list(edges[0].keys())
                writer.writerow(edge_headers)

                # Edge data
                for edge in edges:
                    writer.writerow([edge.get(h, '') for h in edge_headers])

    def export_with_zones_as_containers(self, topology_json_path: str, output_path: Optional[str] = None) -> str:
        """
        Export with security zones as containers (groups)

        This creates a hierarchical structure where zones are containers
        and applications are grouped within them.

        Args:
            topology_json_path: Path to topology JSON file
            output_path: Optional output path

        Returns:
            Path to generated CSV file
        """
        logger.info(f"[LUCID] Exporting with zone containers from {topology_json_path}...")

        # Load topology data
        with open(topology_json_path, 'r') as f:
            topology_data = json.load(f)

        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f'lucidchart_zones_{timestamp}.csv'
        else:
            output_path = Path(output_path)

        # Group apps by zone
        zones = {}
        for app_id, app_data in topology_data.get('topology', {}).items():
            zone = app_data.get('security_zone', 'UNKNOWN')
            if zone not in zones:
                zones[zone] = []
            zones[zone].append((app_id, app_data))

        # Create nodes: zones as containers + apps as children
        nodes = []
        edges = []

        # Add zone containers
        for zone_name in zones.keys():
            zone_node = {
                'Id': f'ZONE_{zone_name}',
                'Name': zone_name,
                'Type': 'Zone',
                'Shape': 'Container',
                'Color': self.ZONE_COLORS.get(zone_name, '#9E9E9E'),
                'IsContainer': 'true'
            }
            nodes.append(zone_node)

        # Add applications within zones
        for zone_name, apps in zones.items():
            for app_id, app_data in apps:
                app_node = {
                    'Id': app_id,
                    'Name': app_id,
                    'Type': app_data.get('app_type', 'application'),
                    'Zone': zone_name,
                    'ParentId': f'ZONE_{zone_name}',  # Child of zone container
                    'Shape': self._get_shape(app_data.get('app_type', 'default')),
                    'Color': self.ZONE_COLORS.get(zone_name, '#9E9E9E'),
                    'Confidence': f"{app_data.get('confidence', 0.0):.2f}",
                    'RiskLevel': app_data.get('risk_level', 'UNKNOWN')
                }
                nodes.append(app_node)

                # Add dependency edges
                for dep in app_data.get('predicted_dependencies', []):
                    edge = {
                        'Source': app_id,
                        'Target': dep,
                        'Label': 'depends on',
                        'Style': 'solid',
                        'Direction': 'forward'
                    }
                    edges.append(edge)

        # Write to CSV
        self._write_lucidchart_csv(nodes, edges, output_path)

        logger.info(f"[OK] Lucidchart zone export saved: {output_path}")
        return str(output_path)


def export_lucidchart_from_json(topology_json_path: str, output_path: Optional[str] = None,
                                 with_zones: bool = False) -> str:
    """
    Convenience function to export Lucidchart CSV from topology JSON

    Args:
        topology_json_path: Path to incremental_topology.json
        output_path: Optional output path
        with_zones: If True, create zone containers

    Returns:
        Path to generated CSV file
    """
    exporter = LucidchartExporter()

    if with_zones:
        return exporter.export_with_zones_as_containers(topology_json_path, output_path)
    else:
        return exporter.export_from_topology_json(topology_json_path, output_path)


if __name__ == '__main__':
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Export topology to Lucidchart CSV')
    parser.add_argument('--topology', required=True, help='Path to incremental_topology.json')
    parser.add_argument('--output', help='Output CSV path (optional)')
    parser.add_argument('--zones', action='store_true', help='Create zone containers')

    args = parser.parse_args()

    output_path = export_lucidchart_from_json(
        args.topology,
        args.output,
        with_zones=args.zones
    )

    print(f"[OK] Lucidchart export created: {output_path}")
    print("\nTo import into Lucidchart:")
    print("1. Open Lucidchart")
    print("2. Go to File → Import Data")
    print("3. Select 'Import from CSV'")
    print(f"4. Upload {output_path}")
    print("5. Map columns and generate diagram")
