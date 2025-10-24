#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retroactive Updater
===================
Updates historical flows.csv files when new hostname information is discovered

When App #50 discovers a hostname for an IP that Apps #1-49 used,
update all previous flows.csv files with the new information.

Author: Enterprise Security Team
Version: 1.0
"""

import csv
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class RetroactiveUpdater:
    """
    Updates historical flows.csv files when new hostname information is discovered

    Process:
    1. Detect DNS changes from DNSCacheManager
    2. Find all flows.csv files with affected IPs
    3. Update each file with new hostname information
    4. Log all updates for audit trail

    Update Log: persistent_data/retroactive_updates.log
    """

    def __init__(self, apps_dir: str = 'persistent_data/applications',
                 log_path: str = 'persistent_data/retroactive_updates.log'):
        """
        Initialize Retroactive Updater

        Args:
            apps_dir: Directory containing application subdirectories
            log_path: Path to update log file
        """
        self.apps_dir = Path(apps_dir)
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Track updates
        self.updates_made = []

        logger.info(f"RetroactiveUpdater initialized")
        logger.info(f"  Apps directory: {self.apps_dir}")
        logger.info(f"  Update log: {self.log_path}")

    def update_flows_for_ip_changes(self, ip_changes: Dict[str, Dict]):
        """
        Update all flows.csv files for changed IPs

        Args:
            ip_changes: Dict of IP → changed DNS result from DNSCacheManager
                {
                    "10.100.246.18": {
                        "hostname": "WAPRCG.rgbk.com",
                        "hostname_full": "VMware AD6FD1 | WAPRCG.rgbk.com",
                        "status": "valid",
                        ...
                    }
                }
        """
        if not ip_changes:
            logger.info("No IP changes to process")
            return

        logger.info(f"Processing retroactive updates for {len(ip_changes)} changed IPs")

        # Get all application directories
        if not self.apps_dir.exists():
            logger.error(f"Apps directory not found: {self.apps_dir}")
            return

        app_dirs = [d for d in self.apps_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(app_dirs)} application directories")

        # Process each application
        for app_dir in app_dirs:
            flows_csv = app_dir / 'flows.csv'

            if not flows_csv.exists():
                continue

            # Check if this app has any affected IPs
            affected = self._check_if_flows_affected(flows_csv, ip_changes)

            if affected:
                logger.info(f"Updating {app_dir.name}: {len(affected)} affected IPs")
                self._update_flows_file(flows_csv, ip_changes, app_dir.name)

        logger.info(f"Retroactive update complete: {len(self.updates_made)} files updated")
        self._write_update_log()

    def _check_if_flows_affected(self, flows_csv: Path, ip_changes: Dict[str, Dict]) -> Set[str]:
        """
        Check if flows.csv contains any affected IPs

        Args:
            flows_csv: Path to flows.csv
            ip_changes: Dict of changed IPs

        Returns:
            Set of affected IPs found in file
        """
        affected_ips = set()

        try:
            with open(flows_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    src_ip = row.get('Source IP', '').strip()
                    dst_ip = row.get('Dest IP', '').strip()

                    if src_ip in ip_changes:
                        affected_ips.add(src_ip)
                    if dst_ip in ip_changes:
                        affected_ips.add(dst_ip)

        except Exception as e:
            logger.error(f"Error checking flows file {flows_csv}: {e}")

        return affected_ips

    def _update_flows_file(self, flows_csv: Path, ip_changes: Dict[str, Dict], app_name: str):
        """
        Update flows.csv file with new hostname information

        Args:
            flows_csv: Path to flows.csv
            ip_changes: Dict of changed IPs
            app_name: Application name for logging
        """
        try:
            # Create backup
            backup_path = flows_csv.with_suffix('.csv.backup')
            shutil.copy2(flows_csv, backup_path)

            # Read all rows
            rows = []
            fieldnames = []

            with open(flows_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)

            # Update rows
            updates_count = 0

            for row in rows:
                src_ip = row.get('Source IP', '').strip()
                dst_ip = row.get('Dest IP', '').strip()

                # Update Source IP hostname
                if src_ip in ip_changes:
                    change = ip_changes[src_ip]
                    old_hostname = row.get('Source Hostname', '')

                    # Update hostname (use only DNS result for comparison)
                    if change['hostname']:
                        row['Source Hostname'] = change['hostname']

                    # Update full hostname if column exists
                    if 'Source Hostname (Full)' in fieldnames:
                        row['Source Hostname (Full)'] = change['hostname_full']

                    # Update DNS status if column exists
                    if 'Source DNS Status' in fieldnames:
                        row['Source DNS Status'] = change['status']

                    if old_hostname != change['hostname']:
                        updates_count += 1
                        logger.debug(f"  {app_name}: Source {src_ip}: {old_hostname} → {change['hostname']}")

                # Update Dest IP hostname
                if dst_ip in ip_changes:
                    change = ip_changes[dst_ip]
                    old_hostname = row.get('Dest Hostname', '')

                    # Update hostname (use only DNS result for comparison)
                    if change['hostname']:
                        row['Dest Hostname'] = change['hostname']

                    # Update full hostname if column exists
                    if 'Dest Hostname (Full)' in fieldnames:
                        row['Dest Hostname (Full)'] = change['hostname_full']

                    # Update DNS status if column exists
                    if 'Dest DNS Status' in fieldnames:
                        row['Dest DNS Status'] = change['status']

                    if old_hostname != change['hostname']:
                        updates_count += 1
                        logger.debug(f"  {app_name}: Dest {dst_ip}: {old_hostname} → {change['hostname']}")

            # Write updated rows
            with open(flows_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"  [OK] Updated {flows_csv.name}: {updates_count} changes")

            # Track update
            self.updates_made.append({
                'app_name': app_name,
                'flows_csv': str(flows_csv),
                'updates_count': updates_count,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error updating flows file {flows_csv}: {e}")
            # Restore backup if update failed
            if backup_path.exists():
                shutil.copy2(backup_path, flows_csv)
                logger.info(f"  Restored backup for {flows_csv}")

    def _write_update_log(self):
        """Write update log to file"""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Retroactive Update Session: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n\n")

                for update in self.updates_made:
                    f.write(f"App: {update['app_name']}\n")
                    f.write(f"File: {update['flows_csv']}\n")
                    f.write(f"Updates: {update['updates_count']}\n")
                    f.write(f"Timestamp: {update['timestamp']}\n")
                    f.write(f"{'-'*80}\n")

                f.write(f"\nTotal files updated: {len(self.updates_made)}\n")
                f.write(f"{'='*80}\n\n")

            logger.info(f"Update log written to: {self.log_path}")

        except Exception as e:
            logger.error(f"Failed to write update log: {e}")

    def update_single_app(self, app_name: str, ip_hostname_map: Dict[str, Dict]):
        """
        Update a single application's flows.csv with hostname information

        Args:
            app_name: Application name
            ip_hostname_map: Dict of IP → hostname information
        """
        app_dir = self.apps_dir / app_name
        flows_csv = app_dir / 'flows.csv'

        if not flows_csv.exists():
            logger.warning(f"flows.csv not found for {app_name}")
            return

        affected = self._check_if_flows_affected(flows_csv, ip_hostname_map)

        if affected:
            logger.info(f"Updating {app_name}: {len(affected)} affected IPs")
            self._update_flows_file(flows_csv, ip_hostname_map, app_name)
            self._write_update_log()
        else:
            logger.info(f"No updates needed for {app_name}")

    def get_update_statistics(self) -> Dict:
        """
        Get update statistics

        Returns:
            Dict with statistics
        """
        total_updates = sum(u['updates_count'] for u in self.updates_made)

        return {
            'files_updated': len(self.updates_made),
            'total_updates': total_updates,
            'apps_affected': [u['app_name'] for u in self.updates_made]
        }


if __name__ == '__main__':
    # Test the retroactive updater
    updater = RetroactiveUpdater()

    # Test with sample IP changes
    ip_changes = {
        '10.100.246.18': {
            'hostname': 'WAPRCG.rgbk.com',
            'hostname_full': 'VMware AD6FD1 | WAPRCG.rgbk.com',
            'status': 'valid',
            'is_vmware': True,
            'vmware_info': 'VMware AD6FD1'
        }
    }

    # Process updates
    updater.update_flows_for_ip_changes(ip_changes)

    # Get statistics
    stats = updater.get_update_statistics()
    print(f"Update statistics: {stats}")
