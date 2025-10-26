#!/usr/bin/env python3
"""
Enhanced Application Diagram Generator
=======================================
Generates rich, interactive HTML diagrams with:
- Multiple views (Architecture, Full Flow, Upstream, Downstream)
- Stats dashboard (flows, VMware count, DNS failures)
- Server grouping with clickable modals
- Flow counts on connections
- VMware/ESXi detection
- Zero Trust Network Analysis
- Executive Deliverables

This is a comprehensive visualization tool for network segmentation analysis.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedApplicationDiagramGenerator:
    """Generates enhanced application diagrams with comprehensive analysis"""

    def __init__(self):
        """Initialize the enhanced diagram generator"""
        self.logger = logging.getLogger(__name__)

    def generate_from_flows(
        self,
        app_code: str,
        flows_data: List[Dict],
        output_dir: str = "outputs_final/enhanced_diagrams"
    ) -> bool:
        """
        Generate enhanced application diagram from flow data

        Args:
            app_code: Application code (e.g., 'AODSVY')
            flows_data: List of enriched flow records
            output_dir: Output directory for HTML file

        Returns:
            True if successful
        """
        try:
            output_path = Path(output_dir) / f"{app_code}_enhanced_application_diagram.html"
            return self.generate_enhanced_diagram(app_code, flows_data, str(output_path))
        except Exception as e:
            self.logger.error(f"Error generating enhanced diagram for {app_code}: {e}")
            return False

    def generate_enhanced_diagram(
        self,
        app_code: str,
        flows_data: List[Dict],
        output_path: str
    ) -> bool:
        """
        Generate complete enhanced diagram with all views and analysis

        Args:
            app_code: Application code
            flows_data: List of flow records
            output_path: Full path to output HTML file

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Generating enhanced diagram for {app_code}...")

            # Calculate statistics
            stats = self._calculate_stats(app_code, flows_data)

            # Group servers by tier and relationship
            groups = self._group_servers(app_code, flows_data)

            # Perform Zero Trust analysis
            zt_analysis = self._perform_zero_trust_analysis(app_code, flows_data, groups)

            # Generate executive deliverables
            exec_deliverables = self._generate_executive_deliverables(app_code, stats, zt_analysis)

            # Generate all diagram views
            diagrams = {
                'architecture': self._generate_architecture_diagram(app_code, groups, flows_data),
                'fullflow': self._generate_fullflow_diagram(app_code, groups, flows_data),
                'upstream': self._generate_upstream_diagram(app_code, groups, flows_data),
                'downstream': self._generate_downstream_diagram(app_code, groups, flows_data)
            }

            # Generate modal data for clickable server lists
            modal_data = self._generate_modal_data(groups)

            # Generate complete HTML
            html = self._generate_complete_html(
                app_code=app_code,
                stats=stats,
                diagrams=diagrams,
                modal_data=modal_data,
                zt_analysis=zt_analysis,
                exec_deliverables=exec_deliverables
            )

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            self.logger.info(f"[OK] Enhanced diagram: {output_file.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate enhanced diagram: {e}", exc_info=True)
            return False

    def _calculate_stats(self, app_code: str, flows_data: List[Dict]) -> Dict:
        """Calculate comprehensive statistics"""
        stats = {
            'total_flows': len(flows_data),
            'internal_flows': 0,
            'outbound_to_apps': 0,
            'external_flows': 0,
            'destination_apps': set(),
            'vmware_instances': 0,
            'failed_dns': 0,
            'unique_sources': set(),
            'unique_dests': set()
        }

        for flow in flows_data:
            src_app = flow.get('source_app_code')
            dst_app = flow.get('dest_app_code')
            src_ip = flow.get('source_ip')
            dst_ip = flow.get('dest_ip')
            src_host = flow.get('source_hostname', src_ip)

            # Track unique IPs
            if src_app == app_code:
                stats['unique_sources'].add(src_ip)
            if dst_app == app_code or dst_app is None:
                stats['unique_dests'].add(dst_ip)

            # Classify flow type
            if src_app == app_code and dst_app == app_code:
                stats['internal_flows'] += 1
            elif src_app == app_code and dst_app and dst_app != app_code:
                stats['outbound_to_apps'] += 1
                stats['destination_apps'].add(dst_app)
            elif src_app == app_code:
                stats['external_flows'] += 1

            # Detect VMware
            if any(x in str(src_host).lower() for x in ['vmware', 'esxi', 'vm-', '-vm']):
                stats['vmware_instances'] += 1

            # Count DNS failures
            if src_host == src_ip or not src_host:
                stats['failed_dns'] += 1

        stats['destination_apps_count'] = len(stats['destination_apps'])
        stats['unique_source_count'] = len(stats['unique_sources'])
        stats['unique_dest_count'] = len(stats['unique_dests'])

        return stats

    def _group_servers(self, app_code: str, flows_data: List[Dict]) -> Dict:
        """Group servers by tier, type, and relationship"""
        groups = {
            'web': [],
            'app': [],
            'database': [],
            'cache': [],
            'messaging': [],
            'domain_controller': [],
            'other': [],
            'upstream_apps': defaultdict(list),
            'downstream_apps': defaultdict(list),
            'external': [],
            'all_app_servers': []
        }

        seen = {'sources': set(), 'dests': set()}

        for flow in flows_data:
            src_ip = flow.get('source_ip')
            src_host = flow.get('source_hostname', src_ip)
            src_app = flow.get('source_app_code')
            src_type = flow.get('source_server_type', 'General')

            dst_ip = flow.get('dest_ip')
            dst_host = flow.get('dest_hostname', dst_ip)
            dst_app = flow.get('dest_app_code')
            dst_type = flow.get('dest_server_type', 'General')

            # Group source servers (this app)
            if src_app == app_code and src_ip not in seen['sources']:
                server_info = {
                    'ip': src_ip,
                    'hostname': src_host,
                    'type': src_type,
                    'display': f"{src_ip} ({src_host})" if src_host != src_ip else src_ip
                }

                # Classify by server type
                tier_map = {
                    'Web': 'web',
                    'App': 'app',
                    'Database': 'database',
                    'Cache': 'cache',
                    'Message Queue': 'messaging',
                    'Domain Controller': 'domain_controller'
                }

                tier = tier_map.get(src_type, 'other')
                groups[tier].append(server_info)
                groups['all_app_servers'].append(server_info)
                seen['sources'].add(src_ip)

            # Group upstream apps
            if src_app and src_app != app_code:
                server_info = {
                    'ip': src_ip,
                    'hostname': src_host,
                    'type': src_type,
                    'display': f"{src_ip} ({src_host})" if src_host != src_ip else src_ip
                }
                if server_info not in groups['upstream_apps'][src_app]:
                    groups['upstream_apps'][src_app].append(server_info)

            # Group downstream
            if dst_ip not in seen['dests']:
                server_info = {
                    'ip': dst_ip,
                    'hostname': dst_host,
                    'type': dst_type,
                    'display': f"{dst_ip} ({dst_host})" if dst_host != dst_ip else dst_ip
                }

                if dst_app and dst_app != app_code:
                    groups['downstream_apps'][dst_app].append(server_info)
                elif not dst_app:
                    groups['external'].append(server_info)

                seen['dests'].add(dst_ip)

        return groups

    def _generate_architecture_diagram(self, app_code: str, groups: Dict, flows: List[Dict]) -> str:
        """Generate tier-based architecture diagram"""
        lines = ["graph TD"]
        lines.append(f"    %% {app_code} Architecture Diagram")
        lines.append("")

        # Upstream sources
        if groups['upstream_apps']:
            lines.append('    subgraph UPSTREAM["[UP] UPSTREAM SOURCES"]')
            for idx, (app, servers) in enumerate(groups['upstream_apps'].items()):
                flow_count = sum(1 for f in flows if f.get('source_app_code') == app)
                lines.append(f'        UP{idx}["{app}<br/>{flow_count} flows"]:::upstream')
            lines.append("    end")
            lines.append("")

        # Center application
        lines.append(f'    subgraph CENTER["{app_code} APPLICATION"]')

        # NLB (if web tier exists)
        if groups['web']:
            lines.append('        subgraph NLB["[LB] NETWORK LOAD BALANCER (Inferred)"]')
            lines.append('            NLB_NODE["External/Internal Gateway<br/>Distributes traffic to Web Tier"]:::loadbalancer')
            lines.append("        end")

        # Web tier
        if groups['web']:
            lines.append('        subgraph WEB["🌐 WEB TIER"]')
            for idx, srv in enumerate(groups['web'][:2]):
                lines.append(f'            W{idx}["{srv["ip"]}<br/>({srv["hostname"]})"]:::web')
            if len(groups['web']) > 2:
                more = len(groups['web']) - 2
                lines.append(f'            WMORE["... (+{more} more)"]:::webmore')
                lines.append('            click WMORE showWebServers')
            lines.append("        end")

        # ALB (if app tier exists)
        if groups['app']:
            lines.append('        subgraph ALB["[LB] APPLICATION LOAD BALANCER (Inferred)"]')
            lines.append('            ALB_NODE["Internal Gateway/API Gateway<br/>Distributes traffic to App Tier"]:::loadbalancer')
            lines.append("        end")

        # App tier
        if groups['app']:
            lines.append('        subgraph APP["[APP] APPLICATION TIER"]')
            for idx, srv in enumerate(groups['app'][:2]):
                lines.append(f'            A{idx}["{srv["ip"]}<br/>({srv["hostname"]})"]:::app')
            if len(groups['app']) > 2:
                more = len(groups['app']) - 2
                lines.append(f'            AMORE["... (+{more} more)"]:::appmore')
                lines.append('            click AMORE showAppServers')
            lines.append("        end")

        # Database tier
        if groups['database']:
            lines.append('        subgraph DB["🗄️ DATABASE TIER"]')
            for idx, srv in enumerate(groups['database'][:2]):
                lines.append(f'            D{idx}["{srv["ip"]}<br/>({srv["hostname"]})"]:::database')
            if len(groups['database']) > 2:
                more = len(groups['database']) - 2
                lines.append(f'            DMORE["... (+{more} more)"]:::dbmore')
                lines.append('            click DMORE showDatabaseServers')
            lines.append("        end")

        # Other services
        if groups['domain_controller'] or groups['other']:
            lines.append('        subgraph OTHER["🖥️ OTHER SERVICES"]')
            if groups['domain_controller']:
                count = len(groups['domain_controller'])
                lines.append(f'            OTH_DC["Domain Controller<br/>{count} servers"]:::other')
            lines.append("        end")

        lines.append("    end")
        lines.append("")

        # External
        if groups['external']:
            ext_count = len(groups['external'])
            ext_flows = sum(1 for f in flows if not f.get('dest_app_code'))
            lines.append(f'    EXTERNAL["🌍 EXTERNAL / INTERNET<br/>{ext_count} destinations | {ext_flows} flows"]:::external')
            lines.append("")

        # Connections
        if groups['upstream_apps']:
            for idx in range(len(groups['upstream_apps'])):
                lines.append(f"    UP{idx} --> CENTER")
        if groups['external']:
            lines.append("    CENTER --> EXTERNAL")

        lines.append("")

        # Styles
        lines.extend([
            "    %% Styles",
            "    classDef upstream fill:#E3F2FD,stroke:#1976D2,stroke-width:1.5px,color:#000",
            "    classDef web fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff",
            "    classDef webmore fill:#81C784,stroke:#2E7D32,stroke-width:1.5px,stroke-dasharray:5,color:#fff",
            "    classDef app fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff",
            "    classDef appmore fill:#FFB74D,stroke:#E65100,stroke-width:1.5px,stroke-dasharray:5,color:#fff",
            "    classDef database fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff",
            "    classDef dbmore fill:#BA68C8,stroke:#6A1B9A,stroke-width:1.5px,stroke-dasharray:5,color:#fff",
            "    classDef loadbalancer fill:#FFF,stroke:#F44336,stroke-width:2px,color:#000",
            "    classDef other fill:#607D8B,stroke:#37474F,stroke-width:1.5px,color:#fff",
            "    classDef external fill:#F44336,stroke:#C62828,stroke-width:1.5px,color:#fff"
        ])

        return '\n'.join(lines)

    def _generate_fullflow_diagram(self, app_code: str, groups: Dict, flows: List[Dict]) -> str:
        """Generate full flow diagram (Source Apps → App → Dest Apps)"""
        lines = ["graph LR"]
        lines.append(f"    %% FULL FLOW: Source Apps → {app_code} → Destination Apps")
        lines.append("")

        # Upstream apps
        for idx, (app, servers) in enumerate(groups['upstream_apps'].items()):
            flow_count = sum(1 for f in flows if f.get('source_app_code') == app)
            server_count = len(servers)

            # Show first 2 IPs
            ip_lines = [f"{s['ip']} ({s['hostname']})" for s in servers[:2]]
            if server_count > 2:
                ip_lines.append(f"... (+{server_count-2} more)")

            ips_display = "<br/>".join(ip_lines)
            lines.append(f'    SRC_APP_{idx}["<b>{app}</b><br/>{ips_display}<br/>{server_count} Servers | {flow_count} Flows"]:::upstream')

        # Center app
        app_server_count = len(groups['all_app_servers'])
        app_flow_count = len(flows)

        app_ips = [f"{s['ip']} ({s['hostname']})" for s in groups['all_app_servers'][:2]]
        if app_server_count > 2:
            app_ips.append(f"... (+{app_server_count-2} more)")

        app_display = "<br/>".join(app_ips)
        lines.append(f'    CENTER["<b>{app_code} (CENTER)</b><br/>{app_display}<br/>{app_server_count} Servers | {app_flow_count} Flows"]:::centerapp')
        lines.append("")

        # Connections from upstream
        for idx in range(len(groups['upstream_apps'])):
            flow_count = list(groups['upstream_apps'].values())[idx]
            lines.append(f"    SRC_APP_{idx} .->|{len(flow_count)}| CENTER")

        # External
        if groups['external']:
            ext_count = len(groups['external'])
            ext_flows = sum(1 for f in flows if not f.get('dest_app_code'))

            ext_ips = [groups['external'][i]['ip'] for i in range(min(3, len(groups['external'])))]
            if ext_count > 3:
                ext_ips.append(f"... (+{ext_count-3} more)")

            ext_display = "<br/>".join(ext_ips)
            lines.append(f'    EXTERNAL["<b>External / Internet</b><br/>{ext_display}<br/>{ext_count} Destinations | {ext_flows} Flows"]:::external')
            lines.append(f"    CENTER -->|{ext_flows}| EXTERNAL")

        lines.append("")
        lines.extend([
            "    %% Styles",
            "    classDef centerapp fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff",
            "    classDef upstream fill:#2196F3,stroke:#1565C0,stroke-width:1.5px,color:#fff",
            "    classDef external fill:#F44336,stroke:#C62828,stroke-width:1.5px,color:#fff"
        ])

        return '\n'.join(lines)

    def _generate_upstream_diagram(self, app_code: str, groups: Dict, flows: List[Dict]) -> str:
        """Generate upstream-only diagram"""
        lines = ["graph LR"]
        lines.append(f"    %% UPSTREAM: Who sends data TO {app_code}")
        lines.append("")

        # Source apps
        for idx, (app, servers) in enumerate(groups['upstream_apps'].items()):
            flow_count = sum(1 for f in flows if f.get('source_app_code') == app and f.get('dest_app_code') == app_code)
            server_count = len(servers)

            ip_lines = [f"{s['ip']} ({s['hostname']})" for s in servers[:2]]
            if server_count > 2:
                ip_lines.append(f"... (+{server_count-2} more)")

            ips_display = "<br/>".join(ip_lines)
            lines.append(f'    SRC_APP_{idx}["<b>{app}</b><br/>{ips_display}<br/>{server_count} Servers | {flow_count} Flows"]:::sourceapp')

        # Target (this app)
        target_servers = [s for s in groups['all_app_servers'] if any(
            f.get('dest_ip') == s['ip'] for f in flows
        )]
        target_count = len(target_servers)
        target_flows = sum(1 for f in flows if f.get('dest_app_code') == app_code)

        target_ips = [f"{s['ip']} ({s['hostname']})" for s in target_servers[:2]]
        if target_count > 2:
            target_ips.append(f"... (+{target_count-2} more)")

        target_display = "<br/>".join(target_ips)
        vmware_count = sum(1 for s in target_servers if 'vmware' in s['hostname'].lower() or 'esxi' in s['hostname'].lower())
        lines.append(f'    TARGET[("<b>{app_code} (TARGET)</b><br/>{target_display}<br/>{target_count} Servers | {target_flows} Flows | {vmware_count} VMware")]:::targetapp')
        lines.append("")

        # Connections
        for idx in range(len(groups['upstream_apps'])):
            app_name = list(groups['upstream_apps'].keys())[idx]
            flow_count = sum(1 for f in flows if f.get('source_app_code') == app_name)
            lines.append(f"    SRC_APP_{idx} -->|{flow_count}| TARGET")

        lines.append("")
        lines.extend([
            "    %% Styles",
            "    classDef targetapp fill:#4CAF50,stroke:#2E7D32,stroke-width:4px,color:#fff",
            "    classDef sourceapp fill:#2196F3,stroke:#1565C0,stroke-width:3px,color:#fff"
        ])

        return '\n'.join(lines)

    def _generate_downstream_diagram(self, app_code: str, groups: Dict, flows: List[Dict]) -> str:
        """Generate downstream-only diagram"""
        lines = ["graph LR"]
        lines.append(f"    %% DOWNSTREAM: Where {app_code} sends data")
        lines.append("")

        # Source (this app)
        source_servers = [s for s in groups['all_app_servers'] if any(
            f.get('source_ip') == s['ip'] for f in flows
        )]
        source_count = len(source_servers)
        source_flows = sum(1 for f in flows if f.get('source_app_code') == app_code)

        source_ips = [f"{s['ip']} ({s['hostname']})" for s in source_servers[:3]]
        if source_count > 3:
            source_ips.append(f"... (+{source_count-3} more)")

        source_display = "<br/>".join(source_ips)
        lines.append(f'    SOURCE["<b>{app_code}</b><br/>{source_display}<br/>{source_count} Servers | {source_flows} Flows"]:::sourceapp')
        lines.append("")

        # Internal traffic
        internal_count = sum(1 for f in flows if f.get('source_app_code') == app_code and f.get('dest_app_code') == app_code)
        if internal_count > 0:
            lines.append(f'    INTERNAL["<b>Internal Traffic</b><br/>{internal_count} Flows"]:::internal')
            lines.append(f"    SOURCE .->|{internal_count}| INTERNAL")
            lines.append("")

        # External
        if groups['external']:
            ext_count = len(groups['external'])
            ext_flows = sum(1 for f in flows if f.get('source_app_code') == app_code and not f.get('dest_app_code'))

            ext_ips = [groups['external'][i]['ip'] for i in range(min(3, len(groups['external'])))]
            if ext_count > 3:
                ext_ips.append(f"... (+{ext_count-3} more)")

            ext_display = "<br/>".join(ext_ips)
            lines.append(f'    EXTERNAL["<b>External / Internet</b><br/>{ext_display}<br/>{ext_count} Destinations | {ext_flows} Flows"]:::external')
            lines.append(f"    SOURCE -->|{ext_flows}| EXTERNAL")

        lines.append("")
        lines.extend([
            "    %% Styles",
            "    classDef sourceapp fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff",
            "    classDef internal fill:#9C27B0,stroke:#6A1B9A,stroke-width:1.5px,color:#fff",
            "    classDef external fill:#F44336,stroke:#C62828,stroke-width:1.5px,color:#fff"
        ])

        return '\n'.join(lines)

    def _generate_modal_data(self, groups: Dict) -> str:
        """Generate JavaScript object with server details for modals"""
        modal_data = {}

        # Architecture view modals
        if groups['web']:
            modal_data['ARCH_WEB'] = {
                'title': f"🌐 Web Tier Servers",
                'items': groups['web']
            }

        if groups['app']:
            modal_data['ARCH_APP'] = {
                'title': f"[APP] Application Tier Servers",
                'items': groups['app']
            }

        if groups['database']:
            modal_data['ARCH_DB'] = {
                'title': f"🗄️ Database Tier Servers",
                'items': groups['database']
            }

        if groups['external']:
            modal_data['EXTERNAL'] = {
                'title': "External / Internet Destinations",
                'items': groups['external']
            }

        return json.dumps(modal_data, indent=2)

    def _perform_zero_trust_analysis(self, app_code: str, flows: List[Dict], groups: Dict) -> Dict:
        """Perform Zero Trust network analysis"""
        analysis = {
            'micro_segmentation': [],
            'least_privilege_violations': [],
            'trust_boundaries': [],
            'lateral_movement_risks': [],
            'critical_asset_exposure': [],
            'segmentation_score': 0
        }

        # Analyze micro-segmentation opportunities
        if len(groups['database']) > 0:
            db_external_flows = sum(1 for f in flows
                                   if any(f.get('source_ip') == s['ip'] for s in groups['database'])
                                   and not f.get('dest_app_code'))
            if db_external_flows > 0:
                analysis['micro_segmentation'].append({
                    'risk': 'HIGH',
                    'finding': f'Database servers have {db_external_flows} direct internet connections',
                    'recommendation': 'Isolate database tier in separate VLAN with strict firewall rules'
                })

        # Check for least privilege violations
        web_to_db_direct = sum(1 for f in flows
                              if any(f.get('source_ip') == s['ip'] for s in groups['web'])
                              and any(f.get('dest_ip') == s['ip'] for s in groups['database']))
        if web_to_db_direct > 0:
            analysis['least_privilege_violations'].append({
                'risk': 'MEDIUM',
                'finding': f'Web tier has {web_to_db_direct} direct connections to database tier',
                'recommendation': 'Enforce application tier as mandatory proxy for all database access'
            })

        # Identify trust boundaries
        zones_identified = set()
        if groups['web']: zones_identified.add('DMZ/Web')
        if groups['app']: zones_identified.add('Application')
        if groups['database']: zones_identified.add('Data')

        analysis['trust_boundaries'] = list(zones_identified)

        # Lateral movement risks
        cross_tier_flows = sum(1 for f in flows
                             if f.get('source_app_code') == app_code
                             and f.get('dest_app_code') and f.get('dest_app_code') != app_code)
        if cross_tier_flows > len(groups['upstream_apps']):
            analysis['lateral_movement_risks'].append({
                'risk': 'MEDIUM',
                'finding': f'{cross_tier_flows} connections to {len(groups["downstream_apps"])} different applications',
                'recommendation': 'Review and minimize inter-application dependencies'
            })

        # Critical asset exposure
        if groups['database']:
            upstream_count = len(groups['upstream_apps'])
            if upstream_count > 5:
                analysis['critical_asset_exposure'].append({
                    'risk': 'HIGH',
                    'finding': f'Database accessible from {upstream_count} upstream applications',
                    'recommendation': 'Implement database access control layer with authentication'
                })

        # Calculate segmentation score (0-100)
        score = 100
        score -= len(analysis['micro_segmentation']) * 20
        score -= len(analysis['least_privilege_violations']) * 10
        score -= len(analysis['lateral_movement_risks']) * 5
        score -= len(analysis['critical_asset_exposure']) * 15
        analysis['segmentation_score'] = max(0, score)

        return analysis

    def _generate_executive_deliverables(self, app_code: str, stats: Dict, zt_analysis: Dict) -> Dict:
        """Generate executive summary and deliverables"""
        deliverables = {
            'risk_summary': {'high': 0, 'medium': 0, 'low': 0},
            'key_findings': [],
            'recommendations': [],
            'compliance_impact': [],
            'implementation_timeline': []
        }

        # Count risks
        for finding_list in [zt_analysis['micro_segmentation'],
                            zt_analysis['least_privilege_violations'],
                            zt_analysis['lateral_movement_risks'],
                            zt_analysis['critical_asset_exposure']]:
            for finding in finding_list:
                risk = finding.get('risk', 'LOW')
                deliverables['risk_summary'][risk.lower()] += 1

        # Key findings
        all_findings = (zt_analysis['micro_segmentation'] +
                       zt_analysis['least_privilege_violations'] +
                       zt_analysis['lateral_movement_risks'] +
                       zt_analysis['critical_asset_exposure'])

        deliverables['key_findings'] = sorted(all_findings,
                                             key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x['risk'], 3))[:5]

        # Recommendations (prioritized)
        for finding in deliverables['key_findings']:
            deliverables['recommendations'].append({
                'priority': finding['risk'],
                'action': finding['recommendation'],
                'effort': 'Medium' if finding['risk'] == 'HIGH' else 'Low'
            })

        # Compliance impact
        if deliverables['risk_summary']['high'] > 0:
            deliverables['compliance_impact'].append('PCI-DSS: Network segmentation requirements may not be met')
        if stats['failed_dns'] > stats['total_flows'] * 0.3:
            deliverables['compliance_impact'].append('SOC 2: Asset inventory completeness concerns')

        # Implementation timeline
        if deliverables['risk_summary']['high'] > 0:
            deliverables['implementation_timeline'].append({
                'phase': 'Phase 1 (Immediate)',
                'duration': '2-4 weeks',
                'actions': 'Address HIGH risk findings'
            })
        if deliverables['risk_summary']['medium'] > 0:
            deliverables['implementation_timeline'].append({
                'phase': 'Phase 2 (Short-term)',
                'duration': '1-2 months',
                'actions': 'Address MEDIUM risk findings and enhance monitoring'
            })

        return deliverables


    def _generate_complete_html(self, app_code: str, stats: Dict, diagrams: Dict,
                                modal_data: str, zt_analysis: Dict, exec_deliverables: Dict) -> str:
        """Generate complete HTML with all features - COMPLETE IMPLEMENTATION"""

        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        zt_html = self._build_zero_trust_html(zt_analysis)
        exec_html = self._build_executive_html(exec_deliverables)

        # Complete HTML with all features
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{app_code} - Enhanced Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .header .subtitle {{ font-size: 1.2em; opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; padding: 20px 30px; background: #f8f9fa; }}
        .stat-card {{ background: white; padding: 12px 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-3px); box-shadow: 0 4px 15px rgba(0,0,0,0.12); }}
        .stat-card .value {{ font-size: 1.8em; font-weight: bold; color: #2a5298; margin-bottom: 3px; }}
        .stat-card .label {{ color: #666; font-size: 0.75em; line-height: 1.2; }}
        .toggle-section {{ padding: 20px 30px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }}
        .btn-toggle {{ padding: 12px 24px; border: 2px solid #2a5298; background: white; color: #2a5298; font-weight: 600; border-radius: 5px; cursor: pointer; font-size: 15px; transition: all 0.3s; }}
        .btn-toggle:hover {{ background: #e3f2fd; }}
        .btn-toggle.active {{ background: #2a5298; color: white; }}
        .controls {{ padding: 20px 30px; background: #fff; border-bottom: 2px solid #e0e0e0; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }}
        .btn {{ padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; }}
        .btn-primary {{ background: #2a5298; color: white; }}
        .btn-primary:hover {{ background: #1e3c72; transform: scale(1.05); }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .diagram-container {{ padding: 30px; background: white; overflow-x: auto; width: 100%; position: relative; }}
        .diagram-view {{ min-height: 600px; background: white; width: 100%; display: none; }}
        .diagram-view.active-view {{ display: block; }}
        .mermaid {{ width: 100%; max-width: 100%; }}
        .analysis-section {{ padding: 30px; background: white; border-top: 2px solid #e0e0e0; }}
        .analysis-section h2 {{ color: #1e3c72; margin-bottom: 20px; font-size: 1.8em; }}
        .analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .analysis-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #2a5298; }}
        .analysis-card h3 {{ color: #2a5298; margin-bottom: 15px; font-size: 1.2em; }}
        .risk-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: 600; margin-right: 8px; }}
        .risk-high {{ background: #ffebee; color: #c62828; }}
        .risk-medium {{ background: #fff3e0; color: #ef6c00; }}
        .risk-low {{ background: #e8f5e9; color: #2e7d32; }}
        .finding-item {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .segmentation-score {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin: 20px 0; }}
        .score-value {{ font-size: 4em; font-weight: bold; margin: 10px 0; }}
        .footer {{ padding: 20px 30px; background: #2a5298; color: white; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{app_code}</h1>
            <div class="subtitle">Enhanced Application Architecture & Zero Trust Analysis</div>
            <div class="subtitle">Generated on {timestamp}</div>
        </div>

        <div class="stats">
            <div class="stat-card"><div class="value">{stats['total_flows']}</div><div class="label">Total Flows</div></div>
            <div class="stat-card"><div class="value">{stats['internal_flows']}</div><div class="label">Internal Flows</div></div>
            <div class="stat-card"><div class="value">{stats['outbound_to_apps']}</div><div class="label">Outbound to Apps</div></div>
            <div class="stat-card"><div class="value">{stats['external_flows']}</div><div class="label">External Flows</div></div>
            <div class="stat-card"><div class="value">{stats['destination_apps_count']}</div><div class="label">Destination Apps</div></div>
            <div class="stat-card"><div class="value">{stats['vmware_instances']}</div><div class="label">VMware Instances</div></div>
            <div class="stat-card"><div class="value">{stats['failed_dns']}</div><div class="label">Failed DNS</div></div>
        </div>

        <div class="toggle-section">
            <button class="btn-toggle active" onclick="showView('architecture')" id="btn-architecture">[ARCH] Architecture</button>
            <button class="btn-toggle" onclick="showView('fullflow')" id="btn-fullflow">[FLOW] Full Flow</button>
            <button class="btn-toggle" onclick="showView('upstream')" id="btn-upstream">[UP] Upstream</button>
            <button class="btn-toggle" onclick="showView('downstream')" id="btn-downstream">[DOWN] Downstream</button>
            <button class="btn-toggle" onclick="showView('zerotrust')" id="btn-zerotrust">[ZT] Zero Trust</button>
            <button class="btn-toggle" onclick="showView('executive')" id="btn-executive">[EXEC] Executive</button>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="zoomIn()">[ZOOM] Zoom In</button>
            <button class="btn btn-primary" onclick="zoomOut()">[ZOOM] Zoom Out</button>
            <button class="btn btn-primary" onclick="resetZoom()">[RESET] Reset</button>
        </div>

        <div class="diagram-container">
            <div id="view-architecture" class="diagram-view active-view">
                <pre class="mermaid">{diagrams['architecture']}</pre>
            </div>
            <div id="view-fullflow" class="diagram-view">
                <pre class="mermaid">{diagrams['fullflow']}</pre>
            </div>
            <div id="view-upstream" class="diagram-view">
                <pre class="mermaid">{diagrams['upstream']}</pre>
            </div>
            <div id="view-downstream" class="diagram-view">
                <pre class="mermaid">{diagrams['downstream']}</pre>
            </div>
            <div id="view-zerotrust" class="diagram-view">{zt_html}</div>
            <div id="view-executive" class="diagram-view">{exec_html}</div>
        </div>

        <div class="footer">&copy; 2025 Enterprise Security Team | Network Segmentation Analysis</div>
    </div>

    <script>
        // Render all Mermaid diagrams on page load
        mermaid.initialize({{startOnLoad: false, theme: 'default', securityLevel: 'loose'}});

        window.addEventListener('load', function() {{
            mermaid.run();
        }});

        let currentZoom = 1;
        let currentView = 'architecture';

        function showView(view) {{
            ['architecture', 'fullflow', 'upstream', 'downstream', 'zerotrust', 'executive'].forEach(v => {{
                document.getElementById('view-' + v).classList.remove('active-view');
                document.getElementById('btn-' + v).classList.remove('active');
            }});
            document.getElementById('view-' + view).classList.add('active-view');
            document.getElementById('btn-' + view).classList.add('active');
            currentView = view;
            resetZoom();
        }}

        function zoomIn() {{ currentZoom += 0.1; document.getElementById('view-' + currentView).style.transform = `scale(${{currentZoom}})`; }}
        function zoomOut() {{ currentZoom = Math.max(0.5, currentZoom - 0.1); document.getElementById('view-' + currentView).style.transform = `scale(${{currentZoom}})`; }}
        function resetZoom() {{ currentZoom = 1; document.getElementById('view-' + currentView).style.transform = 'scale(1)'; }}
    </script>
</body>
</html>'''

    def _build_zero_trust_html(self, zt_analysis: Dict) -> str:
        """Build Zero Trust Analysis section"""
        score_color = '#4CAF50' if zt_analysis['segmentation_score'] > 70 else '#FF9800' if zt_analysis['segmentation_score'] > 40 else '#F44336'
        html = f'''<div class="analysis-section">
            <h2>[ZT] Zero Trust Network Analysis</h2>
            <div class="segmentation-score">
                <h3>Segmentation Score</h3>
                <div class="score-value" style="color: {score_color};">{zt_analysis['segmentation_score']}</div>
                <p>Out of 100</p>
            </div>
            <div class="analysis-grid">'''

        for finding in zt_analysis.get('micro_segmentation', []) + zt_analysis.get('least_privilege_violations', []) + zt_analysis.get('critical_asset_exposure', []):
            html += f'''<div class="analysis-card">
                <div class="finding-item">
                    <span class="risk-badge risk-{finding['risk'].lower()}">{finding['risk']}</span>
                    <p><strong>Finding:</strong> {finding['finding']}</p>
                    <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
                </div>
            </div>'''

        html += '''</div></div>'''
        return html

    def _build_executive_html(self, exec_deliverables: Dict) -> str:
        """Build Executive Summary section"""
        html = f'''<div class="analysis-section">
            <h2>[EXEC] Executive Summary</h2>
            <div class="analysis-grid">
                <div class="analysis-card">
                    <h3>Risk Summary</h3>
                    <div class="finding-item">
                        <span class="risk-badge risk-high">HIGH: {exec_deliverables['risk_summary']['high']}</span>
                        <span class="risk-badge risk-medium">MEDIUM: {exec_deliverables['risk_summary']['medium']}</span>
                        <span class="risk-badge risk-low">LOW: {exec_deliverables['risk_summary']['low']}</span>
                    </div>
                </div>'''

        if exec_deliverables['key_findings']:
            html += '''<div class="analysis-card"><h3>Top Findings</h3>'''
            for finding in exec_deliverables['key_findings'][:3]:
                html += f'''<div class="finding-item">
                    <span class="risk-badge risk-{finding['risk'].lower()}">{finding['risk']}</span>
                    <p>{finding['finding']}</p>
                </div>'''
            html += '''</div>'''

        if exec_deliverables['recommendations']:
            html += '''<div class="analysis-card"><h3>Recommendations</h3>'''
            for idx, rec in enumerate(exec_deliverables['recommendations'][:3], 1):
                html += f'''<div class="finding-item">
                    <p><strong>{idx}. [{rec['priority']}]</strong> {rec['action']}</p>
                    <p style="color: #666;">Effort: {rec['effort']}</p>
                </div>'''
            html += '''</div>'''

        html += '''</div></div>'''
        return html
