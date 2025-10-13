# -*- coding: utf-8 -*-
"""
Agentic AI Components for Network Segmentation
===============================================

This package contains advanced AI-powered analysis components
that operate completely locally without external API calls:

Components:
-----------
1. LocalSemanticAnalyzer: Knowledge graph-based application analysis
   - Pattern recognition and inference
   - Dependency reasoning
   - Compliance detection
   - Technology stack identification

2. GraphTopologyAnalyzer: Advanced graph algorithms for topology discovery
   - Community detection (Louvain, Label Propagation)
   - Centrality analysis (PageRank, Betweenness, Closeness)
   - Path analysis and service chain discovery
   - Cycle detection for circular dependencies
   - Bridge detection for critical connections
   - Hierarchical structure analysis

All components are designed for:
- 100% local processing (no data leaves your network)
- Production-ready error handling
- Comprehensive logging
- Extensible architecture
- Integration with existing analysis pipeline

Author: Enterprise Security Team
Version: 3.0 - AI-Enhanced Network Analysis
"""

import logging

logger = logging.getLogger(__name__)

# Version
__version__ = '3.0.0'

# Import components (with graceful fallback)
try:
    from .local_semantic_analyzer import (
        LocalSemanticAnalyzer,
        ApplicationKnowledgeGraph,
        DependencyReasoner,
        PatternLearner
    )
    SEMANTIC_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Local Semantic Analyzer not available: {e}")
    SEMANTIC_AVAILABLE = False

try:
    from .graph_topology_analyzer import (
        GraphTopologyAnalyzer,
        CommunityDetector,
        CentralityAnalyzer,
        PathAnalyzer,
        CycleDetector,
        BridgeDetector,
        HierarchyAnalyzer
    )
    GRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph Topology Analyzer not available: {e}")
    GRAPH_AVAILABLE = False

# Public API
__all__ = [
    # Semantic Analysis
    'LocalSemanticAnalyzer',
    'ApplicationKnowledgeGraph',
    'DependencyReasoner',
    'PatternLearner',

    # Graph Analysis
    'GraphTopologyAnalyzer',
    'CommunityDetector',
    'CentralityAnalyzer',
    'PathAnalyzer',
    'CycleDetector',
    'BridgeDetector',
    'HierarchyAnalyzer',

    # Flags
    'SEMANTIC_AVAILABLE',
    'GRAPH_AVAILABLE',
]

# Package initialization
logger.info(f"Agentic AI Components v{__version__} loaded")
if SEMANTIC_AVAILABLE:
    logger.info("  ✓ Local Semantic Analyzer available")
if GRAPH_AVAILABLE:
    logger.info("  ✓ Graph Topology Analyzer available")


def get_available_components() -> dict:
    """
    Get information about available components

    Returns:
        Dictionary with component availability and descriptions
    """
    components = {
        'semantic_analyzer': {
            'available': SEMANTIC_AVAILABLE,
            'description': 'Knowledge graph-based application analysis',
            'features': [
                'Pattern recognition',
                'Dependency inference',
                'Compliance detection',
                'Tech stack identification'
            ]
        },
        'graph_analyzer': {
            'available': GRAPH_AVAILABLE,
            'description': 'Advanced graph algorithms for topology analysis',
            'features': [
                'Community detection',
                'Centrality analysis',
                'Path analysis',
                'Cycle detection',
                'Critical infrastructure detection'
            ]
        }
    }

    return components


def check_dependencies() -> dict:
    """
    Check status of optional dependencies

    Returns:
        Dictionary with dependency status
    """
    dependencies = {}

    # Check NetworkX
    try:
        import networkx
        dependencies['networkx'] = {
            'available': True,
            'version': networkx.__version__,
            'required_for': ['GraphTopologyAnalyzer']
        }
    except ImportError:
        dependencies['networkx'] = {
            'available': False,
            'required_for': ['GraphTopologyAnalyzer'],
            'install': 'pip install networkx'
        }

    # Check NumPy
    try:
        import numpy
        dependencies['numpy'] = {
            'available': True,
            'version': numpy.__version__,
            'required_for': ['Various statistical computations']
        }
    except ImportError:
        dependencies['numpy'] = {
            'available': False,
            'required_for': ['Various statistical computations'],
            'install': 'pip install numpy'
        }

    # Check scikit-learn
    try:
        import sklearn
        dependencies['scikit-learn'] = {
            'available': True,
            'version': sklearn.__version__,
            'required_for': ['Clustering algorithms']
        }
    except ImportError:
        dependencies['scikit-learn'] = {
            'available': False,
            'required_for': ['Clustering algorithms'],
            'install': 'pip install scikit-learn'
        }

    return dependencies


# Convenience function for quick setup
def create_semantic_analyzer(persistence_manager=None):
    """
    Factory function to create LocalSemanticAnalyzer

    Args:
        persistence_manager: Optional persistence manager for data storage

    Returns:
        LocalSemanticAnalyzer instance or None if not available
    """
    if not SEMANTIC_AVAILABLE:
        logger.error("LocalSemanticAnalyzer not available. Check dependencies.")
        return None

    return LocalSemanticAnalyzer(persistence_manager=persistence_manager)


def create_graph_analyzer():
    """
    Factory function to create GraphTopologyAnalyzer

    Returns:
        GraphTopologyAnalyzer instance or None if not available
    """
    if not GRAPH_AVAILABLE:
        logger.error("GraphTopologyAnalyzer not available. Check dependencies.")
        return None

    return GraphTopologyAnalyzer()


# Example usage documentation
USAGE_EXAMPLE = """
Example Usage:
--------------

# Semantic Analysis
from src.agentic import create_semantic_analyzer

analyzer = create_semantic_analyzer()
result = analyzer.analyze_application(
    app_name="payment-service",
    metadata={'type': 'api'},
    observed_peers=['database-postgres', 'cache-redis']
)

print(f"Security Zone: {result['security_zone']}")
print(f"Compliance: {result['compliance_requirements']}")

# Graph Analysis
from src.agentic import create_graph_analyzer

graph_analyzer = create_graph_analyzer()
graph = graph_analyzer.build_graph_from_flows(
    applications=['web', 'api', 'db'],
    flows=[
        {'source': 'web', 'destination': 'api', 'bytes': 1000},
        {'source': 'api', 'destination': 'db', 'bytes': 500}
    ]
)

results = graph_analyzer.comprehensive_analysis()
print(f"Communities: {results['communities']}")
print(f"Critical Nodes: {results['critical_nodes']}")
"""
