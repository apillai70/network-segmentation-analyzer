# -*- coding: utf-8 -*-
"""
Network Segmentation Analyzer - Web Application
================================================
Flask-based web interface for network topology visualization and analysis

Features:
- Interactive topology visualization (D3.js)
- Real-time application discovery monitoring
- Zone distribution charts
- Dependency graph exploration
- Incremental learning status dashboard
- Search and filtering
- No Docker dependency - lightweight Flask server

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0 - Web Interface
"""

import logging
import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.persistence.unified_persistence import create_persistence_manager
from web_app.api_routes import init_api_routes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(
    __name__,
    template_folder='web_app/templates',
    static_folder='web_app/static'
)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False

# Initialize persistence manager
pm = create_persistence_manager(
    prefer_postgres=True,
    auto_fallback=True
)

# Optional: Initialize incremental learner if available
incremental_learner = None
semantic_analyzer = None

try:
    from src.core.incremental_learner import IncrementalLearningSystem
    from src.agentic.local_semantic_analyzer import LocalSemanticAnalyzer

    # Initialize semantic analyzer
    semantic_analyzer = LocalSemanticAnalyzer(persistence_manager=pm)

    # Initialize incremental learner (optional)
    # Note: ensemble_model and topology_system would need to be initialized
    # For web app, we'll make it optional
    logger.info("[OK] Semantic analyzer initialized")
except Exception as e:
    logger.warning(f"Could not initialize incremental learning: {e}")

# Initialize API routes
api_bp = init_api_routes(pm, semantic_analyzer, incremental_learner)
app.register_blueprint(api_bp)


# ============================================================================
# Web Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        stats = pm.get_statistics()
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return render_template('index.html', stats={}, error=str(e))


@app.route('/topology')
def topology():
    """Topology visualization page"""
    return render_template('topology.html')


@app.route('/applications')
def applications():
    """Applications list page"""
    try:
        apps = pm.list_applications()
        return render_template('applications.html', applications=apps)
    except Exception as e:
        logger.error(f"Error loading applications: {e}")
        return render_template('applications.html', applications=[], error=str(e))


@app.route('/application/<app_id>')
def application_detail(app_id: str):
    """Application detail page"""
    try:
        app = pm.get_application(app_id)
        if not app:
            return render_template('error.html', message=f'Application {app_id} not found'), 404

        # Get topology data
        topology = pm.get_topology_data(app_id)
        topo = topology[0] if topology else {}

        return render_template('application_detail.html', application=app, topology=topo)
    except Exception as e:
        logger.error(f"Error loading application {app_id}: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/zones')
def zones():
    """Security zones overview page"""
    try:
        topology = pm.get_topology_data()

        # Group by zone
        zones_data = {}
        for topo in topology:
            zone = topo.get('security_zone', 'UNKNOWN')
            if zone not in zones_data:
                zones_data[zone] = []
            zones_data[zone].append(topo)

        return render_template('zones.html', zones=zones_data)
    except Exception as e:
        logger.error(f"Error loading zones: {e}")
        return render_template('zones.html', zones={}, error=str(e))


@app.route('/incremental')
def incremental_learning():
    """Incremental learning status page"""
    try:
        if incremental_learner:
            stats = incremental_learner.get_statistics()
        else:
            stats = {
                'status': 'not_enabled',
                'message': 'Incremental learning not initialized'
            }

        return render_template('incremental.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading incremental learning page: {e}")
        return render_template('incremental.html', stats={}, error=str(e))


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', message='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal error: {error}")
    return render_template('error.html', message='Internal server error'), 500


# ============================================================================
# Static Files
# ============================================================================

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        app.static_folder,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


# ============================================================================
# Template Filters
# ============================================================================

@app.template_filter('datetime')
def format_datetime(value):
    """Format datetime for display"""
    if not value:
        return 'N/A'

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value

    return value.strftime('%Y-%m-%d %H:%M:%S')


@app.template_filter('number')
def format_number(value):
    """Format number with commas"""
    if value is None:
        return '0'
    try:
        return f"{int(value):,}"
    except:
        return str(value)


# ============================================================================
# Development Server
# ============================================================================

def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run Flask development server

    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 5000)
        debug: Enable debug mode (default: False)
    """
    logger.info("=" * 80)
    logger.info("Network Segmentation Analyzer - Web Interface")
    logger.info("=" * 80)
    logger.info(f"  Server: Flask {app.name}")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Debug: {debug}")
    logger.info(f"  Backend: {pm.backend}")
    logger.info("=" * 80)
    logger.info(f"  Access at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    logger.info("=" * 80)
    logger.info("")

    app.run(host=host, port=port, debug=debug)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Network Segmentation Analyzer Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--postgres-host', help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, help='PostgreSQL port')
    parser.add_argument('--postgres-db', help='PostgreSQL database')
    parser.add_argument('--postgres-user', help='PostgreSQL user')
    parser.add_argument('--postgres-password', help='PostgreSQL password')

    args = parser.parse_args()

    # Update PostgreSQL config if provided
    if any([args.postgres_host, args.postgres_port, args.postgres_db, args.postgres_user, args.postgres_password]):
        postgres_config = {
            'host': args.postgres_host or pm.postgres_config['host'],
            'port': args.postgres_port or pm.postgres_config['port'],
            'database': args.postgres_db or pm.postgres_config['database'],
            'user': args.postgres_user or pm.postgres_config['user'],
            'password': args.postgres_password or pm.postgres_config['password']
        }

        logger.info("Reinitializing with custom PostgreSQL config...")
        pm = create_persistence_manager(postgres_config=postgres_config)

    # Run server
    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        pm.close()
        logger.info("Goodbye!")
    except Exception as e:
        logger.error(f"Server error: {e}")
        pm.close()
        sys.exit(1)
