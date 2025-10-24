#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Reference Manager
=======================
Manages IP-hostname cross-referencing across all applications

Tracks which IPs are used as Source or Dest across different apps
to identify valid inter-application flows.

Author: Enterprise Security Team
Version: 1.0
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CrossReferenceManager:
    """
    Manages cross-referencing of IPs and hostnames across all applications

    Database Structure:
    {
        "10.100.246.18": {
            "hostname": "WAPRCG.rgbk.com",
            "hostname_full": "VMware AD6FD1 | WAPRCG.rgbk.com",
            "source_apps": ["APP1", "APP2"],  # Apps where this IP is a source
            "dest_apps": ["APP3", "APP4"],     # Apps where this IP is a destination
            "last_updated": "2025-01-15T10:30:00",
            "dns_status": "valid",
            "is_vmware": true
        }
    }

    Stored in: persistent_data/cross_reference/ip_hostname_db.json
    """

    def __init__(self, db_path: str = 'persistent_data/cross_reference/ip_hostname_db.json'):
        """
        Initialize Cross-Reference Manager

        Args:
            db_path: Path to cross-reference database JSON file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory database
        self.database: Dict[str, Dict] = {}

        # Load existing database
        self.load_database()

        logger.info(f"CrossReferenceManager initialized")
        logger.info(f"  Database: {self.db_path}")
        logger.info(f"  Existing IPs: {len(self.database)}")

    def load_database(self):
        """Load cross-reference database from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.database = json.load(f)
                logger.info(f"Loaded cross-reference database: {len(self.database)} IPs")
            except Exception as e:
                logger.error(f"Failed to load cross-reference database: {e}")
                self.database = {}
        else:
            self.database = {}
            logger.info("No existing cross-reference database found, starting fresh")

    def save_database(self):
        """Save cross-reference database to JSON file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.database, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved cross-reference database: {len(self.database)} IPs")
        except Exception as e:
            logger.error(f"Failed to save cross-reference database: {e}")

    def add_source_ip(self, app_id: str, ip: str, hostname: str,
                     hostname_full: str, dns_status: str):
        """
        Add or update a source IP entry

        Args:
            app_id: Application ID
            ip: Source IP address
            hostname: Hostname (for comparisons)
            hostname_full: Full hostname (with VMware info)
            dns_status: DNS validation status
        """
        if ip not in self.database:
            self.database[ip] = {
                'hostname': hostname,
                'hostname_full': hostname_full,
                'source_apps': [],
                'dest_apps': [],
                'last_updated': datetime.now().isoformat(),
                'dns_status': dns_status,
                'is_vmware': '|' in hostname_full
            }

        # Update if better information available
        entry = self.database[ip]

        # Add app to source_apps if not already there
        if app_id not in entry['source_apps']:
            entry['source_apps'].append(app_id)

        # Update hostname if current entry is empty/unknown or new one is better
        if (not entry['hostname'] or entry['hostname'] == 'Unknown' or
            dns_status in ['valid', 'valid_forward_only']):
            entry['hostname'] = hostname
            entry['hostname_full'] = hostname_full
            entry['dns_status'] = dns_status
            entry['is_vmware'] = '|' in hostname_full
            entry['last_updated'] = datetime.now().isoformat()

    def add_dest_ip(self, app_id: str, ip: str, hostname: str,
                   hostname_full: str, dns_status: str):
        """
        Add or update a destination IP entry

        Args:
            app_id: Application ID
            ip: Destination IP address
            hostname: Hostname (for comparisons)
            hostname_full: Full hostname (with VMware info)
            dns_status: DNS validation status
        """
        if ip not in self.database:
            self.database[ip] = {
                'hostname': hostname,
                'hostname_full': hostname_full,
                'source_apps': [],
                'dest_apps': [],
                'last_updated': datetime.now().isoformat(),
                'dns_status': dns_status,
                'is_vmware': '|' in hostname_full
            }

        # Update if better information available
        entry = self.database[ip]

        # Add app to dest_apps if not already there
        if app_id not in entry['dest_apps']:
            entry['dest_apps'].append(app_id)

        # Update hostname if current entry is empty/unknown or new one is better
        if (not entry['hostname'] or entry['hostname'] == 'Unknown' or
            dns_status in ['valid', 'valid_forward_only']):
            entry['hostname'] = hostname
            entry['hostname_full'] = hostname_full
            entry['dns_status'] = dns_status
            entry['is_vmware'] = '|' in hostname_full
            entry['last_updated'] = datetime.now().isoformat()

    def get_hostname_for_ip(self, ip: str) -> Optional[Dict]:
        """
        Get hostname information for an IP

        Args:
            ip: IP address

        Returns:
            Dict with hostname info or None if not found
        """
        return self.database.get(ip)

    def find_apps_with_source_ip(self, ip: str) -> List[str]:
        """
        Find all apps that use this IP as a source

        Args:
            ip: IP address

        Returns:
            List of app IDs
        """
        entry = self.database.get(ip)
        if entry:
            return entry.get('source_apps', [])
        return []

    def find_apps_with_dest_ip(self, ip: str) -> List[str]:
        """
        Find all apps that use this IP as a destination

        Args:
            ip: IP address

        Returns:
            List of app IDs
        """
        entry = self.database.get(ip)
        if entry:
            return entry.get('dest_apps', [])
        return []

    def check_cross_reference(self, ip: str, is_source: bool = True) -> Dict:
        """
        Check if this IP has cross-references in other apps

        Args:
            ip: IP address to check
            is_source: True if checking source IP, False if checking dest IP

        Returns:
            Dict with cross-reference information:
            {
                'found': bool,
                'hostname': str or None,
                'hostname_full': str or None,
                'referenced_apps': List[str],
                'is_valid_flow': bool
            }
        """
        entry = self.database.get(ip)

        if not entry:
            return {
                'found': False,
                'hostname': None,
                'hostname_full': None,
                'referenced_apps': [],
                'is_valid_flow': False
            }

        # If checking dest IP, see if it's a source IP in other apps
        # This indicates a valid inter-application flow
        if not is_source:
            source_apps = entry.get('source_apps', [])
            if source_apps:
                return {
                    'found': True,
                    'hostname': entry.get('hostname'),
                    'hostname_full': entry.get('hostname_full'),
                    'referenced_apps': source_apps,
                    'is_valid_flow': True  # Dest IP is Source IP elsewhere
                }

        # If checking source IP, see if it's a dest IP in other apps
        if is_source:
            dest_apps = entry.get('dest_apps', [])
            if dest_apps:
                return {
                    'found': True,
                    'hostname': entry.get('hostname'),
                    'hostname_full': entry.get('hostname_full'),
                    'referenced_apps': dest_apps,
                    'is_valid_flow': True  # Source IP is Dest IP elsewhere
                }

        return {
            'found': False,
            'hostname': entry.get('hostname'),
            'hostname_full': entry.get('hostname_full'),
            'referenced_apps': [],
            'is_valid_flow': False
        }

    def get_all_ips(self) -> List[str]:
        """Get all IPs in database"""
        return list(self.database.keys())

    def get_statistics(self) -> Dict:
        """
        Get cross-reference database statistics

        Returns:
            Dict with statistics
        """
        total_ips = len(self.database)
        ips_as_source = sum(1 for entry in self.database.values() if entry.get('source_apps'))
        ips_as_dest = sum(1 for entry in self.database.values() if entry.get('dest_apps'))
        ips_as_both = sum(1 for entry in self.database.values()
                         if entry.get('source_apps') and entry.get('dest_apps'))
        vmware_ips = sum(1 for entry in self.database.values() if entry.get('is_vmware'))

        dns_statuses = {}
        for entry in self.database.values():
            status = entry.get('dns_status', 'unknown')
            dns_statuses[status] = dns_statuses.get(status, 0) + 1

        return {
            'total_ips': total_ips,
            'ips_as_source': ips_as_source,
            'ips_as_dest': ips_as_dest,
            'ips_as_both': ips_as_both,
            'vmware_ips': vmware_ips,
            'dns_statuses': dns_statuses
        }


if __name__ == '__main__':
    # Test the cross-reference manager
    manager = CrossReferenceManager()

    # Add some test data
    manager.add_source_ip('APP1', '10.100.246.18', 'WAPRCG.rgbk.com',
                         'VMware AD6FD1 | WAPRCG.rgbk.com', 'valid')

    manager.add_dest_ip('APP2', '10.100.246.18', 'WAPRCG.rgbk.com',
                       'VMware AD6FD1 | WAPRCG.rgbk.com', 'valid')

    # Check cross-reference
    cross_ref = manager.check_cross_reference('10.100.246.18', is_source=False)
    print(f"Cross-reference check: {cross_ref}")

    # Get statistics
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")

    # Save database
    manager.save_database()
    print(f"Database saved to: {manager.db_path}")
