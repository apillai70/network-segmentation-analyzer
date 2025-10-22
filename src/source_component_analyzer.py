#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Source Component Analyzer
=========================
Analyzes source IPs per application to identify component types (web, app, db)
based on ports and protocols used.

Features:
- Identifies unique source IPs per application
- Classifies sources by component type (web, app, database)
- Analyzes port patterns and protocol usage
- Generates component composition reports
"""

import logging
from collections import defaultdict
from typing import List, Dict, Set
from src.server_classifier import ServerClassifier

logger = logging.getLogger(__name__)


class SourceComponentAnalyzer:
    """Analyzes source IPs to determine component types"""

    # Port-based component classification
    PORT_PATTERNS = {
        'web': {80, 443, 8080, 8443, 8888, 9000},
        'app': {8000, 8001, 8002, 8003, 8004, 8005, 8081, 8082, 9001, 9002},
        'database': {1433, 1521, 3306, 5432, 27017, 6379}  # SQL Server, Oracle, MySQL, PostgreSQL, MongoDB, Redis
    }

    # Protocol-based component classification
    PROTOCOL_PATTERNS = {
        'web': {'HTTP', 'HTTPS', 'SSL', 'TLS'},
        'app': {'TCP', 'gRPC', 'SOAP', 'REST'},
        'database': {'TDS', 'TNS', 'MySQL', 'PostgreSQL', 'MongoDB'}
    }

    def __init__(self):
        """Initialize source component analyzer"""
        self.classifier = ServerClassifier()
        logger.info("SourceComponentAnalyzer initialized")

    def analyze_source_components(self, app_name: str, flow_records: List,
                                  hostname_resolver=None) -> Dict:
        """
        Analyze source IPs to identify component types

        Args:
            app_name: Application name
            flow_records: List of FlowRecord objects
            hostname_resolver: Optional hostname resolver

        Returns:
            Dict with source analysis results
        """
        logger.info(f"Analyzing source components for: {app_name}")

        # Track source IPs with their characteristics
        source_ips = defaultdict(lambda: {
            'hostname': None,
            'ports': set(),
            'protocols': set(),
            'dst_ips': set(),
            'bytes_sent': 0,
            'flow_count': 0,
            'component_type': None,
            'server_classification': None
        })

        # Collect source IP information
        for record in flow_records:
            if not record.src_ip or record.src_ip == 'nan':
                continue

            src_ip = record.src_ip

            # Resolve hostname if available
            if hostname_resolver and not source_ips[src_ip]['hostname']:
                source_ips[src_ip]['hostname'] = hostname_resolver.resolve(src_ip)

            # Collect characteristics
            if hasattr(record, 'dst_port') and record.dst_port:
                try:
                    source_ips[src_ip]['ports'].add(int(record.dst_port))
                except:
                    pass

            if hasattr(record, 'protocol') and record.protocol:
                source_ips[src_ip]['protocols'].add(record.protocol.upper())

            if hasattr(record, 'dst_ip') and record.dst_ip:
                source_ips[src_ip]['dst_ips'].add(record.dst_ip)

            source_ips[src_ip]['bytes_sent'] += getattr(record, 'bytes', 0)
            source_ips[src_ip]['flow_count'] += 1

        # Classify each source IP
        for src_ip, data in source_ips.items():
            # Classify by ports and protocols
            data['component_type'] = self._classify_component(
                data['ports'],
                data['protocols']
            )

            # Use server classifier if hostname available
            if data['hostname']:
                data['server_classification'] = self.classifier.classify_server(
                    hostname=data['hostname'],
                    protocols=list(data['protocols']),
                    ports=list(data['ports'])
                )

        # Group by component type
        by_component = {
            'web': [],
            'app': [],
            'database': [],
            'unknown': []
        }

        for src_ip, data in source_ips.items():
            component_type = data['component_type'] or 'unknown'
            by_component[component_type].append({
                'ip': src_ip,
                'hostname': data['hostname'] or src_ip,
                'ports': sorted(data['ports']),
                'protocols': sorted(data['protocols']),
                'destinations': len(data['dst_ips']),
                'bytes_sent': data['bytes_sent'],
                'flow_count': data['flow_count'],
                'server_type': data['server_classification']['type'] if data['server_classification'] else None
            })

        # Sort each component by traffic volume
        for component in by_component:
            by_component[component].sort(
                key=lambda x: (x['bytes_sent'], x['flow_count']),
                reverse=True
            )

        # Detect load balancers in destination flows
        load_balancer_detected = self._detect_load_balancers(flow_records, hostname_resolver)

        # Generate summary statistics
        summary = {
            'app_name': app_name,
            'total_source_ips': len(source_ips),
            'by_component': by_component,
            'component_counts': {
                'web': len(by_component['web']),
                'app': len(by_component['app']),
                'database': len(by_component['database']),
                'unknown': len(by_component['unknown'])
            },
            'load_balancer_detected': load_balancer_detected,
            'architecture_pattern': self._determine_architecture_pattern(by_component, load_balancer_detected)
        }

        logger.info(f"  Source IPs: {summary['total_source_ips']}")
        logger.info(f"    Web: {summary['component_counts']['web']}")
        logger.info(f"    App: {summary['component_counts']['app']}")
        logger.info(f"    Database: {summary['component_counts']['database']}")
        logger.info(f"    Unknown: {summary['component_counts']['unknown']}")

        if load_balancer_detected:
            logger.info(f"  ⚠️ Load Balancer Detected: {len(load_balancer_detected)} found")
            logger.info(f"  Architecture Pattern: {summary['architecture_pattern']}")

        return summary

    def _classify_component(self, ports: Set[int], protocols: Set[str]) -> str:
        """
        Classify component type based on ports and protocols

        Args:
            ports: Set of ports used
            protocols: Set of protocols used

        Returns:
            Component type: 'web', 'app', 'database', or None
        """
        if not ports and not protocols:
            return None

        scores = {'web': 0, 'app': 0, 'database': 0}

        # Score by ports
        for component, port_set in self.PORT_PATTERNS.items():
            matches = len(ports & port_set)
            if matches > 0:
                scores[component] += matches * 2  # Weight ports heavily

        # Score by protocols
        for component, proto_set in self.PROTOCOL_PATTERNS.items():
            matches = len(protocols & proto_set)
            if matches > 0:
                scores[component] += matches

        # Return component with highest score
        if sum(scores.values()) == 0:
            return None

        return max(scores.items(), key=lambda x: x[1])[0]

    def _detect_load_balancers(self, flow_records: List, hostname_resolver=None) -> List[Dict]:
        """
        Detect load balancers in destination flows

        Args:
            flow_records: List of FlowRecord objects
            hostname_resolver: Optional hostname resolver

        Returns:
            List of detected load balancers with details
        """
        load_balancers = []
        dest_servers = defaultdict(lambda: {
            'hostname': None,
            'protocols': set(),
            'ports': set(),
            'flow_count': 0
        })

        # Collect destination information
        for record in flow_records:
            if not record.dst_ip or record.dst_ip == 'nan':
                continue

            dst_ip = record.dst_ip

            if hostname_resolver and not dest_servers[dst_ip]['hostname']:
                dest_servers[dst_ip]['hostname'] = hostname_resolver.resolve(dst_ip)

            if hasattr(record, 'dst_port') and record.dst_port:
                try:
                    dest_servers[dst_ip]['ports'].add(int(record.dst_port))
                except:
                    pass

            if hasattr(record, 'protocol') and record.protocol:
                dest_servers[dst_ip]['protocols'].add(record.protocol.upper())

            dest_servers[dst_ip]['flow_count'] += 1

        # Check each destination for load balancer characteristics
        for dst_ip, data in dest_servers.items():
            hostname = data['hostname'] or dst_ip

            # Use server classifier to check if it's a load balancer
            classification = self.classifier.classify_server(
                hostname=hostname,
                protocols=list(data['protocols']),
                ports=list(data['ports'])
            )

            # Identify load balancers
            if classification['type'] in ['F5 Load Balancer', 'Traffic Manager', 'Azure Traffic Manager']:
                load_balancers.append({
                    'ip': dst_ip,
                    'hostname': hostname,
                    'type': classification['type'],
                    'protocols': sorted(data['protocols']),
                    'ports': sorted(data['ports']),
                    'flow_count': data['flow_count']
                })

            # Also detect by hostname patterns (f5, loadbalancer, lb, etc.)
            elif any(keyword in hostname.lower() for keyword in ['f5', 'loadbalancer', 'load-balancer', 'lb-', '-lb', 'trafficmanager', 'traffic-manager']):
                load_balancers.append({
                    'ip': dst_ip,
                    'hostname': hostname,
                    'type': 'Load Balancer (detected by name)',
                    'protocols': sorted(data['protocols']),
                    'ports': sorted(data['ports']),
                    'flow_count': data['flow_count']
                })

        return load_balancers

    def _determine_architecture_pattern(self, by_component: Dict, load_balancers: List) -> str:
        """
        Determine application architecture pattern

        Args:
            by_component: Component classification results
            load_balancers: List of detected load balancers

        Returns:
            Architecture pattern description
        """
        web_count = len(by_component['web'])
        app_count = len(by_component['app'])
        db_count = len(by_component['database'])
        lb_count = len(load_balancers) if load_balancers else 0

        # Pattern detection
        patterns = []

        # Load balancer presence
        if lb_count > 0:
            patterns.append(f"Load Balanced ({lb_count} LB)")

        # Multi-tier architecture
        if web_count > 0 and app_count > 0 and db_count > 0:
            patterns.append(f"3-Tier (Web:{web_count}/App:{app_count}/DB:{db_count})")
        elif web_count > 0 and app_count > 0:
            patterns.append(f"2-Tier (Web:{web_count}/App:{app_count})")
        elif app_count > 0 and db_count > 0:
            patterns.append(f"2-Tier (App:{app_count}/DB:{db_count})")

        # High availability indicators
        if web_count > 1:
            patterns.append(f"HA Web Cluster ({web_count} nodes)")
        if app_count > 1:
            patterns.append(f"HA App Cluster ({app_count} nodes)")
        if db_count > 1:
            patterns.append(f"HA DB Cluster ({db_count} nodes)")

        # Simple patterns
        if not patterns:
            if web_count > 0:
                patterns.append(f"Web Only ({web_count})")
            elif app_count > 0:
                patterns.append(f"App Only ({app_count})")
            elif db_count > 0:
                patterns.append(f"DB Only ({db_count})")
            else:
                patterns.append("Unknown Pattern")

        return " | ".join(patterns)

    def generate_component_report(self, analysis: Dict) -> str:
        """
        Generate human-readable component analysis report

        Args:
            analysis: Result from analyze_source_components()

        Returns:
            Formatted report string
        """
        lines = []
        lines.append(f"\n{'='*80}")
        lines.append(f"Source Component Analysis: {analysis['app_name']}")
        lines.append(f"{'='*80}\n")

        lines.append(f"Total Source IPs: {analysis['total_source_ips']}\n")

        # Architecture pattern
        lines.append(f"Architecture Pattern: {analysis['architecture_pattern']}\n")

        # Load balancer detection
        if analysis['load_balancer_detected']:
            lines.append(f"⚠️  LOAD BALANCERS DETECTED ({len(analysis['load_balancer_detected'])}):")
            for lb in analysis['load_balancer_detected']:
                lines.append(f"  ├─ {lb['hostname']} ({lb['ip']})")
                lines.append(f"  │  Type: {lb['type']}")
                lines.append(f"  │  Ports: {', '.join(map(str, lb['ports']))}")
                lines.append(f"  │  Flows: {lb['flow_count']}")
            lines.append("")

        # Component breakdown
        lines.append("Component Breakdown:")
        lines.append(f"  - Web Servers:      {analysis['component_counts']['web']}")
        lines.append(f"  - App Servers:      {analysis['component_counts']['app']}")
        lines.append(f"  - Database Servers: {analysis['component_counts']['database']}")
        lines.append(f"  - Unknown:          {analysis['component_counts']['unknown']}\n")

        # High availability warning
        web_count = analysis['component_counts']['web']
        app_count = analysis['component_counts']['app']
        lb_count = len(analysis['load_balancer_detected']) if analysis['load_balancer_detected'] else 0

        if (web_count > 1 or app_count > 1) and lb_count == 0:
            lines.append("⚠️  WARNING: Multiple web/app servers detected but NO load balancer found!")
            lines.append("   This may indicate:")
            lines.append("   - Missing load balancer in network flow data")
            lines.append("   - Load balancer not captured in CSV files")
            lines.append("   - DNS-based load balancing (no dedicated LB appliance)")
            lines.append("")

        # Detailed breakdown by component
        for component_type in ['web', 'app', 'database']:
            servers = analysis['by_component'][component_type]
            if not servers:
                continue

            lines.append(f"\n{component_type.upper()} SERVERS ({len(servers)}):")
            lines.append("-" * 80)

            for server in servers[:10]:  # Top 10 per component
                lines.append(f"\n  {server['hostname']} ({server['ip']})")
                lines.append(f"    Ports: {', '.join(map(str, server['ports'][:10]))}")
                lines.append(f"    Protocols: {', '.join(server['protocols'][:10])}")
                lines.append(f"    Destinations: {server['destinations']}")
                lines.append(f"    Traffic: {server['bytes_sent']:,} bytes")
                if server['server_type']:
                    lines.append(f"    Type: {server['server_type']}")

        return '\n'.join(lines)


# Convenience function
def analyze_source_components(app_name: str, flow_records: List,
                              hostname_resolver=None) -> Dict:
    """
    Analyze source IPs to identify component types

    Args:
        app_name: Application name
        flow_records: List of FlowRecord objects
        hostname_resolver: Optional hostname resolver

    Returns:
        Analysis results dict
    """
    analyzer = SourceComponentAnalyzer()
    return analyzer.analyze_source_components(app_name, flow_records, hostname_resolver)


if __name__ == '__main__':
    print("Source Component Analyzer")
    print("=" * 80)
    print("Usage:")
    print("  from src.source_component_analyzer import analyze_source_components")
    print("  results = analyze_source_components(app_name, flow_records, resolver)")
    print("  print(analyzer.generate_component_report(results))")
