# -*- coding: utf-8 -*-
"""
Web App API Routes
==================
REST API endpoints for network segmentation analyzer web application

Features:
- Application list and details
- Topology data access
- Real-time statistics
- Analysis results
- Zone distribution
- Dependency graph data

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0 - Web Interface
"""

import logging
from flask import Blueprint, jsonify, request
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


def init_api_routes(pm, semantic_analyzer=None, incremental_learner=None):
    """
    Initialize API routes with dependencies

    Args:
        pm: Persistence manager
        semantic_analyzer: Optional semantic analyzer
        incremental_learner: Optional incremental learner
    """

    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'backend': pm.backend if hasattr(pm, 'backend') else 'unknown'
        })

    @api_bp.route('/statistics', methods=['GET'])
    def get_statistics():
        """Get overall statistics"""
        try:
            stats = pm.get_statistics()

            # Add incremental learning stats if available
            if incremental_learner:
                learning_stats = incremental_learner.get_statistics()
                stats['incremental_learning'] = learning_stats

            return jsonify({
                'success': True,
                'statistics': stats,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/applications', methods=['GET'])
    def list_applications():
        """List all applications"""
        try:
            apps = pm.list_applications()

            return jsonify({
                'success': True,
                'count': len(apps),
                'applications': apps
            })
        except Exception as e:
            logger.error(f"Error listing applications: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/applications/<app_id>', methods=['GET'])
    def get_application(app_id: str):
        """Get application details"""
        try:
            app = pm.get_application(app_id)

            if not app:
                return jsonify({
                    'success': False,
                    'error': 'Application not found'
                }), 404

            return jsonify({
                'success': True,
                'application': app
            })
        except Exception as e:
            logger.error(f"Error getting application {app_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/topology', methods=['GET'])
    def get_topology():
        """Get topology data for all applications"""
        try:
            app_id = request.args.get('app_id')

            topology = pm.get_topology_data(app_id)

            return jsonify({
                'success': True,
                'count': len(topology),
                'topology': topology
            })
        except Exception as e:
            logger.error(f"Error getting topology: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/topology/graph', methods=['GET'])
    def get_topology_graph():
        """Get topology as graph data (nodes and edges) for visualization"""
        try:
            topology = pm.get_topology_data()

            # Build graph structure
            nodes = []
            edges = []
            node_map = {}
            dependency_nodes = {}  # Track dependency nodes to create

            # First pass: Create application nodes
            for idx, topo in enumerate(topology):
                app_id = topo['app_id']
                zone = topo['security_zone']

                # Create node
                node = {
                    'id': app_id,
                    'label': app_id,
                    'zone': zone,
                    'characteristics': topo.get('characteristics', []),
                    'group': zone
                }
                nodes.append(node)
                node_map[app_id] = idx

                # Collect dependencies for second pass
                dependencies = topo.get('dependencies', [])
                if isinstance(dependencies, list):
                    for dep in dependencies:
                        if isinstance(dep, dict):
                            target = dep.get('name', dep.get('type', 'unknown'))
                            dep_type = dep.get('type', 'unknown')

                            # Store edge
                            edges.append({
                                'source': app_id,
                                'target': target,
                                'type': dep_type,
                                'confidence': dep.get('confidence', 0.5)
                            })

                            # Track dependency node if not already an app
                            if target not in node_map and target not in dependency_nodes:
                                dependency_nodes[target] = dep_type

            # Second pass: Create nodes for dependencies that aren't apps
            for dep_name, dep_type in dependency_nodes.items():
                # Infer zone based on dependency type
                zone_map = {
                    'database': 'DATA_TIER',
                    'cache': 'CACHE_TIER',
                    'message_queue': 'MESSAGING_TIER',
                    'messaging': 'MESSAGING_TIER',
                    'api': 'APP_TIER',
                    'other_apis': 'APP_TIER',
                    'web': 'WEB_TIER'
                }
                inferred_zone = zone_map.get(dep_type, 'UNKNOWN')

                # Create dependency node
                dep_node = {
                    'id': dep_name,
                    'label': dep_name,
                    'zone': inferred_zone,
                    'characteristics': [dep_type],
                    'group': inferred_zone,
                    'is_dependency': True  # Mark as inferred node
                }
                nodes.append(dep_node)
                node_map[dep_name] = len(nodes) - 1

            return jsonify({
                'success': True,
                'graph': {
                    'nodes': nodes,
                    'edges': edges
                }
            })
        except Exception as e:
            logger.error(f"Error getting topology graph: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/zones', methods=['GET'])
    def get_zones():
        """Get zone distribution"""
        try:
            topology = pm.get_topology_data()

            # Count applications per zone
            zone_distribution = {}
            for topo in topology:
                zone = topo.get('security_zone', 'UNKNOWN')
                zone_distribution[zone] = zone_distribution.get(zone, 0) + 1

            # Format for chart
            zones = [
                {'zone': zone, 'count': count}
                for zone, count in zone_distribution.items()
            ]

            return jsonify({
                'success': True,
                'zones': zones
            })
        except Exception as e:
            logger.error(f"Error getting zones: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/analysis', methods=['GET'])
    def get_analysis():
        """Get analysis results"""
        try:
            app_id = request.args.get('app_id')
            analysis_type = request.args.get('type')

            results = pm.get_analysis_results(app_id, analysis_type)

            return jsonify({
                'success': True,
                'count': len(results),
                'results': results
            })
        except Exception as e:
            logger.error(f"Error getting analysis: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/incremental/status', methods=['GET'])
    def get_incremental_status():
        """Get incremental learning status"""
        try:
            if not incremental_learner:
                return jsonify({
                    'success': False,
                    'error': 'Incremental learning not enabled'
                }), 404

            stats = incremental_learner.get_statistics()

            return jsonify({
                'success': True,
                'status': stats
            })
        except Exception as e:
            logger.error(f"Error getting incremental status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/search', methods=['GET'])
    def search_applications():
        """Search applications by name or characteristics"""
        try:
            query = request.args.get('q', '').lower()

            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query parameter required'
                }), 400

            apps = pm.list_applications()
            topology = pm.get_topology_data()

            # Create topology lookup
            topo_map = {t['app_id']: t for t in topology}

            # Search
            results = []
            for app in apps:
                app_id = app['app_id']
                app_lower = app_id.lower()

                # Check app name
                if query in app_lower:
                    results.append({
                        **app,
                        'topology': topo_map.get(app_id, {}),
                        'match_type': 'name'
                    })
                    continue

                # Check topology characteristics
                if app_id in topo_map:
                    topo = topo_map[app_id]
                    characteristics = topo.get('characteristics', [])
                    zone = topo.get('security_zone', '')

                    if any(query in str(c).lower() for c in characteristics):
                        results.append({
                            **app,
                            'topology': topo,
                            'match_type': 'characteristic'
                        })
                        continue

                    if query in zone.lower():
                        results.append({
                            **app,
                            'topology': topo,
                            'match_type': 'zone'
                        })

            return jsonify({
                'success': True,
                'query': query,
                'count': len(results),
                'results': results
            })
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/export', methods=['GET'])
    def export_data():
        """Export all data as JSON"""
        try:
            export_format = request.args.get('format', 'json')

            if export_format != 'json':
                return jsonify({
                    'success': False,
                    'error': 'Only JSON format supported'
                }), 400

            data = {
                'timestamp': datetime.now().isoformat(),
                'applications': pm.list_applications(),
                'topology': pm.get_topology_data(),
                'analysis': pm.get_analysis_results(),
                'statistics': pm.get_statistics()
            }

            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/dependencies/<app_id>', methods=['GET'])
    def get_dependencies(app_id: str):
        """Get dependencies for specific application"""
        try:
            topology = pm.get_topology_data(app_id)

            if not topology:
                return jsonify({
                    'success': False,
                    'error': 'Application not found'
                }), 404

            app_topo = topology[0]
            dependencies = app_topo.get('dependencies', [])

            return jsonify({
                'success': True,
                'app_id': app_id,
                'zone': app_topo.get('security_zone'),
                'dependencies': dependencies
            })
        except Exception as e:
            logger.error(f"Error getting dependencies for {app_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/characteristics', methods=['GET'])
    def get_characteristics():
        """Get all unique characteristics across applications"""
        try:
            topology = pm.get_topology_data()

            # Collect all characteristics
            all_chars = set()
            for topo in topology:
                chars = topo.get('characteristics', [])
                if isinstance(chars, list):
                    all_chars.update(chars)

            characteristics = sorted(list(all_chars))

            return jsonify({
                'success': True,
                'characteristics': characteristics
            })
        except Exception as e:
            logger.error(f"Error getting characteristics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @api_bp.route('/export/lucidchart', methods=['GET'])
    def export_lucidchart():
        """Export topology as Lucidchart CSV"""
        try:
            import sys
            import json
            from pathlib import Path
            from flask import send_file

            # Import Lucidchart exporter
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.exporters.lucidchart_exporter import LucidchartExporter

            # Get topology data
            topology_data = pm.get_topology_data()

            # Build topology JSON structure
            topology_export = {
                'timestamp': datetime.now().isoformat(),
                'topology': {}
            }

            for topo in topology_data:
                topology_export['topology'][topo['app_id']] = topo

            # Create temporary JSON file
            temp_dir = Path('outputs_final')
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_json = temp_dir / 'temp_topology.json'

            with open(temp_json, 'w') as f:
                json.dump(topology_export, f, indent=2)

            # Export to Lucidchart CSV
            exporter = LucidchartExporter()
            with_zones = request.args.get('zones', 'false').lower() == 'true'

            if with_zones:
                csv_path = exporter.export_with_zones_as_containers(str(temp_json))
            else:
                csv_path = exporter.export_from_topology_json(str(temp_json))

            # Clean up temp file
            temp_json.unlink(missing_ok=True)

            return send_file(
                csv_path,
                as_attachment=True,
                download_name=f'lucidchart_topology_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mimetype='text/csv'
            )

        except Exception as e:
            logger.error(f"Error exporting to Lucidchart: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return api_bp


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_graph_statistics(topology: List[Dict]) -> Dict:
    """Calculate graph statistics"""

    stats = {
        'total_nodes': len(topology),
        'total_edges': 0,
        'zones': {},
        'avg_dependencies': 0
    }

    total_deps = 0

    for topo in topology:
        zone = topo.get('security_zone', 'UNKNOWN')
        stats['zones'][zone] = stats['zones'].get(zone, 0) + 1

        deps = topo.get('dependencies', [])
        if isinstance(deps, list):
            total_deps += len(deps)
            stats['total_edges'] += len(deps)

    if len(topology) > 0:
        stats['avg_dependencies'] = round(total_deps / len(topology), 2)

    return stats
