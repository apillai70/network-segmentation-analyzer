#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Processing Script - Process Files in Batches
===================================================
Processes network flow files in configurable batches and generates all reports.

This script orchestrates the complete workflow:
1. Process batch of N files (incremental learning + Mermaid diagrams)
2. Verify and generate PNG files (CRITICAL - needs mermaid-cli)
3. Generate network segmentation reports (optional)
4. Generate architecture documents (optional)
5. Repeat for next batch

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
    PNG files require mermaid-cli (mmdc) to be installed:

    npm install -g @mermaid-js/mermaid-cli

    If mmdc is not found, only .mmd and .html files will be generated.
    The script will automatically verify and regenerate missing PNGs after each batch.

Author: Enterprise Security Team
Version: 1.2 - PNG Verification
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
                logger.error(f"✗ {description} failed after {elapsed:.1f}s")
                return False, ''.join(output_lines)

            elapsed = time.time() - start_time
            logger.info(f"✓ {description} completed in {elapsed:.1f}s")
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
            logger.info(f"✓ {description} completed in {elapsed:.1f}s")

            if result.stdout:
                logger.debug(f"STDOUT:\n{result.stdout}")

            return True, result.stdout

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ {description} failed after {elapsed:.1f}s")
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
        logger.info("✓ File tracking cleared - all files will be reprocessed")
    else:
        logger.warning("⚠ Failed to clear file tracking - continuing anyway")

    return success


def process_batch(batch_size=10):
    """Process a batch of files with real-time per-file status"""
    logger.info("\n" + "="*80)
    logger.info(f"STEP 1: PROCESSING BATCH ({batch_size} files)")
    logger.info("="*80)

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

    return success


