# -*- coding: utf-8 -*-
"""
Advanced Graph Topology Analyzer
=================================
NetworkX-based graph algorithms for topology discovery - NO EXTERNAL APIs

Comprehensive graph analysis:
- Community detection (Louvain, Label Propagation, etc.)
- Centrality analysis (PageRank, Betweenness, Closeness)
- Shortest path analysis for dependency discovery
- Cycle detection for circular dependencies
- Bridge detection for critical connections
- Network flow analysis
- Hierarchical clustering

100% LOCAL PROCESSING

Author: Enterprise Security Team
Version: 3.0 - Advanced Graph Analytics
"""

import logging
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import NetworkX (optional but recommended)
try:
    import networkx as nx
    from networkx.algorithms import community
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available. Install with: pip install networkx")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available. Install with: pip install numpy")


class CommunityDetector:
    """
    Advanced community detection algorithms

    Identifies application clusters and micro-segmentation zones
    """

    def __init__(self, graph: 'nx.Graph' = None):
        """
        Args:
            graph: NetworkX graph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for community detection")

        self.graph = graph

    def louvain_communities(self, resolution: float = 1.0) -> List[Set]:
        """
        Louvain method for community detection

        Args:
            resolution: Resolution parameter (higher = more communities)

        Returns:
            List of communities (sets of node IDs)
        """
        if self.graph is None:
            return []

        try:
            # NetworkX community detection
            communities_generator = community.louvain_communities(
                self.graph, resolution=resolution
            )
            communities = list(communities_generator)

            logger.info(f"Louvain: detected {len(communities)} communities")

            return communities
        except Exception as e:
            logger.error(f"Louvain community detection failed: {e}")
            return []

    def label_propagation_communities(self) -> List[Set]:
        """
        Label propagation algorithm for community detection

        Fast method suitable for large graphs

        Returns:
            List of communities
        """
        if self.graph is None:
            return []

        try:
            communities_generator = community.label_propagation_communities(self.graph)
            communities = list(communities_generator)

            logger.info(f"Label Propagation: detected {len(communities)} communities")

            return communities
        except Exception as e:
            logger.error(f"Label propagation failed: {e}")
            return []

    def greedy_modularity_communities(self) -> List[Set]:
        """
        Greedy modularity maximization

        Returns:
            List of communities
        """
        if self.graph is None:
            return []

        try:
            communities_generator = community.greedy_modularity_communities(self.graph)
            communities = list(communities_generator)

            logger.info(f"Greedy Modularity: detected {len(communities)} communities")

            return communities
        except Exception as e:
            logger.error(f"Greedy modularity failed: {e}")
            return []

    def detect_all_methods(self) -> Dict[str, List[Set]]:
        """
        Run all community detection methods and compare

        Returns:
            Dictionary with results from each method
        """
        results = {
            'louvain': self.louvain_communities(),
            'label_propagation': self.label_propagation_communities(),
            'greedy_modularity': self.greedy_modularity_communities()
        }

        # Compute modularity for each method
        for method, communities in results.items():
            if communities:
                mod = self.compute_modularity(communities)
                logger.info(f"  {method}: modularity={mod:.4f}")

        return results

    def compute_modularity(self, communities: List[Set]) -> float:
        """
        Compute modularity of a community partition

        Modularity measures quality of network division

        Returns:
            Modularity score (-1 to 1, higher is better)
        """
        if self.graph is None or not communities:
            return 0.0

        try:
            mod = community.modularity(self.graph, communities)
            return mod
        except Exception as e:
            logger.error(f"Modularity computation failed: {e}")
            return 0.0


class CentralityAnalyzer:
    """
    Node centrality analysis

    Identifies critical applications and network hubs
    """

    def __init__(self, graph: 'nx.Graph' = None):
        """
        Args:
            graph: NetworkX graph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for centrality analysis")

        self.graph = graph

    def degree_centrality(self) -> Dict[str, float]:
        """
        Degree centrality: number of connections

        Returns:
            Dictionary mapping node -> centrality score
        """
        if self.graph is None:
            return {}

        return nx.degree_centrality(self.graph)

    def betweenness_centrality(self, normalized: bool = True) -> Dict[str, float]:
        """
        Betweenness centrality: how often node is on shortest paths

        Identifies critical bridges and bottlenecks

        Returns:
            Dictionary mapping node -> centrality score
        """
        if self.graph is None:
            return {}

        return nx.betweenness_centrality(self.graph, normalized=normalized)

    def closeness_centrality(self) -> Dict[str, float]:
        """
        Closeness centrality: average distance to all other nodes

        Identifies central/accessible nodes

        Returns:
            Dictionary mapping node -> centrality score
        """
        if self.graph is None:
            return {}

        try:
            return nx.closeness_centrality(self.graph)
        except Exception as e:
            logger.error(f"Closeness centrality failed: {e}")
            return {}

    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """
        PageRank centrality: importance based on link structure

        Returns:
            Dictionary mapping node -> PageRank score
        """
        if self.graph is None:
            return {}

        return nx.pagerank(self.graph, alpha=alpha)

    def eigenvector_centrality(self, max_iter: int = 100) -> Dict[str, float]:
        """
        Eigenvector centrality: importance based on neighbor importance

        Returns:
            Dictionary mapping node -> centrality score
        """
        if self.graph is None:
            return {}

        try:
            return nx.eigenvector_centrality(self.graph, max_iter=max_iter)
        except Exception as e:
            logger.warning(f"Eigenvector centrality failed: {e}")
            return {}

    def analyze_all_centralities(self) -> Dict[str, Dict[str, float]]:
        """
        Compute all centrality metrics

        Returns:
            Dictionary with all centrality measures
        """
        results = {
            'degree': self.degree_centrality(),
            'betweenness': self.betweenness_centrality(),
            'closeness': self.closeness_centrality(),
            'pagerank': self.pagerank(),
            'eigenvector': self.eigenvector_centrality()
        }

        # Find top nodes for each metric
        for metric, scores in results.items():
            if scores:
                top_node = max(scores.items(), key=lambda x: x[1])
                logger.info(f"  Top {metric}: {top_node[0]} (score: {top_node[1]:.4f})")

        return results

    def identify_critical_nodes(
        self,
        threshold_percentile: float = 90.0
    ) -> Dict[str, List[str]]:
        """
        Identify critical nodes based on multiple centrality metrics

        Args:
            threshold_percentile: Percentile threshold for criticality

        Returns:
            Dictionary of critical nodes per metric
        """
        if not NUMPY_AVAILABLE:
            logger.warning("NumPy required for percentile calculation")
            return {}

        import numpy as np

        all_centralities = self.analyze_all_centralities()
        critical_nodes = {}

        for metric, scores in all_centralities.items():
            if not scores:
                continue

            values = np.array(list(scores.values()))
            threshold = np.percentile(values, threshold_percentile)

            critical = [
                node for node, score in scores.items()
                if score >= threshold
            ]

            critical_nodes[metric] = critical

        return critical_nodes


