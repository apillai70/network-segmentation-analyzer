"""
COPY THIS FILE TO PRODUCTION AS: src/analysis/__init__.py
===========================================================

This file should be placed at:
C:\Users\RC34361\network-segmentation-analyzer\src\analysis\__init__.py

This makes src/analysis/ a proper Python package that exports the analysis classes.
"""

# Option 1: Import from sibling analysis.py file (if it exists)
try:
    import importlib.util
    from pathlib import Path

    # Try to load analysis.py from parent src/ directory
    analysis_py_file = Path(__file__).parent.parent / 'analysis.py'

    if analysis_py_file.exists():
        spec = importlib.util.spec_from_file_location("_analysis_module", analysis_py_file)
        _analysis = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_analysis)

        TrafficAnalyzer = _analysis.TrafficAnalyzer
        SegmentationRule = _analysis.SegmentationRule
        NetworkZone = _analysis.NetworkZone
        analyze_traffic = _analysis.analyze_traffic

        __all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone', 'analyze_traffic']

    else:
        # If analysis.py doesn't exist as sibling, the classes should be in this package
        # This means the code was copied into this __init__.py
        # The actual class definitions will be below (if you copied analysis.py content here)
        raise ImportError("Need to define classes here or copy from analysis.py")

except Exception as e:
    # Option 2: Fallback - try importing from path manipulation
    import sys
    from pathlib import Path

    # Add parent directory to path
    parent = str(Path(__file__).parent.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    try:
        # Try importing analysis module
        from analysis import TrafficAnalyzer, SegmentationRule, NetworkZone, analyze_traffic
        __all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone', 'analyze_traffic']
    except ImportError:
        # Last resort: Classes must be defined in this file
        # If you see this error, you need to copy the content of analysis.py here
        raise ImportError(
            f"Cannot import analysis classes. Original error: {e}\n"
            "Solution: Copy the entire content of src/analysis.py into this __init__.py file"
        )
