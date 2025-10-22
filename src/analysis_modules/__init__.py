"""
Analysis Module
===============
Re-exports core analysis classes from parent analysis module.
"""

# Import from the analysis.py file in the parent src/ directory
# Using relative import to avoid conflicts
try:
    # Try importing from parent src directory
    from ..analysis import TrafficAnalyzer, SegmentationRule, NetworkZone
except ImportError:
    # Fallback: try absolute import (for backwards compatibility)
    try:
        from src.analysis import TrafficAnalyzer, SegmentationRule, NetworkZone
    except ImportError:
        # Last resort: manipulate path
        import sys
        from pathlib import Path
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        from analysis import TrafficAnalyzer, SegmentationRule, NetworkZone

__all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone']
