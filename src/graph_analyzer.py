"""
Graph-Based Network Path Analysis & Gap Detection
===================================================
Provides shortest path, gap analysis, and policy violation detection
WITHOUT requiring a Graph Database - pure Python in-memory solution.

Features:
- Shortest path finding between any two IPs
- All paths enumeration (with depth limit)
- Gap analysis (expected flows that don't exist)
- Policy violation detection
- Interactive HTML visualization

Author: Network Security Team
Version: 1.0
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available. Install with: pip install networkx")


class GraphAnalyzer:
    """
    In-memory graph analysis for network flows
    No Graph DB required - uses NetworkX for graph algorithms
    """

    def __init__(self, flow_records: List):
        """
        Initialize with flow records

        Args:
            flow_records: List of FlowRecord objects
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is required. Install with: pip install networkx")

        self.records = flow_records
        self.graph = nx.DiGraph()  # Directed graph (flows have direction)
        self.node_metadata = {}  # IP -> {app_code, tier, hostname, etc.}

        logger.info(f"GraphAnalyzer initialized with {len(flow_records)} records")
        self._build_graph()

    def _build_graph(self):
        """Build NetworkX graph from flow records"""
        logger.info("Building in-memory network graph...")

        edge_stats = defaultdict(lambda: {
            'flows': 0,
            'bytes': 0,
            'protocols': set(),
            'ports': set()
        })

        # Aggregate flows into edges
        for record in self.records:
            if record.src_ip and record.dst_ip:
                # Add edge with aggregated stats
                key = (record.src_ip, record.dst_ip)
                edge_stats[key]['flows'] += 1
                edge_stats[key]['bytes'] += record.bytes
                edge_stats[key]['protocols'].add(record.transport)
                if record.port:
                    edge_stats[key]['ports'].add(record.port)

                # Store node metadata
                if record.src_ip not in self.node_metadata:
                    self.node_metadata[record.src_ip] = {
                        'hostname': record.src_hostname,
                        'app_code': record.app_name,
                        'is_internal': record.is_internal
                    }
                if record.dst_ip not in self.node_metadata:
                    self.node_metadata[record.dst_ip] = {
                        'hostname': record.dst_hostname,
                        'app_code': record.app_name,
                        'is_internal': record.is_internal
                    }

        # Add edges to graph
        for (src, dst), stats in edge_stats.items():
            self.graph.add_edge(
                src, dst,
                flows=stats['flows'],
                bytes=stats['bytes'],
                protocols=list(stats['protocols']),
                ports=sorted(stats['ports']),
                weight=stats['flows']  # For shortest path algorithms
            )

        logger.info(f"  Graph built: {self.graph.number_of_nodes()} nodes, "
                   f"{self.graph.number_of_edges()} edges")

    def find_shortest_path(self, source_ip: str, target_ip: str) -> Optional[Dict]:
        """
        Find shortest path between two IPs

        Args:
            source_ip: Source IP address
            target_ip: Target IP address

        Returns:
            Dict with path information or None if no path exists
        """
        logger.info(f"Finding shortest path: {source_ip} → {target_ip}")

        if source_ip not in self.graph:
            logger.warning(f"Source IP not found in graph: {source_ip}")
            return None

        if target_ip not in self.graph:
            logger.warning(f"Target IP not found in graph: {target_ip}")
            return None

        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, source_ip, target_ip, weight='weight')

            # Calculate path metrics
            total_flows = 0
            total_bytes = 0
            hops = []

            for i in range(len(path) - 1):
                src, dst = path[i], path[i + 1]
                edge_data = self.graph[src][dst]

                total_flows += edge_data['flows']
                total_bytes += edge_data['bytes']

                hops.append({
                    'from': src,
                    'from_hostname': self.node_metadata.get(src, {}).get('hostname', ''),
                    'to': dst,
                    'to_hostname': self.node_metadata.get(dst, {}).get('hostname', ''),
                    'flows': edge_data['flows'],
                    'bytes': edge_data['bytes'],
                    'protocols': edge_data['protocols'],
                    'ports': edge_data['ports']
                })

            result = {
                'path': path,
                'path_length': len(path) - 1,  # Number of hops
                'total_flows': total_flows,
                'total_bytes': total_bytes,
                'hops': hops
            }

            logger.info(f"  ✓ Path found: {len(path)} nodes, {len(path)-1} hops")
            return result

        except nx.NetworkXNoPath:
            logger.warning(f"  ✗ No path exists between {source_ip} and {target_ip}")
            return None

    def find_all_paths(self, source_ip: str, target_ip: str,
                       max_depth: int = 5) -> List[List[str]]:
        """
        Find all simple paths between two IPs (up to max_depth)

        Args:
            source_ip: Source IP address
            target_ip: Target IP address
            max_depth: Maximum path length (default: 5 hops)

        Returns:
            List of paths (each path is a list of IPs)
        """
        logger.info(f"Finding all paths: {source_ip} → {target_ip} (max depth: {max_depth})")

        try:
            paths = list(nx.all_simple_paths(
                self.graph, source_ip, target_ip, cutoff=max_depth
            ))
            logger.info(f"  ✓ Found {len(paths)} paths")
            return paths

        except (nx.NodeNotFound, nx.NetworkXNoPath):
            logger.warning(f"  ✗ No paths found")
            return []

    def analyze_gaps(self, expected_topology: Dict[str, List[Tuple[str, str]]]) -> List[Dict]:
        """
        Detect gaps in network topology (expected connections that don't exist)

        Args:
            expected_topology: Dict mapping tier pairs to expected connections
                Example: {
                    'WEB_to_APP': [('10.1.1.1', '10.2.2.2'), ...],
                    'APP_to_DB': [('10.2.2.2', '10.3.3.3'), ...]
                }

        Returns:
            List of gap dictionaries with details
        """
        logger.info("Analyzing topology gaps...")

        gaps = []
        total_expected = 0

        for gap_type, expected_connections in expected_topology.items():
            for src, dst in expected_connections:
                total_expected += 1

                if not self.graph.has_edge(src, dst):
                    # Gap found!
                    gaps.append({
                        'gap_type': gap_type,
                        'source_ip': src,
                        'source_hostname': self.node_metadata.get(src, {}).get('hostname', ''),
                        'source_app': self.node_metadata.get(src, {}).get('app_code', ''),
                        'destination_ip': dst,
                        'destination_hostname': self.node_metadata.get(dst, {}).get('hostname', ''),
                        'destination_app': self.node_metadata.get(dst, {}).get('app_code', ''),
                        'severity': self._assess_gap_severity(gap_type),
                        'recommendation': self._get_gap_recommendation(gap_type)
                    })

        logger.info(f"  Found {len(gaps)} gaps out of {total_expected} expected connections "
                   f"({len(gaps)/total_expected*100:.1f}% gap rate)")

        return gaps

    def detect_policy_violations(self, policies: List[Dict]) -> List[Dict]:
        """
        Detect flows that violate security policies

        Args:
            policies: List of policy dictionaries
                Example: {
                    'name': 'No WEB to DB direct access',
                    'source_tier': 'WEB',
                    'destination_tier': 'DATABASE',
                    'action': 'DENY'
                }

        Returns:
            List of violation dictionaries
        """
        logger.info(f"Checking {len(policies)} security policies...")

        violations = []

        for policy in policies:
            if policy['action'] != 'DENY':
                continue  # Only check DENY policies

            # Find all edges matching the policy pattern
            for src, dst, edge_data in self.graph.edges(data=True):
                src_tier = self._classify_node_tier(src)
                dst_tier = self._classify_node_tier(dst)

                if (src_tier == policy['source_tier'] and
                    dst_tier == policy['destination_tier']):

                    violations.append({
                        'policy_name': policy['name'],
                        'source_ip': src,
                        'source_hostname': self.node_metadata.get(src, {}).get('hostname', ''),
                        'source_tier': src_tier,
                        'destination_ip': dst,
                        'destination_hostname': self.node_metadata.get(dst, {}).get('hostname', ''),
                        'destination_tier': dst_tier,
                        'flows': edge_data['flows'],
                        'protocols': edge_data['protocols'],
                        'ports': edge_data['ports'],
                        'severity': 'HIGH'
                    })

        logger.info(f"  Found {len(violations)} policy violations")
        return violations

    def get_node_neighbors(self, ip_address: str, direction: str = 'both') -> Dict:
        """
        Get all neighbors (upstream/downstream) of a node

        Args:
            ip_address: IP address to analyze
            direction: 'upstream', 'downstream', or 'both'

        Returns:
            Dict with upstream and downstream neighbors
        """
        result = {
            'ip': ip_address,
            'hostname': self.node_metadata.get(ip_address, {}).get('hostname', ''),
            'upstream': [],
            'downstream': []
        }

        if direction in ['upstream', 'both']:
            # Predecessors (who connects TO this node)
            for pred in self.graph.predecessors(ip_address):
                edge_data = self.graph[pred][ip_address]
                result['upstream'].append({
                    'ip': pred,
                    'hostname': self.node_metadata.get(pred, {}).get('hostname', ''),
                    'flows': edge_data['flows'],
                    'protocols': edge_data['protocols'],
                    'ports': edge_data['ports']
                })

        if direction in ['downstream', 'both']:
            # Successors (who this node connects TO)
            for succ in self.graph.successors(ip_address):
                edge_data = self.graph[ip_address][succ]
                result['downstream'].append({
                    'ip': succ,
                    'hostname': self.node_metadata.get(succ, {}).get('hostname', ''),
                    'flows': edge_data['flows'],
                    'protocols': edge_data['protocols'],
                    'ports': edge_data['ports']
                })

        return result

    def calculate_centrality_metrics(self) -> Dict[str, Dict]:
        """
        Calculate graph centrality metrics for all nodes
        Helps identify critical nodes in the network

        Returns:
            Dict mapping IP addresses to centrality metrics
        """
        logger.info("Calculating centrality metrics...")

        metrics = {}

        # Degree centrality (how many connections)
        degree_centrality = nx.degree_centrality(self.graph)

        # Betweenness centrality (how often node is on shortest paths)
        betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')

        # PageRank (importance based on connections)
        pagerank = nx.pagerank(self.graph, weight='weight')

        for node in self.graph.nodes():
            metrics[node] = {
                'ip': node,
                'hostname': self.node_metadata.get(node, {}).get('hostname', ''),
                'degree_centrality': degree_centrality.get(node, 0),
                'betweenness_centrality': betweenness_centrality.get(node, 0),
                'pagerank': pagerank.get(node, 0),
                'in_degree': self.graph.in_degree(node),
                'out_degree': self.graph.out_degree(node)
            }

        logger.info(f"  ✓ Calculated metrics for {len(metrics)} nodes")
        return metrics

    def export_for_visualization(self, output_path: str):
        """
        Export graph data for D3.js or other visualization tools

        Args:
            output_path: Path to save JSON file
        """
        logger.info(f"Exporting graph for visualization: {output_path}")

        # Prepare nodes
        nodes = []
        for node in self.graph.nodes():
            nodes.append({
                'id': node,
                'label': self.node_metadata.get(node, {}).get('hostname', node),
                'app_code': self.node_metadata.get(node, {}).get('app_code', ''),
                'is_internal': self.node_metadata.get(node, {}).get('is_internal', True),
                'in_degree': self.graph.in_degree(node),
                'out_degree': self.graph.out_degree(node)
            })

        # Prepare edges
        edges = []
        for src, dst, data in self.graph.edges(data=True):
            edges.append({
                'source': src,
                'target': dst,
                'flows': data['flows'],
                'bytes': data['bytes'],
                'protocols': data['protocols'],
                'ports': data['ports']
            })

        # Export
        graph_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'generated_at': str(Path(__file__).parent)
            }
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)

        logger.info(f"  ✓ Graph data exported: {output_path}")

    def _classify_node_tier(self, ip_address: str) -> str:
        """Classify node into tier based on IP pattern"""
        if ip_address.startswith('10.164.105.'):
            return 'WEB'
        elif ip_address.startswith('10.100.246.') or ip_address.startswith('10.165.116.'):
            return 'APP'
        elif ip_address.startswith('10.164.116.'):
            return 'DATABASE'
        elif ip_address.startswith('10.164.144.'):
            return 'CACHE'
        elif ip_address.startswith('10.164.145.'):
            return 'QUEUE'
        else:
            return 'UNKNOWN'

    def _assess_gap_severity(self, gap_type: str) -> str:
        """Assess severity of a topology gap"""
        if 'WEB' in gap_type and 'APP' in gap_type:
            return 'HIGH'
        elif 'APP' in gap_type and 'DB' in gap_type:
            return 'CRITICAL'
        else:
            return 'MEDIUM'

    def _get_gap_recommendation(self, gap_type: str) -> str:
        """Get recommendation for addressing a gap"""
        recommendations = {
            'WEB_to_APP': 'Verify application tier is reachable from web tier. Check firewall rules.',
            'APP_to_DB': 'CRITICAL: Application cannot reach database. Check network segmentation.',
            'APP_to_CACHE': 'Performance may be degraded. Verify cache tier connectivity.'
        }
        return recommendations.get(gap_type, 'Review network connectivity and firewall rules.')


