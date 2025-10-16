#!/usr/bin/env python3
"""
Clean Up for Fresh Start
========================
Removes all old data, tracking, and generated files to start fresh with real customer data.

Usage:
    python cleanup_fresh_start.py
    python cleanup_fresh_start.py --move-file data/App_Code_AODSVY.csv
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

def print_header():
    print("=" * 80)
    print("🧹 CLEANUP FOR FRESH START")
    print("=" * 80)
    print()

def cleanup_tracking():
    """Remove file tracking data"""
    print("[INFO] Cleaning up file tracking...")

    tracking_files = [
        'outputs_final/persistent_data/file_tracking.json',
        'outputs_final/persistent_data/.file_tracker',
        'outputs_final/persistent_data/tracking.json'
    ]

    for file in tracking_files:
        path = Path(file)
        if path.exists():
            path.unlink()
            print(f"  [OK] Deleted: {file}")
        else:
            print(f"  - Not found: {file}")

def cleanup_topology():
    """Remove topology data"""
    print("\n🗺️  Cleaning up topology data...")

    # Delete topology file
    topo_file = Path('outputs_final/incremental_topology.json')
    if topo_file.exists():
        topo_file.unlink()
        print(f"  [OK] Deleted: {topo_file}")

    # Delete topology directories
    topo_dirs = [
        'outputs_final/persistent_data/topology',
        'outputs_final/persistent_data/flows'
    ]

    for dir_path in topo_dirs:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            print(f"  [OK] Deleted: {dir_path}/")

def cleanup_outputs():
    """Remove generated outputs"""
    print("\n[DATA] Cleaning up generated outputs...")

    # Diagrams
    diagram_dir = Path('outputs_final/diagrams')
    if diagram_dir.exists():
        for ext in ['*.png', '*.mmd', '*.html', '*.csv']:
            for file in diagram_dir.glob(ext):
                file.unlink()
                print(f"  [OK] Deleted: {file.name}")

    # Word reports
    word_dir = Path('outputs_final/word_reports')
    if word_dir.exists():
        shutil.rmtree(word_dir)
        print(f"  [OK] Deleted: outputs_final/word_reports/")

def cleanup_models():
    """Remove model checkpoints"""
    print("\n🤖 Cleaning up model checkpoints...")

    model_dirs = [
        'models/incremental',
        'models/ensemble'
    ]

    for dir_path in model_dirs:
        path = Path(dir_path)
        if path.exists():
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"  [OK] Cleaned: {dir_path}/")

def cleanup_input_files():
    """Remove generated input files (keep applicationList.csv)"""
    print("\n[FOLDER] Cleaning up generated input files...")

    input_dir = Path('data/input')
    if input_dir.exists():
        deleted = 0
        for file in input_dir.glob('App_Code_*.csv'):
            file.unlink()
            print(f"  [OK] Deleted: {file.name}")
            deleted += 1

        if deleted == 0:
            print("  - No App_Code_*.csv files found")

        # Keep applicationList.csv
        app_list = input_dir / 'applicationList.csv'
        if app_list.exists():
            print(f"  [OK] Kept: applicationList.csv")

def recreate_directories():
    """Recreate necessary directory structure"""
    print("\n📂 Recreating directory structure...")

    directories = [
        'outputs_final/persistent_data/topology',
        'outputs_final/persistent_data/flows',
        'outputs_final/diagrams',
        'outputs_final/word_reports/architecture',
        'outputs_final/word_reports/netseg',
        'models/incremental',
        'models/ensemble',
        'logs'
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  [OK] Created: {dir_path}/")

def move_file_to_input(source_file):
    """Move a file to data/input/ directory"""
    print(f"\n[STEP] Moving file to data/input/...")

    source = Path(source_file)
    if not source.exists():
        print(f"  [ERROR] File not found: {source_file}")
        return False

    # Ensure it's an App_Code file
    if not source.name.startswith('App_Code_'):
        print(f"  [WARNING]️  Warning: File doesn't follow App_Code_*.csv naming")

    # Move to input directory
    dest = Path('data/input') / source.name
    dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(source), str(dest))
    print(f"  [OK] Moved: {source} → {dest}")
    return True

def verify_clean_state():
    """Verify system is in clean state"""
    print("\n[SUCCESS] Verifying clean state...")

    checks = []

    # Check tracking
    tracking_file = Path('outputs_final/persistent_data/file_tracking.json')
    checks.append(("File tracking cleared", not tracking_file.exists()))

    # Check topology
    topo_file = Path('outputs_final/incremental_topology.json')
    checks.append(("Topology cleared", not topo_file.exists()))

    # Check input files
    input_dir = Path('data/input')
    app_files = list(input_dir.glob('App_Code_*.csv')) if input_dir.exists() else []
    checks.append(("Input directory ready", input_dir.exists()))
    checks.append(("applicationList.csv exists", (input_dir / 'applicationList.csv').exists()))

    # Print results
    all_passed = True
    for check, passed in checks:
        status = "[OK]" if passed else "[ERROR]"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False

    # Count App_Code files
    if app_files:
        print(f"\n[INFO] Found {len(app_files)} file(s) ready to process:")
        for file in app_files:
            print(f"    - {file.name}")
    else:
        print(f"\n[INFO] No App_Code_*.csv files in data/input/ yet")
        print("    Add your first file to data/input/ and run:")
        print("    python run_incremental_learning.py --batch")

    return all_passed

def main():
    parser = argparse.ArgumentParser(
        description='Clean up system for fresh start with customer data'
    )
    parser.add_argument(
        '--move-file',
        type=str,
        help='Move a file to data/input/ directory'
    )
    parser.add_argument(
        '--keep-logs',
        action='store_true',
        help='Keep log files'
    )

    args = parser.parse_args()

    print_header()

    # Confirm
    response = input("[WARNING]️  This will DELETE all existing data. Continue? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("[ERROR] Cancelled")
        return 1

    print()

    # Run cleanup
    cleanup_tracking()
    cleanup_topology()
    cleanup_outputs()
    cleanup_models()
    cleanup_input_files()

    # Clean logs (optional)
    if not args.keep_logs:
        print("\n[NOTE] Cleaning up log files...")
        logs_dir = Path('logs')
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                log_file.unlink()
                print(f"  [OK] Deleted: {log_file.name}")

    # Recreate structure
    recreate_directories()

    # Move file if specified
    if args.move_file:
        move_file_to_input(args.move_file)

    # Verify
    verify_clean_state()

    print("\n" + "=" * 80)
    print("[SUCCESS] CLEANUP COMPLETE!")
    print("=" * 80)
    print("\n[START] Next steps:")
    print("   1. Ensure your file is in data/input/App_Code_*.csv")
    print("   2. Run: python run_incremental_learning.py --batch")
    print("   3. Verify: python scripts/manage_file_tracking.py --list")
    print()

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING]️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
