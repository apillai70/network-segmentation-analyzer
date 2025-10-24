#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Generate Grouped Diagram from Enriched DataFrame
===========================================================
Shows how to use the enriched flows.csv (18 columns) to generate
diagrams with servers grouped by their destination application.

Example:
  App A -> App B (database servers grouped under App B)
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

def classify_server_tier(hostname: str, ip: str) -> str:
    """
    Classify server into web/app/db/cache tier

    Args:
        hostname: Server hostname
        ip: Server IP

    Returns:
        Tier: 'web', 'app', 'db', 'cache', 'mq', 'unknown'
    """
    hostname_lower = hostname.lower()

    # Database tier
    if any(x in hostname_lower for x in ['db', 'database', 'sql', 'oracle', 'mongo', 'postgres']):
        return 'db'

    # Cache tier
    if any(x in hostname_lower for x in ['redis', 'memcache', 'cache']):
        return 'cache'

    # Message queue tier
    if any(x in hostname_lower for x in ['kafka', 'rabbit', 'mq', 'queue']):
        return 'mq'

    # Web tier
    if any(x in hostname_lower for x in ['web', 'http', 'nginx', 'apache', 'iis']):
        return 'web'

    # App tier
    if any(x in hostname_lower for x in ['app', 'api', 'service', 'srv']):
        return 'app'

    # Check by IP pattern (10.x.x.x patterns)
    if ip.startswith('10.100.'):
        return 'web'  # Assuming 10.100.x.x is web tier
    elif ip.startswith('10.10.'):
        return 'app'  # Assuming 10.10.x.x is app tier
    elif ip.startswith('172.16.'):
        return 'db'   # Assuming 172.16.x.x is db tier

    return 'app'  # Default to app tier


