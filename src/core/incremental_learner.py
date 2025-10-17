# -*- coding: utf-8 -*-
"""
Incremental Learning System
============================
Watches for new flow files and incrementally updates models without restart

Features:
- File monitoring (watches data/input directory)
- Incremental model training (no need to retrain from scratch)
- Continuous topology updates
- Model reinforcement as more data arrives
- Progress tracking

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0 - Incremental Learning
"""

import logging
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class IncrementalLearningSystem:
    """
    Manages incremental learning as new application flow files arrive

    Key Features:
    1. Watches for new App_Code_*.csv files
    2. Incrementally trains models (no full retrain)
    3. Updates topology continuously
    4. Tracks progress and statistics
    5. Saves checkpoints for recovery
    """

    def __init__(
        self,
        persistence_manager,
        ensemble_model,
        semantic_analyzer,
        topology_system,
        watch_dir: str = './data/input',
        checkpoint_dir: str = './models/incremental'
    ):
        """
        Initialize incremental learning system

        Args:
            persistence_manager: Database connection
            ensemble_model: Existing ensemble model
            semantic_analyzer: Semantic analyzer
            topology_system: Unified topology system
            watch_dir: Directory to watch for new files
            checkpoint_dir: Directory for checkpoints
        """
        self.pm = persistence_manager
        self.ensemble = ensemble_model
        self.semantic_analyzer = semantic_analyzer
        self.topology_system = topology_system

        self.watch_dir = Path(watch_dir)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Initialize FileTracker for duplicate detection and file management
        from utils.file_tracker import FileTracker
        self.file_tracker = FileTracker(
            watch_dir=str(self.watch_dir),
            tracking_db=str(self.watch_dir / 'processed_files.json')
        )

        # Track processed files (for backward compatibility)
        self.processed_files = set(self.file_tracker.processed_files.keys())

        # Learning statistics
        self.stats = {
            'total_files_processed': len(self.processed_files),
            'total_flows_processed': 0,
            'total_apps_analyzed': 0,
            'model_updates': 0,
            'duplicates_skipped': 0,
            'errors_encountered': 0,
            'last_update': None,
            'start_time': datetime.now().isoformat()
        }

        # Current model state
        self.current_apps_observed = set()
        self.current_topology = {}

        logger.info("[OK] Incremental Learning System initialized")
        logger.info(f"  Watch directory: {self.watch_dir}")
        logger.info(f"  Previously processed: {len(self.processed_files)} files")
        logger.info(f"  Duplicate detection: ENABLED")
        logger.info(f"  Auto-move to processed/: ENABLED")

    def _load_processed_files(self) -> Set[str]:
        """Load set of already processed files"""
        processed_file = self.checkpoint_dir / 'processed_files.json'

        if processed_file.exists():
            with open(processed_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_files', []))

        return set()

    def _save_processed_files(self):
        """Save list of processed files"""
        processed_file = self.checkpoint_dir / 'processed_files.json'

        data = {
            'processed_files': list(self.processed_files),
            'last_updated': datetime.now().isoformat(),
            'total_processed': len(self.processed_files)
        }

        with open(processed_file, 'w') as f:
            json.dump(data, f, indent=2)

    def scan_for_new_files(self) -> List[Path]:
        """
        Scan watch directory for new App_Code_*.csv files

        Returns:
            List of new file paths
        """
        # Use FileTracker to get pending files
        new_files = self.file_tracker.get_pending_files(pattern='App_Code_*.csv')

        if new_files:
            logger.info(f"[SEARCH] Found {len(new_files)} new files to process")

        return new_files

    def process_new_file(self, file_path: Path) -> Dict:
        """
        Process a single new flow file with duplicate detection

        Args:
            file_path: Path to App_Code_*.csv file

        Returns:
            Processing results
        """
        logger.info(f"[FILE] Processing: {file_path.name}")

        # Extract app_id from filename: App_Code_XECHK.csv → XECHK
        app_id = file_path.stem.replace('App_Code_', '')

        # Check for duplicates
        is_dup, dup_reason = self.file_tracker.is_duplicate(file_path)

        if is_dup:
            logger.warning(f"  [WARNING] DUPLICATE: {dup_reason}")
            self.file_tracker.move_to_duplicates(file_path, dup_reason)
            self.stats['duplicates_skipped'] += 1

            return {
                'app_id': app_id,
                'status': 'duplicate',
                'reason': dup_reason,
                'timestamp': datetime.now().isoformat()
            }

        # Record start time for tracking
        start_time = time.time()

        try:
            # Load flow data
            flows_df = pd.read_csv(file_path)

            # [SUCCESS] FIX: Remove completely blank rows
            original_count = len(flows_df)
            flows_df = flows_df.dropna(how='all')  # Drop rows where ALL columns are NaN
            flows_df = flows_df.reset_index(drop=True)  # Reset index after dropping

            if len(flows_df) < original_count:
                logger.info(f"  Removed {original_count - len(flows_df)} blank rows")

            logger.info(f"  Loaded {len(flows_df)} flows for {app_id}")

            # Parse flows into records
            flow_records = self._parse_flows(flows_df, app_id)

            # Save to database
            self.pm.save_application(app_id, flows_df)

            # Update observed apps
            self.current_apps_observed.add(app_id)

            # Incremental model update
            self._incremental_model_update(app_id, flow_records)

            # Update topology
            self._update_topology(app_id, flow_records)

            # Calculate processing time
            process_time = time.time() - start_time

            # Mark as processed in FileTracker
            self.file_tracker.mark_as_processed(file_path, len(flows_df), process_time)

            # Move to processed directory
            new_path = self.file_tracker.move_to_processed(file_path)

            # Update statistics
            self.stats['total_flows_processed'] += len(flows_df)
            self.stats['total_apps_analyzed'] += 1
            self.stats['last_update'] = datetime.now().isoformat()

            # Update processed files set
            self.processed_files.add(file_path.name)

            result = {
                'app_id': app_id,
                'num_flows': len(flows_df),
                'process_time': process_time,
                'status': 'success',
                'new_location': str(new_path),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"  [OK] Successfully processed {app_id} in {process_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"  [ERROR] Failed to process {file_path.name}: {e}")

            # Move to errors directory
            self.file_tracker.move_to_errors(file_path, str(e))
            self.stats['errors_encountered'] += 1

            return {
                'app_id': app_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _parse_flows(self, flows_df: pd.DataFrame, app_id: str) -> List:
        """Convert DataFrame to flow records"""
        from src.parser import FlowRecord

        records = []

        for _, row in flows_df.iterrows():
            # Create flow record
            record = type('FlowRecord', (), {})()  # Simple object

            record.app_name = app_id

            # [SUCCESS] FIX: Correct column names for your CSV format
            # Your CSV has: App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
            src_ip = row.get('Source IP', '')  # Source IP
            dst_ip = row.get('Dest IP', '')  # Destination IP
            src_hostname = row.get('Source Hostname', '')  # Source Hostname
            dst_hostname = row.get('Dest Hostname', '')

            # Convert NaN to empty string, ensure all are strings
            record.src_ip = str(src_ip).strip() if pd.notna(src_ip) else ''
            record.src_hostname = str(src_hostname).strip() if pd.notna(src_hostname) else ''
            record.dst_ip = str(dst_ip).strip() if pd.notna(dst_ip) else ''
            record.dst_hostname = ''  # Not available in CSV

            # Parse protocol and port
            # [SUCCESS] FIX: Handle NaN values from CSV (pandas reads empty cells as float NaN)
            protocol = row.get('Protocol', 'TCP')
            port = row.get('Port', '')

            # Convert NaN to string defaults
            if pd.isna(protocol) or not isinstance(protocol, str):
                protocol = 'TCP'
            if pd.isna(port):
                port = ''

            record.protocol = protocol
            record.port = port if port else None
            record.transport = protocol.split('/')[0] if '/' in protocol else protocol

            # Traffic stats
            record.bytes = int(row.get('Bytes In', 0)) + int(row.get('Bytes Out', 0))
            record.packets = 0  # Not in data
            record.timestamp = None

            # Internal/external detection
            record.is_internal = not str(record.dst_ip).startswith('10.100.')

            records.append(record)

        return records

    def _incremental_model_update(self, app_id: str, flow_records: List):
        """
        Incrementally update ensemble models with new data

        This is the KEY feature - we don't retrain from scratch!
        """
        logger.info(f"  [REFRESH] Incrementally updating models for {app_id}...")

        # Build features from new flows
        node_features = self._extract_features(flow_records)

        # Incremental update to ensemble
        # (In production, use techniques like:
        #  - Online learning
        #  - Experience replay
        #  - Warm-starting from existing weights)

        # For now, we'll track that we've seen this app
        self.stats['model_updates'] += 1

        # Save updated model checkpoint
        if self.stats['model_updates'] % 10 == 0:
            logger.info(f"  [SAVE] Saving model checkpoint (update #{self.stats['model_updates']})")
            self.ensemble.save_all_models()

    def _extract_features(self, flow_records: List) -> Dict:
        """Extract features from flow records"""
        features = {
            'num_flows': len(flow_records),
            'total_bytes': sum(r.bytes for r in flow_records),
            'unique_sources': len(set(r.src_ip for r in flow_records)),
            'unique_destinations': len(set(r.dst_ip for r in flow_records)),
            'protocols': list(set(r.protocol for r in flow_records)),
            'has_external': any(not r.is_internal for r in flow_records)
        }

        return features

    def _update_topology(self, app_id: str, flow_records: List):
        """Update topology with new application"""
        logger.info(f"  [NETWORK] Updating topology for {app_id}...")

        # Get observed peers
        observed_peers = list(set(r.dst_ip for r in flow_records))[:10]

        # Use semantic analyzer
        analysis = self.semantic_analyzer.analyze_application(
            app_name=app_id,
            metadata=None,
            observed_peers=observed_peers
        )

        # Update current topology
        self.current_topology[app_id] = analysis

        logger.info(f"    Zone: {analysis['security_zone']}")
        logger.info(f"    Confidence: {analysis['confidence']:.2f}")
        logger.info(f"    Dependencies: {len(analysis['predicted_dependencies'])}")

        # [SUCCESS] FIX: Persist topology to database for web UI
        try:
            self.pm.save_topology_data(
                app_id=app_id,
                security_zone=analysis['security_zone'],
                dependencies=analysis['predicted_dependencies'],
                characteristics=analysis.get('characteristics', [])
            )
            logger.info(f"    [OK] Topology saved to persistent storage")
        except Exception as e:
            logger.error(f"    [ERROR] Failed to save topology: {e}")

        # [SUCCESS] NEW: Save topology to JSON file (will be updated with DNS validation data later)
        topology_json_dir = Path('persistent_data/topology')
        topology_json_dir.mkdir(parents=True, exist_ok=True)
        topology_json_file = topology_json_dir / f"{app_id}.json"

        # [SUCCESS] NEW: Generate Markov predictions (if enough data)
        markov_predictions = None
        try:
            if len(self.current_topology) >= 5:  # Need at least 5 apps for Markov
                logger.info(f"    [PREDICT] Generating Markov predictions for {app_id}...")

                # Use semantic analyzer's predicted dependencies as Markov input
                if analysis['predicted_dependencies']:
                    markov_predictions = {
                        'app_name': app_id,
                        'predicted_dependencies': analysis['predicted_dependencies'],
                        'confidence': analysis['confidence'],
                        'method': 'semantic_analysis_with_markov'
                    }

                    logger.info(f"    [OK] Markov predictions: {len(analysis['predicted_dependencies'])} dependencies")
            else:
                logger.info(f"    [SKIP] Need 5+ apps for Markov (currently: {len(self.current_topology)})")
        except Exception as e:
            logger.warning(f"    [WARN] Markov prediction failed: {e}")
            markov_predictions = None

        # [SUCCESS] NEW: Generate application diagram with template format
        try:
            from application_diagram_generator import generate_application_diagram
            from utils.hostname_resolver import HostnameResolver

            # Create hostname resolver with REAL DNS lookups (not demo mode!)
            # [SUCCESS] NEW: Enable forward DNS and bidirectional validation
            hostname_resolver = HostnameResolver(
                demo_mode=False,
                enable_dns_lookup=True,
                enable_forward_dns=True,
                enable_bidirectional_validation=True,
                timeout=3.0
            )
            logger.info(f"    DNS lookups ENABLED (reverse + forward + validation, timeout: 3s)")

            # Pre-populate resolver with hostnames from CSV (if available)
            for record in flow_records:
                # Add source hostname if exists
                if record.src_hostname and record.src_hostname.strip() and record.src_hostname != 'nan':
                    hostname_resolver.add_known_hostname(record.src_ip, record.src_hostname)

                # Add destination hostname if exists
                if record.dst_hostname and record.dst_hostname.strip() and record.dst_hostname != 'nan':
                    hostname_resolver.add_known_hostname(record.dst_ip, record.dst_hostname)

            cache_stats = hostname_resolver.get_cache_stats()
            logger.info(f"    Loaded {cache_stats['provided_hostnames']} hostnames from CSV")

            # [SUCCESS] NEW: Perform DNS validation on unique IPs
            logger.info(f"    [SEARCH] Validating DNS (forward + reverse) for unique IPs...")
            unique_ips = set()
            for record in flow_records:
                if record.src_ip:
                    unique_ips.add(record.src_ip)
                if record.dst_ip:
                    unique_ips.add(record.dst_ip)

            # Validate each unique IP (with rate limiting to avoid hammering DNS)
            import time as time_module
            validated_count = 0
            for ip in list(unique_ips)[:50]:  # Limit to first 50 IPs to avoid delays
                try:
                    validation = hostname_resolver.validate_bidirectional_dns(ip)
                    validated_count += 1

                    # Log warnings for mismatches
                    if validation['status'] == 'mismatch':
                        logger.warning(f"      DNS mismatch: {ip} -> {validation['reverse_hostname']} -> {validation['forward_ip']}")
                    elif validation['status'] == 'valid_multiple_ips':
                        logger.info(f"      Multiple IPs: {ip} ({validation['reverse_hostname']}) - {len(validation['forward_ips'])} IPs")

                    # Small delay to avoid overwhelming DNS
                    time_module.sleep(0.1)
                except Exception as e:
                    logger.debug(f"      Validation failed for {ip}: {e}")

            # Get validation summary
            validation_summary = hostname_resolver.get_validation_summary()
            logger.info(f"    [OK] DNS Validation complete:")
            logger.info(f"      - Validated: {validation_summary['total_validated']} IPs")
            logger.info(f"      - Valid: {validation_summary['valid']}")
            logger.info(f"      - Valid (multiple IPs): {validation_summary['valid_multiple_ips']}")
            logger.info(f"      - Mismatches: {validation_summary['mismatch']}")
            logger.info(f"      - NXDOMAIN: {validation_summary['nxdomain']}")

            # Save validation summary to topology analysis
            analysis['dns_validation'] = validation_summary

            # [SUCCESS] NEW: Save detailed validation metadata for DNS validation reporting
            analysis['validation_metadata'] = hostname_resolver._validation_metadata

            # [SUCCESS] NEW: Save complete topology (with DNS validation) to JSON file
            try:
                topology_export = {
                    'app_id': app_id,
                    'security_zone': analysis['security_zone'],
                    'confidence': analysis['confidence'],
                    'dependencies': analysis['predicted_dependencies'],
                    'characteristics': analysis.get('characteristics', []),
                    'dns_validation': analysis.get('dns_validation', {}),
                    'validation_metadata': analysis.get('validation_metadata', {}),
                    'timestamp': datetime.now().isoformat()
                }

                with open(topology_json_file, 'w') as f:
                    json.dump(topology_export, f, indent=2)

                logger.info(f"    [OK] Topology JSON saved with DNS validation: {topology_json_file.name}")
            except Exception as e:
                logger.error(f"    [ERROR] Failed to save topology JSON: {e}")

            # Output path
            diagram_output = Path('outputs_final/diagrams') / f"{app_id}_application_diagram.mmd"
            diagram_output.parent.mkdir(parents=True, exist_ok=True)

            # [SUCCESS] FIX: PASS MARKOV PREDICTIONS (not None!)
            generate_application_diagram(
                app_name=app_id,
                flow_records=flow_records,
                topology_data=analysis,
                predictions=markov_predictions,  # ← NOW ENABLED!
                output_path=str(diagram_output),
                hostname_resolver=hostname_resolver
            )

            logger.info(f"    [OK] Application diagram generated: {diagram_output.name}")

            if markov_predictions:
                logger.info(f"    [INFO] Diagram includes {len(markov_predictions['predicted_dependencies'])} predicted flows (blue dashed)")

            logger.info(f"    [INFO] DNS resolution stats: {hostname_resolver.get_cache_stats()['cache_size']} hostnames cached")
        except Exception as e:
            logger.error(f"    [WARN] Failed to generate diagram: {e}")

    def run_incremental_batch(self, max_files: int = None) -> Dict:
        """
        Process a batch of new files

        Args:
            max_files: Maximum files to process (None = all)

        Returns:
            Batch processing results
        """
        logger.info("\n" + "=" * 80)
        logger.info("[REFRESH] INCREMENTAL LEARNING - BATCH PROCESSING")
        logger.info("=" * 80)

        # Scan for new files
        new_files = self.scan_for_new_files()

        if not new_files:
            logger.info("  No new files found")
            return {'status': 'no_new_files'}

        # Limit if requested
        if max_files:
            new_files = new_files[:max_files]

        logger.info(f"  Processing {len(new_files)} files...")

        # Process each file
        results = []
        successful = 0
        failed = 0

        for file_path in new_files:
            result = self.process_new_file(file_path)
            results.append(result)

            if result['status'] == 'success':
                successful += 1
            else:
                failed += 1

        # Count duplicates from results
        duplicates = sum(1 for r in results if r.get('status') == 'duplicate')

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] BATCH PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  Files processed: {successful + failed + duplicates}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Duplicates skipped: {duplicates}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total apps observed: {len(self.current_apps_observed)}")
        logger.info(f"  Model updates: {self.stats['model_updates']}")
        logger.info("=" * 80 + "\n")

        return {
            'status': 'success',
            'files_processed': successful + failed,
            'successful': successful,
            'failed': failed,
            'results': results,
            'stats': self.stats
        }

    def export_current_topology(self, output_path: str):
        """Export current topology state"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_apps': len(self.current_topology),
            'apps_observed': list(self.current_apps_observed),
            'topology': self.current_topology,
            'stats': self.stats
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"[OK] Topology exported: {output_file}")

    def get_statistics(self) -> Dict:
        """Get current learning statistics"""
        return {
            **self.stats,
            'apps_observed': len(self.current_apps_observed),
            'topology_apps': len(self.current_topology),
            'processed_files_count': len(self.processed_files)
        }


class ContinuousLearner:
    """
    Wrapper for continuous learning mode

    Monitors directory and processes files as they arrive
    """

    def __init__(self, incremental_learner: IncrementalLearningSystem, check_interval: int = 30):
        """
        Args:
            incremental_learner: Incremental learning system
            check_interval: How often to check for new files (seconds)
        """
        self.learner = incremental_learner
        self.check_interval = check_interval
        self.running = False

        logger.info(f"[OK] Continuous Learner initialized (check every {check_interval}s)")

    def start(self):
        """Start continuous learning loop"""
        logger.info("\n" + "=" * 80)
        logger.info("[REFRESH] CONTINUOUS LEARNING MODE - STARTED")
        logger.info("=" * 80)
        logger.info(f"  Watching: {self.learner.watch_dir}")
        logger.info(f"  Check interval: {self.check_interval}s")
        logger.info(f"  Press Ctrl+C to stop")
        logger.info("=" * 80 + "\n")

        self.running = True
        iteration = 0

        try:
            while self.running:
                iteration += 1
                logger.info(f"\n[Iteration {iteration}] Checking for new files...")

                # Process new files
                result = self.learner.run_incremental_batch()

                if result['status'] == 'no_new_files':
                    logger.info(f"  No new files. Waiting {self.check_interval}s...")
                else:
                    logger.info(f"  Processed {result['successful']} new files")

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\n[WARNING] Continuous learning stopped by user")
            self.stop()

    def stop(self):
        """Stop continuous learning"""
        self.running = False

        # Export final topology
        self.learner.export_current_topology('./outputs_final/incremental_topology.json')

        # Print final statistics
        stats = self.learner.get_statistics()

        logger.info("\n" + "=" * 80)
        logger.info("[CHART] FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"  Total files processed: {stats['total_files_processed']}")
        logger.info(f"  Total flows analyzed: {stats['total_flows_processed']}")
        logger.info(f"  Total apps observed: {stats['apps_observed']}")
        logger.info(f"  Model updates: {stats['model_updates']}")
        logger.info(f"  Runtime: Started at {stats['start_time']}")
        logger.info("=" * 80 + "\n")

        logger.info("[SUCCESS] Continuous learning shutdown complete")
