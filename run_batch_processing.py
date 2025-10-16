#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Processing Script - Process Files in Batches
===================================================
Processes network flow files in configurable batches and generates all reports.

This script orchestrates the complete workflow:
1. Process batch of N files (incremental learning)
2. Generate .mmd and .html diagrams for ALL applications
3. Generate PNG files using Python Mermaid.ink API (no Node.js/Chrome!)
4. Generate network segmentation reports (optional)
5. Generate architecture documents (optional)
6. Repeat for next batch

Usage Examples:
    # Process all 138 files in batches of 10 (RECOMMENDED)
    python run_batch_processing.py --batch-size 10

    # Process with Mermaid diagrams only (fastest)
    python run_batch_processing.py --batch-size 10 --output-format mermaid

    # Process with Lucidchart CSVs only
    python run_batch_processing.py --batch-size 10 --output-format lucid

    # Process with both Mermaid + Lucidchart (default)
    python run_batch_processing.py --batch-size 10 --output-format both

    # Process 20 files at a time (faster batches)
    python run_batch_processing.py --batch-size 20

    # Process only first 5 batches (50 files if batch-size=10)
    python run_batch_processing.py --batch-size 10 --max-batches 5

    # Skip architecture docs (faster - only netseg reports)
    python run_batch_processing.py --batch-size 10 --skip-architecture

    # Clear all tracking first (reprocess everything)
    python run_batch_processing.py --batch-size 10 --clear-first

Per-File Status:
    The script shows real-time status for EACH file as it's processed:
    - File name being processed
    - Success/failure status
    - Flows analyzed
    - Diagrams generated (.mmd, .html, .png)
    - Time taken per file

IMPORTANT - PNG Generation:
    PNG files are generated using Python Mermaid.ink API - NO Node.js required!
    The script automatically generates .mmd, .html, and .png files for all applications.

    Rate limiting: The Mermaid.ink API has rate limits. Large batches may need delays.

