#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple File Processor with FileTracker
=======================================
Processes network flow files one by one with duplicate detection

This is a simplified version that focuses on file processing without
the complex ML components that have import issues.

Usage:
    # Process all pending files
    python process_files_simple.py

    # Process only 5 files
    python process_files_simple.py --max-files 5

    # Continuous mode (watch for new files)
    python process_files_simple.py --continuous

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os

# Force UTF-8 encoding (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
import logging
import time
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.file_tracker import FileTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/file_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SimpleFileProcessor:
    """Simple file processor with FileTracker integration"""

    def __init__(self, watch_dir='./data/input'):
        """Initialize processor"""
        self.watch_dir = Path(watch_dir)
        self.file_tracker = FileTracker(
            watch_dir=str(watch_dir),
            tracking_db=str(self.watch_dir / 'processed_files.json')
        )

        self.stats = {
            'total_processed': 0,
            'total_flows': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'start_time': datetime.now()
        }

        logger.info("✓ Simple File Processor initialized")
        logger.info(f"  Watch directory: {self.watch_dir}")

    def process_file(self, file_path: Path) -> dict:
        """Process a single file"""
        logger.info(f"📄 Processing: {file_path.name}")

        # Extract app_id
        app_id = file_path.stem.replace('App_Code_', '')

        # Check for duplicates
        is_dup, dup_reason = self.file_tracker.is_duplicate(file_path)

        if is_dup:
            logger.warning(f"  ⚠ DUPLICATE: {dup_reason}")
            self.file_tracker.move_to_duplicates(file_path, dup_reason)
            self.stats['total_duplicates'] += 1

            return {
                'app_id': app_id,
                'status': 'duplicate',
                'reason': dup_reason
            }

        start_time = time.time()

        try:
            # Read CSV
            df = pd.read_csv(file_path)
            logger.info(f"  ✓ Loaded {len(df)} flows for {app_id}")

            # Basic validation
            required_cols = ['App', 'Source IP', 'Dest IP']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Simulate processing (in real system, this would do ML/analysis)
            time.sleep(0.1)  # Simulate work

            # Calculate processing time
            process_time = time.time() - start_time

            # Mark as processed
            self.file_tracker.mark_as_processed(file_path, len(df), process_time)

            # Move to processed directory
            new_path = self.file_tracker.move_to_processed(file_path)

            # Update stats
            self.stats['total_processed'] += 1
            self.stats['total_flows'] += len(df)

            logger.info(f"  ✓ Successfully processed {app_id} in {process_time:.2f}s")

            return {
                'app_id': app_id,
                'status': 'success',
                'num_flows': len(df),
                'process_time': process_time,
                'new_location': str(new_path)
            }

        except Exception as e:
            logger.error(f"  ❌ Error processing {file_path.name}: {e}")

            # Move to errors directory
            self.file_tracker.move_to_errors(file_path, str(e))
            self.stats['total_errors'] += 1

            return {
                'app_id': app_id,
                'status': 'error',
                'error': str(e)
            }

    def process_batch(self, max_files=None):
        """Process a batch of pending files"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 BATCH FILE PROCESSING")
        logger.info("=" * 80)

        # Get pending files
        pending_files = self.file_tracker.get_pending_files(pattern='App_Code_*.csv')

        if not pending_files:
            logger.info("  No pending files found")
            return {'status': 'no_files'}

        # Limit if requested
        if max_files:
            pending_files = pending_files[:max_files]

        logger.info(f"  Processing {len(pending_files)} files...\n")

        # Process each file
        results = []
        for file_path in pending_files:
            result = self.process_file(file_path)
            results.append(result)

        # Count results by status
        successful = sum(1 for r in results if r['status'] == 'success')
        duplicates = sum(1 for r in results if r['status'] == 'duplicate')
        errors = sum(1 for r in results if r['status'] == 'error')

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ BATCH PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  Files processed: {len(results)}")
        logger.info(f"  ✓ Successful: {successful}")
        logger.info(f"  ⚠ Duplicates: {duplicates}")
        logger.info(f"  ✗ Errors: {errors}")
        logger.info(f"  Total flows: {self.stats['total_flows']:,}")
        logger.info("=" * 80 + "\n")

        return {
            'status': 'success',
            'total': len(results),
            'successful': successful,
            'duplicates': duplicates,
            'errors': errors,
            'results': results
        }

    def process_continuous(self, check_interval=30):
        """Process files continuously (watch mode)"""
        logger.info("\n" + "=" * 80)
        logger.info("🔄 CONTINUOUS FILE PROCESSING")
        logger.info("=" * 80)
        logger.info(f"  Watching: {self.watch_dir}")
        logger.info(f"  Check interval: {check_interval}s")
        logger.info(f"  Press Ctrl+C to stop")
        logger.info("=" * 80 + "\n")

        iteration = 0

        try:
            while True:
                iteration += 1
                logger.info(f"[Iteration {iteration}] Checking for new files...")

                # Process new files
                result = self.process_batch()

                if result['status'] == 'no_files':
                    logger.info(f"  No new files. Waiting {check_interval}s...\n")
                else:
                    logger.info(f"  Processed {result['successful']} new files\n")

                # Wait before next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("\n⚠️  Continuous processing stopped by user")
            self.print_final_stats()

    def print_final_stats(self):
        """Print final statistics"""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"  Files processed: {self.stats['total_processed']}")
        logger.info(f"  Total flows: {self.stats['total_flows']:,}")
        logger.info(f"  Duplicates skipped: {self.stats['total_duplicates']}")
        logger.info(f"  Errors: {self.stats['total_errors']}")
        logger.info(f"  Duration: {duration:.1f}s")
        logger.info(f"  Avg: {self.stats['total_processed'] / max(duration, 1):.2f} files/sec")
        logger.info("=" * 80 + "\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Simple File Processor with Duplicate Detection'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum files to process (default: all)'
    )

    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Continuous mode - watch for new files'
    )

    parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Check interval for continuous mode (seconds)'
    )

    parser.add_argument(
        '--watch-dir',
        type=str,
        default='./data/input',
        help='Directory to watch'
    )

    args = parser.parse_args()

    # Print banner
    print("\n" + "=" * 80)
    print("SIMPLE FILE PROCESSOR v3.0")
    print("=" * 80)
    print("📁 File Management with Duplicate Detection")
    print("🔄 Automatic Moving to processed/duplicates/errors/")
    print("=" * 80 + "\n")

    # Initialize processor
    processor = SimpleFileProcessor(watch_dir=args.watch_dir)

    try:
        if args.continuous:
            # Continuous mode
            processor.process_continuous(check_interval=args.check_interval)
        else:
            # Batch mode
            result = processor.process_batch(max_files=args.max_files)
            processor.print_final_stats()

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
