#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic Flow Data Generator
==============================
Generates realistic network flow files for all applications in applicationList.csv

Features:
- Realistic traffic patterns based on app type
- IPv4 and IPv6 support
- Smart recognition of application types (DM_* for datamarts, etc.)
- Consistent patterns across related apps
- Realistic protocols and ports

Usage:
    python scripts/generate_synthetic_flows.py
    python scripts/generate_synthetic_flows.py --num-apps 140
    python scripts/generate_synthetic_flows.py --output-dir data/input
"""

import sys
import pandas as pd
import numpy as np
import random
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import logging

# Force UTF-8 encoding for console output (Windows fix)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyntheticFlowGenerator:
    """
    Generates realistic network flow data for applications

    Smart detection of:
    - Datamarts (DM_*) → heavy database/analytics traffic
    - Web apps (*WEB*, *UI*) → HTTP/HTTPS traffic
    - APIs (*API*, *SVC*) → REST/SOAP traffic
    - Databases (*DB*, *SQL*) → database protocols
    - Payment apps (*PAY*, *BILL*) → secure external connections
    """

    def __init__(self, seed=42):
        """Initialize generator with random seed for reproducibility"""
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

        # IP ranges for different zones
        self.ip_ranges = {
            'WEB_TIER': '10.164.144.0/24',
            'APP_TIER': '10.164.145.0/24',
            'DATA_TIER': '10.164.105.0/24',
            'CACHE_TIER': '10.164.116.0/24',
            'MESSAGING_TIER': '10.165.116.0/24',
            'MANAGEMENT_TIER': '10.100.160.0/24',
            'EXTERNAL': '10.100.246.0/24'
        }

        # IPv6 ranges
        self.ipv6_ranges = {
            'WEB_TIER': '2001:0db8:ea19:a1e1::/64',
            'APP_TIER': '2001:0db8:2bda:f8d3::/64',
            'DATA_TIER': '2001:0db8:548b:87b5::/64',
            'CACHE_TIER': '2001:0db8:2582:6d22::/64',
            'MESSAGING_TIER': '2001:0db8:4c3a:9f21::/64',
            'EXTERNAL': '2001:0db8:1a2b:3c4d::/64'
        }

        # Protocol patterns by app type
        self.protocol_patterns = {
            'web': ['HTTP', 'HTTPS', 'HTTP2-SSL', 'HTTP-TUNNEL/HTTPS'],
            'api': ['HTTPS', 'HTTP2-SSL', 'TLS', 'REST', 'SOAP'],
            'database': ['DB2', 'ORACLE', 'SQL', 'POSTGRESQL', 'MYSQL', 'TLS'],
            'datamart': ['DB2', 'ORACLE', 'SQL', 'ODBC', 'JDBC', 'TLS'],
            'cache': ['REDIS', 'MEMCACHED', 'TCP'],
            'messaging': ['IBMMQ', 'KAFKA', 'RABBITMQ', 'AMQP', 'TCP'],
            'payment': ['HTTPS', 'TLS', 'HTTP2-SSL'],
            'default': ['TCP', 'HTTP', 'HTTPS']
        }

        # Port patterns
        self.common_ports = {
            'HTTP': [80, 8080, 8081],
            'HTTPS': [443, 8443],
            'DATABASE': [1521, 3306, 5432, 1433, 27017],
            'CACHE': [6379, 11211],
            'MESSAGING': [9092, 5672, 15672],
            'LDAP': [389, 636],
            'SSH': [22],
            'DNS': [53]
        }

        logger.info("✓ Synthetic Flow Generator initialized")

    def identify_app_type(self, app_id: str, app_name: str) -> str:
        """
        Identify application type from ID and name

        Special patterns:
        - DM_* → datamart
        - *API*, *SVC* → api
        - *WEB*, *UI*, *FRONT* → web
        - *DB*, *SQL*, *DATABASE* → database
        - *PAY*, *BILL*, *CARD* → payment
        - *CACHE*, *REDIS* → cache
        - *KAFKA*, *MQ*, *QUEUE* → messaging
        """
        app_id_lower = app_id.lower()
        app_name_lower = app_name.lower()

        # Datamarts (priority)
        if app_id.startswith('DM_'):
            return 'datamart'

        # Web applications
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['web', 'ui', 'frontend', 'portal', 'dashboard']):
            return 'web'

        # APIs
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['api', 'svc', 'service', 'gateway']):
            return 'api'

        # Databases
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['db', 'database', 'sql', 'oracle', 'postgres', 'mysql']):
            return 'database'

        # Payment/Financial
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['pay', 'bill', 'card', 'transaction', 'financial']):
            return 'payment'

        # Cache
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['cache', 'redis', 'memcache']):
            return 'cache'

        # Messaging
        if any(kw in app_id_lower or kw in app_name_lower
               for kw in ['kafka', 'mq', 'queue', 'message', 'broker']):
            return 'messaging'

        return 'default'

    def generate_ip(self, zone: str, use_ipv6: bool = False) -> str:
        """Generate random IP in specified zone"""
        if use_ipv6:
            network = ipaddress.IPv6Network(self.ipv6_ranges.get(zone, self.ipv6_ranges['APP_TIER']))
            # Generate random IP in range
            random_int = random.randint(0, 2**64 - 1)
            ip = ipaddress.IPv6Address(int(network.network_address) + random_int)
            return str(ip)
        else:
            network = ipaddress.IPv4Network(self.ip_ranges.get(zone, self.ip_ranges['APP_TIER']))
            random_ip = random.randint(0, network.num_addresses - 1)
            ip = network.network_address + random_ip
            return str(ip)

    def generate_flows_for_app(
        self,
        app_id: str,
        app_name: str,
        num_flows: int = None,
        ipv6_ratio: float = 0.15
    ) -> pd.DataFrame:
        """
        Generate realistic flows for an application

        Args:
            app_id: Application ID (e.g., 'XECHK', 'DM_BLZE')
            app_name: Application name
            num_flows: Number of flows (auto-calculated if None)
            ipv6_ratio: Ratio of IPv6 flows (default 15%)

        Returns:
            DataFrame with flow records
        """
        app_type = self.identify_app_type(app_id, app_name)

        # Determine number of flows based on app type
        if num_flows is None:
            flow_counts = {
                'datamart': (80, 200),      # High database traffic
                'web': (50, 150),           # Moderate web traffic
                'api': (60, 180),           # Moderate API traffic
                'database': (100, 250),     # High query traffic
                'payment': (40, 100),       # Lower but secure traffic
                'cache': (30, 80),          # Moderate cache traffic
                'messaging': (50, 120),     # Moderate message traffic
                'default': (30, 100)        # Default range
            }
            min_flows, max_flows = flow_counts[app_type]
            num_flows = random.randint(min_flows, max_flows)

        flows = []

        # Determine primary zone for this app
        zone_mapping = {
            'datamart': 'DATA_TIER',
            'web': 'WEB_TIER',
            'api': 'APP_TIER',
            'database': 'DATA_TIER',
            'payment': 'APP_TIER',
            'cache': 'CACHE_TIER',
            'messaging': 'MESSAGING_TIER',
            'default': 'APP_TIER'
        }
        primary_zone = zone_mapping[app_type]

        # Generate flows
        for i in range(num_flows):
            use_ipv6 = random.random() < ipv6_ratio

            # Source and destination based on app type
            if app_type == 'datamart':
                # Datamarts receive data from apps, query databases
                src_zone = random.choice(['APP_TIER', 'DATA_TIER', 'EXTERNAL'])
                dst_zone = 'DATA_TIER'
            elif app_type == 'web':
                # Web apps receive from external, call APIs
                src_zone = random.choice(['EXTERNAL', 'EXTERNAL', 'WEB_TIER'])
                dst_zone = random.choice(['WEB_TIER', 'APP_TIER'])
            elif app_type == 'api':
                # APIs receive from web/other APIs, call databases
                src_zone = random.choice(['WEB_TIER', 'APP_TIER', 'EXTERNAL'])
                dst_zone = random.choice(['APP_TIER', 'DATA_TIER', 'CACHE_TIER'])
            elif app_type == 'database':
                # Databases receive queries from apps
                src_zone = random.choice(['APP_TIER', 'DATA_TIER'])
                dst_zone = 'DATA_TIER'
            elif app_type == 'payment':
                # Payment apps call external gateways and databases
                src_zone = 'APP_TIER'
                dst_zone = random.choice(['DATA_TIER', 'EXTERNAL', 'APP_TIER'])
            else:
                src_zone = random.choice(list(self.ip_ranges.keys()))
                dst_zone = random.choice(list(self.ip_ranges.keys()))

            src_ip = self.generate_ip(src_zone, use_ipv6)
            dst_ip = self.generate_ip(dst_zone, use_ipv6)

            # Protocol selection based on app type
            protocols = self.protocol_patterns.get(app_type, self.protocol_patterns['default'])
            protocol = random.choice(protocols)

            # Port selection
            if protocol in ['HTTP', 'HTTPS']:
                port = random.choice(self.common_ports.get(protocol.upper(), [80]))
            elif 'SQL' in protocol or 'DB' in protocol or app_type in ['database', 'datamart']:
                port = random.choice(self.common_ports['DATABASE'])
            elif protocol == 'REDIS':
                port = 6379
            elif protocol in ['KAFKA', 'RABBITMQ', 'IBMMQ']:
                port = random.choice(self.common_ports['MESSAGING'])
            elif protocol == 'LDAP':
                port = random.choice(self.common_ports['LDAP'])
            elif random.random() < 0.7:  # 70% have explicit port
                port = random.choice([80, 443, 8080, 8443, 1521, 3306, 5432, 22, 389])
            else:
                port = ''

            # Traffic volumes (bytes in/out)
            if app_type == 'datamart':
                # High data transfer for datamarts
                bytes_in = random.randint(1000000, 5000000)
                bytes_out = random.randint(500000, 4000000)
            elif app_type == 'web':
                # Moderate web traffic
                bytes_in = random.randint(500000, 3000000)
                bytes_out = random.randint(800000, 4000000)
            elif app_type == 'database':
                # High query traffic
                bytes_in = random.randint(800000, 4000000)
                bytes_out = random.randint(1000000, 5000000)
            else:
                bytes_in = random.randint(100000, 4000000)
                bytes_out = random.randint(100000, 4000000)

            # Sometimes have zero traffic (connection setup only)
            if random.random() < 0.1:
                bytes_in, bytes_out = 0, 0

            flow = {
                'App': app_id,
                'Source IP': src_ip,
                'Source Hostname': '',  # Usually empty
                'Dest IP': dst_ip,
                'Dest Hostname': '',    # Usually empty
                'Port': port,
                'Protocol': protocol,
                'Bytes In': bytes_in,
                'Bytes Out': bytes_out
            }

            flows.append(flow)

        df = pd.DataFrame(flows)

        logger.info(f"  Generated {len(df)} flows for {app_id} ({app_type})")
        logger.info(f"    IPv6: {len(df[df['Source IP'].str.contains(':')])} flows")
        logger.info(f"    Protocols: {df['Protocol'].unique()[:5]}")

        return df

    def generate_all_apps(
        self,
        app_list_path: str,
        output_dir: str,
        num_apps: int = 140,
        start_index: int = 0
    ):
        """
        Generate flow files for multiple applications

        Args:
            app_list_path: Path to applicationList.csv
            output_dir: Directory to save generated files
            num_apps: Number of apps to generate (default 140)
            start_index: Starting index in app list (default 0)
        """
        logger.info(f"🔥 Generating synthetic flows for {num_apps} applications...")

        # Load application list (try multiple encodings)
        try:
            apps_df = pd.read_csv(app_list_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                apps_df = pd.read_csv(app_list_path, encoding='latin-1')
                logger.info("  Used latin-1 encoding for application list")
            except UnicodeDecodeError:
                apps_df = pd.read_csv(app_list_path, encoding='cp1252')
                logger.info("  Used Windows-1252 encoding for application list")

        logger.info(f"  Loaded {len(apps_df)} applications from catalog")

        # Select apps to generate
        selected_apps = apps_df.iloc[start_index:start_index + num_apps]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_count = 0

        for idx, row in selected_apps.iterrows():
            app_id = row['app_id']
            app_name = row['app_name']

            # Generate flows
            flows_df = self.generate_flows_for_app(app_id, app_name)

            # Save to file
            output_file = output_path / f'App_Code_{app_id}.csv'
            flows_df.to_csv(output_file, index=False)

            generated_count += 1

            if generated_count % 10 == 0:
                logger.info(f"  Progress: {generated_count}/{num_apps} files generated")

        logger.info(f"\n✅ Generated {generated_count} application flow files")
        logger.info(f"  Output directory: {output_path}")
        logger.info(f"  File naming: App_Code_{{APP_ID}}.csv")

        # Generate summary
        summary = {
            'total_apps': generated_count,
            'output_dir': str(output_path),
            'timestamp': datetime.now().isoformat(),
            'apps_generated': [f'App_Code_{row["app_id"]}.csv' for _, row in selected_apps.iterrows()]
        }

        summary_file = output_path / 'generation_summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"  Summary: {summary_file}")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate synthetic network flow data')
    parser.add_argument(
        '--app-list',
        default='data/input/applicationList.csv',
        help='Path to applicationList.csv'
    )
    parser.add_argument(
        '--output-dir',
        default='data/input',
        help='Output directory for flow files'
    )
    parser.add_argument(
        '--num-apps',
        type=int,
        default=140,
        help='Number of applications to generate (default: 140)'
    )
    parser.add_argument(
        '--start-index',
        type=int,
        default=0,
        help='Starting index in app list (default: 0)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    # Generate flows
    generator = SyntheticFlowGenerator(seed=args.seed)
    generator.generate_all_apps(
        app_list_path=args.app_list,
        output_dir=args.output_dir,
        num_apps=args.num_apps,
        start_index=args.start_index
    )


if __name__ == '__main__':
    main()