Author: Enterprise Security Team
Version: 2.0 - Python PNG Generation (No Node.js!)
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import time
import logging

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup logging
log_file = Path('logs') / f'batch_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_command(cmd, description, show_realtime=False):
    """Run a command and capture output

    Args:
        cmd: Command to run
        description: Description for logging
        show_realtime: If True, show output in real-time (for per-file status)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"{'='*80}\n")

    start_time = time.time()

    try:
        if show_realtime:
            # Real-time output for per-file status
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            output_lines = []
            for line in process.stdout:
                # Print to console and log
                print(line, end='')
                output_lines.append(line)
                logger.debug(line.rstrip())

            process.wait()

            if process.returncode != 0:
                elapsed = time.time() - start_time
                logger.error(f"[ERROR] {description} failed after {elapsed:.1f}s")
                return False, ''.join(output_lines)

            elapsed = time.time() - start_time
            logger.info(f"[OK] {description} completed in {elapsed:.1f}s")
            return True, ''.join(output_lines)
        else:
            # Captured output for quieter commands
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            elapsed = time.time() - start_time
            logger.info(f"[OK] {description} completed in {elapsed:.1f}s")

            if result.stdout:
                logger.debug(f"STDOUT:\n{result.stdout}")

            return True, result.stdout

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        logger.error(f"[ERROR] {description} failed after {elapsed:.1f}s")
        logger.error(f"Error: {e}")

        if e.stdout:
            logger.error(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr}")

        return False, e.stderr


def count_unprocessed_files(input_dir='./data/input'):
    """Count CSV files in input directory"""
    input_path = Path(input_dir)
    if not input_path.exists():
        return 0

    csv_files = list(input_path.glob('App_Code_*.csv'))
    return len(csv_files)


def clear_file_tracking():
    """Clear all file tracking (forces reprocessing)"""
    logger.info("\n" + "="*80)
    logger.info("CLEARING FILE TRACKING")
    logger.info("="*80)

    cmd = [sys.executable, 'scripts/manage_file_tracking.py', '--reset', '--confirm']
    success, _ = run_command(cmd, "Clear file tracking")

    if success:
        logger.info("[OK] File tracking cleared - all files will be reprocessed")
    else:
        logger.warning("[WARNING] Failed to clear file tracking - continuing anyway")

    return success


def process_batch(batch_size=10):
    """Process a batch of files with real-time per-file status

    Returns:
        tuple: (success, list of app_codes processed)
    """
    logger.info("\n" + "="*80)
    logger.info(f"STEP 1: PROCESSING BATCH ({batch_size} files)")
    logger.info("="*80)

    # Check how many files will be processed
    from pathlib import Path
    import json

    # Get unprocessed files
    input_dir = Path('./data/input')
    file_tracker_path = input_dir / 'processed_files.json'

    processed_files = set()
    if file_tracker_path.exists():
        with open(file_tracker_path, 'r') as f:
            data = json.load(f)
            processed_files = set(data.get('processed_files', {}).keys())

    all_csv_files = sorted(input_dir.glob('App_Code_*.csv'))
    new_files = [f for f in all_csv_files if f.name not in processed_files][:batch_size]

    # Extract app codes that will be processed
    app_codes_to_process = [f.stem.replace('App_Code_', '') for f in new_files]

    logger.info(f"  Apps to process: {', '.join(app_codes_to_process[:5])}" +
                (f" ... and {len(app_codes_to_process)-5} more" if len(app_codes_to_process) > 5 else ""))

    cmd = [
        sys.executable,
        'run_incremental_learning.py',
        '--batch',
        '--max-files', str(batch_size)
    ]

    # Use real-time output to show per-file status
    success, output = run_command(
        cmd,
        f"Process batch of {batch_size} files",
        show_realtime=True  # Show each file as it's processed
    )

    return success, app_codes_to_process


def generate_netseg_reports(app_codes=None):
    """Generate network segmentation reports (Word docs only - diagrams already generated)

    Args:
        app_codes: List of app codes to process. If None, processes all apps.
    """
    logger.info("\n" + "="*80)
    if app_codes:
        logger.info(f"STEP 4: GENERATING NETWORK SEGMENTATION REPORTS (Word docs) FOR {len(app_codes)} APPS")
    else:
        logger.info("STEP 4: GENERATING NETWORK SEGMENTATION REPORTS (Word docs)")
    logger.info("="*80)

    # Skip diagram generation (already done by Python PNG generation in Step 3)
    # Only generate Word documents from existing PNGs
    cmd = [sys.executable, 'generate_all_reports.py', '--skip-diagrams']
    if app_codes:
        cmd.extend(['--apps'] + app_codes)

    success, output = run_command(
        cmd,
        f"Generate network segmentation reports (Word docs only) for {len(app_codes) if app_codes else 'all'} applications",
        show_realtime=True
    )
    return success


def generate_mmd_and_html(app_codes=None):
    """Generate .mmd and .html files for specified applications

    Args:
        app_codes: List of app codes to process. If None, processes all apps.
    """
    logger.info("\n" + "="*80)
    if app_codes:
        logger.info(f"STEP 2: GENERATING MMD AND HTML DIAGRAMS FOR {len(app_codes)} APPS")
    else:
        logger.info("STEP 2: GENERATING MMD AND HTML DIAGRAMS FOR ALL APPS")
    logger.info("="*80)

    cmd = [sys.executable, 'regenerate_all_mmds.py']
    if app_codes:
        cmd.extend(['--apps'] + app_codes)

    success, output = run_command(
        cmd,
        f"Generate .mmd and .html diagrams for {len(app_codes) if app_codes else 'all'} applications",
        show_realtime=True
    )
    return success


def fix_mmd_fencing(app_codes=None):
    """Fix markdown fencing in .mmd files (add ```mermaid wrapping)

    Args:
        app_codes: List of app codes to process. If None, processes all .mmd files.

    Returns:
        bool: True if successful
    """
    logger.info("\n" + "="*80)
    if app_codes:
        logger.info(f"STEP 2B: FIXING MARKDOWN FENCING FOR {len(app_codes)} APPS")
    else:
        logger.info("STEP 2B: FIXING MARKDOWN FENCING FOR ALL MMD FILES")
    logger.info("="*80)

    diagrams_dir = Path('outputs_final/diagrams')

    # Find .mmd files to fix
    if app_codes:
        mmd_files = [diagrams_dir / f'{app_code}_diagram.mmd' for app_code in app_codes]
        mmd_files = [f for f in mmd_files if f.exists()]
    else:
        mmd_files = list(diagrams_dir.glob('*.mmd'))

    if not mmd_files:
        logger.warning("No .mmd files found to fix")
        return True

    logger.info(f"Checking {len(mmd_files)} .mmd files for markdown fencing...")

    success = 0
    skipped = 0

    for mmd_file in mmd_files:
        # Read content
        with open(mmd_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Check if already has markdown fencing
        if content.startswith('```mermaid'):
            logger.debug(f"  {mmd_file.name} - Already has fencing (skipped)")
            skipped += 1
            continue

        # Add markdown fencing
        new_content = f"```mermaid\n{content}\n```"

        # Write back
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info(f"  [OK] {mmd_file.name} - Added markdown fencing")
        success += 1

    logger.info(f"[OK] Markdown fencing: {success} fixed, {skipped} skipped")
    return True


def generate_pngs_python(app_codes=None):
    """Generate PNG files using Python Mermaid.ink API (no Node.js required)

    Args:
        app_codes: List of app codes to process. If None, processes all apps.
    """
    logger.info("\n" + "="*80)
    if app_codes:
        logger.info(f"STEP 3: GENERATING PNG FILES FOR {len(app_codes)} APPS (Python/Mermaid.ink API)")
    else:
        logger.info("STEP 3: GENERATING PNG FILES (Python/Mermaid.ink API)")
    logger.info("="*80)

    cmd = [sys.executable, 'generate_pngs_python.py']
    if app_codes:
        cmd.extend(['--apps'] + app_codes)

    success, output = run_command(
        cmd,
        f"Generate PNG files for {len(app_codes) if app_codes else 'all'} applications",
        show_realtime=True
    )
    return success


def generate_architecture_docs():
    """Generate architecture documents"""
    logger.info("\n" + "="*80)
    logger.info("STEP 3: GENERATING ARCHITECTURE DOCUMENTS")
    logger.info("="*80)

    # Run simple architecture docs
    cmd1 = [sys.executable, 'generate_application_word_docs.py']
    success1, _ = run_command(cmd1, "Generate application architecture docs")

    # Run comprehensive solution design docs
    cmd2 = [sys.executable, 'generate_solution_design_docs.py']
    success2, _ = run_command(cmd2, "Generate solution design docs")

    return success1 or success2  # Success if at least one worked


def main():
    """Main batch processing orchestration"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Process network flow files in batches with full report generation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of files to process per batch (default: 10)'
    )

    parser.add_argument(
        '--max-batches',
        type=int,
        default=None,
        help='Maximum number of batches to process (default: unlimited)'
    )

    parser.add_argument(
        '--clear-first',
        action='store_true',
        help='Clear file tracking before starting (reprocess all files)'
    )

    parser.add_argument(
        '--skip-architecture',
        action='store_true',
        help='Skip architecture document generation (faster)'
    )

    parser.add_argument(
        '--skip-reports',
        action='store_true',
        help='Skip all report generation (only do analysis)'
    )

    parser.add_argument(
        '--output-format',
        choices=['mermaid', 'lucid', 'both'],
        default='both',
        help='Output format: mermaid (diagrams only), lucid (Lucidchart CSV), or both (default: both)'
    )

    parser.add_argument(
        '--filter-nonexistent',
        dest='filter_nonexistent',
        action='store_true',
        default=True,
        help='Filter flows where both IPs are non-existent domains (default: True)'
    )

    parser.add_argument(
        '--no-filter-nonexistent',
        dest='filter_nonexistent',
        action='store_false',
        help='Disable filtering of non-existent domain flows (show all flows)'
    )

    parser.add_argument(
        '--mark-nonexistent',
        dest='mark_nonexistent',
        action='store_true',
        default=True,
        help='Show "server-not-found" for non-existent domains (default: True)'
    )

    parser.add_argument(
        '--no-mark-nonexistent',
        dest='mark_nonexistent',
        action='store_false',
        help='Show raw IP addresses for non-existent domains'
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("BATCH PROCESSING ORCHESTRATOR")
    print("="*80)
    print(f"Batch size: {args.batch_size} files per batch")
    print(f"Max batches: {args.max_batches if args.max_batches else 'unlimited'}")
    print(f"Clear tracking first: {'Yes' if args.clear_first else 'No'}")
    print(f"Output format: {args.output_format.upper()}")
    print(f"  - Mermaid diagrams: {'Yes' if args.output_format in ['mermaid', 'both'] else 'No'}")
    print(f"  - Lucidchart CSVs: {'Yes' if args.output_format in ['lucid', 'both'] else 'No'}")
    print(f"Generate netseg reports: {'No' if args.skip_reports else 'Yes'}")
    print(f"Generate architecture docs: {'No' if args.skip_architecture else 'Yes (requires PNGs)'}")
    print(f"Flow filtering:")
    print(f"  - Filter non-existent: {'Yes' if args.filter_nonexistent else 'No'}")
    print(f"  - Mark non-existent: {'Yes (server-not-found)' if args.mark_nonexistent else 'No (show IPs)'}")
    print("="*80 + "\n")

    start_time = datetime.now()
    logger.info(f"Batch processing started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 0: Clear tracking if requested
    if args.clear_first:
        clear_file_tracking()
        time.sleep(2)  # Give file system time to settle

    # Count total files
    total_files = count_unprocessed_files()
    total_batches = (total_files + args.batch_size - 1) // args.batch_size  # Ceiling division

    if args.max_batches:
        total_batches = min(total_batches, args.max_batches)

    logger.info(f"\nTotal files to process: {total_files}")
    logger.info(f"Total batches planned: {total_batches}")

    if total_files == 0:
        logger.warning("\n[WARNING] No files to process!")
        logger.info("\nPossible reasons:")
        logger.info("  1. All files already processed (use --clear-first to reprocess)")
        logger.info("  2. No CSV files in data/input/")
        logger.info("  3. Files don't match pattern App_Code_*.csv")
        return

    # Statistics
    stats = {
        'batches_processed': 0,
        'batches_failed': 0,
        'reports_generated': 0,
        'reports_failed': 0,
        'architecture_generated': 0,
        'architecture_failed': 0
    }

    # Process batches
    batch_num = 1

    while batch_num <= total_batches:
        logger.info("\n\n" + "="*80)
        logger.info(f"BATCH {batch_num}/{total_batches}")
        logger.info("="*80)

        # Step 1: Process batch
        batch_success, app_codes_processed = process_batch(args.batch_size)

        if batch_success:
            stats['batches_processed'] += 1

            logger.info(f"\n[OK] Batch processing complete: {len(app_codes_processed)} apps processed")

            # Step 2: Generate .mmd and .html diagrams ONLY for apps in this batch
            if args.output_format in ['mermaid', 'both']:
                mmd_success = generate_mmd_and_html(app_codes_processed)
                if not mmd_success:
                    logger.warning("[WARNING] MMD generation had some failures - continuing...")

                # Step 2B: Fix markdown fencing in .mmd files for Mermaid.ink API compatibility
                fix_mmd_fencing(app_codes_processed)

            # Step 3: Generate PNGs ONLY for apps in this batch (no Node.js/Chrome!)
            if args.output_format in ['mermaid', 'both']:
                png_success = generate_pngs_python(app_codes_processed)
                if png_success:
                    logger.info("[OK] PNG generation complete")
                else:
                    logger.warning("[WARNING] Some PNGs may be missing")

            # Step 4: Generate network segmentation reports (ONLY for apps in this batch)
            if not args.skip_reports:
                if args.output_format in ['lucid', 'both']:
                    reports_success = generate_netseg_reports(app_codes_processed)

                    if reports_success:
                        stats['reports_generated'] += 1
                    else:
                        stats['reports_failed'] += 1
                        logger.warning("[WARNING] Report generation failed - continuing...")

            # Step 5: Generate architecture docs (INDEPENDENT of skip_reports flag)
            if not args.skip_architecture:
                # Verify PNGs exist first (architecture docs require them)
                diagrams_dir = Path('outputs_final/diagrams')
                png_files = list(diagrams_dir.glob('*_application_diagram.png')) if diagrams_dir.exists() else []

                if png_files:
                    logger.info(f"\n[INFO] Found {len(png_files)} PNG files for architecture docs")
                    arch_success = generate_architecture_docs()

                    if arch_success:
                        stats['architecture_generated'] += 1
                    else:
                        stats['architecture_failed'] += 1
                        logger.warning("[WARNING] Architecture doc generation failed - continuing...")
                else:
                    logger.warning("\n[WARNING] Cannot generate architecture docs - No PNG files found")
                    logger.info("  Architecture documents require PNG diagrams")
                    logger.info("  Solutions:")
                    logger.info("    1. Install mmdc: npm install -g @mermaid-js/mermaid-cli")
                    logger.info("    2. Run: python generate_missing_pngs.py")
                    logger.info("    3. Re-run batch processing after PNG generation")
                    stats['architecture_failed'] += 1

            # Check if more files remain
            remaining_files = count_unprocessed_files()

            logger.info(f"\n[OK] Batch {batch_num} complete")
            logger.info(f"  Remaining files: {remaining_files}")

            if remaining_files == 0:
                logger.info("\n[SUCCESS] All files processed!")
                break

            batch_num += 1

        else:
            stats['batches_failed'] += 1
            logger.error(f"\n[ERROR] Batch {batch_num} failed!")

            user_input = input("\nContinue to next batch? (y/n): ").strip().lower()

            if user_input != 'y':
                logger.info("User chose to stop processing")
                break

            batch_num += 1

    # Step 6: Build master topology from persistent data (runs ONCE at the end)
    if stats['batches_processed'] > 0:
        logger.info("\n\n" + "="*80)
        logger.info("STEP 6: BUILDING MASTER TOPOLOGY FROM PERSISTENT DATA")
        logger.info("="*80)

        try:
            cmd = [sys.executable, 'build_master_topology.py']
            topology_success, _ = run_command(
                cmd,
                "Build cumulative master topology",
                show_realtime=True
            )

            if topology_success:
                logger.info("[OK] Master topology built successfully")
                stats['master_topology_built'] = True
            else:
                logger.warning("[WARNING] Master topology build had issues")
                stats['master_topology_built'] = False

        except Exception as e:
            logger.error(f"[ERROR] Master topology build failed: {e}")
            stats['master_topology_built'] = False

    # Step 7: Generate threat surface documents (runs ONCE at the end for ALL apps)
    if stats['batches_processed'] > 0 and stats.get('master_topology_built', True):
        logger.info("\n\n" + "="*80)
        logger.info("STEP 7: GENERATING THREAT SURFACE & NETWORK SEGMENTATION DOCUMENTS")
        logger.info("="*80)

        try:
            cmd = [sys.executable, 'generate_threat_surface_docs.py']
            threat_success, _ = run_command(
                cmd,
                "Generate threat surface analysis documents",
                show_realtime=True
            )

            if threat_success:
                logger.info("[OK] Threat surface documents generated successfully")
                stats['threat_surface_generated'] = True
            else:
                logger.warning("[WARNING] Threat surface document generation had some issues")
                stats['threat_surface_generated'] = False

        except Exception as e:
            logger.error(f"[ERROR] Threat surface document generation failed: {e}")
            stats['threat_surface_generated'] = False

    # Final summary
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print("\n\n" + "="*80)
    print("BATCH PROCESSING COMPLETE")
    print("="*80)
    print(f"\nStart time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print()
    print("Statistics:")
    print(f"  Batches processed: {stats['batches_processed']}/{total_batches}")
    print(f"  Batches failed: {stats['batches_failed']}")

    if not args.skip_reports:
        print(f"  Netseg reports generated: {stats['reports_generated']}")
        print(f"  Netseg reports failed: {stats['reports_failed']}")

    if not args.skip_architecture:
        print(f"  Architecture docs generated: {stats['architecture_generated']}")
        print(f"  Architecture docs failed: {stats['architecture_failed']}")

    if stats.get('master_topology_built'):
        print(f"  Master topology built: [SUCCESS]")

    if stats.get('threat_surface_generated'):
        print(f"  Threat surface docs generated: [SUCCESS]")

    print()
    print("Output locations:")
    print("  Diagrams: outputs_final/diagrams/")
    print("  Network segmentation reports: outputs_final/word_reports/netseg/")
    print("  Architecture documents: outputs_final/word_reports/architecture/")
    print("  Threat surface analysis: outputs_final/word_reports/threat_surface/")
    print("  Persistent topology (individual): persistent_data/topology/")
    print("  Master topology (cumulative): persistent_data/master_topology.json")
    print()
    print(f"Log file: {log_file}")
    print("="*80)

    logger.info(f"\n[SUCCESS] Batch processing complete - {elapsed/60:.1f} minutes")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\n[WARNING] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)