def generate_grouped_diagram(app_name: str, flows_df: pd.DataFrame) -> str:
    """
    Generate Mermaid diagram with servers grouped by tier AND dest app

    Shows internal flow: APP.web -> APP.app -> APP.db -> DEST_APP.servers

    Args:
        app_name: Source application name
        flows_df: DataFrame with 18 enriched columns

    Returns:
        Mermaid diagram string
    """

    # ===========================================================================
    # STEP 1: Classify SOURCE servers by tier (web/app/db)
    # ===========================================================================

    # Get unique source servers
    source_servers = flows_df[['Source IP', 'Source Hostname', 'Source Hostname (Full)', 'Source Is VMware', 'Source DNS Status']].drop_duplicates()

    # Classify each source server by tier
    source_tiers = defaultdict(list)

    for _, row in source_servers.iterrows():
        tier = classify_server_tier(row['Source Hostname'], row['Source IP'])
        source_tiers[tier].append({
            'ip': row['Source IP'],
            'hostname': row['Source Hostname'],
            'hostname_full': row['Source Hostname (Full)'],
            'is_vmware': row['Source Is VMware'],
            'dns_status': row['Source DNS Status']
        })

    # ===========================================================================
    # STEP 2: Analyze flows by direction and destination app
    # ===========================================================================

    # Group 1: Internal flows (same app)
    internal_flows = flows_df[flows_df['Flow Direction'] == 'internal']

    # Group 2: Outbound flows (to other apps) - GROUP BY DEST APP
    outbound_flows = flows_df[flows_df['Flow Direction'] == 'outbound']

    # Group 3: External flows (unknown/internet)
    external_flows = flows_df[flows_df['Flow Direction'] == 'external']

    # ===========================================================================
    # STEP 2: Build groups for destination apps
    # ===========================================================================

    # dest_app_groups: { "ALIBABA": [list of servers], "ANSIBLE": [servers], ... }
    dest_app_groups = defaultdict(list)

    for _, row in outbound_flows.iterrows():
        dest_app = row['Dest App']
        if dest_app:
            server_info = {
                'ip': row['Dest IP'],
                'hostname': row['Dest Hostname'],
                'hostname_full': row['Dest Hostname (Full)'],
                'is_vmware': row['Dest Is VMware'],
                'dns_status': row['Dest DNS Status'],
                'port': row['Port'],
                'protocol': row['Protocol'],
                'bytes': row['Bytes In'] + row['Bytes Out']
            }
            dest_app_groups[dest_app].append(server_info)

    # ===========================================================================
    # STEP 3: Generate Mermaid diagram with subgraphs for each Dest App
    # ===========================================================================

    mermaid = "graph TB\n"
    mermaid += f"    %% Application: {app_name}\n\n"

    # ===========================================================================
    # Show SOURCE tiers (web/app/db) as subgraphs
    # ===========================================================================

    tier_order = ['web', 'app', 'db', 'cache', 'mq']  # Display order
    tier_labels = {
        'web': 'Web Tier',
        'app': 'App Tier',
        'db': 'Database Tier',
        'cache': 'Cache Tier',
        'mq': 'Message Queue'
    }

    source_tier_nodes = {}  # Track node IDs for each tier

    for tier in tier_order:
        if tier not in source_tiers:
            continue

        servers = source_tiers[tier]
        tier_label = tier_labels.get(tier, tier.upper())

        mermaid += f"    subgraph {app_name}_{tier.upper()}[\"{app_name} - {tier_label}\"]\n"
        mermaid += f"        direction TB\n"

        for idx, server in enumerate(servers):
            node_id = f"SRC_{tier.upper()}_{idx}"
            source_tier_nodes.setdefault(tier, []).append(node_id)

            hostname = server['hostname_full']
            ip = server['ip']
            dns_status = server['dns_status']
            is_vmware = server['is_vmware']

            # Determine style
            if is_vmware:
                shape_start, shape_end = "[(", ")]"
                style_class = "vmware"
            elif dns_status in ['NXDOMAIN', 'unknown']:
                shape_start, shape_end = "[", "]"
                style_class = "redborder"
            else:
                shape_start, shape_end = "[", "]"
                style_class = "normal"

            mermaid += f"        {node_id}{shape_start}\"{hostname}<br/>{ip}\"{shape_end}:::{style_class}\n"

        mermaid += f"    end\n\n"

    # Connect tiers in flow order: web -> app -> db
    if 'web' in source_tier_nodes and 'app' in source_tier_nodes:
        for web_node in source_tier_nodes['web']:
            for app_node in source_tier_nodes['app'][:1]:  # Connect to first app node
                mermaid += f"    {web_node} -->|internal| {app_node}\n"

    if 'app' in source_tier_nodes and 'db' in source_tier_nodes:
        for app_node in source_tier_nodes['app']:
            for db_node in source_tier_nodes['db'][:1]:  # Connect to first db node
                mermaid += f"    {app_node} -->|internal| {db_node}\n"

    mermaid += "\n"

    # ===========================================================================
    # Group by Dest App using subgraphs
    # ===========================================================================

    for dest_app, servers in dest_app_groups.items():
        # Create subgraph for this destination app
        mermaid += f"    subgraph {dest_app}_SERVERS[\"{dest_app} Servers\"]\n"
        mermaid += f"        direction TB\n"

        # Add each server in this group
        for idx, server in enumerate(servers):
            node_id = f"{dest_app}_SRV_{idx}"
            hostname = server['hostname_full']
            ip = server['ip']
            dns_status = server['dns_status']
            is_vmware = server['is_vmware']

            # Determine shape and style based on VMware and DNS status
            if is_vmware:
                shape_start, shape_end = "[(", ")]"  # Cylinder for VMware
                style_class = "vmware"
            elif dns_status in ['NXDOMAIN', 'unknown']:
                shape_start, shape_end = "[", "]"  # Rectangle with RED BORDER
                style_class = "redborder"
            else:
                shape_start, shape_end = "[", "]"  # Normal rectangle
                style_class = "normal"

            # Add node
            mermaid += f"        {node_id}{shape_start}\"{hostname}<br/>{ip}\"{shape_end}:::{style_class}\n"

        mermaid += f"    end\n\n"

        # Connect from last source tier (db or app) to this dest app group
        # Determine which tier initiates outbound connections
        last_tier = None
        if 'db' in source_tier_nodes:
            last_tier = 'db'
        elif 'app' in source_tier_nodes:
            last_tier = 'app'
        elif 'web' in source_tier_nodes:
            last_tier = 'web'

        if last_tier and last_tier in source_tier_nodes:
            # Connect from first node of last tier
            source_node = source_tier_nodes[last_tier][0]
            mermaid += f"    {source_node} -->|depends on| {dest_app}_SERVERS\n"

    # ===========================================================================
    # Add external destinations (internet-facing, no app grouping)
    # ===========================================================================

    if len(external_flows) > 0:
        mermaid += f"\n    subgraph EXTERNAL[\"External / Internet\"]\n"
        mermaid += f"        direction TB\n"

        external_dests = external_flows[['Dest IP', 'Dest Hostname', 'Dest DNS Status']].drop_duplicates().head(5)

        for idx, row in external_dests.iterrows():
            node_id = f"EXT_{idx}"
            dns_status = row['Dest DNS Status']
            style_class = "redborder" if dns_status in ['NXDOMAIN', 'unknown'] else "external"

            mermaid += f"        {node_id}[\"{row['Dest Hostname']}<br/>{row['Dest IP']}\"]:::{style_class}\n"

        mermaid += f"    end\n\n"

        # Connect from last source tier to external
        if last_tier and last_tier in source_tier_nodes:
            source_node = source_tier_nodes[last_tier][0]
            mermaid += f"    {source_node} -->|external| EXTERNAL\n"

    # ===========================================================================
    # Add legend with styles
    # ===========================================================================

    mermaid += "\n    %% Styles\n"
    mermaid += "    classDef sourceapp fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff\n"
    mermaid += "    classDef normal fill:#E3F2FD,stroke:#1976D2,stroke-width:2px\n"
    mermaid += "    classDef vmware fill:#FFF3E0,stroke:#F57C00,stroke-width:2px\n"
    mermaid += "    classDef redborder fill:#FFEBEE,stroke:#F44336,stroke-width:3px\n"
    mermaid += "    classDef internal fill:#F1F8E9,stroke:#689F38,stroke-width:2px\n"
    mermaid += "    classDef external fill:#FCE4EC,stroke:#C2185B,stroke-width:2px\n"

    return mermaid


