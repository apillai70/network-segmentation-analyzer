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
            }
        }

        logger.info(f"  Source IPs: {summary['total_source_ips']}")
        logger.info(f"    Web: {summary['component_counts']['web']}")
        logger.info(f"    App: {summary['component_counts']['app']}")
        logger.info(f"    Database: {summary['component_counts']['database']}")
        logger.info(f"    Unknown: {summary['component_counts']['unknown']}")

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

        # Component breakdown
        lines.append("Component Breakdown:")
        lines.append(f"  - Web Servers:      {analysis['component_counts']['web']}")
        lines.append(f"  - App Servers:      {analysis['component_counts']['app']}")
        lines.append(f"  - Database Servers: {analysis['component_counts']['database']}")
        lines.append(f"  - Unknown:          {analysis['component_counts']['unknown']}\n")

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
