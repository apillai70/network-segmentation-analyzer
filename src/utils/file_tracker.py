#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Tracker for Incremental Learning
======================================
Tracks processed files, detects duplicates, and manages file organization

Features:
- SHA256 file hashing for duplicate detection
- Row-level signature calculation
- Maintains processed file database
- Moves files to appropriate folders (processed/duplicates/errors)

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os

# Force UTF-8 encoding for console output (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    # Check if stdout/stderr have already been wrapped
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FileTracker:
    """
    Tracks processed files and detects duplicates

    Maintains a JSON database with:
    - filename
    - file_hash (SHA256)
    - timestamp
    - row_count
    - flow_signatures (unique flow hashes)
    """

    def __init__(self, watch_dir: str = './data/input', tracking_db: str = './data/input/processed_files.json'):
        """
        Initialize file tracker

        Args:
            watch_dir: Directory to watch for new files
            tracking_db: Path to JSON database for tracking
        """
        self.watch_dir = Path(watch_dir)
        self.tracking_db = Path(tracking_db)

        # Create subdirectories
        self.processed_dir = self.watch_dir / 'processed'
        self.duplicates_dir = self.watch_dir / 'duplicates'
        self.errors_dir = self.watch_dir / 'errors'

        for dir_path in [self.processed_dir, self.duplicates_dir, self.errors_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Load tracking database
        self.processed_files = self._load_tracking_db()

        logger.info(f"✓ FileTracker initialized")
        logger.info(f"  Watch: {self.watch_dir}")
        logger.info(f"  Tracked files: {len(self.processed_files)}")

    def _load_tracking_db(self) -> Dict:
        """Load tracking database from JSON"""
        if self.tracking_db.exists():
            try:
                with open(self.tracking_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load tracking DB: {e}")
                return {}
        return {}

    def _save_tracking_db(self):
        """Save tracking database to JSON"""
        try:
            with open(self.tracking_db, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tracking DB: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file content

        Args:
            file_path: Path to file

        Returns:
            Hex string of SHA256 hash
        """
        sha256 = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)

            return sha256.hexdigest()

        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return None

    def calculate_flow_signatures(self, file_path: Path, max_rows: int = 1000) -> List[str]:
        """
        Calculate unique signatures for flows (for row-level dedup)

        Args:
            file_path: Path to CSV file
            max_rows: Maximum rows to process (for performance)

        Returns:
            List of flow signature hashes
        """
        try:
            # Read CSV
            df = pd.read_csv(file_path, nrows=max_rows)

            # Expected columns
            required_cols = ['App', 'Source IP', 'Dest IP', 'Port', 'Protocol']

            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing required columns in {file_path.name}")
                return []

            # Create signature for each row (sorted for consistency)
            signatures = []
            for _, row in df.iterrows():
                # Create signature from key fields
                sig_data = f"{row['App']}|{row['Source IP']}|{row['Dest IP']}|{row['Port']}|{row['Protocol']}"

                # Hash the signature
                sig_hash = hashlib.md5(sig_data.encode('utf-8')).hexdigest()
                signatures.append(sig_hash)

            return signatures

        except Exception as e:
            logger.error(f"Failed to calculate flow signatures for {file_path}: {e}")
            return []

    def is_duplicate(self, file_path: Path) -> Tuple[bool, str]:
        """
        Check if file is a duplicate

        Args:
            file_path: Path to file to check

        Returns:
            Tuple of (is_duplicate: bool, reason: str)
        """
        filename = file_path.name

        # Check if filename already processed
        if filename in self.processed_files:
            existing_entry = self.processed_files[filename]

            # Calculate hash of new file
            new_hash = self.calculate_file_hash(file_path)

            if new_hash is None:
                return (False, "Could not calculate hash")

            # Compare hashes
            if existing_entry['file_hash'] == new_hash:
                return (True, f"Exact duplicate of processed file (hash: {new_hash[:8]}...)")
            else:
                return (False, f"Same filename but different content (updated file)")

        # Not a duplicate
        return (False, "New file")

    def check_row_overlap(self, file_path: Path, threshold: float = 0.8) -> Tuple[bool, float]:
        """
        Check if file has significant row overlap with processed files

        Args:
            file_path: Path to file to check
            threshold: Ratio of overlapping rows to consider duplicate (0.8 = 80%)

        Returns:
            Tuple of (has_overlap: bool, overlap_ratio: float)
        """
        try:
            # Calculate signatures for new file
            new_signatures = set(self.calculate_flow_signatures(file_path))

            if not new_signatures:
                return (False, 0.0)

            # Check overlap with each processed file
            max_overlap_ratio = 0.0

            for filename, entry in self.processed_files.items():
                if 'flow_signatures' not in entry:
                    continue

                processed_signatures = set(entry['flow_signatures'])

                # Calculate overlap
                overlap = len(new_signatures & processed_signatures)
                overlap_ratio = overlap / len(new_signatures)

                max_overlap_ratio = max(max_overlap_ratio, overlap_ratio)

                if overlap_ratio >= threshold:
                    logger.warning(f"  {file_path.name} has {overlap_ratio:.1%} row overlap with {filename}")
                    return (True, overlap_ratio)

            return (False, max_overlap_ratio)

        except Exception as e:
            logger.error(f"Failed to check row overlap: {e}")
            return (False, 0.0)

    def mark_as_processed(self, file_path: Path, row_count: int, process_time: float):
        """
        Mark file as processed and record metadata

        Args:
            file_path: Path to processed file
            row_count: Number of rows processed
            process_time: Time taken to process (seconds)
        """
        filename = file_path.name

        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)

        # Calculate flow signatures (sample first 1000 rows)
        flow_signatures = self.calculate_flow_signatures(file_path, max_rows=1000)

        # Record in database
        self.processed_files[filename] = {
            'file_hash': file_hash,
            'timestamp': datetime.now().isoformat(),
            'row_count': row_count,
            'process_time': process_time,
            'flow_signatures': flow_signatures,
            'original_path': str(file_path),
            'processed_path': str(self.processed_dir / filename)
        }

        # Save database
        self._save_tracking_db()

        logger.info(f"  Marked {filename} as processed (hash: {file_hash[:8]}...)")

    def move_to_processed(self, file_path: Path) -> Path:
        """
        Move file to processed directory

        Args:
            file_path: Path to file to move

        Returns:
            New path in processed directory
        """
        try:
            dest_path = self.processed_dir / file_path.name

            # Handle name collision
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.processed_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            shutil.move(str(file_path), str(dest_path))
            logger.info(f"  ✓ Moved to: {dest_path.relative_to(self.watch_dir)}")

            return dest_path

        except Exception as e:
            logger.error(f"Failed to move {file_path} to processed: {e}")
            return file_path

    def move_to_duplicates(self, file_path: Path, reason: str) -> Path:
        """
        Move file to duplicates directory

        Args:
            file_path: Path to file to move
            reason: Reason for duplicate detection

        Returns:
            New path in duplicates directory
        """
        try:
            dest_path = self.duplicates_dir / file_path.name

            # Handle name collision
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.duplicates_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            shutil.move(str(file_path), str(dest_path))
            logger.info(f"  ⚠ Duplicate detected: {reason}")
            logger.info(f"  ✓ Moved to: {dest_path.relative_to(self.watch_dir)}")

            return dest_path

        except Exception as e:
            logger.error(f"Failed to move {file_path} to duplicates: {e}")
            return file_path

    def move_to_errors(self, file_path: Path, error: str) -> Path:
        """
        Move file to errors directory

        Args:
            file_path: Path to file to move
            error: Error message

        Returns:
            New path in errors directory
        """
        try:
            dest_path = self.errors_dir / file_path.name

            # Handle name collision
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.errors_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            shutil.move(str(file_path), str(dest_path))

            # Save error log
            error_log_path = dest_path.with_suffix('.error.txt')
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write(f"Error processing: {file_path.name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Error: {error}\n")

            logger.error(f"  ✗ Processing failed: {error}")
            logger.info(f"  ✓ Moved to: {dest_path.relative_to(self.watch_dir)}")

            return dest_path

        except Exception as e:
            logger.error(f"Failed to move {file_path} to errors: {e}")
            return file_path

    def get_pending_files(self, pattern: str = 'App_Code_*.csv') -> List[Path]:
        """
        Get list of pending files to process

        Args:
            pattern: Glob pattern for files

        Returns:
            List of file paths to process
        """
        all_files = list(self.watch_dir.glob(pattern))

        # Filter out files in subdirectories
        pending_files = [f for f in all_files if f.parent == self.watch_dir]

        # Sort by modification time (oldest first)
        pending_files.sort(key=lambda f: f.stat().st_mtime)

        return pending_files

    def forget_file(self, filename: str) -> bool:
        """
        Remove a file from tracking database (allows reprocessing)

        Args:
            filename: Name of file to forget (e.g., 'App_Code_XECHK.csv')

        Returns:
            True if removed, False if not found
        """
        if filename in self.processed_files:
            del self.processed_files[filename]
            self._save_tracking_db()
            logger.info(f"✓ Removed {filename} from tracking database")
            logger.info(f"  File can now be reprocessed if placed in {self.watch_dir}")
            return True
        else:
            logger.warning(f"  {filename} not found in tracking database")
            return False

    def reset_all_tracking(self, confirm: bool = False):
        """
        Clear all tracking data (DANGEROUS - requires confirmation)

        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            logger.error("Reset requires confirm=True parameter")
            return False

        self.processed_files = {}
        self._save_tracking_db()
        logger.warning("⚠ All file tracking data cleared!")
        logger.info("  All files can now be reprocessed")
        return True

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            'total_processed': len(self.processed_files),
            'total_rows': sum(entry.get('row_count', 0) for entry in self.processed_files.values()),
            'avg_process_time': sum(entry.get('process_time', 0) for entry in self.processed_files.values()) / max(len(self.processed_files), 1),
            'pending_files': len(self.get_pending_files()),
            'duplicate_files': len(list(self.duplicates_dir.glob('*.csv'))),
            'error_files': len(list(self.errors_dir.glob('*.csv')))
        }
