#!/usr/bin/env python3
"""
Regenerate Application Diagrams with Fixed Controls
====================================================

This script regenerates all *_application_diagram.html files with the
improved control buttons:
- Half-size buttons (70px instead of 140px)
- Half-size pan control (55px instead of 110px)
- Fixed pan directions (no longer inverted)
- Arrow symbols showing correct directions
- No jitter on interaction

Usage:
    python regenerate_diagrams_fixed_controls.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.application_diagram_generator import ApplicationDiagramGenerator
from src.persistence.unified_persistence import UnifiedPersistenceManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Regenerate all application diagrams"""
    print("\n" + "="*80)
    print("REGENERATING APPLICATION DIAGRAMS WITH FIXED CONTROLS")
    print("="*80)

    try:
        # Initialize persistence manager
        pm = UnifiedPersistenceManager()

        # Get all applications
        apps_raw = pm.list_applications()

        if not apps_raw:
            print("\n[X] No applications found in database")
            print("\nRun batch processing first:")
            print("  python run_batch_processing.py --batch-size 10")
            return False

        # Extract app IDs (apps might be dicts)
        if isinstance(apps_raw[0], dict):
            apps = [app['app_id'] for app in apps_raw if 'app_id' in app]
        else:
            apps = apps_raw

        print(f"\nFound {len(apps)} applications")
        print(f"Apps: {', '.join(str(a) for a in apps[:5])}" + (f" ... and {len(apps)-5} more" if len(apps) > 5 else ""))

        # Initialize diagram generator
        generator = ApplicationDiagramGenerator(pm)

        print("\nRegenerating diagrams...")

        success_count = 0
        error_count = 0

        for app_id in apps:
            try:
                print(f"\n  Processing {app_id}...", end=" ", flush=True)

                # Generate diagram
                generator.generate_application_diagram(app_id)

                print("✓")
                success_count += 1

            except Exception as e:
                print(f"[X] {e}")
                error_count += 1

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Success: {success_count}")
        print(f"  Errors:  {error_count}")
        print(f"  Total:   {len(apps)}")

        print("\n[OK] Diagrams regenerated with fixed controls!")
        print("\nWhat's new:")
        print("  [OK] Half-size buttons (70px wide)")
        print("  [OK] Half-size pan control (55px circle)")
        print("  [OK] Fixed pan directions (arrows work correctly now!)")
        print("  [OK] Arrow symbols show correct direction")
        print("  [OK] Smooth animations, no jitter")

        print("\nOutput location:")
        print("  outputs_final/diagrams/*_application_diagram.html")

        print("\nTest a diagram:")
        if apps:
            print(f"  start outputs_final/diagrams/{apps[0]}_application_diagram.html")

        return True

    except Exception as e:
        print(f"\n[X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