def main():
    """Example usage"""

    # Read enriched flows.csv
    app_name = "ANSIBLE"
    flows_csv = Path(f'persistent_data/applications/{app_name}/flows.csv')

    if not flows_csv.exists():
        print(f"File not found: {flows_csv}")
        return

    df = pd.read_csv(flows_csv)
    print(f"Loaded {len(df)} flows for {app_name}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Generate diagram
    diagram = generate_grouped_diagram(app_name, df)

    # Save to file
    output_file = Path(f'outputs/{app_name}_grouped_diagram.mmd')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(diagram)

    print(f"Generated grouped diagram: {output_file}")
    print()
    print("=" * 80)
    print("DIAGRAM PREVIEW:")
    print("=" * 80)
    print(diagram)
    print()

    # Show summary
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)

    # Count flows by direction
    print(f"Internal flows: {len(df[df['Flow Direction'] == 'internal'])}")
    print(f"Outbound flows: {len(df[df['Flow Direction'] == 'outbound'])}")
    print(f"External flows: {len(df[df['Flow Direction'] == 'external'])}")
    print()

    # Show destination apps
    dest_apps = df[df['Dest App'].notna()]['Dest App'].unique()
    print(f"Destination apps ({len(dest_apps)}):")
    for dest_app in dest_apps:
        count = len(df[df['Dest App'] == dest_app])
        print(f"  - {dest_app}: {count} flows")


if __name__ == '__main__':
    main()