class PathAnalyzer:
    """
    Path analysis for dependency discovery

    Analyzes paths between applications to understand dependencies
    """

    def __init__(self, graph: 'nx.DiGraph' = None):
        """
        Args:
            graph: NetworkX directed graph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for path analysis")

        self.graph = graph

    def shortest_path(self, source: str, target: str) -> List[str]:
        """
        Find shortest path between two nodes

        Returns:
            List of nodes in path (empty if no path exists)
        """
        if self.graph is None:
            return []

        try:
            path = nx.shortest_path(self.graph, source, target)
            return path
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            logger.warning(f"Node not found: {source} or {target}")
            return []

    def all_shortest_paths(self, source: str, target: str) -> List[List[str]]:
        """
        Find all shortest paths between two nodes

        Returns:
            List of paths (each path is a list of nodes)
        """
        if self.graph is None:
            return []

        try:
            paths = list(nx.all_shortest_paths(self.graph, source, target))
            return paths
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def dependency_chain(self, app: str, max_depth: int = 5) -> Dict:
        """
        Find complete dependency chain for an application

        Args:
            app: Application node
            max_depth: Maximum depth to traverse

        Returns:
            Dependency chain information
        """
        if self.graph is None:
            return {}

        # Find all paths from app (dependencies)
        descendants = nx.descendants(self.graph, app) if app in self.graph else set()

        # Find all paths to app (dependents)
        ancestors = nx.ancestors(self.graph, app) if app in self.graph else set()

        return {
            'application': app,
            'depends_on': list(descendants),
            'depended_by': list(ancestors),
            'dependency_count': len(descendants),
            'dependent_count': len(ancestors)
        }

    def find_service_chains(self, min_length: int = 3) -> List[List[str]]:
        """
        Find service chains (linear dependency sequences)

        Args:
            min_length: Minimum chain length

        Returns:
            List of service chains
        """
        if self.graph is None:
            return []

        chains = []

        # Find all simple paths
        for source in self.graph.nodes():
            for target in self.graph.nodes():
                if source == target:
                    continue

                try:
                    paths = nx.all_simple_paths(
                        self.graph, source, target, cutoff=min_length
                    )

                    for path in paths:
                        if len(path) >= min_length:
                            chains.append(path)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

        # Remove duplicates and sort by length
        unique_chains = []
        seen = set()

        for chain in chains:
            chain_tuple = tuple(chain)
            if chain_tuple not in seen:
                seen.add(chain_tuple)
                unique_chains.append(chain)

        unique_chains.sort(key=len, reverse=True)

        logger.info(f"Found {len(unique_chains)} service chains")

        return unique_chains


class CycleDetector:
    """
    Cycle detection for circular dependencies

    Identifies problematic circular dependencies in application topology
    """

    def __init__(self, graph: 'nx.DiGraph' = None):
        """
        Args:
            graph: NetworkX directed graph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for cycle detection")

        self.graph = graph

    def find_cycles(self) -> List[List[str]]:
        """
        Find all cycles in graph

        Returns:
            List of cycles (each cycle is a list of nodes)
        """
        if self.graph is None:
            return []

        try:
            cycles = list(nx.simple_cycles(self.graph))
            logger.info(f"Found {len(cycles)} cycles")
            return cycles
        except Exception as e:
            logger.error(f"Cycle detection failed: {e}")
            return []

    def is_dag(self) -> bool:
        """
        Check if graph is a Directed Acyclic Graph (DAG)

        Returns:
            True if DAG, False if cycles exist
        """
        if self.graph is None:
            return True

        return nx.is_directed_acyclic_graph(self.graph)

    def strongly_connected_components(self) -> List[Set[str]]:
        """
        Find strongly connected components

        Each component is a set of mutually reachable nodes

        Returns:
            List of strongly connected components
        """
        if self.graph is None:
            return []

        components = list(nx.strongly_connected_components(self.graph))
        logger.info(f"Found {len(components)} strongly connected components")

        return components

    def identify_circular_dependencies(self) -> List[Dict]:
        """
        Identify and analyze circular dependencies

        Returns:
            List of circular dependency information
        """
        cycles = self.find_cycles()

        circular_deps = []
        for i, cycle in enumerate(cycles):
            circular_deps.append({
                'cycle_id': i,
                'applications': cycle,
                'length': len(cycle),
                'severity': 'HIGH' if len(cycle) <= 3 else 'MEDIUM'
            })

        return circular_deps


