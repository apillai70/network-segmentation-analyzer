# -*- coding: utf-8 -*-
"""
Web App Module
==============
Flask web application for network segmentation analyzer
"""

__version__ = '3.0'

# Import Flask app from parent level web_app.py
try:
    import sys
    from pathlib import Path
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Import app from web_app.py (at root level)
    import web_app as _web_app_module
    app = _web_app_module.app
except Exception as e:
    # If import fails, app will be None
    app = None
