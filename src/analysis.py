"""
Network Traffic Analysis and Segmentation Rule Generator
=========================================================
Analyzes parsed network flows and generates actionable segmentation recommendations,
firewall rules, and security policies.

Author: Network Security Team
Version: 2.0
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
import ipaddress

logger = logging.getLogger(__name__)


@dataclass
class SegmentationRule:
    """Represents a network segmentation rule"""
    priority: int
    source: str
    destination: str
    protocol: str
    port: str
    action: str  # allow, deny
    justification: str
    risk_score: int
    enforcement_target: str  # firewall, nsg, sg, acl
    complexity: str  # low, medium, high
    zone_src: str = ''
    zone_dst: str = ''
    rule_id: str = ''

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NetworkZone:
    """Network segmentation zone"""
    zone_name: str
    zone_type: str  # macro, micro
    members: Set[str]  # IP addresses or hostnames
    description: str
    security_level: int  # 1-5 (1=lowest, 5=highest)
    parent_zone: Optional[str] = None


class TrafficAnalyzer:
    """Analyzes network traffic and generates segmentation recommendations"""

    # Port to service mapping
    PORT_SERVICES = {
        80: 'HTTP', 443: 'HTTPS', 22: 'SSH', 23: 'Telnet', 21: 'FTP',
        25: 'SMTP', 53: 'DNS', 3306: 'MySQL', 5432: 'PostgreSQL',
        27017: 'MongoDB', 6379: 'Redis', 9092: 'Kafka', 9200: 'Elasticsearch',
        8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 3389: 'RDP', 389: 'LDAP',
        636: 'LDAPS', 9090: 'Prometheus', 5044: 'Filebeat', 50000: 'Jenkins',
        7077: 'Spark', 9000: 'HDFS', 50010: 'HDFS-Data', 5000: 'Docker-Registry'
    }

    # Service to tier mapping
    SERVICE_TIERS = {
        'web': {'HTTP', 'HTTPS', 'HTTP-Alt', 'HTTPS-Alt'},
        'app': {'HTTP-Alt', 'HTTPS-Alt'},
        'data': {'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'HDFS'},
        'messaging': {'Kafka', 'RabbitMQ'},
        'infrastructure': {'DNS', 'LDAP', 'LDAPS'},
        'management': {'SSH', 'Prometheus', 'Jenkins', 'Grafana'}
    }

    def __init__(self, flow_records: List):
        """Initialize with parsed flow records"""
        self.records = flow_records
        self.zones: Dict[str, NetworkZone] = {}
        self.rules: List[SegmentationRule] = []
        self.analysis_results = {}

        logger.info(f"TrafficAnalyzer initialized with {len(flow_records)} records")

    def analyze(self) -> Dict:
        """Run comprehensive traffic analysis"""
        logger.info("Starting comprehensive traffic analysis...")

        self.analysis_results = {
            'summary': self._compute_summary_stats(),
            'top_talkers': self._identify_top_talkers(),
            'port_analysis': self._analyze_ports(),
            'peer_pairs': self._analyze_peer_pairs(),
            'suspicious_flows': self._identify_suspicious_flows(),
            'temporal_patterns': self._analyze_temporal_patterns(),
            'flow_classification': self._classify_flows(),
            'zones': self._generate_zones(),
            'rules': self._generate_segmentation_rules()
        }

        logger.info("✓ Analysis complete")
        return self.analysis_results

    def _compute_summary_stats(self) -> Dict:
        """Compute high-level summary statistics"""
        logger.info("  Computing summary statistics...")

        total_bytes = sum(r.bytes for r in self.records)
        total_packets = sum(r.packets for r in self.records)

        apps = Counter(r.app_name for r in self.records)
        protocols = Counter(r.transport for r in self.records)
        ports = Counter(r.port for r in self.records if r.port)

        return {
            'total_flows': len(self.records),
            'total_bytes': total_bytes,
            'total_packets': total_packets,
            'unique_apps': len(apps),
            'app_distribution': dict(apps.most_common(10)),
            'protocol_distribution': dict(protocols),
            'top_ports': dict(ports.most_common(10)),
            'internal_flows': sum(1 for r in self.records if r.is_internal),
            'external_flows': sum(1 for r in self.records if not r.is_internal),
            'suspicious_count': sum(1 for r in self.records if r.is_suspicious)
        }

    def _identify_top_talkers(self, top_n: int = 10) -> Dict:
        """Identify top talkers by bytes and sessions"""
        logger.info("  Identifying top talkers...")

        # By source IP
        src_bytes = defaultdict(int)
        src_sessions = defaultdict(int)

        # By destination IP
        dst_bytes = defaultdict(int)
        dst_sessions = defaultdict(int)

        for record in self.records:
            src_bytes[record.src_ip] += record.bytes
            src_sessions[record.src_ip] += 1
            dst_bytes[record.dst_ip] += record.bytes
            dst_sessions[record.dst_ip] += 1

        return {
            'top_sources_by_bytes': dict(Counter(src_bytes).most_common(top_n)),
            'top_sources_by_sessions': dict(Counter(src_sessions).most_common(top_n)),
            'top_destinations_by_bytes': dict(Counter(dst_bytes).most_common(top_n)),
            'top_destinations_by_sessions': dict(Counter(dst_sessions).most_common(top_n))
        }

    def _analyze_ports(self) -> Dict:
        """Analyze port usage and classify services"""
        logger.info("  Analyzing ports and services...")

        port_stats = defaultdict(lambda: {
            'count': 0,
            'bytes': 0,
            'unique_sources': set(),
            'unique_destinations': set()
        })

        for record in self.records:
            if record.port:
                stats = port_stats[record.port]
                stats['count'] += 1
                stats['bytes'] += record.bytes
                stats['unique_sources'].add(record.src_ip)
                stats['unique_destinations'].add(record.dst_ip)

        # Convert sets to counts and identify service
        analyzed_ports = {}
        for port, stats in port_stats.items():
            service = self.PORT_SERVICES.get(port, 'Unknown')
            analyzed_ports[port] = {
                'service': service,
                'count': stats['count'],
                'bytes': stats['bytes'],
                'unique_sources': len(stats['unique_sources']),
                'unique_destinations': len(stats['unique_destinations']),
                'is_rare': stats['count'] < 5  # Flag rare ports
            }

        # Sort by usage
        sorted_ports = sorted(
            analyzed_ports.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        return {
            'total_unique_ports': len(port_stats),
            'port_details': dict(sorted_ports[:20]),  # Top 20
            'rare_ports': {p: d for p, d in analyzed_ports.items() if d['is_rare']}
        }

    def _analyze_peer_pairs(self, top_n: int = 20) -> List[Dict]:
        """Analyze frequently communicating peer pairs"""
        logger.info("  Analyzing peer pairs...")

        pair_stats = defaultdict(lambda: {
            'flows': 0,
            'bytes': 0,
            'protocols': set(),
            'ports': set()
        })

        for record in self.records:
            pair = (record.src_ip, record.dst_ip)
            stats = pair_stats[pair]
            stats['flows'] += 1
            stats['bytes'] += record.bytes
            stats['protocols'].add(record.transport)
            if record.port:
                stats['ports'].add(record.port)

        # Convert to list and sort
        pairs_list = []
        for (src, dst), stats in pair_stats.items():
            pairs_list.append({
                'source': src,
                'destination': dst,
                'flows': stats['flows'],
                'bytes': stats['bytes'],
                'protocols': list(stats['protocols']),
                'ports': sorted(stats['ports'])
            })

        pairs_list.sort(key=lambda x: x['flows'], reverse=True)
        return pairs_list[:top_n]

    def _identify_suspicious_flows(self) -> List[Dict]:
        """Identify and categorize suspicious flows"""
        logger.info("  Identifying suspicious flows...")

        suspicious = []
        for record in self.records:
            if record.is_suspicious:
                suspicious.append({
                    'source': f"{record.src_hostname or record.src_ip}",
                    'destination': f"{record.dst_hostname or record.dst_ip}",
                    'protocol': record.protocol,
                    'risk_score': record.risk_score,
                    'reason': self._get_suspicion_reason(record)
                })

        suspicious.sort(key=lambda x: x['risk_score'], reverse=True)
        return suspicious

    def _get_suspicion_reason(self, record) -> str:
        """Determine why a flow is suspicious"""
        reasons = []

        if not record.is_internal:
            reasons.append("External access")

        if record.port in [22, 3389, 23]:
            reasons.append(f"Management port {record.port} exposed")

        if record.port in [3306, 5432, 27017, 6379]:
            reasons.append(f"Database port {record.port} exposed")

        if 'malicious' in record.src_hostname.lower() or 'malicious' in record.dst_hostname.lower():
            reasons.append("Malicious hostname detected")

        if 'scanner' in record.src_hostname.lower() or 'bot' in record.src_hostname.lower():
            reasons.append("Scanner/bot activity")

        return '; '.join(reasons) if reasons else "Unknown risk"

    def _analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal traffic patterns"""
        logger.info("  Analyzing temporal patterns...")

        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)

        for record in self.records:
            if record.timestamp:
                hour_distribution[record.timestamp.hour] += 1
                day_distribution[record.timestamp.strftime('%A')] += 1

        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else 0
        peak_day = max(day_distribution.items(), key=lambda x: x[1])[0] if day_distribution else 'Unknown'

        return {
            'hour_distribution': dict(hour_distribution),
            'day_distribution': dict(day_distribution),
            'peak_hour': peak_hour,
            'peak_day': peak_day
        }

    def _classify_flows(self) -> Dict:
        """Classify flows into categories"""
        logger.info("  Classifying flows...")

        classification = {
            'internal': 0,
            'external_inbound': 0,
            'external_outbound': 0,
            'east_west': 0,
            'north_south': 0
        }

        for record in self.records:
            if record.is_internal:
                classification['internal'] += 1
                classification['east_west'] += 1
            else:
                classification['north_south'] += 1
                # Check if inbound or outbound
                try:
                    if ipaddress.IPv4Address(record.src_ip).is_private:
                        classification['external_outbound'] += 1
                    else:
                        classification['external_inbound'] += 1
                except:
                    pass

        return classification

    def _generate_zones(self) -> Dict[str, NetworkZone]:
        """Generate network segmentation zones based on traffic patterns"""
        logger.info("  Generating network zones...")

        # Analyze hosts by their roles
        host_roles = self._classify_hosts_by_role()

        # Create zones
        self.zones = {}

        # Macro zones
        self.zones['EXTERNAL'] = NetworkZone(
            zone_name='EXTERNAL',
            zone_type='macro',
            members=set(),
            description='Internet-facing zone',
            security_level=1
        )

        self.zones['DMZ'] = NetworkZone(
            zone_name='DMZ',
            zone_type='macro',
            members=set(),
            description='Demilitarized zone for public services',
            security_level=2
        )

        self.zones['INTERNAL'] = NetworkZone(
            zone_name='INTERNAL',
            zone_type='macro',
            members=set(),
            description='Internal network',
            security_level=3
        )

        # Micro zones (application tiers)
        for tier_name, hosts in host_roles.items():
            if tier_name == 'WEB_TIER':
                zone = NetworkZone(
                    zone_name='WEB_TIER',
                    zone_type='micro',
                    members=set(hosts),
                    description='Web servers and load balancers',
                    security_level=2,
                    parent_zone='INTERNAL'
                )
            elif tier_name == 'APP_TIER':
                zone = NetworkZone(
                    zone_name='APP_TIER',
                    zone_type='micro',
                    members=set(hosts),
                    description='Application servers',
                    security_level=3,
                    parent_zone='INTERNAL'
                )
            elif tier_name == 'DATA_TIER':
                zone = NetworkZone(
                    zone_name='DATA_TIER',
                    zone_type='micro',
                    members=set(hosts),
                    description='Databases and storage',
                    security_level=4,
                    parent_zone='INTERNAL'
                )
            elif tier_name == 'MESSAGING_TIER':
                zone = NetworkZone(
                    zone_name='MESSAGING_TIER',
                    zone_type='micro',
                    members=set(hosts),
                    description='Message queues and event buses',
                    security_level=3,
                    parent_zone='INTERNAL'
                )
            elif tier_name == 'MANAGEMENT_TIER':
                zone = NetworkZone(
                    zone_name='MANAGEMENT_TIER',
                    zone_type='micro',
                    members=set(hosts),
                    description='Monitoring, orchestration, and management',
                    security_level=4,
                    parent_zone='INTERNAL'
                )
            else:
                zone = NetworkZone(
                    zone_name=tier_name,
                    zone_type='micro',
                    members=set(hosts),
                    description=f'{tier_name} services',
                    security_level=3,
                    parent_zone='INTERNAL'
                )

            self.zones[tier_name] = zone

        # Convert zones to serializable format
        zones_dict = {}
        for zone_name, zone in self.zones.items():
            zones_dict[zone_name] = {
                'zone_name': zone.zone_name,
                'zone_type': zone.zone_type,
                'members': list(zone.members),
                'description': zone.description,
                'security_level': zone.security_level,
                'parent_zone': zone.parent_zone
            }

        return zones_dict

    def _classify_hosts_by_role(self) -> Dict[str, Set[str]]:
        """Classify hosts into tiers based on services they provide"""
        host_services = defaultdict(set)

        # Collect services per destination host
        for record in self.records:
            if record.port and record.dst_ip:
                service = self.PORT_SERVICES.get(record.port, 'Unknown')
                host_services[record.dst_ip].add(service)

        # Classify into tiers
        tiers = defaultdict(set)

        for host, services in host_services.items():
            # Web tier
            if services & {'HTTP', 'HTTPS'}:
                tiers['WEB_TIER'].add(host)
            # Data tier
            elif services & {'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'HDFS'}:
                tiers['DATA_TIER'].add(host)
            # Messaging tier
            elif services & {'Kafka'}:
                tiers['MESSAGING_TIER'].add(host)
            # Management tier
            elif services & {'Prometheus', 'Jenkins', 'SSH'}:
                tiers['MANAGEMENT_TIER'].add(host)
            # Application tier (default)
            else:
                tiers['APP_TIER'].add(host)

        return dict(tiers)

    def _generate_segmentation_rules(self) -> List[SegmentationRule]:
        """Generate prioritized segmentation rules"""
        logger.info("  Generating segmentation rules...")

        self.rules = []
        rule_id = 1000

        # Rule 1: Deny all by default (implicit)
        self.rules.append(SegmentationRule(
            priority=9999,
            source='any',
            destination='any',
            protocol='any',
            port='any',
            action='deny',
            justification='Default deny policy for zero-trust architecture',
            risk_score=0,
            enforcement_target='firewall',
            complexity='low',
            rule_id=f'RULE-{rule_id}'
        ))
        rule_id += 1

        # Rule 2: Block management ports from external
        for port, service in [(22, 'SSH'), (3389, 'RDP'), (23, 'Telnet')]:
            self.rules.append(SegmentationRule(
                priority=100 + rule_id,
                source='EXTERNAL',
                destination='any',
                protocol='tcp',
                port=str(port),
                action='deny',
                justification=f'Block {service} access from external networks - high security risk',
                risk_score=90,
                enforcement_target='perimeter-firewall',
                complexity='low',
                zone_src='EXTERNAL',
                zone_dst='INTERNAL',
                rule_id=f'RULE-{rule_id}'
            ))
            rule_id += 1

        # Rule 3: Block database ports from external
        for port, service in [(3306, 'MySQL'), (5432, 'PostgreSQL'), (27017, 'MongoDB'), (6379, 'Redis')]:
            self.rules.append(SegmentationRule(
                priority=200 + rule_id,
                source='EXTERNAL',
                destination='DATA_TIER',
                protocol='tcp',
                port=str(port),
                action='deny',
                justification=f'Block direct {service} access from external - data exfiltration risk',
                risk_score=95,
                enforcement_target='perimeter-firewall',
                complexity='low',
                zone_src='EXTERNAL',
                zone_dst='DATA_TIER',
                rule_id=f'RULE-{rule_id}'
            ))
            rule_id += 1

        # Rule 4: Allow HTTP/HTTPS to web tier from external
        for port, service in [(80, 'HTTP'), (443, 'HTTPS')]:
            self.rules.append(SegmentationRule(
                priority=300,
                source='any',
                destination='WEB_TIER',
                protocol='tcp',
                port=str(port),
                action='allow',
                justification=f'Allow {service} traffic to web tier - legitimate public access',
                risk_score=20,
                enforcement_target='perimeter-firewall',
                complexity='low',
                zone_src='EXTERNAL',
                zone_dst='WEB_TIER',
                rule_id=f'RULE-{rule_id}'
            ))
            rule_id += 1

        # Rule 5: Web tier to app tier
        self.rules.append(SegmentationRule(
            priority=400,
            source='WEB_TIER',
            destination='APP_TIER',
            protocol='tcp',
            port='8080,8443',
            action='allow',
            justification='Allow web tier to communicate with application tier',
            risk_score=15,
            enforcement_target='internal-firewall',
            complexity='medium',
            zone_src='WEB_TIER',
            zone_dst='APP_TIER',
            rule_id=f'RULE-{rule_id}'
        ))
        rule_id += 1

        # Rule 6: App tier to data tier (database access)
        for port, service in [(3306, 'MySQL'), (5432, 'PostgreSQL'), (27017, 'MongoDB')]:
            self.rules.append(SegmentationRule(
                priority=500 + rule_id,
                source='APP_TIER',
                destination='DATA_TIER',
                protocol='tcp',
                port=str(port),
                action='allow',
                justification=f'Allow app tier to access {service} databases',
                risk_score=25,
                enforcement_target='internal-firewall',
                complexity='medium',
                zone_src='APP_TIER',
                zone_dst='DATA_TIER',
                rule_id=f'RULE-{rule_id}'
            ))
            rule_id += 1

        # Rule 7: App tier to cache tier
        self.rules.append(SegmentationRule(
            priority=600,
            source='APP_TIER',
            destination='DATA_TIER',
            protocol='tcp',
            port='6379',
            action='allow',
            justification='Allow app tier to access Redis cache',
            risk_score=20,
            enforcement_target='internal-firewall',
            complexity='low',
            zone_src='APP_TIER',
            zone_dst='DATA_TIER',
            rule_id=f'RULE-{rule_id}'
        ))
        rule_id += 1

        # Rule 8: App tier to messaging tier
        self.rules.append(SegmentationRule(
            priority=700,
            source='APP_TIER',
            destination='MESSAGING_TIER',
            protocol='tcp',
            port='9092,5672',
            action='allow',
            justification='Allow app tier to access message queues (Kafka, RabbitMQ)',
            risk_score=20,
            enforcement_target='internal-firewall',
            complexity='medium',
            zone_src='APP_TIER',
            zone_dst='MESSAGING_TIER',
            rule_id=f'RULE-{rule_id}'
        ))
        rule_id += 1

        # Rule 9: Management tier monitoring access
        self.rules.append(SegmentationRule(
            priority=800,
            source='MANAGEMENT_TIER',
            destination='any',
            protocol='tcp',
            port='9090,9100,4040',
            action='allow',
            justification='Allow management tier to collect metrics from all tiers',
            risk_score=30,
            enforcement_target='internal-firewall',
            complexity='high',
            zone_src='MANAGEMENT_TIER',
            zone_dst='INTERNAL',
            rule_id=f'RULE-{rule_id}'
        ))
        rule_id += 1

        # Rule 10: Deny DATA_TIER to WEB_TIER (prevent reverse flow)
        self.rules.append(SegmentationRule(
            priority=150,
            source='DATA_TIER',
            destination='WEB_TIER',
            protocol='any',
            port='any',
            action='deny',
            justification='Prevent reverse traffic from data tier to web tier - data exfiltration protection',
            risk_score=85,
            enforcement_target='internal-firewall',
            complexity='low',
            zone_src='DATA_TIER',
            zone_dst='WEB_TIER',
            rule_id=f'RULE-{rule_id}'
        ))

        # Sort by priority
        self.rules.sort(key=lambda r: r.priority)

        logger.info(f"  ✓ Generated {len(self.rules)} segmentation rules")
        return self.rules

    def export_rules_csv(self, output_path: str):
        """Export rules to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'rule_id', 'priority', 'source', 'destination', 'protocol', 'port',
                'action', 'justification', 'risk_score', 'enforcement_target',
                'complexity', 'zone_src', 'zone_dst'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for rule in self.rules:
                writer.writerow(rule.to_dict())

        logger.info(f"✓ Exported {len(self.rules)} rules to {output_path}")

    def export_iptables_rules(self, output_path: str):
        """Export rules as IPTables script"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "#!/bin/bash",
            "# Generated Network Segmentation Rules - IPTables Format",
            "# Auto-generated by Network Segmentation Analyzer",
            "",
            "# Flush existing rules",
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "",
            "# Allow established connections",
            "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
            "iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT",
            ""
        ]

        for rule in self.rules:
            if rule.action == 'deny':
                continue  # Handle deny rules at the end

            lines.append(f"# {rule.justification}")
            if rule.port and rule.port != 'any':
                ports = rule.port.replace(',', ',--dport ')
                lines.append(
                    f"iptables -A FORWARD -p {rule.protocol} --dport {ports} "
                    f"-m comment --comment '{rule.rule_id}' -j ACCEPT"
                )
            lines.append("")

        lines.extend([
            "# Default deny",
            "iptables -A FORWARD -j LOG --log-prefix 'SEGMENTATION_DENY: '",
            "iptables -A FORWARD -j DROP",
            "",
            "echo 'Segmentation rules applied successfully'"
        ])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"✓ Exported IPTables rules to {output_path}")

    def export_aws_security_groups(self, output_path: str):
        """Export rules as AWS Security Group JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        security_groups = {}

        # Create security group per zone
        for zone_name, zone in self.zones.items():
            if zone.zone_type == 'micro':
                sg_name = f"sg-{zone_name.lower().replace('_', '-')}"
                security_groups[sg_name] = {
                    'GroupName': sg_name,
                    'Description': zone.description,
                    'VpcId': 'vpc-XXXXXXXX',
                    'IngressRules': [],
                    'EgressRules': []
                }

        # Add rules to appropriate security groups
        for rule in self.rules:
            if rule.action == 'allow' and rule.zone_dst in security_groups:
                sg_name = f"sg-{rule.zone_dst.lower().replace('_', '-')}"

                if rule.port and rule.port != 'any':
                    for port in rule.port.split(','):
                        security_groups[sg_name]['IngressRules'].append({
                            'IpProtocol': rule.protocol,
                            'FromPort': int(port),
                            'ToPort': int(port),
                            'SourceSecurityGroupName': f"sg-{rule.zone_src.lower().replace('_', '-')}" if rule.zone_src != 'any' else None,
                            'CidrIp': '0.0.0.0/0' if rule.zone_src == 'any' else None,
                            'Description': rule.justification
                        })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'SecurityGroups': list(security_groups.values())}, f, indent=2)

        logger.info(f"✓ Exported AWS Security Groups to {output_path}")

    def export_analysis_report(self, output_path: str):
        """Export complete analysis report as JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': self.analysis_results.get('summary', {}),
            'top_talkers': self.analysis_results.get('top_talkers', {}),
            'port_analysis': self.analysis_results.get('port_analysis', {}),
            'peer_pairs': self.analysis_results.get('peer_pairs', []),
            'suspicious_flows': self.analysis_results.get('suspicious_flows', []),
            'temporal_patterns': self.analysis_results.get('temporal_patterns', {}),
            'flow_classification': self.analysis_results.get('flow_classification', {}),
            'zones': self.analysis_results.get('zones', {}),
            'rules': [rule.to_dict() for rule in self.rules]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"✓ Exported analysis report to {output_path}")


