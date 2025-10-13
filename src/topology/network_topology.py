"""Network topology builder and analyzer."""

import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Set
from collections import defaultdict


class NetworkTopology:
    """Build and analyze network topology from connection data."""
    
    def __init__(self):
        """Initialize the network topology."""
        self.graph = nx.DiGraph()
        self.connections = []
    
    def add_connections(self, connections: List[Dict[str, str]]):
        """Add connections to the topology.
        
        Args:
            connections: List of connection dictionaries with 'source', 'destination', 'protocol' keys
        """
        self.connections.extend(connections)
        
        for conn in connections:
            source = conn.get('source', 'unknown')
            destination = conn.get('destination', 'unknown')
            protocol = conn.get('protocol', 'unknown')
            port = conn.get('port', 'unknown')
            
            # Add edge with protocol and port as attributes
            if self.graph.has_edge(source, destination):
                # Update existing edge with additional protocol
                edge_data = self.graph[source][destination]
                if 'protocols' not in edge_data:
                    edge_data['protocols'] = set()
                edge_data['protocols'].add(protocol)
                if 'ports' not in edge_data:
                    edge_data['ports'] = set()
                edge_data['ports'].add(str(port))
            else:
                self.graph.add_edge(source, destination, 
                                   protocols={protocol}, 
                                   ports={str(port)})
    
    def get_nodes(self) -> List[str]:
        """Get all nodes in the topology.
        
        Returns:
            List of node names
        """
        return list(self.graph.nodes())
    
    def get_edges(self) -> List[tuple]:
        """Get all edges in the topology.
        
        Returns:
            List of edge tuples (source, destination, attributes)
        """
        return [(u, v, d) for u, v, d in self.graph.edges(data=True)]
    
    def get_statistics(self) -> Dict:
        """Get topology statistics.
        
        Returns:
            Dictionary with topology statistics
        """
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'total_connections': len(self.connections),
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }
    
    def identify_segments(self) -> Dict[str, List[str]]:
        """Identify network segments using community detection.
        
        Returns:
            Dictionary mapping segment IDs to lists of nodes
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        
        # Find weakly connected components as segments
        segments = {}
        for idx, component in enumerate(nx.connected_components(undirected)):
            segments[f"segment_{idx + 1}"] = list(component)
        
        return segments
    
    def get_connections_by_protocol(self) -> Dict[str, int]:
        """Get connection count by protocol.
        
        Returns:
            Dictionary mapping protocol to connection count
        """
        protocol_count = defaultdict(int)
        for conn in self.connections:
            protocol = conn.get('protocol', 'unknown')
            protocol_count[protocol] += 1
        return dict(protocol_count)
    
    def visualize(self, output_path: str = "network_topology.png"):
        """Visualize the network topology.
        
        Args:
            output_path: Path to save the visualization
        """
        if self.graph.number_of_nodes() == 0:
            print("No nodes to visualize")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Use spring layout for better visualization
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.graph, pos, node_color='lightblue', 
                              node_size=500, alpha=0.9)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, alpha=0.6)
        
        # Draw labels
        nx.draw_networkx_labels(self.graph, pos, font_size=8)
        
        plt.title("Network Topology", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Topology visualization saved to: {output_path}")
    
    def generate_report(self) -> str:
        """Generate a text report of the network topology.
        
        Returns:
            String containing the topology report
        """
        report = []
        report.append("=" * 60)
        report.append("NETWORK TOPOLOGY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Statistics
        stats = self.get_statistics()
        report.append("STATISTICS:")
        report.append(f"  Total Nodes: {stats['total_nodes']}")
        report.append(f"  Total Edges: {stats['total_edges']}")
        report.append(f"  Total Connections: {stats['total_connections']}")
        report.append(f"  Network Density: {stats['density']:.4f}")
        report.append("")
        
        # Protocols
        protocols = self.get_connections_by_protocol()
        report.append("CONNECTIONS BY PROTOCOL:")
        for protocol, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {protocol}: {count}")
        report.append("")
        
        # Segments
        segments = self.identify_segments()
        report.append("NETWORK SEGMENTS:")
        for segment_id, nodes in segments.items():
            report.append(f"  {segment_id}: {len(nodes)} nodes")
            report.append(f"    Nodes: {', '.join(sorted(nodes)[:10])}")
            if len(nodes) > 10:
                report.append(f"    ... and {len(nodes) - 10} more")
        report.append("")
        
        # Top communicators
        report.append("TOP COMMUNICATORS:")
        out_degrees = dict(self.graph.out_degree())
        top_out = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        for node, degree in top_out:
            report.append(f"  {node}: {degree} outgoing connections")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
