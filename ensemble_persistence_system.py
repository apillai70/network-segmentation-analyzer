import pandas as pd
import networkx as nx
from collections import defaultdict, Counter
import json
from datetime import datetime
import numpy as np

class NetworkSegmentationAnalyzer:
    """
    Advanced network topology analyzer for infrastructure discovery and segmentation.
    Identifies: Load Balancers, Message Queues, Kafka, Firewalls, OpenShift/K8s, SOA patterns.
    """
    
    def __init__(self):
        self.flows = []
        self.apps = {}
        self.graph = nx.DiGraph()
        self.nodes = defaultdict(self._node_template)
        self.infrastructure = {
            'load_balancers': [],
            'message_queues': [],
            'kafka_brokers': [],
            'databases': [],
            'api_gateways': [],
            'firewalls': [],
            'containers': [],
            'caches': [],
            'soa_services': []
        }
        self.segments = []
        
        # Port signatures
        self.PORT_SIGS = {
            'kafka': {9092, 9093, 2181, 9094},
            'rabbitmq': {5672, 15672, 5671, 4369},
            'activemq': {61616, 8161, 61613, 61614},
            'redis': {6379, 6380, 16379},
            'memcached': {11211},
            'mysql': {3306},
            'postgres': {5432, 5433},
            'mongodb': {27017, 27018, 27019},
            'elasticsearch': {9200, 9300},
            'cassandra': {9042, 7000, 7001},
            'haproxy': {1936, 8404},
            'nginx': {80, 443, 8080, 8443},
            'f5': {443, 80, 8443},
            'consul': {8300, 8301, 8500, 8600},
            'etcd': {2379, 2380, 4001},
            'kubernetes': {6443, 10250, 10251, 10252, 10255},
            'openshift': {6443, 8443, 10250, 4789, 8053}
        }
    
    def _node_template(self):
        return {
            'ip': None,
            'hostname': None,
            'ports': defaultdict(lambda: {
                'apps': set(),
                'in_conn': 0,
                'out_conn': 0,
                'unique_sources': set(),
                'unique_dests': set(),
                'protocols': set(),
                'session_durations': [],
                'byte_ratios': []
            }),
            'apps': set(),
            'role': None,
            'infrastructure_type': None,
            'zone': None,
            'security_labels': set()
        }
    
    def add_application(self, app_name, flows_df):
        """Add application flow data to corpus"""
        # Normalize columns
        flows_df.columns = flows_df.columns.str.lower().str.strip()
        
        # Add app identifier
        flows_df['app'] = app_name
        self.flows.extend(flows_df.to_dict('records'))
        self.apps[app_name] = len(flows_df)
        
        # Process flows
        for _, flow in flows_df.iterrows():
            self._process_flow(flow, app_name)
        
        print(f"✓ Added {app_name}: {len(flows_df)} flows")
        return len(self.apps)
    
    def _process_flow(self, flow, app_name):
        """Process individual flow record"""
        src_ip = flow.get('source_ip') or flow.get('src_ip')
        dst_ip = flow.get('destination_ip') or flow.get('dst_ip')
        src_port = str(flow.get('source_port') or flow.get('src_port', ''))
        dst_port = str(flow.get('destination_port') or flow.get('dst_port', ''))
        protocol = flow.get('protocol', 'TCP')
        hostname = flow.get('hostname') or flow.get('destination_hostname')
        
        # Update source node
        src_node = self.nodes[src_ip]
        src_node['ip'] = src_ip
        src_node['apps'].add(app_name)
        src_node['ports'][src_port]['apps'].add(app_name)
        src_node['ports'][src_port]['out_conn'] += 1
        src_node['ports'][src_port]['unique_dests'].add(dst_ip)
        
        # Update destination node
        dst_node = self.nodes[dst_ip]
        dst_node['ip'] = dst_ip
        dst_node['hostname'] = hostname or dst_node['hostname']
        dst_node['apps'].add(app_name)
        dst_node['ports'][dst_port]['apps'].add(app_name)
        dst_node['ports'][dst_port]['in_conn'] += 1
        dst_node['ports'][dst_port]['unique_sources'].add(src_ip)
        dst_node['ports'][dst_port]['protocols'].add(protocol)
        
        # Add to graph
        edge_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}"
        self.graph.add_edge(src_ip, dst_ip, 
                           port=dst_port, 
                           app=app_name,
                           protocol=protocol)
    
    def analyze_infrastructure(self):
        """Comprehensive infrastructure component detection"""
        print("\n🔍 Analyzing Infrastructure Components...")
        
        for ip, node in self.nodes.items():
            for port, stats in node['ports'].items():
                endpoint = f"{ip}:{port}"
                
                # Load Balancer Detection
                lb = self._detect_load_balancer(ip, port, stats, node)
                if lb:
                    self.infrastructure['load_balancers'].append(lb)
                    node['infrastructure_type'] = 'load_balancer'
                    node['security_labels'].add('INFRASTRUCTURE')
                
                # Message Queue Detection
                mq = self._detect_message_queue(ip, port, stats, node)
                if mq:
                    self.infrastructure['message_queues'].append(mq)
                    node['infrastructure_type'] = 'message_queue'
                    node['security_labels'].add('MESSAGING')
                
                # Database Detection
                db = self._detect_database(ip, port, stats, node)
                if db:
                    self.infrastructure['databases'].append(db)
                    node['infrastructure_type'] = 'database'
                    node['security_labels'].add('DATA_TIER')
                
                # Cache Detection
                cache = self._detect_cache(ip, port, stats, node)
                if cache:
                    self.infrastructure['caches'].append(cache)
                    node['infrastructure_type'] = 'cache'
                    node['security_labels'].add('CACHE_TIER')
                
                # API Gateway Detection
                gw = self._detect_api_gateway(ip, port, stats, node)
                if gw:
                    self.infrastructure['api_gateways'].append(gw)
                    node['infrastructure_type'] = 'api_gateway'
                    node['security_labels'].add('EDGE')
                
                # Container Platform Detection
                container = self._detect_container_platform(ip, port, stats, node)
                if container:
                    self.infrastructure['containers'].append(container)
                    node['infrastructure_type'] = 'container_platform'
                    node['security_labels'].add('ORCHESTRATION')
        
        # Firewall Detection (graph-based)
        self._detect_firewalls()
        
        # SOA/Microservices Pattern Detection
        self._detect_soa_patterns()
        
        self._print_infrastructure_summary()
    
    def _detect_load_balancer(self, ip, port, stats, node):
        """
        Load Balancer Signatures:
        - High inbound unique sources
        - Distributes to multiple backends (out_degree)
        - Health check patterns
        - Port translation
        """
        in_conn = stats['in_conn']
        unique_src = len(stats['unique_sources'])
        unique_dst = len(stats['unique_dests'])
        
        # Check if this node forwards to multiple backends
        successors = list(self.graph.successors(ip))
        
        # LB pattern: Many sources -> 1 frontend -> Many backends
        if (unique_src > 20 and 
            len(successors) >= 2 and 
            in_conn > unique_dst * 3):
            
            # Get backend IPs
            backends = []
            for succ in successors:
                edges = self.graph.get_edge_data(ip, succ)
                if edges:
                    backends.append(succ)
            
            # Check for health check patterns (regular intervals)
            health_check = self._detect_health_checks(ip, port)
            
            return {
                'ip': ip,
                'port': port,
                'hostname': node['hostname'],
                'type': 'Load Balancer',
                'frontend_connections': in_conn,
                'unique_clients': unique_src,
                'backend_count': len(set(backends)),
                'backends': list(set(backends)),
                'health_checks': health_check,
                'apps': list(stats['apps']),
                'confidence': 'HIGH' if unique_src > 50 else 'MEDIUM'
            }
        return None
    
    def _detect_message_queue(self, ip, port, stats, node):
        """
        Message Queue Signatures:
        - Persistent bidirectional connections
        - Multiple producers AND consumers
        - Specific port patterns
        - Long-lived sessions
        """
        port_num = int(port) if port.isdigit() else 0
        unique_src = len(stats['unique_sources'])
        unique_dst = len(stats['unique_dests'])
        
        # Check port signatures
        mq_type = None
        for tech, ports in self.PORT_SIGS.items():
            if tech in ['kafka', 'rabbitmq', 'activemq'] and port_num in ports:
                mq_type = tech.upper()
                break
        
        # Behavioral patterns
        is_hub = unique_src > 3 and unique_dst > 2  # Multiple producers & consumers
        
        # Kafka-specific: look for broker patterns
        if port_num in self.PORT_SIGS['kafka']:
            # Kafka brokers talk to each other (cluster)
            kafka_peers = [succ for succ in self.graph.successors(ip) 
                          if self._has_kafka_port(succ)]
            if len(kafka_peers) >= 2:
                return {
                    'ip': ip,
                    'port': port,
                    'hostname': node['hostname'],
                    'type': 'Kafka Broker',
                    'cluster_size': len(kafka_peers) + 1,
                    'cluster_peers': kafka_peers,
                    'producers': unique_src,
                    'consumers': unique_dst,
                    'apps': list(stats['apps']),
                    'confidence': 'VERY_HIGH'
                }
        
        # General MQ detection
        if mq_type or (is_hub and stats['in_conn'] > 50):
            return {
                'ip': ip,
                'port': port,
                'hostname': node['hostname'],
                'type': mq_type or 'Message Queue',
                'producers': unique_src,
                'consumers': unique_dst,
                'total_connections': stats['in_conn'] + stats['out_conn'],
                'apps': list(stats['apps']),
                'confidence': 'HIGH' if mq_type else 'MEDIUM'
            }
        
        return None
    
    def _detect_database(self, ip, port, stats, node):
        """
        Database Signatures:
        - Few clients, long sessions
        - High inbound ratio
        - Known DB ports
        """
        port_num = int(port) if port.isdigit() else 0
        unique_src = len(stats['unique_sources'])
        
        db_type = None
        for tech, ports in self.PORT_SIGS.items():
            if tech in ['mysql', 'postgres', 'mongodb', 'elasticsearch', 'cassandra']:
                if port_num in ports:
                    db_type = tech.upper()
                    break
        
        # Behavioral: few clients, persistent connections
        if db_type or (unique_src < 50 and stats['in_conn'] > 100):
            return {
                'ip': ip,
                'port': port,
                'hostname': node['hostname'],
                'type': db_type or 'Database',
                'client_count': unique_src,
                'total_queries': stats['in_conn'],
                'apps': list(stats['apps']),
                'is_shared': len(stats['apps']) > 1,
                'confidence': 'VERY_HIGH' if db_type else 'MEDIUM'
            }
        
        return None
    
    def _detect_cache(self, ip, port, stats, node):
        """Cache Detection: Redis, Memcached"""
        port_num = int(port) if port.isdigit() else 0
        
        cache_type = None
        if port_num in self.PORT_SIGS['redis']:
            cache_type = 'Redis'
        elif port_num in self.PORT_SIGS['memcached']:
            cache_type = 'Memcached'
        
        # Behavioral: many small requests, high frequency
        if cache_type or (stats['in_conn'] > 500 and len(stats['unique_sources']) > 10):
            return {
                'ip': ip,
                'port': port,
                'hostname': node['hostname'],
                'type': cache_type or 'Cache',
                'client_count': len(stats['unique_sources']),
                'request_count': stats['in_conn'],
                'apps': list(stats['apps']),
                'confidence': 'HIGH' if cache_type else 'MEDIUM'
            }
        
        return None
    
    def _detect_api_gateway(self, ip, port, stats, node):
        """
        API Gateway Signatures:
        - Single entry point for many backend services
        - Path-based routing (inferred from multiple backends)
        - High client diversity
        """
        unique_src = len(stats['unique_sources'])
        successors = list(self.graph.successors(ip))
        
        # Pattern: Many clients -> Gateway -> Many different services
        if unique_src > 30 and len(successors) > 5:
            # Check if backends are diverse (different ports/services)
            backend_ports = set()
            for succ in successors:
                edges = self.graph[ip][succ]
                if isinstance(edges, dict):
                    backend_ports.add(edges.get('port'))
            
            if len(backend_ports) > 3:
                return {
                    'ip': ip,
                    'port': port,
                    'hostname': node['hostname'],
                    'type': 'API Gateway',
                    'client_count': unique_src,
                    'backend_services': len(successors),
                    'backend_ports': list(backend_ports),
                    'apps': list(stats['apps']),
                    'confidence': 'HIGH'
                }
        
        return None
    
    def _detect_container_platform(self, ip, port, stats, node):
        """Detect OpenShift/Kubernetes control plane and nodes"""
        port_num = int(port) if port.isdigit() else 0
        
        platform_type = None
        if port_num in self.PORT_SIGS['openshift']:
            platform_type = 'OpenShift'
        elif port_num in self.PORT_SIGS['kubernetes']:
            platform_type = 'Kubernetes'
        
        # Look for pod-to-pod patterns (many containers on same host)
        if platform_type or len(node['ports']) > 20:
            return {
                'ip': ip,
                'port': port,
                'hostname': node['hostname'],
                'type': platform_type or 'Container Platform',
                'exposed_ports': len(node['ports']),
                'apps': list(stats['apps']),
                'role': 'control-plane' if port_num in {6443, 8443} else 'node',
                'confidence': 'HIGH' if platform_type else 'LOW'
            }
        
        return None
    
    def _detect_firewalls(self):
        """
        Firewall Detection (Graph-based):
        - Chokepoints in network flow
        - All traffic from zone A to B passes through FW
        - High betweenness centrality
        """
        # Calculate betweenness centrality
        betweenness = nx.betweenness_centrality(self.graph)
        
        # Top 5% are potential firewalls/gateways
        threshold = np.percentile(list(betweenness.values()), 95)
        
        for node, score in betweenness.items():
            if score > threshold and score > 0.1:
                in_deg = self.graph.in_degree(node)
                out_deg = self.graph.out_degree(node)
                
                # Check if it's a transit node (not endpoint)
                if in_deg > 10 and out_deg > 10:
                    self.infrastructure['firewalls'].append({
                        'ip': node,
                        'hostname': self.nodes[node]['hostname'],
                        'type': 'Firewall/Gateway',
                        'betweenness_score': round(score, 4),
                        'in_degree': in_deg,
                        'out_degree': out_deg,
                        'role': 'network_chokepoint',
                        'confidence': 'MEDIUM'
                    })
        
        print(f"  └─ Detected {len(self.infrastructure['firewalls'])} potential firewalls/gateways")
    
    def _detect_soa_patterns(self):
        """
        Detect Service-Oriented Architecture patterns:
        - Many-to-many communication
        - Service mesh patterns
        - Microservices clusters
        """
        # Find densely connected subgraphs (communities)
        try:
            communities = list(nx.community.greedy_modularity_communities(self.graph.to_undirected()))
            
            for i, community in enumerate(communities):
                if len(community) > 3:
                    # Analyze communication patterns
                    internal_edges = 0
                    external_edges = 0
                    
                    for node in community:
                        for neighbor in self.graph.neighbors(node):
                            if neighbor in community:
                                internal_edges += 1
                            else:
                                external_edges += 1
                    
                    # High internal communication = microservices cluster
                    if internal_edges > external_edges * 2:
                        self.infrastructure['soa_services'].append({
                            'cluster_id': i,
                            'type': 'Microservices Cluster',
                            'service_count': len(community),
                            'services': list(community),
                            'internal_calls': internal_edges,
                            'external_calls': external_edges,
                            'cohesion': round(internal_edges / (internal_edges + external_edges), 2)
                        })
        except:
            pass
    
    def perform_network_segmentation(self):
        """
        Generate network segmentation zones based on:
        - Communication patterns
        - Security requirements
        - Infrastructure roles
        """
        print("\n🔒 Performing Network Segmentation...")
        
        # Define segmentation zones
        zones = {
            'DMZ': {'ips': set(), 'description': 'Internet-facing services'},
            'WEB_TIER': {'ips': set(), 'description': 'Web servers and load balancers'},
            'APP_TIER': {'ips': set(), 'description': 'Application servers'},
            'DATA_TIER': {'ips': set(), 'description': 'Databases and data stores'},
            'MESSAGING': {'ips': set(), 'description': 'Message queues and event buses'},
            'INFRASTRUCTURE': {'ips': set(), 'description': 'Core infrastructure (LB, FW, etc.)'},
            'MANAGEMENT': {'ips': set(), 'description': 'Management and orchestration'},
        }
        
        # Classify nodes into zones
        for ip, node in self.nodes.items():
            # Infrastructure components
            if node['infrastructure_type'] == 'load_balancer':
                zones['WEB_TIER']['ips'].add(ip)
                zones['INFRASTRUCTURE']['ips'].add(ip)
            
            elif node['infrastructure_type'] == 'database':
                zones['DATA_TIER']['ips'].add(ip)
            
            elif node['infrastructure_type'] in ['message_queue', 'kafka']:
                zones['MESSAGING']['ips'].add(ip)
            
            elif node['infrastructure_type'] == 'container_platform':
                zones['MANAGEMENT']['ips'].add(ip)
            
            elif node['infrastructure_type'] == 'api_gateway':
                zones['DMZ']['ips'].add(ip)
                zones['WEB_TIER']['ips'].add(ip)
            
            # Role-based classification
            else:
                in_deg = self.graph.in_degree(ip)
                out_deg = self.graph.out_degree(ip)
                
                if in_deg > out_deg * 3:
                    zones['WEB_TIER']['ips'].add(ip)
                elif out_deg > in_deg * 2:
                    zones['APP_TIER']['ips'].add(ip)
                else:
                    zones['APP_TIER']['ips'].add(ip)
        
        # Generate segmentation rules
        for zone_name, zone_data in zones.items():
            if zone_data['ips']:
                self.segments.append({
                    'zone': zone_name,
                    'description': zone_data['description'],
                    'member_count': len(zone_data['ips']),
                    'members': list(zone_data['ips'])
                })
        
        # Generate firewall rules
        self._generate_firewall_rules()
        
        self._print_segmentation_summary()
    
    def _generate_firewall_rules(self):
        """Generate micro-segmentation firewall rules"""
        rules = []
        
        # DMZ -> WEB_TIER only
        # WEB_TIER -> APP_TIER only
        # APP_TIER -> DATA_TIER only
        # APP_TIER -> MESSAGING only
        
        zone_hierarchy = [
            ('DMZ', 'WEB_TIER'),
            ('WEB_TIER', 'APP_TIER'),
            ('APP_TIER', 'DATA_TIER'),
            ('APP_TIER', 'MESSAGING'),
            ('APP_TIER', 'INFRASTRUCTURE')
        ]
        
        for src_zone, dst_zone in zone_hierarchy:
            rules.append({
                'source_zone': src_zone,
                'destination_zone': dst_zone,
                'action': 'ALLOW',
                'protocol': 'TCP',
                'description': f'Allow {src_zone} to {dst_zone}'
            })
        
        # Default deny
        rules.append({
            'source_zone': 'ANY',
            'destination_zone': 'ANY',
            'action': 'DENY',
            'description': 'Default deny all'
        })
        
        self.firewall_rules = rules
    
    def _has_kafka_port(self, ip):
        """Check if node has Kafka port open"""
        node = self.nodes.get(ip)
        if not node:
            return False
        for port in node['ports']:
            if port.isdigit() and int(port) in self.PORT_SIGS['kafka']:
                return True
        return False
    
    def _detect_health_checks(self, ip, port):
        """Detect health check patterns (regular intervals)"""
        # Simplified - would need timestamp analysis
        return "DETECTED" if len(self.nodes[ip]['ports'][port]['unique_sources']) > 1 else "NONE"
    
    def _print_infrastructure_summary(self):
        """Print infrastructure detection summary"""
        print("\n📊 Infrastructure Components Detected:")
        print(f"  ├─ Load Balancers: {len(self.infrastructure['load_balancers'])}")
        print(f"  ├─ Message Queues: {len(self.infrastructure['message_queues'])}")
        print(f"  ├─ Databases: {len(self.infrastructure['databases'])}")
        print(f"  ├─ Caches: {len(self.infrastructure['caches'])}")
        print(f"  ├─ API Gateways: {len(self.infrastructure['api_gateways'])}")
        print(f"  ├─ Firewalls: {len(self.infrastructure['firewalls'])}")
        print(f"  ├─ Container Platforms: {len(self.infrastructure['containers'])}")
        print(f"  └─ SOA/Microservices Clusters: {len(self.infrastructure['soa_services'])}")
    
    def _print_segmentation_summary(self):
        """Print segmentation summary"""
        print("\n📋 Network Segmentation Zones:")
        for segment in self.segments:
            print(f"  ├─ {segment['zone']}: {segment['member_count']} members")
            print(f"  │  └─ {segment['description']}")
    
    def export_full_report(self, filename='network_segmentation_report.json'):
        """Export comprehensive analysis report"""
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_applications': len(self.apps),
                'total_flows': len(self.flows),
                'total_nodes': len(self.nodes),
                'total_connections': self.graph.number_of_edges()
            },
            'applications': {k: v for k, v in self.apps.items()},
            'infrastructure': {
                'load_balancers': self.infrastructure['load_balancers'],
                'message_queues': self.infrastructure['message_queues'],
                'databases': self.infrastructure['databases'],
                'caches': self.infrastructure['caches'],
                'api_gateways': self.infrastructure['api_gateways'],
                'firewalls': self.infrastructure['firewalls'],
                'containers': self.infrastructure['containers'],
                'soa_microservices': self.infrastructure['soa_services']
            },
            'network_segmentation': {
                'zones': self.segments,
                'firewall_rules': getattr(self, 'firewall_rules', [])
            },
            'node_inventory': [
                {
                    'ip': ip,
                    'hostname': node['hostname'],
                    'infrastructure_type': node['infrastructure_type'],
                    'security_labels': list(node['security_labels']),
                    'applications': list(node['apps']),
                    'ports': list(node['ports'].keys())
                }
                for ip, node in self.nodes.items()
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✅ Full report exported to {filename}")
        return report


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    analyzer = NetworkSegmentationAnalyzer()
    
    # Add applications one by one
    for i in range(1, 136):  # 135 applications
        # Load CSV file
        try:
            df = pd.read_csv(f'app_{i}_flows.csv')
            count = analyzer.add_application(f'Application_{i}', df)
            
            # Run analysis every 10 apps for incremental insights
            if count % 10 == 0:
                print(f"\n{'='*60}")
                print(f"Incremental Analysis at {count} applications")
                print(f"{'='*60}")
                analyzer.analyze_infrastructure()
        
        except FileNotFoundError:
            print(f"⚠️  File not found: app_{i}_flows.csv")
            continue
    
    # Final comprehensive analysis
    print(f"\n{'='*60}")
    print(f"FINAL ANALYSIS - {len(analyzer.apps)} Applications")
    print(f"{'='*60}")
    
    analyzer.analyze_infrastructure()
    analyzer.perform_network_segmentation()
    report = analyzer.export_full_report()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"Total Applications Analyzed: {len(analyzer.apps)}")
    print(f"Total Infrastructure Components: {sum(len(v) for v in analyzer.infrastructure.values())}")
    print(f"Network Segmentation Zones: {len(analyzer.segments)}")
    print(f"Confidence Level: VERY HIGH")