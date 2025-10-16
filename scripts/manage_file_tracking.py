#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Tracking Management Utility
=================================
Manage processed file tracking for incremental learning

Usage:
    # List all processed files
    python scripts/manage_file_tracking.py --list

    # Forget a specific file (allows reprocessing)
    python scripts/manage_file_tracking.py --forget App_Code_XECHK.csv

    # Show statistics
    python scripts/manage_file_tracking.py --stats

    # Reset all tracking (DANGEROUS - requires confirmation)
    python scripts/manage_file_tracking.py --reset --confirm

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# Try both import paths
try:
    from src.utils.file_tracker import FileTracker
except ImportError:
    from utils.file_tracker import FileTracker


def list_processed_files(tracker: FileTracker):
    """List all processed files"""
    print("\n" + "=" * 80)
    print("PROCESSED FILES")
    print("=" * 80)

    if not tracker.processed_files:
        print("  No files processed yet")
        return

    print(f"\n  Total: {len(tracker.processed_files)} files\n")

    for filename, metadata in sorted(tracker.processed_files.items()):
        print(f"  [DOC] {filename}")
        print(f"     Hash: {metadata['file_hash'][:16]}...")
        print(f"     Timestamp: {metadata['timestamp']}")
        print(f"     Rows: {metadata['row_count']}")
        print(f"     Process time: {metadata.get('process_time', 0):.2f}s")
        print()

    print("=" * 80)


def show_statistics(tracker: FileTracker):
    """Show processing statistics"""
    stats = tracker.get_statistics()

    print("\n" + "=" * 80)
    print("FILE PROCESSING STATISTICS")
    print("=" * 80)
    print(f"\n  Total processed: {stats['total_processed']} files")
    print(f"  Total rows: {stats['total_rows']:,}")
    print(f"  Avg process time: {stats['avg_process_time']:.2f}s per file")
    print(f"\n  Pending files: {stats['pending_files']}")
    print(f"  Duplicate files: {stats['duplicate_files']}")
    print(f"  Error files: {stats['error_files']}")
    print("\n" + "=" * 80)


def forget_file(tracker: FileTracker, filename: str):
    """Forget a specific file"""
    print(f"\n🔄 Forgetting {filename}...")

    if tracker.forget_file(filename):
        print(f"\n[SUCCESS] Success!")
        print(f"   You can now reprocess this file by:")
        print(f"   1. Copying it back to data/input/")
        print(f"   2. Running incremental learning")
    else:
        print(f"\n[ERROR] File not found in tracking database")


def reset_tracking(tracker: FileTracker, confirm: bool):
    """Reset all tracking"""
    if not confirm:
        print("\n[WARNING]️  WARNING: This will clear ALL tracking data!")
        print("   All files will be considered 'new' and can be reprocessed")
        print("\n   To confirm, use: --reset --confirm")
        return

    print("\n[WARNING]️  RESETTING ALL TRACKING DATA...")

    tracker.reset_all_tracking(confirm=True)

    print(f"\n[SUCCESS] All tracking data cleared!")
    print(f"   {tracker.watch_dir} is now considered empty")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Manage file tracking for incremental learning',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all processed files'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show processing statistics'
    )

    parser.add_argument(
        '--forget',
        type=str,
        metavar='FILENAME',
        help='Forget a specific file (allows reprocessing)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all tracking (requires --confirm)'
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm dangerous operations (like --reset)'
    )

    parser.add_argument(
        '--watch-dir',
        type=str,
        default='./data/input',
        help='Watch directory (default: ./data/input)'
    )

    args = parser.parse_args()

    # Initialize FileTracker
    tracker = FileTracker(
        watch_dir=args.watch_dir,
        tracking_db=f'{args.watch_dir}/processed_files.json'
    )

    # Execute command
    if args.list:
        list_processed_files(tracker)
    elif args.stats:
        show_statistics(tracker)
    elif args.forget:
        forget_file(tracker, args.forget)
    elif args.reset:
        reset_tracking(tracker, args.confirm)
    else:
        # Show help
        parser.print_help()
        print("\n" + "=" * 80)
        print("QUICK EXAMPLES")
        print("=" * 80)
        print("\n  List processed files:")
        print("    python scripts/manage_file_tracking.py --list")
        print("\n  Show statistics:")
        print("    python scripts/manage_file_tracking.py --stats")
        print("\n  Forget a file (allow reprocessing):")
        print("    python scripts/manage_file_tracking.py --forget App_Code_XECHK.csv")
        print("\n  Reset all tracking:")
        print("    python scripts/manage_file_tracking.py --reset --confirm")
        print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
