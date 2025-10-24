#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Cache Manager
=================
Persistent DNS cache with smart validation

Cache DNS results forever, but validate on every lookup.
If DNS changes, update cache and trigger retroactive updates.

Author: Enterprise Security Team
Version: 1.0
"""

import json
import logging
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DNSCacheManager:
    """
    Persistent DNS cache with smart validation

    Cache Structure:
    {
        "10.100.246.18": {
            "reverse_hostname": "WAPRCG.rgbk.com",
            "forward_ip": "10.100.246.18",
            "status": "valid",
            "timestamp": "2025-01-15T10:30:00",
            "is_vmware": true,
            "vmware_info": "VMware AD6FD1"
        }
    }

    Stored in: persistent_data/dns_cache.json

    Key Feature: Cache forever, but validate on every lookup
    If DNS changed, update cache and trigger retroactive updates
    """

    def __init__(self, cache_path: str = 'persistent_data/dns_cache.json',
                 timeout: float = 2.0):
        """
        Initialize DNS Cache Manager

        Args:
            cache_path: Path to DNS cache JSON file
            timeout: DNS lookup timeout in seconds
        """
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

        # In-memory cache
        self.cache: Dict[str, Dict] = {}

        # Track changes for retroactive updates
        self.changes: Dict[str, Dict] = {}

        # Load existing cache
        self.load_cache()

        logger.info(f"DNSCacheManager initialized")
        logger.info(f"  Cache: {self.cache_path}")
        logger.info(f"  Cached IPs: {len(self.cache)}")

    def load_cache(self):
        """Load DNS cache from JSON file"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded DNS cache: {len(self.cache)} IPs")
            except Exception as e:
                logger.error(f"Failed to load DNS cache: {e}")
                self.cache = {}
        else:
            self.cache = {}
            logger.info("No existing DNS cache found, starting fresh")

    def save_cache(self):
        """Save DNS cache to JSON file"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved DNS cache: {len(self.cache)} IPs")
        except Exception as e:
            logger.error(f"Failed to save DNS cache: {e}")

    def _perform_reverse_dns(self, ip: str) -> Tuple[Optional[str], str]:
        """
        Perform reverse DNS lookup (IP → hostname)

        Args:
            ip: IP address

        Returns:
            Tuple of (hostname, status)
            status: "valid", "NXDOMAIN", "timeout"
        """
        try:
            socket.setdefaulttimeout(self.timeout)
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname, "valid"
        except socket.herror:
            # Non-existent domain
            return None, "NXDOMAIN"
        except socket.timeout:
            return None, "timeout"
        except Exception as e:
            logger.debug(f"Reverse DNS failed for {ip}: {e}")
            return None, "error"

    def _perform_forward_dns(self, hostname: str) -> Tuple[Optional[str], str]:
        """
        Perform forward DNS lookup (hostname → IP)

        Args:
            hostname: Hostname

        Returns:
            Tuple of (ip, status)
            status: "valid", "NXDOMAIN", "timeout"
        """
        try:
            socket.setdefaulttimeout(self.timeout)
            ip = socket.gethostbyname(hostname)
            return ip, "valid"
        except socket.gaierror:
            return None, "NXDOMAIN"
        except socket.timeout:
            return None, "timeout"
        except Exception as e:
            logger.debug(f"Forward DNS failed for {hostname}: {e}")
            return None, "error"

    def _detect_vmware(self, hostname: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if hostname contains VMware patterns

        Args:
            hostname: Hostname to check

        Returns:
            Tuple of (is_vmware, vmware_info)
        """
        if not hostname:
            return False, None

        hostname_lower = hostname.lower()

        # Check for VMware patterns
        if 'vmware' in hostname_lower or 'vm-' in hostname_lower or 'vmhost' in hostname_lower:
            # Extract VMware info (part before pipe or before domain)
            if '|' in hostname:
                vmware_info = hostname.split('|')[0].strip()
            elif '.' in hostname:
                # Extract first part before domain
                vmware_info = hostname.split('.')[0].strip()
            else:
                vmware_info = hostname

            return True, vmware_info

        return False, None

    def lookup_with_validation(self, ip: str, fallback_hostname: Optional[str] = None) -> Dict:
        """
        Lookup IP with smart validation

        Process:
        1. Check cache
        2. Perform fresh DNS lookup
        3. If DNS changed, update cache and mark for retroactive update
        4. If reverse DNS fails, try forward DNS on fallback_hostname

        Args:
            ip: IP address to lookup
            fallback_hostname: Fallback hostname to try if reverse DNS fails (from Name column)

        Returns:
            Dict with DNS information:
            {
                'ip': str,
                'hostname': str or None,
                'hostname_full': str,  # "VMware AD6FD1 | WAPRCG.rgbk.com" or just hostname
                'status': str,  # "valid", "valid_forward_only", "mismatch", "NXDOMAIN", "unknown"
                'is_vmware': bool,
                'vmware_info': str or None,
                'changed': bool,  # True if DNS changed from cache
                'timestamp': str
            }
        """
        # Check cache
        cached = self.cache.get(ip)

        # Perform fresh reverse DNS lookup
        reverse_hostname, reverse_status = self._perform_reverse_dns(ip)

        # Handle reverse DNS results
        if reverse_status == "valid" and reverse_hostname:
            # Success! Now verify with forward DNS
            forward_ip, forward_status = self._perform_forward_dns(reverse_hostname)

            if forward_status == "valid" and forward_ip == ip:
                # Perfect match
                final_hostname = reverse_hostname
                final_status = "valid"
            elif forward_status == "valid" and forward_ip != ip:
                # Mismatch - use reverse result but mark it
                final_hostname = reverse_hostname
                final_status = "mismatch"
                logger.warning(f"DNS mismatch for {ip}: reverse={reverse_hostname}, forward={forward_ip}")
            else:
                # Forward DNS failed but reverse succeeded
                final_hostname = reverse_hostname
                final_status = "valid"

        elif reverse_status == "NXDOMAIN" and fallback_hostname:
            # Reverse DNS failed, try forward DNS on fallback hostname
            logger.debug(f"Reverse DNS failed for {ip}, trying forward DNS on {fallback_hostname}")
            forward_ip, forward_status = self._perform_forward_dns(fallback_hostname)

            if forward_status == "valid" and forward_ip == ip:
                # Forward DNS matched!
                final_hostname = fallback_hostname
                final_status = "valid_forward_only"
            else:
                # Both failed
                final_hostname = fallback_hostname if fallback_hostname else None
                final_status = "NXDOMAIN"

        else:
            # Both failed or no fallback
            final_hostname = fallback_hostname if fallback_hostname else None
            final_status = "NXDOMAIN" if reverse_status == "NXDOMAIN" else "unknown"

        # Detect VMware
        is_vmware, vmware_info = self._detect_vmware(final_hostname)

        # Build hostname_full
        if is_vmware and vmware_info:
            hostname_full = f"{vmware_info} | {final_hostname}"
        else:
            hostname_full = final_hostname if final_hostname else "Unknown"

        # Check if DNS changed
        changed = False
        if cached:
            if (cached.get('reverse_hostname') != final_hostname or
                cached.get('status') != final_status):
                changed = True
                logger.info(f"DNS changed for {ip}: {cached.get('reverse_hostname')} → {final_hostname}")

        # Build result
        result = {
            'ip': ip,
            'hostname': final_hostname,
            'hostname_full': hostname_full,
            'status': final_status,
            'is_vmware': is_vmware,
            'vmware_info': vmware_info,
            'changed': changed,
            'timestamp': datetime.now().isoformat()
        }

        # Update cache
        self.cache[ip] = {
            'reverse_hostname': final_hostname,
            'forward_ip': ip,
            'status': final_status,
            'timestamp': result['timestamp'],
            'is_vmware': is_vmware,
            'vmware_info': vmware_info
        }

        # Track changes for retroactive updates
        if changed:
            self.changes[ip] = result

        return result

    def get_cached(self, ip: str) -> Optional[Dict]:
        """
        Get cached DNS result (no validation)

        Args:
            ip: IP address

        Returns:
            Cached result or None
        """
        return self.cache.get(ip)

    def get_changes(self) -> Dict[str, Dict]:
        """
        Get all DNS changes detected since last clear

        Returns:
            Dict of IP → changed result
        """
        return self.changes.copy()

    def clear_changes(self):
        """Clear tracked changes"""
        self.changes = {}

    def get_statistics(self) -> Dict:
        """
        Get DNS cache statistics

        Returns:
            Dict with statistics
        """
        total_ips = len(self.cache)
        valid_ips = sum(1 for entry in self.cache.values() if entry.get('status') == 'valid')
        vmware_ips = sum(1 for entry in self.cache.values() if entry.get('is_vmware'))
        nxdomain_ips = sum(1 for entry in self.cache.values() if entry.get('status') == 'NXDOMAIN')

        return {
            'total_ips': total_ips,
            'valid_ips': valid_ips,
            'vmware_ips': vmware_ips,
            'nxdomain_ips': nxdomain_ips,
            'changes_detected': len(self.changes)
        }


if __name__ == '__main__':
    # Test the DNS cache manager
    manager = DNSCacheManager()

    # Test lookup with validation
    result = manager.lookup_with_validation('10.100.246.18', fallback_hostname='WAPRCG.rgbk.com')
    print(f"DNS lookup result: {result}")

    # Get statistics
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")

    # Save cache
    manager.save_cache()
    print(f"Cache saved to: {manager.cache_path}")