def generate_netseg_reports():
    """Generate network segmentation reports"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2: GENERATING NETWORK SEGMENTATION REPORTS")
    logger.info("="*80)

    cmd = [sys.executable, 'generate_all_reports.py']
    success, output = run_command(
        cmd, 
        "Generate network segmentation reports",
        show_realtime=True  # ← ADD THIS!
    )
    return success


def verify_and_generate_pngs():
    """Verify PNG files exist and regenerate missing ones"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2B: VERIFYING PNG FILES")
    logger.info("="*80)

    diagrams_dir = Path('outputs_final/diagrams')
    if not diagrams_dir.exists():
        logger.warning("Diagrams directory not found")
        return False

    # Find all .mmd files
    mmd_files = list(diagrams_dir.glob('*.mmd'))

    if not mmd_files:
        logger.info("No Mermaid files found - skipping PNG verification")
        return True

    missing_pngs = []
    for mmd_file in mmd_files:
        png_file = mmd_file.with_suffix('.png')
        if not png_file.exists():
            missing_pngs.append(mmd_file)

    logger.info(f"Found {len(mmd_files)} Mermaid diagrams")
    logger.info(f"Missing {len(missing_pngs)} PNG files")

    if missing_pngs:
        logger.info("Regenerating missing PNGs...")
        import subprocess
        import tempfile
        import shutil

        # Try to find mmdc - check multiple locations
        mmdc_cmd = None

        # Method 1: Check if mmdc is in PATH (works if nodeenv activated or globally installed)
        mmdc_in_path = shutil.which('mmdc')
        if mmdc_in_path:
            try:
                result = subprocess.run([mmdc_in_path, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    mmdc_cmd = mmdc_in_path
                    logger.info(f"Found mmdc in PATH: {mmdc_in_path}")
            except:
                pass

        # Method 2: Check for nodeenv in project directory (common for customer deployments)
        if not mmdc_cmd:
            project_root = Path(__file__).parent
            
            nodeenv_mmdc = project_root / 'nodeenv' / 'Scripts' / 'mmdc.cmd'
            if nodeenv_mmdc.exists():
                # Windows: Try both mmdc.cmd and mmdc.bat
                for ext in ['.cmd', '.bat', '']:
                    nodeenv_mmdc = project_root / 'nodeenv' / 'Scripts' / f'mmdc{ext}'
                    if nodeenv_mmdc.exists():
                        try:
                            result = subprocess.run([str(nodeenv_mmdc), '--version'], 
                            capture_output=True, timeout=5)
                            if result.returncode == 0:
                                mmdc_cmd = str(nodeenv_mmdc)
                                logger.info(f"Found mmdc in nodeenv: {mmdc_cmd}")
                                break
                        except:
                            pass

        # Method 3: Try standard Windows npm global location
        if not mmdc_cmd:
            import os
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                npm_mmdc = Path(user_profile) / 'AppData' / 'Roaming' / 'npm' / 'mmdc.cmd'
                if npm_mmdc.exists():
                    try:
                        result = subprocess.run([str(npm_mmdc), '--version'], capture_output=True, timeout=5)
                        if result.returncode == 0:
                            mmdc_cmd = str(npm_mmdc)
                            logger.info(f"Found mmdc in npm global: {mmdc_cmd}")
                    except:
                        pass

        # Method 4: Last resort - try 'mmdc' directly
        if not mmdc_cmd:
            try:
                result = subprocess.run(['mmdc', '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    mmdc_cmd = 'mmdc'
                    logger.info("Found mmdc (direct command)")
            except:
                pass

        if not mmdc_cmd:
            logger.warning("⚠ mmdc (mermaid-cli) not found - cannot generate PNGs")
            logger.info("Solutions:")
            logger.info("  1. Activate nodeenv: source nodeenv/bin/activate (Linux) or nodeenv\\Scripts\\activate (Windows)")
            logger.info("  2. Install globally: npm install -g @mermaid-js/mermaid-cli")
            logger.info("  3. Install in nodeenv: nodeenv/Scripts/npm install -g @mermaid-js/mermaid-cli")
            return False

        success_count = 0
        for mmd_file in missing_pngs:
            try:
                # Read and clean mermaid content
                with open(mmd_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract graph content
                lines = content.split('\n')
                graph_lines = []
                in_graph = False

                for line in lines:
                    if line.strip().startswith('```mermaid'):
                        in_graph = True
                        continue
                    elif line.strip() == '```':
                        in_graph = False
                        break
                    elif in_graph:
                        graph_lines.append(line)

                clean_content = '\n'.join(graph_lines).strip()

                # Write to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
                    tmp.write(clean_content)
                    tmp_path = tmp.name

                # Generate PNG
                png_path = mmd_file.with_suffix('.png')
                result = subprocess.run(
                    [mmdc_cmd, '-i', tmp_path, '-o', str(png_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    logger.info(f"  ✓ {mmd_file.stem}.png")
                    success_count += 1
                else:
                    logger.warning(f"  ✗ {mmd_file.stem}.png - {result.stderr[:100]}")

                # Clean up temp
                Path(tmp_path).unlink()

            except Exception as e:
                logger.warning(f"  ✗ {mmd_file.stem}.png - {str(e)[:100]}")

        logger.info(f"PNG generation: {success_count}/{len(missing_pngs)} successful")
        return success_count > 0
    else:
        logger.info("✓ All PNG files present")
        return True


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
        logger.warning("\n⚠ No files to process!")
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
        batch_success = process_batch(args.batch_size)

        if batch_success:
            stats['batches_processed'] += 1

            # Step 2: Generate reports FIRST (creates .mmd files)
            if not args.skip_reports:
                if args.output_format in ['lucid', 'both']:
                    reports_success = generate_netseg_reports()  # ← CREATE .mmd FILES FIRST!

                    if reports_success:
                        stats['reports_generated'] += 1
                    else:
                        stats['reports_failed'] += 1
                        logger.warning("⚠ Report generation failed - continuing...")

            # Step 2B: THEN verify and generate PNGs (now .mmd files exist!)
            if args.output_format in ['mermaid', 'both']:
                png_success = verify_and_generate_pngs()  # ← NOW .mmd FILES EXIST!

                if png_success:
                    logger.info("✓ PNG verification complete")
                else:
                    logger.warning("⚠ Some PNGs may be missing (mmdc not found?)")

            # Step 4: Generate architecture docs (INDEPENDENT of skip_reports flag)
            if not args.skip_architecture:
                # Verify PNGs exist first (architecture docs require them)
                diagrams_dir = Path('outputs_final/diagrams')
                png_files = list(diagrams_dir.glob('*_application_diagram.png')) if diagrams_dir.exists() else []

                if png_files:
                    logger.info(f"\n📄 Found {len(png_files)} PNG files for architecture docs")
                    arch_success = generate_architecture_docs()

                    if arch_success:
                        stats['architecture_generated'] += 1
                    else:
                        stats['architecture_failed'] += 1
                        logger.warning("⚠ Architecture doc generation failed - continuing...")
                else:
                    logger.warning("\n⚠ Cannot generate architecture docs - No PNG files found")
                    logger.info("  Architecture documents require PNG diagrams")
                    logger.info("  Solutions:")
                    logger.info("    1. Install mmdc: npm install -g @mermaid-js/mermaid-cli")
                    logger.info("    2. Run: python generate_missing_pngs.py")
                    logger.info("    3. Re-run batch processing after PNG generation")
                    stats['architecture_failed'] += 1

            # Check if more files remain
            remaining_files = count_unprocessed_files()

            logger.info(f"\n✓ Batch {batch_num} complete")
            logger.info(f"  Remaining files: {remaining_files}")

            if remaining_files == 0:
                logger.info("\n🎉 All files processed!")
                break

            batch_num += 1

        else:
            stats['batches_failed'] += 1
            logger.error(f"\n✗ Batch {batch_num} failed!")

            user_input = input("\nContinue to next batch? (y/n): ").strip().lower()

            if user_input != 'y':
                logger.info("User chose to stop processing")
                break

            batch_num += 1

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

    print()
    print("Output locations:")
    print("  Diagrams: outputs_final/diagrams/")
    print("  Network segmentation reports: outputs_final/word_reports/netseg/")
    print("  Architecture documents: outputs_final/word_reports/architecture/")
    print("  Topology data: persistent_data/topology/")
    print()
    print(f"Log file: {log_file}")
    print("="*80)

    logger.info(f"\n✅ Batch processing complete - {elapsed/60:.1f} minutes")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