class BridgeDetector:
    """
    Bridge detection for critical connections

    Identifies edges whose removal would disconnect the network
    """

    def __init__(self, graph: 'nx.Graph' = None):
        """
        Args:
            graph: NetworkX graph (undirected)
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for bridge detection")

        self.graph = graph

    def find_bridges(self) -> List[Tuple[str, str]]:
        """
        Find all bridges (critical edges)

        Returns:
            List of bridge edges
        """
        if self.graph is None:
            return []

        try:
            bridges = list(nx.bridges(self.graph))
            logger.info(f"Found {len(bridges)} bridge connections")
            return bridges
        except Exception as e:
            logger.error(f"Bridge detection failed: {e}")
            return []

    def find_articulation_points(self) -> Set[str]:
        """
        Find articulation points (critical nodes)

        Nodes whose removal would increase number of connected components

        Returns:
            Set of articulation point nodes
        """
        if self.graph is None:
            return set()

        try:
            articulation_points = set(nx.articulation_points(self.graph))
            logger.info(f"Found {len(articulation_points)} articulation points")
            return articulation_points
        except Exception as e:
            logger.error(f"Articulation point detection failed: {e}")
            return set()

    def analyze_critical_infrastructure(self) -> Dict:
        """
        Comprehensive critical infrastructure analysis

        Returns:
            Dictionary with bridges and articulation points
        """
        bridges = self.find_bridges()
        articulation_points = self.find_articulation_points()

        return {
            'critical_edges': [
                {
                    'source': edge[0],
                    'target': edge[1],
                    'type': 'bridge',
                    'impact': 'Network partition if removed'
                }
                for edge in bridges
            ],
            'critical_nodes': [
                {
                    'node': node,
                    'type': 'articulation_point',
                    'impact': 'Network fragmentation if removed'
                }
                for node in articulation_points
            ]
        }


class HierarchyAnalyzer:
    """
    Hierarchical structure analysis

    Identifies application tiers and layering
    """

    def __init__(self, graph: 'nx.DiGraph' = None):
        """
        Args:
            graph: NetworkX directed graph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for hierarchy analysis")

        self.graph = graph

    def topological_sort(self) -> List[str]:
        """
        Topological sort of DAG

        Orders applications by dependency

        Returns:
            List of nodes in topological order
        """
        if self.graph is None:
            return []

        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            logger.warning("Graph contains cycles, cannot topologically sort")
            return []

    def compute_layers(self) -> Dict[int, List[str]]:
        """
        Compute application layers/tiers

        Layer 0: No dependencies (leaf nodes)
        Layer 1: Depends only on Layer 0
        etc.

        Returns:
            Dictionary mapping layer -> list of applications
        """
        if self.graph is None:
            return {}

        layers = defaultdict(list)
        visited = set()

        # BFS-based layer computation
        queue = deque()

        # Find nodes with no incoming edges (sources/top layer)
        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0:
                queue.append((node, 0))
                visited.add(node)

        while queue:
            node, layer = queue.popleft()
            layers[layer].append(node)

            # Add successors to next layer
            for successor in self.graph.successors(node):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, layer + 1))

        logger.info(f"Computed {len(layers)} application layers")

        return dict(layers)

    def identify_tier_structure(self) -> Dict:
        """
        Identify traditional tier structure (web, app, data, etc.)

        Returns:
            Tier classification
        """
        layers = self.compute_layers()

        # Map layers to tiers
        tier_mapping = {
            'presentation_tier': [],
            'application_tier': [],
            'data_tier': [],
            'infrastructure_tier': []
        }

        # Simple heuristic: top layers = presentation, bottom = data
        num_layers = len(layers)

        for layer_idx, nodes in layers.items():
            if layer_idx == 0 and num_layers > 1:
                tier_mapping['presentation_tier'].extend(nodes)
            elif layer_idx == num_layers - 1 and num_layers > 1:
                tier_mapping['data_tier'].extend(nodes)
            else:
                tier_mapping['application_tier'].extend(nodes)

        return tier_mapping


