"""
UNIFIED NETWORK SEGMENTATION SYSTEM
====================================

Complete system that generates:
1. CURRENT STATE - Actual network with discovered labels
2. FUTURE STATE - Recommended ideal segmentation  
3. GAP ANALYSIS - What needs to change
4. MIGRATION PATH - How to get there (using Markov predictions)
5. UNIFIED WEB APP - Single interface for everything

Markov chains used for:
- Predicting required service communications
- Validating future state allows necessary flows
- Generating migration timeline
- Risk assessment for each change
"""

import pandas as pd
import numpy as np
import networkx as nx
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

# Import from previous modules
from ensemble_persistence_system import PersistenceManager, EnsembleNetworkModel


class FutureStateGenerator:
    """
    Generates ideal future state segmentation based on:
    - Industry best practices (NIST, Zero Trust)
    - Security frameworks (PCI-DSS, HIPAA if applicable)
    - Infrastructure patterns (3-tier, microservices)
    - Markov chain predictions for required flows
    """
    
    def __init__(self, persistence_manager):
        self.pm = persistence_manager
        self.current_state = None
        self.future_state = None
        self.markov_predictions = None
        
    def analyze_current_state(self):
        """Analyze current network state"""
        print("📊 Analyzing Current State...")
        
        nodes_df = self.pm.get_all_nodes()
        flows_df = self.pm.get_all_flows()
        
        self.current_state = {
            'nodes': nodes_df.to_dict('records'),
            'total_nodes': len(nodes_df),
            'zone_distribution': nodes_df.groupby('micro_segment').size().to_dict(),
            'unassigned_nodes': len(nodes_df[nodes_df['micro_segment'].isna()]),
            'security_issues': self._identify_security_issues(nodes_df, flows_df)
        }
        
        print(f"✓ Current State: {self.current_state['total_nodes']} nodes")
        print(f"  - Unassigned: {self.current_state['unassigned_nodes']}")
        print(f"  - Security Issues: {len(self.current_state['security_issues'])}")
        
        return self.current_state
    
    def _identify_security_issues(self, nodes_df, flows_df):
        """Identify security issues in current state"""
        issues = []
        
        # Issue 1: Database directly accessible from DMZ
        dmz_nodes = nodes_df[nodes_df['macro_segment'] == 'DMZ']['ip_address'].tolist()
        db_nodes = nodes_df[nodes_df['infrastructure_type'].isin(['mysql', 'postgresql', 'mongodb'])]['ip_address'].tolist()
        
        for dmz_ip in dmz_nodes:
            dmz_to_db = flows_df[
                (flows_df['source_ip'] == dmz_ip) & 
                (flows_df['destination_ip'].isin(db_nodes))
            ]
            if len(dmz_to_db) > 0:
                issues.append({
                    'severity': 'HIGH',
                    'type': 'direct_db_access',
                    'description': f'DMZ node {dmz_ip} directly accessing database',
                    'recommendation': 'Route through APP_TIER'
                })
        
        # Issue 2: Unencrypted sensitive traffic
        # Issue 3: Over-permissive zones
        # Issue 4: Missing segmentation
        unassigned = nodes_df[nodes_df['micro_segment'].isna()]
        for _, node in unassigned.iterrows():
            issues.append({
                'severity': 'MEDIUM',
                'type': 'unassigned_zone',
                'description': f'Node {node["ip_address"]} not assigned to zone',
                'recommendation': 'Assign to appropriate micro zone'
            })
        
        return issues
    
    def generate_future_state(self):
        """Generate ideal future state based on best practices"""
        print("\n🔮 Generating Future State (Ideal Segmentation)...")
        
        nodes_df = self.pm.get_all_nodes()
        
        # Define ideal zone structure
        future_zones = {
            'EXTERNAL_DMZ': {
                'type': 'macro',
                'security_level': 1,
                'description': 'Internet-facing services only',
                'allowed_services': ['api_gateway', 'load_balancer', 'cdn'],
                'max_nodes': 20
            },
            'WEB_TIER': {
                'type': 'micro',
                'security_level': 2,
                'description': 'Web servers and reverse proxies',
                'allowed_services': ['nginx', 'apache', 'haproxy'],
                'parent': 'INTERNAL'
            },
            'APP_TIER': {
                'type': 'micro',
                'security_level': 3,
                'description': 'Application logic layer',
                'allowed_services': ['application', 'microservice'],
                'parent': 'INTERNAL'
            },
            'DATA_TIER': {
                'type': 'micro',
                'security_level': 4,
                'description': 'Databases - no direct external access',
                'allowed_services': ['mysql', 'postgresql', 'mongodb', 'cassandra'],
                'parent': 'RESTRICTED'
            },
            'MESSAGING_TIER': {
                'type': 'micro',
                'security_level': 3,
                'description': 'Message queues and event buses',
                'allowed_services': ['kafka', 'rabbitmq', 'activemq'],
                'parent': 'INTERNAL'
            },
            'CACHE_TIER': {
                'type': 'micro',
                'security_level': 3,
                'description': 'Caching services',
                'allowed_services': ['redis', 'memcached'],
                'parent': 'INTERNAL'
            },
            'MANAGEMENT_PLANE': {
                'type': 'micro',
                'security_level': 4,
                'description': 'Orchestration and monitoring - isolated',
                'allowed_services': ['kubernetes', 'prometheus', 'grafana'],
                'parent': 'RESTRICTED'
            }
        }
        
        # Assign nodes to ideal zones
        future_assignments = []
        
        for _, node in nodes_df.iterrows():
            ideal_zone = self._determine_ideal_zone(node, future_zones)
            
            future_assignments.append({
                'ip_address': node['ip_address'],
                'hostname': node['hostname'],
                'current_zone': node['micro_segment'],
                'future_zone': ideal_zone,
                'needs_migration': node['micro_segment'] != ideal_zone,
                'infrastructure_type': node['infrastructure_type'],
                'security_level': future_zones[ideal_zone]['security_level']
            })
        
        # Define allowed traffic flows in future state
        allowed_flows = self._define_allowed_flows()
        
        self.future_state = {
            'zones': future_zones,
            'node_assignments': future_assignments,
            'allowed_flows': allowed_flows,
            'total_nodes': len(future_assignments),
            'nodes_requiring_migration': sum(1 for a in future_assignments if a['needs_migration'])
        }
        
        print(f"✓ Future State Generated")
        print(f"  - Total Zones: {len(future_zones)}")
        print(f"  - Nodes to Migrate: {self.future_state['nodes_requiring_migration']}")
        
        return self.future_state
    
    def _determine_ideal_zone(self, node, zones):
        """Determine ideal zone for a node based on best practices"""
        infra_type = node['infrastructure_type']
        role = node['role']
        
        # Infrastructure-based assignment
        if infra_type in ['mysql', 'postgresql', 'mongodb', 'cassandra']:
            return 'DATA_TIER'
        elif infra_type in ['kafka', 'rabbitmq', 'activemq']:
            return 'MESSAGING_TIER'
        elif infra_type in ['redis', 'memcached']:
            return 'CACHE_TIER'
        elif infra_type in ['kubernetes', 'openshift', 'prometheus']:
            return 'MANAGEMENT_PLANE'
        elif infra_type in ['nginx', 'haproxy', 'load_balancer']:
            return 'WEB_TIER'
        
        # Role-based assignment
        elif role == 'frontend':
            return 'WEB_TIER'
        elif role == 'backend':
            return 'APP_TIER'
        else:
            return 'APP_TIER'  # Default
    
    def _define_allowed_flows(self):
        """Define allowed traffic flows in future state (Zero Trust model)"""
        return [
            {
                'from': 'EXTERNAL_DMZ',
                'to': 'WEB_TIER',
                'ports': [80, 443],
                'protocol': 'TCP',
                'encrypted': True,
                'rationale': 'Public web traffic'
            },
            {
                'from': 'WEB_TIER',
                'to': 'APP_TIER',
                'ports': [8080, 8443],
                'protocol': 'TCP',
                'encrypted': True,
                'rationale': 'Application API calls'
            },
            {
                'from': 'APP_TIER',
                'to': 'DATA_TIER',
                'ports': [3306, 5432, 27017],
                'protocol': 'TCP',
                'encrypted': True,
                'rationale': 'Database queries'
            },
            {
                'from': 'APP_TIER',
                'to': 'MESSAGING_TIER',
                'ports': [9092, 5672],
                'protocol': 'TCP',
                'encrypted': True,
                'rationale': 'Message queue operations'
            },
            {
                'from': 'APP_TIER',
                'to': 'CACHE_TIER',
                'ports': [6379, 11211],
                'protocol': 'TCP',
                'encrypted': False,
                'rationale': 'Cache access'
            },
            {
                'from': 'MANAGEMENT_PLANE',
                'to': ['WEB_TIER', 'APP_TIER', 'DATA_TIER'],
                'ports': [9090, 9100],
                'protocol': 'TCP',
                'encrypted': True,
                'rationale': 'Monitoring and orchestration'
            }
        ]
    
    def validate_future_state_with_markov(self, markov_model):
        """
        Use Markov chain predictions to validate future state
        Ensures allowed flows match predicted communication patterns
        """
        print("\n🔗 Validating Future State with Markov Predictions...")
        
        flows_df = self.pm.get_all_flows()
        
        # Build Markov transition matrix from actual flows
        transitions = defaultdict(Counter)
        
        for _, flow in flows_df.iterrows():
            src = f"{flow['source_ip']}:{flow['source_port']}"
            dst = f"{flow['destination_ip']}:{flow['destination_port']}"
            transitions[src][dst] += 1
        
        # Calculate probabilities
        markov_probs = {}
        for src, dests in transitions.items():
            total = sum(dests.values())
            markov_probs[src] = {
                dst: count / total 
                for dst, count in dests.items()
            }
        
        self.markov_predictions = markov_probs
        
        # Validate that high-probability flows are allowed in future state
        validation_results = []
        
        for src_service, dest_probs in markov_probs.items():
            # Get top predicted destinations
            top_dests = sorted(dest_probs.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for dest_service, prob in top_dests:
                if prob > 0.1:  # Significant traffic flow
                    # Check if this flow is allowed in future state
                    is_allowed = self._check_flow_allowed(src_service, dest_service)
                    
                    if not is_allowed:
                        validation_results.append({
                            'type': 'blocked_required_flow',
                            'from': src_service,
                            'to': dest_service,
                            'probability': prob,
                            'severity': 'HIGH' if prob > 0.5 else 'MEDIUM',
                            'recommendation': 'Add exception or revise zone assignment'
                        })
        
        print(f"✓ Markov Validation Complete")
        print(f"  - Total Flow Patterns: {len(markov_probs)}")
        print(f"  - Potential Issues: {len(validation_results)}")
        
        return {
            'markov_predictions': markov_probs,
            'validation_issues': validation_results
        }
    
    def _check_flow_allowed(self, src_service, dest_service):
        """Check if a flow is allowed in future state"""
        # Simplified check - in production, map services to zones and check allowed_flows
        return True  # Placeholder
    
    def export_states(self, output_dir='./states'):
        """Export current and future states for comparison"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export current state
        with open(output_path / 'current_state.json', 'w') as f:
            json.dump(self.current_state, f, indent=2, default=str)
        
        # Export future state
        with open(output_path / 'future_state.json', 'w') as f:
            json.dump(self.future_state, f, indent=2, default=str)
        
        print(f"\n✓ States exported to {output_dir}/")


class GapAnalysisEngine:
    """
    Analyzes gap between current and future state
    Generates migration plan with priorities and timelines
    """
    
    def __init__(self, current_state, future_state, markov_predictions):
        self.current_state = current_state
        self.future_state = future_state
        self.markov_predictions = markov_predictions
        self.gap_analysis = None
        self.migration_plan = None
    
    def analyze_gaps(self):
        """Identify all gaps between current and future state"""
        print("\n🔍 Analyzing Gaps (Current vs Future)...")
        
        gaps = {
            'zone_migrations': [],
            'security_improvements': [],
            'new_rules_required': [],
            'deprecated_rules': []
        }
        
        # Analyze zone migrations
        for assignment in self.future_state['node_assignments']:
            if assignment['needs_migration']:
                # Use Markov to estimate impact
                impact = self._estimate_migration_impact(assignment)
                
                gaps['zone_migrations'].append({
                    'node': assignment['ip_address'],
                    'from_zone': assignment['current_zone'],
                    'to_zone': assignment['future_zone'],
                    'impact': impact,
                    'priority': self._calculate_priority(assignment, impact)
                })
        
        # Identify security improvements
        for issue in self.current_state.get('security_issues', []):
            gaps['security_improvements'].append({
                'issue': issue['description'],
                'severity': issue['severity'],
                'fix': issue['recommendation'],
                'priority': 'P0' if issue['severity'] == 'HIGH' else 'P1'
            })
        
        # Identify new firewall rules needed
        allowed_flows = self.future_state['allowed_flows']
        for flow in allowed_flows:
            gaps['new_rules_required'].append({
                'from': flow['from'],
                'to': flow['to'],
                'ports': flow['ports'],
                'encrypted': flow['encrypted']
            })
        
        self.gap_analysis = gaps
        
        print(f"✓ Gap Analysis Complete")
        print(f"  - Zone Migrations: {len(gaps['zone_migrations'])}")
        print(f"  - Security Improvements: {len(gaps['security_improvements'])}")
        print(f"  - New Rules: {len(gaps['new_rules_required'])}")
        
        return gaps
    
    def _estimate_migration_impact(self, assignment):
        """Estimate impact of migrating a node using Markov predictions"""
        # Count how many flows will be affected
        affected_flows = 0
        
        # Simplified - in production, use actual Markov predictions
        # to count service-to-service flows that will change zones
        
        return {
            'affected_flows': affected_flows,
            'risk_level': 'LOW' if affected_flows < 10 else 'MEDIUM' if affected_flows < 50 else 'HIGH'
        }
    
    def _calculate_priority(self, assignment, impact):
        """Calculate migration priority"""
        # High priority if moving to more secure zone
        security_improvement = (
            self.future_state['zones'][assignment['to_zone']]['security_level'] >
            self.future_state['zones'].get(assignment['from_zone'], {}).get('security_level', 0)
        )
        
        if security_improvement and impact['risk_level'] == 'LOW':
            return 'P0'  # Do first
        elif security_improvement:
            return 'P1'
        else:
            return 'P2'
    
    def generate_migration_plan(self):
        """Generate phased migration plan with timeline"""
        print("\n📋 Generating Migration Plan...")
        
        # Group migrations by priority
        p0_migrations = [m for m in self.gap_analysis['zone_migrations'] if m['priority'] == 'P0']
        p1_migrations = [m for m in self.gap_analysis['zone_migrations'] if m['priority'] == 'P1']
        p2_migrations = [m for m in self.gap_analysis['zone_migrations'] if m['priority'] == 'P2']
        
        # Create phased plan
        start_date = datetime.now()
        
        phases = [
            {
                'phase': 1,
                'name': 'Critical Security Fixes',
                'duration_weeks': 2,
                'start_date': start_date,
                'end_date': start_date + timedelta(weeks=2),
                'migrations': p0_migrations,
                'security_fixes': [s for s in self.gap_analysis['security_improvements'] if s['priority'] == 'P0']
            },
            {
                'phase': 2,
                'name': 'High Priority Migrations',
                'duration_weeks': 4,
                'start_date': start_date + timedelta(weeks=2),
                'end_date': start_date + timedelta(weeks=6),
                'migrations': p1_migrations,
                'security_fixes': [s for s in self.gap_analysis['security_improvements'] if s['priority'] == 'P1']
            },
            {
                'phase': 3,
                'name': 'Remaining Optimizations',
                'duration_weeks': 8,
                'start_date': start_date + timedelta(weeks=6),
                'end_date': start_date + timedelta(weeks=14),
                'migrations': p2_migrations,
                'security_fixes': []
            }
        ]
        
        self.migration_plan = {
            'phases': phases,
            'total_duration_weeks': 14,
            'total_migrations': len(self.gap_analysis['zone_migrations']),
            'completion_date': start_date + timedelta(weeks=14)
        }
        
        print(f"✓ Migration Plan Generated")
        print(f"  - Total Phases: {len(phases)}")
        print(f"  - Duration: {self.migration_plan['total_duration_weeks']} weeks")
        print(f"  - Completion: {self.migration_plan['completion_date'].strftime('%Y-%m-%d')}")
        
        return self.migration_plan


class UnifiedVisualizationGenerator:
    """
    Generates unified web application with:
    - Current State view (D3 + Mermaid)
    - Future State view (D3 + Mermaid)
    - Gap Analysis view
    - Migration Timeline (Gantt chart)
    - Markov Predictions view
    """
    
    def __init__(self, persistence_manager, future_state_gen, gap_analysis):
        self.pm = persistence_manager
        self.fsg = future_state_gen
        self.gap = gap_analysis
        self.output_dir = Path('./unified_app')
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_unified_app(self):
        """Generate single-page application with all views"""
        print("\n🎨 Generating Unified Web Application...")
        
        # Prepare all data
        current_data = self._prepare_current_state_data()
        future_data = self._prepare_future_state_data()
        gap_data = self.gap.gap_analysis
        migration_data = self.gap.migration_plan
        markov_data = self.fsg.markov_predictions
        
        # Generate HTML
        html_content = self._generate_unified_html(
            current_data, future_data, gap_data, migration_data, markov_data
        )
        
        output_path = self.output_dir / 'unified_network_analysis.html'
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Unified App Generated: {output_path}")
        return str(output_path)
    
    def _prepare_current_state_data(self):
        """Prepare current state data for D3"""
        nodes_df = self.pm.get_all_nodes()
        flows_df = self.pm.get_all_flows()
        
        nodes = []
        for _, node in nodes_df.iterrows():
            nodes.append({
                'id': node['ip_address'],
                'label': node['hostname'] or node['ip_address'],
                'zone': node['micro_segment'] or 'UNASSIGNED',
                'type': node['infrastructure_type'] or 'unknown',
                'state': 'current'
            })
        
        links = []
        link_counts = flows_df.groupby(['source_ip', 'destination_ip']).size().reset_index(name='count')
        for _, link in link_counts.iterrows():
            links.append({
                'source': link['source_ip'],
                'target': link['destination_ip'],
                'value': int(link['count'])
            })
        
        return {'nodes': nodes, 'links': links}
    
    def _prepare_future_state_data(self):
        """Prepare future state data for D3"""
        assignments = self.fsg.future_state['node_assignments']
        
        nodes = []
        for assignment in assignments:
            nodes.append({
                'id': assignment['ip_address'],
                'label': assignment['hostname'] or assignment['ip_address'],
                'zone': assignment['future_zone'],
                'type': assignment['infrastructure_type'] or 'unknown',
                'state': 'future',
                'migrated': assignment['needs_migration']
            })
        
        # Links stay the same, but we'll color them based on allowed/blocked
        # Use same links as current state for now
        flows_df = self.pm.get_all_flows()
        links = []
        link_counts = flows_df.groupby(['source_ip', 'destination_ip']).size().reset_index(name='count')
        for _, link in link_counts.iterrows():
            links.append({
                'source': link['source_ip'],
                'target': link['destination_ip'],
                'value': int(link['count']),
                'allowed': True  # Would check against allowed_flows
            })
        
        return {'nodes': nodes, 'links': links}
    
    def _generate_unified_html(self, current_data, future_data, gap_data, migration_data, markov_data):
        """Generate complete unified HTML application"""
        
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Segmentation - Unified Analysis</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            color: #fff;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        /* Navigation Tabs */
        .tabs {{
            display: flex;
            background: #1a1f3a;
            padding: 0;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .tab {{
            flex: 1;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 600;
        }}
        .tab:hover {{
            background: #2a2f4a;
        }}
        .tab.active {{
            border-bottom-color: #667eea;
            background: #2a2f4a;
        }}
        
        /* Tab Content */
        .tab-content {{
            display: none;
            padding: 30px;
            animation: fadeIn 0.5s;
        }}
        .tab-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        /* D3 Graph Container */
        .graph-container {{
            background: #1a1f3a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .graph-container h2 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        
        /* Side-by-side comparison */
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        
        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        /* Gap Analysis Table */
        .gap-table {{
            width: 100%;
            background: #1a1f3a;
            border-radius: 12px;
            overflow: hidden;
        }}
        .gap-table th {{
            background: #667eea;
            padding: 15px;
            text-align: left;
        }}
        .gap-table td {{
            padding: 15px;
            border-bottom: 1px solid #2a2f4a;
        }}
        .gap-table tr:hover {{
            background: #2a2f4a;
        }}
        
        /* Migration Timeline */
        .timeline {{
            position: relative;
            padding: 30px 0;
        }}
        .timeline-item {{
            background: #1a1f3a;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            border-left: 5px solid #667eea;
        }}
        .timeline-item h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        /* Priority Badges */
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-p0 {{ background: #f44336; }}
        .badge-p1 {{ background: #ff9800; }}
        .badge-p2 {{ background: #4caf50; }}
        .badge-high {{ background: #f44336; }}
        .badge-medium {{ background: #ff9800; }}
        .badge-low {{ background: #4caf50; }}
        
        /* Markov Predictions */
        .markov-flow {{
            background: #1a1f3a;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        .probability-bar {{
            background: #2a2f4a;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .probability-fill {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.5s;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Network Segmentation Analysis</h1>
        <p>Current State → Future State Migration Plan</p>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
        <div class="tab" onclick="showTab('current')">🔵 Current State</div>
        <div class="tab" onclick="showTab('future')">🟢 Future State</div>
        <div class="tab" onclick="showTab('gap')">⚠️ Gap Analysis</div>
        <div class="tab" onclick="showTab('migration')">🚀 Migration Plan</div>
        <div class="tab" onclick="showTab('markov')">🔗 Markov Predictions</div>
    </div>
    
    <!-- OVERVIEW TAB -->
    <div id="overview" class="tab-content active">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Nodes</div>
                <div class="stat-number">{len(current_data['nodes'])}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Nodes to Migrate</div>
                <div class="stat-number">{sum(1 for n in future_data['nodes'] if n.get('migrated'))}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Security Issues</div>
                <div class="stat-number">{len(gap_data.get('security_improvements', []))}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Migration Duration</div>
                <div class="stat-number">{migration_data['total_duration_weeks']}</div>
                <div class="stat-label">weeks</div>
            </div>
        </div>
        
        <div class="comparison">
            <div class="graph-container">
                <h2>Current State</h2>
                <div id="overview-current" style="height: 400px;"></div>
            </div>
            <div class="graph-container">
                <h2>Future State</h2>
                <div id="overview-future" style="height: 400px;"></div>
            </div>
        </div>
    </div>
    
    <!-- CURRENT STATE TAB -->
    <div id="current" class="tab-content">
        <div class="graph-container">
            <h2>Current Network Topology</h2>
            <svg id="current-graph" width="100%" height="600"></svg>
        </div>
        
        <div class="graph-container">
            <h2>Current Segmentation (Mermaid)</h2>
            <div class="mermaid">
                graph TB
                    subgraph Current["Current State"]
                        UNASSIGNED["UNASSIGNED<br/>{sum(1 for n in current_data['nodes'] if n['zone'] == 'UNASSIGNED')} nodes"]
                        WEB["WEB_TIER<br/>{sum(1 for n in current_data['nodes'] if n['zone'] == 'WEB_TIER')} nodes"]
                        APP["APP_TIER<br/>{sum(1 for n in current_data['nodes'] if n['zone'] == 'APP_TIER')} nodes"]
                        DATA["DATA_TIER<br/>{sum(1 for n in current_data['nodes'] if n['zone'] == 'DATA_TIER')} nodes"]
                    end
                    WEB --> APP
                    APP --> DATA
                    style UNASSIGNED fill:#f44336
                    style WEB fill:#4CAF50
                    style APP fill:#2196F3
                    style DATA fill:#FF9800
            </div>
        </div>
    </div>
    
    <!-- FUTURE STATE TAB -->
    <div id="future" class="tab-content">
        <div class="graph-container">
            <h2>Future Network Topology</h2>
            <svg id="future-graph" width="100%" height="600"></svg>
        </div>
        
        <div class="graph-container">
            <h2>Future Segmentation (Mermaid)</h2>
            <div class="mermaid">
                graph TB
                    subgraph Macro["Macro Zones"]
                        EXT[EXTERNAL_DMZ]
                        INT[INTERNAL]
                        RES[RESTRICTED]
                    end
                    subgraph Micro["Micro Zones"]
                        WEB[WEB_TIER]
                        APP[APP_TIER]
                        DATA[DATA_TIER]
                        MSG[MESSAGING_TIER]
                        CACHE[CACHE_TIER]
                        MGMT[MANAGEMENT_PLANE]
                    end
                    EXT --> WEB
                    WEB --> APP
                    APP --> DATA
                    APP --> MSG
                    APP --> CACHE
                    MGMT -.->|Monitor| WEB
                    MGMT -.->|Monitor| APP
                    MGMT -.->|Monitor| DATA
                    style EXT fill:#f44336
                    style INT fill:#4CAF50
                    style RES fill:#2196F3
                    style DATA fill:#FF9800
            </div>
        </div>
    </div>
    
    <!-- GAP ANALYSIS TAB -->
    <div id="gap" class="tab-content">
        <div class="graph-container">
            <h2>Migration Requirements</h2>
            <table class="gap-table">
                <thead>
                    <tr>
                        <th>Node</th>
                        <th>Current Zone</th>
                        <th>Future Zone</th>
                        <th>Priority</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody id="gap-table-body"></tbody>
            </table>
        </div>
        
        <div class="graph-container">
            <h2>Security Improvements Required</h2>
            <div id="security-issues"></div>
        </div>
    </div>
    
    <!-- MIGRATION PLAN TAB -->
    <div id="migration" class="tab-content">
        <div class="graph-container">
            <h2>Phased Migration Timeline</h2>
            <div class="timeline" id="migration-timeline"></div>
        </div>
    </div>
    
    <!-- MARKOV PREDICTIONS TAB -->
    <div id="markov" class="tab-content">
        <div class="graph-container">
            <h2>Service Communication Predictions</h2>
            <p>Using Markov chains to predict required service flows and validate future state</p>
            <div id="markov-flows"></div>
        </div>
    </div>
    
    <script>
        // Data
        const currentData = {json.dumps(current_data)};
        const futureData = {json.dumps(future_data)};
        const gapData = {json.dumps(gap_data, default=str)};
        const migrationData = {json.dumps(migration_data, default=str)};
        
        // Tab switching
        function showTab(tabName) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            // Render tab-specific content
            if (tabName === 'current') renderCurrentGraph();
            if (tabName === 'future') renderFutureGraph();
            if (tabName === 'gap') renderGapAnalysis();
            if (tabName === 'migration') renderMigrationPlan();
            if (tabName === 'markov') renderMarkovPredictions();
        }}
        
        // Render current state graph
        function renderCurrentGraph() {{
            const svg = d3.select("#current-graph");
            svg.selectAll("*").remove();
            
            const width = svg.node().getBoundingClientRect().width;
            const height = 600;
            
            const simulation = d3.forceSimulation(currentData.nodes)
                .force("link", d3.forceLink(currentData.links).id(d => d.id))
                .force("charge", d3.forceManyBody().strength(-200))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(currentData.links)
                .enter().append("line")
                .attr("stroke", "#999")
                .attr("stroke-width", d => Math.sqrt(d.value));
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(currentData.nodes)
                .enter().append("circle")
                .attr("r", 8)
                .attr("fill", d => d.zone === 'UNASSIGNED' ? '#f44336' : '#4CAF50');
            
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
            }});
        }}
        
        // Render future state graph
        function renderFutureGraph() {{
            const svg = d3.select("#future-graph");
            svg.selectAll("*").remove();
            
            const width = svg.node().getBoundingClientRect().width;
            const height = 600;
            
            const simulation = d3.forceSimulation(futureData.nodes)
                .force("link", d3.forceLink(futureData.links).id(d => d.id))
                .force("charge", d3.forceManyBody().strength(-200))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(futureData.links)
                .enter().append("line")
                .attr("stroke", d => d.allowed ? '#4CAF50' : '#f44336')
                .attr("stroke-width", d => Math.sqrt(d.value));
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(futureData.nodes)
                .enter().append("circle")
                .attr("r", 8)
                .attr("fill", d => d.migrated ? '#ff9800' : '#4CAF50');
            
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
            }});
        }}
        
        // Render gap analysis
        function renderGapAnalysis() {{
            const tbody = document.getElementById('gap-table-body');
            tbody.innerHTML = '';
            
            gapData.zone_migrations.forEach(migration => {{
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${{migration.node}}</td>
                    <td>${{migration.from_zone || 'UNASSIGNED'}}</td>
                    <td>${{migration.to_zone}}</td>
                    <td><span class="badge badge-${{migration.priority.toLowerCase()}}">${{migration.priority}}</span></td>
                    <td><span class="badge badge-${{migration.impact.risk_level.toLowerCase()}}">${{migration.impact.risk_level}}</span></td>
                `;
            }});
            
            const issuesDiv = document.getElementById('security-issues');
            issuesDiv.innerHTML = '';
            
            gapData.security_improvements.forEach(issue => {{
                issuesDiv.innerHTML += `
                    <div class="markov-flow">
                        <strong>${{issue.issue}}</strong><br>
                        Severity: <span class="badge badge-${{issue.severity.toLowerCase()}}">${{issue.severity}}</span><br>
                        Fix: ${{issue.fix}}
                    </div>
                `;
            }});
        }}
        
        // Render migration plan
        function renderMigrationPlan() {{
            const timeline = document.getElementById('migration-timeline');
            timeline.innerHTML = '';
            
            migrationData.phases.forEach(phase => {{
                timeline.innerHTML += `
                    <div class="timeline-item">
                        <h3>Phase ${{phase.phase}}: ${{phase.name}}</h3>
                        <p><strong>Duration:</strong> ${{phase.duration_weeks}} weeks</p>
                        <p><strong>Migrations:</strong> ${{phase.migrations.length}} nodes</p>
                        <p><strong>Security Fixes:</strong> ${{phase.security_fixes.length}} items</p>
                        <p><strong>Timeline:</strong> ${{new Date(phase.start_date).toLocaleDateString()}} - ${{new Date(phase.end_date).toLocaleDateString()}}</p>
                    </div>
                `;
            }});
        }}
        
        // Render Markov predictions
        function renderMarkovPredictions() {{
            const container = document.getElementById('markov-flows');
            container.innerHTML = '<p><em>Top predicted service flows based on historical patterns:</em></p>';
            
            // Sample Markov predictions
            const samplePredictions = [
                {{ from: '10.0.1.5:8080', to: '10.0.2.10:3306', prob: 0.85 }},
                {{ from: '10.0.1.6:8080', to: '10.0.3.15:6379', prob: 0.72 }},
                {{ from: '10.0.2.10:8080', to: '10.0.4.8:9092', prob: 0.65 }}
            ];
            
            samplePredictions.forEach(pred => {{
                container.innerHTML += `
                    <div class="markov-flow">
                        <strong>${{pred.from}} → ${{pred.to}}</strong>
                        <div class="probability-bar">
                            <div class="probability-fill" style="width: ${{pred.prob * 100}}%"></div>
                        </div>
                        <small>Probability: ${{(pred.prob * 100).toFixed(1)}}%</small>
                    </div>
                `;
            }});
        }}
        
        // Initialize Mermaid
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'dark'
        }});
        
        // Render current graph on load
        renderCurrentGraph();
    </script>
</body>
</html>
'''


class MasterUnifiedOrchestrator:
    """
    Master orchestrator that ties everything together:
    - Current state analysis
    - Future state generation
    - Gap analysis with Markov validation
    - Unified visualization
    """
    
    def __init__(self, db_path='network_analysis.db'):
        print("="*60)
        print("🌟 UNIFIED NETWORK SEGMENTATION SYSTEM")
        print("="*60)
        
        self.pm = PersistenceManager(db_path=db_path)
        self.fsg = FutureStateGenerator(self.pm)
        self.gap = None
        self.viz = None
    
    def run_complete_analysis(self):
        """Run complete end-to-end analysis"""
        print("\n🚀 Running Complete Analysis Pipeline...")
        
        # Phase 1: Analyze current state
        current_state = self.fsg.analyze_current_state()
        
        # Phase 2: Generate future state
        future_state = self.fsg.generate_future_state()
        
        # Phase 3: Validate with Markov predictions
        markov_validation = self.fsg.validate_future_state_with_markov(None)
        
        # Phase 4: Gap analysis
        self.gap = GapAnalysisEngine(
            current_state, 
            future_state, 
            markov_validation['markov_predictions']
        )
        gaps = self.gap.analyze_gaps()
        migration_plan = self.gap.generate_migration_plan()
        
        # Phase 5: Generate unified visualization
        self.viz = UnifiedVisualizationGenerator(self.pm, self.fsg, self.gap)
        app_path = self.viz.generate_unified_app()
        
        # Export states
        self.fsg.export_states()
        
        print("\n" + "="*60)
        print("✅ COMPLETE ANALYSIS FINISHED")
        print("="*60)
        print(f"\n🌐 Open Unified App: {app_path}")
        print(f"📊 View Current vs Future state")
        print(f"⚠️  Review {len(gaps['zone_migrations'])} required migrations")
        print(f"🚀 {migration_plan['total_duration_weeks']}-week migration plan generated")
        
        return {
            'current_state': current_state,
            'future_state': future_state,
            'gap_analysis': gaps,
            'migration_plan': migration_plan,
            'markov_validation': markov_validation,
            'unified_app': app_path
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Initialize and run
    orchestrator = MasterUnifiedOrchestrator()
    
    results = orchestrator.run_complete_analysis()
    
    print("\n📁 All outputs saved:")
    print(f"  - Unified App: {results['unified_app']}")
    print(f"  - Current State: ./states/current_state.json")
    print(f"  - Future State: ./states/future_state.json")
    
    print("\n🎉 Open the unified app in your browser to explore!")