# Convenience function
def analyze_network_paths(flow_records: List, output_dir: str = 'outputs/graph_analysis'):
    """
    Perform comprehensive graph analysis on network flows

    Args:
        flow_records: List of FlowRecord objects
        output_dir: Output directory for results

    Returns:
        GraphAnalyzer instance
    """
    if not NETWORKX_AVAILABLE:
        logger.error("NetworkX not installed. Run: pip install networkx")
        return None

    analyzer = GraphAnalyzer(flow_records)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Export graph data
    analyzer.export_for_visualization(str(output_path / 'network_graph.json'))

    # Calculate and export centrality metrics
    metrics = analyzer.calculate_centrality_metrics()
    top_critical = sorted(metrics.items(),
                         key=lambda x: x[1]['betweenness_centrality'],
                         reverse=True)[:10]

    logger.info("\nTop 10 Critical Nodes (by betweenness centrality):")
    for ip, m in top_critical:
        logger.info(f"  {ip} ({m['hostname']}): {m['betweenness_centrality']:.4f}")

    return analyzer


if __name__ == '__main__':
    # Example usage
    from src.parser import parse_network_logs

    print("="*60)
    print("Graph Analysis - Test Run")
    print("="*60)

    # Parse flows
    parser = parse_network_logs('data/input')

    # Analyze
    analyzer = analyze_network_paths(parser.records, 'outputs/graph_analysis')

    # Find shortest path example
    if len(parser.records) > 0:
        src = parser.records[0].src_ip
        dst = parser.records[-1].dst_ip

        path_result = analyzer.find_shortest_path(src, dst)
        if path_result:
            print(f"\nShortest path from {src} to {dst}:")
            print(f"  Hops: {path_result['path_length']}")
            print(f"  Path: {' → '.join(path_result['path'])}")

    print("\n[SUCCESS] Graph analysis complete!")