class GraphTopologyAnalyzer:
    """
    Comprehensive graph topology analyzer

    Integrates all graph analysis components
    """

    def __init__(self):
        """Initialize analyzer"""
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available. Graph analysis will be limited.")
            self.graph = None
        else:
            self.graph = None

        logger.info("Graph Topology Analyzer initialized")

    def build_graph_from_flows(
        self,
        applications: List[str],
        flows: List[Dict],
        directed: bool = True
    ) -> 'nx.Graph':
        """
        Build NetworkX graph from flow data

        Args:
            applications: List of application names
            flows: List of flow dictionaries (source, destination, volume, etc.)
            directed: Whether to create directed graph

        Returns:
            NetworkX graph
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available")
            return None

        # Create graph
        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # Add nodes
        G.add_nodes_from(applications)

        # Add edges from flows
        for flow in flows:
            source = flow.get('source')
            target = flow.get('destination')
            weight = flow.get('bytes', 1)

            if source in applications and target in applications:
                if G.has_edge(source, target):
                    # Accumulate weight
                    G[source][target]['weight'] += weight
                else:
                    G.add_edge(source, target, weight=weight)

        logger.info(f"Built graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        self.graph = G
        return G

    def comprehensive_analysis(self) -> Dict:
        """
        Run comprehensive topology analysis

        Returns:
            Complete analysis results
        """
        if not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("Graph not available for analysis")
            return {}

        logger.info("Running comprehensive graph analysis...")

        results = {}

        # 1. Community Detection
        logger.info("  Running community detection...")
        comm_detector = CommunityDetector(self.graph)
        communities = comm_detector.detect_all_methods()
        results['communities'] = {
            method: [list(comm) for comm in comms]
            for method, comms in communities.items()
        }

        # 2. Centrality Analysis
        logger.info("  Computing centrality metrics...")
        cent_analyzer = CentralityAnalyzer(self.graph)
        centralities = cent_analyzer.analyze_all_centralities()
        critical_nodes = cent_analyzer.identify_critical_nodes()
        results['centrality'] = centralities
        results['critical_nodes'] = critical_nodes

        # 3. Bridge Detection (for undirected view)
        logger.info("  Detecting bridges and articulation points...")
        undirected = self.graph.to_undirected() if self.graph.is_directed() else self.graph
        bridge_detector = BridgeDetector(undirected)
        critical_infra = bridge_detector.analyze_critical_infrastructure()
        results['critical_infrastructure'] = critical_infra

        # 4. Path Analysis (for directed graphs)
        if self.graph.is_directed():
            logger.info("  Analyzing service chains...")
            path_analyzer = PathAnalyzer(self.graph)
            service_chains = path_analyzer.find_service_chains(min_length=3)
            results['service_chains'] = service_chains[:20]  # Top 20

            # 5. Cycle Detection
            logger.info("  Detecting circular dependencies...")
            cycle_detector = CycleDetector(self.graph)
            circular_deps = cycle_detector.identify_circular_dependencies()
            results['circular_dependencies'] = circular_deps

            # 6. Hierarchy Analysis
            logger.info("  Computing application hierarchy...")
            hierarchy_analyzer = HierarchyAnalyzer(self.graph)
            layers = hierarchy_analyzer.compute_layers()
            tier_structure = hierarchy_analyzer.identify_tier_structure()
            results['layers'] = {str(k): v for k, v in layers.items()}
            results['tier_structure'] = tier_structure

        # 7. Basic graph metrics
        logger.info("  Computing graph metrics...")
        results['graph_metrics'] = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph) if self.graph.is_directed()
                           else nx.is_connected(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes()
                         if self.graph.number_of_nodes() > 0 else 0
        }

        logger.info("Comprehensive analysis complete")

        return results

    def export_analysis(self, results: Dict, output_path: str):
        """
        Export analysis results to JSON

        Args:
            results: Analysis results dictionary
            output_path: Path to save JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Analysis exported to {output_path}")

    def export_graph(self, output_path: str, format: str = 'gexf'):
        """
        Export graph to file

        Args:
            output_path: Path to save graph
            format: Format ('gexf', 'graphml', 'gml', 'json')
        """
        if not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("Graph not available for export")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == 'gexf':
            nx.write_gexf(self.graph, output_file)
        elif format == 'graphml':
            nx.write_graphml(self.graph, output_file)
        elif format == 'gml':
            nx.write_gml(self.graph, output_file)
        elif format == 'json':
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(self.graph)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            logger.warning(f"Unknown format: {format}")
            return

        logger.info(f"Graph exported to {output_path} ({format})")