# Convenience function
def analyze_traffic(flow_records: List, output_dir: str = 'outputs') -> TrafficAnalyzer:
    """
    Convenience function to analyze traffic and generate all outputs

    Args:
        flow_records: List of parsed FlowRecord objects
        output_dir: Directory for output files

    Returns:
        TrafficAnalyzer instance
    """
    from datetime import datetime

    analyzer = TrafficAnalyzer(flow_records)
    analyzer.analyze()

    # Export all artifacts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    analyzer.export_rules_csv(str(output_path / 'segmentation_rules.csv'))
    analyzer.export_iptables_rules(str(output_path / 'iptables_rules.sh'))
    analyzer.export_aws_security_groups(str(output_path / 'aws_security_groups.json'))
    analyzer.export_analysis_report(str(output_path / 'analysis_report.json'))

    return analyzer


if __name__ == '__main__':
    # Example usage
    from src.parser import parse_network_logs

    print("="*60)
    print("Traffic Analysis - Test Run")
    print("="*60)

    # Parse logs
    parser = parse_network_logs('data/input')

    # Analyze
    analyzer = analyze_traffic(parser.records, 'outputs')

    print(f"\n📊 Analysis Summary:")
    print(f"  Total flows: {analyzer.analysis_results['summary']['total_flows']}")
    print(f"  Suspicious flows: {analyzer.analysis_results['summary']['suspicious_count']}")
    print(f"  Generated rules: {len(analyzer.rules)}")
    print(f"  Network zones: {len(analyzer.zones)}")

    print("\n✅ Analysis complete!")
