#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hostname Resolver - Resolve IP addresses to hostnames
======================================================
Supports multiple resolution strategies:
1. CSV data (if hostname column exists)
2. Reverse DNS lookup (nslookup)
3. Domain Controller query (production)
4. Synthetic generation (demo mode)

Author: Enterprise Security Team
Version: 1.0
"""

import socket
import logging
import re
from typing import Optional, Dict, Tuple, List
from ipaddress import ip_address, IPv4Address, IPv6Address

logger = logging.getLogger(__name__)


class HostnameResolver:
    """
    Resolve IP addresses to hostnames using multiple strategies

    Resolution Order:
    1. Check cache
    2. Check provided data (CSV column)
    3. Reverse DNS lookup (if enabled)
    4. Domain Controller query (if configured)
    5. Generate synthetic hostname (demo mode)
    """

    def __init__(self,
                 demo_mode: bool = False,
                 enable_dns_lookup: bool = True,
                 enable_forward_dns: bool = True,
                 enable_bidirectional_validation: bool = True,
                 dc_server: Optional[str] = None,
                 dc_domain: Optional[str] = None,
                 timeout: float = 2.0,
                 filter_nonexistent: bool = True,
                 mark_nonexistent: bool = True):
        """
        Args:
            demo_mode: If True, generate synthetic hostnames instead of DNS lookups
            enable_dns_lookup: Enable reverse DNS lookups (IP → hostname)
            enable_forward_dns: Enable forward DNS lookups (hostname → IP)
            enable_bidirectional_validation: Validate forward and reverse DNS match
            dc_server: Domain Controller server address (e.g., "dc1.company.com")
            dc_domain: Domain name (e.g., "company.local")
            timeout: DNS lookup timeout in seconds
            filter_nonexistent: If True, mark non-existent domains for filtering (default: True)
            mark_nonexistent: If True, show "server-not-found" for failed DNS lookups (default: True)
        """
        self.demo_mode = demo_mode
        self.enable_dns_lookup = enable_dns_lookup
        self.enable_forward_dns = enable_forward_dns
        self.enable_bidirectional_validation = enable_bidirectional_validation
        self.dc_server = dc_server
        self.dc_domain = dc_domain
        self.timeout = timeout
        self.filter_nonexistent = filter_nonexistent
        self.mark_nonexistent = mark_nonexistent

        # Cache for resolved hostnames (IP → hostname)
        self._cache: Dict[str, str] = {}

        # Cache for forward DNS (hostname → IP)
        self._forward_cache: Dict[str, str] = {}

        # Multiple IPs per host (hostname → list of IPs for VM + ESXi scenarios)
        self._multiple_ips: Dict[str, List[str]] = {}

        # Provided hostnames (from CSV or other sources)
        self._provided_hostnames: Dict[str, str] = {}

        # Track non-existent domains
        self._nonexistent_ips: set = set()

        # Validation metadata
        self._validation_metadata: Dict[str, Dict] = {}  # IP → {status, timestamp, mismatch_details}

        logger.info(f"HostnameResolver initialized")
        logger.info(f"  Demo mode: {demo_mode}")
        logger.info(f"  DNS lookup: {enable_dns_lookup}")
        logger.info(f"  Filter non-existent: {filter_nonexistent}")
        logger.info(f"  Mark non-existent: {mark_nonexistent}")
        if dc_server:
            logger.info(f"  DC Server: {dc_server}")
            logger.info(f"  DC Domain: {dc_domain}")

    def add_known_hostname(self, ip_address: str, hostname: str):
        """
        Add a known IP->hostname mapping (from CSV data)

        Args:
            ip_address: IP address
            hostname: Hostname for this IP
        """
        self._provided_hostnames[ip_address] = hostname
        self._cache[ip_address] = hostname

    def resolve(self, ip_address: str, zone: Optional[str] = None) -> str:
        """
        Resolve IP address to hostname

        Args:
            ip_address: IP address to resolveac
            zone: Security zone hint (for synthetic generation)

        Returns:
            Hostname (or IP if resolution fails)
        """
        # Check cache first
        if ip_address in self._cache:
            return self._cache[ip_address]

        # Check provided hostnames
        if ip_address in self._provided_hostnames:
            hostname = self._provided_hostnames[ip_address]
            self._cache[ip_address] = hostname
            return hostname

        # Try resolution strategies
        hostname = None

        if self.demo_mode:
            # Demo mode: Generate synthetic hostname
            hostname = self._generate_synthetic_hostname(ip_address, zone)
        else:
            # Production mode: Try DNS/DC lookup
            if self.dc_server and self.dc_domain:
                hostname = self._query_domain_controller(ip_address)

            if not hostname and self.enable_dns_lookup:
                hostname = self._reverse_dns_lookup(ip_address)

        # Handle non-existent domains
        if hostname == "NXDOMAIN":
            if self.mark_nonexistent:
                # Show descriptive message for non-existent domains
                hostname = "server-not-found"
                logger.debug(f"Marked {ip_address} as server-not-found (NXDOMAIN)")
            else:
                # Just use IP address
                hostname = ip_address

        # Fallback to IP address if all methods fail
        if not hostname:
            hostname = ip_address

        # Cache the result
        self._cache[ip_address] = hostname
        return hostname

    def resolve_with_display(self, ip_address: str, zone: Optional[str] = None, format: str = 'mermaid') -> Tuple[str, str]:
        """
        Resolve and return both hostname and display name

        Args:
            ip_address: IP address to resolve
            zone: Security zone hint
            format: Display format ('mermaid', 'text', 'html')

        Returns:
            Tuple of (hostname, display_name)
            display_name is formatted hostname with IP
            For multiple IPs: "ESXi:IP1 - Hostname - VM:IP2"
        """
        hostname = self.resolve(ip_address, zone)

        if hostname and hostname != ip_address:
            # Check if this hostname has multiple IPs (VM + ESXi scenario)
            if self.has_multiple_ips(hostname):
                # Use multiple IP formatting
                display_name = self.format_multiple_ips_display(hostname, ip_address)
                return hostname, display_name

            # Got a real hostname - format based on output type
            if format == 'mermaid':
                display_name = f"{hostname}<br/>({ip_address})"
            elif format == 'html':
                display_name = f"{hostname}<br/>({ip_address})"
            else:  # text
                display_name = f"{hostname} ({ip_address})"

            return hostname, display_name
        else:
            # No hostname, just show IP
            return ip_address, ip_address

    def _reverse_dns_lookup(self, ip_address: str) -> Optional[str]:
        """
        Perform reverse DNS lookup (nslookup)

        Args:
            ip_address: IP address to lookup

        Returns:
            Hostname, "NXDOMAIN" for non-existent domains, or None for other failures
        """
        try:
            # Set timeout
            socket.setdefaulttimeout(self.timeout)

            # Perform reverse DNS lookup
            hostname, _, _ = socket.gethostbyaddr(ip_address)

            logger.debug(f"DNS lookup: {ip_address} -> {hostname}")
            return hostname

        except UnicodeError as e:
            # IDNA codec error - hostname or IP too long/malformed
            logger.debug(f"DNS lookup failed for {ip_address}: IDNA codec error ({str(e)[:50]})")
            logger.debug(f"  Likely cause: IP address or hostname too long (DNS label limit: 63 chars)")
            return None
        except socket.herror as e:
            # Host not found (non-existent domain)
            error_msg = str(e).lower()
            if 'host not found' in error_msg or 'no such host' in error_msg:
                logger.debug(f"DNS lookup: {ip_address} -> Non-existent domain")
                self._nonexistent_ips.add(ip_address)
                return "NXDOMAIN"
            logger.debug(f"DNS lookup failed for {ip_address}: {e}")
            return None
        except socket.gaierror as e:
            # Address-related error (often means NXDOMAIN)
            error_msg = str(e).lower()
            if 'name or service not known' in error_msg or 'nodename nor servname provided' in error_msg:
                logger.debug(f"DNS lookup: {ip_address} -> Non-existent domain")
                self._nonexistent_ips.add(ip_address)
                return "NXDOMAIN"
            logger.debug(f"DNS lookup failed for {ip_address}: {e}")
            return None
        except socket.timeout as e:
            logger.debug(f"DNS lookup timeout for {ip_address}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error in DNS lookup for {ip_address}: {e}")
            return None

    def _forward_dns_lookup(self, hostname: str) -> Optional[str]:
        """
        Perform forward DNS lookup (hostname → IP)

        Args:
            hostname: Hostname to lookup

        Returns:
            IP address or None if lookup fails
        """
        # Check forward cache first
        if hostname in self._forward_cache:
            return self._forward_cache[hostname]

        try:
            # Set timeout
            socket.setdefaulttimeout(self.timeout)

            # Perform forward DNS lookup
            ip_address = socket.gethostbyname(hostname)

            # Cache the result
            self._forward_cache[hostname] = ip_address

            logger.debug(f"Forward DNS lookup: {hostname} -> {ip_address}")
            return ip_address

        except socket.gaierror as e:
            logger.debug(f"Forward DNS lookup failed for {hostname}: {e}")
            return None
        except socket.timeout as e:
            logger.debug(f"Forward DNS lookup timeout for {hostname}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error in forward DNS lookup for {hostname}: {e}")
            return None

    def validate_bidirectional_dns(self, ip_address: str, hostname: str = None) -> Dict[str, any]:
        """
        Validate that forward and reverse DNS match (bidirectional validation)

        This detects:
        - DNS mismatches (forward ≠ reverse)
        - Multiple IPs for same hostname (VM + ESXi host)
        - NXDOMAIN / DNS failures

        Args:
            ip_address: IP address to validate
            hostname: Optional hostname (if not provided, will do reverse lookup)

        Returns:
            Dictionary with validation results:
            {
                'valid': bool,              # True if forward and reverse match
                'ip': str,                  # Original IP address
                'reverse_hostname': str,    # Hostname from reverse lookup
                'forward_ip': str,          # IP from forward lookup of reverse_hostname
                'forward_ips': List[str],   # All IPs for this hostname (if multiple)
                'mismatch': str,            # Description of mismatch (if any)
                'status': str,              # 'valid', 'mismatch', 'nxdomain', 'error'
                'timestamp': float          # Validation timestamp
            }
        """
        import time
        result = {
            'valid': False,
            'ip': ip_address,
            'reverse_hostname': None,
            'forward_ip': None,
            'forward_ips': [],
            'mismatch': None,
            'status': 'error',
            'timestamp': time.time()
        }

        # Skip validation if not enabled
        if not self.enable_bidirectional_validation:
            result['status'] = 'validation_disabled'
            result['valid'] = True
            return result

        # Step 1: Reverse DNS lookup (IP → hostname)
        if hostname is None:
            hostname = self._reverse_dns_lookup(ip_address)
            if hostname == "NXDOMAIN":
                result['status'] = 'nxdomain'
                result['mismatch'] = 'Reverse DNS lookup returned NXDOMAIN'
                return result
            elif not hostname:
                result['status'] = 'reverse_lookup_failed'
                result['mismatch'] = 'Reverse DNS lookup failed'
                return result

        result['reverse_hostname'] = hostname

        # Step 2: Forward DNS lookup (hostname → IP)
        if self.enable_forward_dns:
            forward_ip = self._forward_dns_lookup(hostname)
            result['forward_ip'] = forward_ip

            if not forward_ip:
                result['status'] = 'forward_lookup_failed'
                result['mismatch'] = f'Forward DNS lookup failed for {hostname}'
                return result

            # Step 3: Check for multiple IPs (VM + ESXi scenario)
            # Try to get all IPs for this hostname
            try:
                socket.setdefaulttimeout(self.timeout)
                _, _, ip_list = socket.gethostbyname_ex(hostname)
                result['forward_ips'] = ip_list

                # Track multiple IPs for this hostname
                if len(ip_list) > 1:
                    self._multiple_ips[hostname] = ip_list
                    logger.debug(f"Multiple IPs found for {hostname}: {ip_list}")

            except Exception as e:
                logger.debug(f"Could not get multiple IPs for {hostname}: {e}")
                result['forward_ips'] = [forward_ip] if forward_ip else []

            # Step 4: Validate match
            if forward_ip == ip_address:
                # Perfect match
                result['valid'] = True
                result['status'] = 'valid'
            elif ip_address in result['forward_ips']:
                # IP is one of multiple IPs for this hostname (VM + ESXi scenario)
                result['valid'] = True
                result['status'] = 'valid_multiple_ips'
                logger.info(f"Bidirectional DNS valid (multiple IPs): {ip_address} ↔ {hostname} ({len(result['forward_ips'])} IPs)")
            else:
                # Mismatch
                result['valid'] = False
                result['status'] = 'mismatch'
                result['mismatch'] = f"Forward DNS ({forward_ip}) ≠ Original IP ({ip_address})"
                logger.warning(f"DNS mismatch: {ip_address} → {hostname} → {forward_ip}")

        # Cache validation result
        self._validation_metadata[ip_address] = result

        return result

    def _query_domain_controller(self, ip_address: str) -> Optional[str]:
        """
        Query Domain Controller for hostname

        This would use LDAP or Windows API to query AD for the computer name
        associated with an IP address.

        Args:
            ip_address: IP address to lookup

        Returns:
            Hostname from DC or None
        """
        # TODO: Implement actual DC query using:
        # - ldap3 library for LDAP queries
        # - pywin32 for Windows API calls
        # - PowerShell remoting

        # Example structure (not implemented):
        # try:
        #     import ldap3
        #     server = ldap3.Server(self.dc_server)
        #     conn = ldap3.Connection(server, auto_bind=True)
        #
        #     # Search for computer with this IP
        #     search_filter = f'(&(objectClass=computer)(ipAddress={ip_address}))'
        #     conn.search('DC=company,DC=local', search_filter, attributes=['cn'])
        #
        #     if conn.entries:
        #         return conn.entries[0].cn.value
        # except Exception as e:
        #     logger.warning(f"DC query failed: {e}")

        logger.debug(f"DC query not yet implemented for {ip_address}")
        return None

    def _generate_synthetic_hostname(self, ip_address: str, zone: Optional[str] = None) -> str:
        """
        Generate a synthetic hostname for demo purposes

        Creates realistic-looking hostnames based on IP patterns and zones.

        Args:
            ip_address: IP address
            zone: Security zone (e.g., "WEB_TIER", "DATA_TIER")

        Returns:
            Synthetic hostname
        """
        try:
            ip_obj = ip_address(ip_address)

            # Determine IP type and extract octets/segments
            if isinstance(ip_obj, IPv4Address):
                octets = ip_address.split('.')
                last_octet = octets[-1]
                third_octet = octets[-2]
            else:
                # IPv6 - use last segment
                segments = ip_address.split(':')
                last_octet = segments[-1][-2:] if segments[-1] else "00"
                third_octet = segments[-2][-2:] if len(segments) > 1 and segments[-2] else "00"

        except Exception:
            # If IP parsing fails, use hash
            last_octet = str(hash(ip_address) % 256)
            third_octet = str(hash(ip_address) % 100)

        # Generate simple hostname patterns based on IP subnet
        # No redundant prefixes - legend already explains node types
        if ip_address.startswith('10.100.160.'):
            # Management subnet
            hostname = f"mgmt-{last_octet}"
        elif ip_address.startswith('10.100.246.'):
            # Application subnet
            hostname = f"app-{last_octet}"
        elif ip_address.startswith('10.164.105.'):
            # Web tier subnet
            hostname = f"web-{last_octet}"
        elif ip_address.startswith('10.164.116.'):
            # Database subnet
            hostname = f"db-{last_octet}"
        elif ip_address.startswith('10.164.144.'):
            # Cache/Redis subnet
            hostname = f"cache-{last_octet}"
        elif ip_address.startswith('10.164.145.'):
            # Message queue subnet
            hostname = f"mq-{last_octet}"
        elif ip_address.startswith('10.165.116.'):
            # API subnet
            hostname = f"api-{last_octet}"
        elif ip_address.startswith('2001:db8:'):
            # IPv6 - use simple pattern
            hostname = f"ipv6-{last_octet}"
        else:
            # Generic pattern - just use server-### format
            hostname = f"server-{last_octet}"

        # Add domain suffix if configured
        if self.dc_domain:
            hostname = f"{hostname}.{self.dc_domain}"
        elif not self.demo_mode:
            # Production default
            hostname = f"{hostname}.local"

        return hostname

    def _get_zone_prefix(self, zone: Optional[str]) -> str:
        """
        Get hostname prefix based on security zone

        Args:
            zone: Security zone name

        Returns:
            Short prefix for hostname
        """
        if not zone:
            return "srv"

        zone_prefixes = {
            'WEB_TIER': 'web',
            'APP_TIER': 'app',
            'DATA_TIER': 'db',
            'CACHE_TIER': 'cache',
            'MESSAGING_TIER': 'mq',
            'MANAGEMENT_TIER': 'mgmt',
            'INFRASTRUCTURE_TIER': 'infra',
        }

        return zone_prefixes.get(zone, 'srv')

    def is_nonexistent(self, ip_address: str) -> bool:
        """
        Check if an IP address was marked as non-existent (NXDOMAIN)

        Args:
            ip_address: IP address to check

        Returns:
            True if IP is marked as non-existent
        """
        return ip_address in self._nonexistent_ips

    def should_filter_flow(self, src_ip: str, dst_ip: str) -> bool:
        """
        Check if a flow should be filtered based on non-existent domains

        A flow is filtered if BOTH source and destination are non-existent domains.

        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address

        Returns:
            True if flow should be filtered (both IPs are non-existent)
        """
        if not self.filter_nonexistent:
            return False

        # Filter only if BOTH source AND destination are non-existent
        src_nonexistent = self.is_nonexistent(src_ip)
        dst_nonexistent = self.is_nonexistent(dst_ip)

        if src_nonexistent and dst_nonexistent:
            logger.debug(f"Filtering flow: {src_ip} -> {dst_ip} (both non-existent)")
            return True

        return False

    def get_nonexistent_count(self) -> int:
        """
        Get count of non-existent IP addresses

        Returns:
            Number of IPs marked as non-existent
        """
        return len(self._nonexistent_ips)

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get hostname resolution cache statistics

        Returns:
            Dictionary with cache stats
        """
        return {
            'cached_hostnames': len(self._cache),
            'provided_hostnames': len(self._provided_hostnames),
            'cache_size': len(self._cache),
            'nonexistent_ips': len(self._nonexistent_ips)
        }

    def clear_cache(self):
        """Clear the hostname resolution cache"""
        self._cache.clear()
        self._nonexistent_ips.clear()
        self._forward_cache.clear()
        self._validation_metadata.clear()
        logger.info("Hostname resolution cache cleared")

    def get_multiple_ips(self, hostname: str) -> List[str]:
        """
        Get all IP addresses associated with a hostname

        Args:
            hostname: Hostname to lookup

        Returns:
            List of IP addresses (empty if none found)
        """
        return self._multiple_ips.get(hostname, [])

    def has_multiple_ips(self, hostname: str) -> bool:
        """
        Check if a hostname has multiple IP addresses

        Args:
            hostname: Hostname to check

        Returns:
            True if hostname has multiple IPs
        """
        return hostname in self._multiple_ips and len(self._multiple_ips[hostname]) > 1

    def format_multiple_ips_display(self, hostname: str, ip_address: str) -> str:
        """
        Format display name for multiple IPs (VM + ESXi scenario)

        Returns format: "ESXi:IP1 - Hostname - VM:IP2"

        Args:
            hostname: Hostname with multiple IPs
            ip_address: Primary IP address

        Returns:
            Formatted display string
        """
        if not self.has_multiple_ips(hostname):
            return f"{hostname} ({ip_address})"

        ips = self._multiple_ips[hostname]

        # Sort IPs to ensure consistent ordering
        ips_sorted = sorted(ips)

        # Identify which is VM and which is ESXi based on common patterns
        # ESXi hosts often end in .1 or are earlier in subnet
        # This is heuristic - adjust based on your environment
        if len(ips_sorted) == 2:
            # Assume first IP (lower) is ESXi host, second is VM
            esxi_ip = ips_sorted[0]
            vm_ip = ips_sorted[1]

            # If current IP is the ESXi host
            if ip_address == esxi_ip:
                return f"ESXi:{esxi_ip} - {hostname} - VM:{vm_ip}"
            else:
                return f"ESXi:{esxi_ip} - {hostname} - VM:{vm_ip}"
        else:
            # More than 2 IPs - just show all
            ip_list_str = ", ".join(ips_sorted)
            return f"{hostname} (Multiple IPs: {ip_list_str})"

    def get_validation_metadata(self, ip_address: str) -> Optional[Dict]:
        """
        Get validation metadata for an IP address

        Args:
            ip_address: IP address to lookup

        Returns:
            Validation metadata dictionary or None
        """
        return self._validation_metadata.get(ip_address)

    def get_validation_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of DNS validation results

        Returns:
            Dictionary with validation statistics:
            {
                'total_validated': int,
                'valid': int,
                'valid_multiple_ips': int,
                'mismatch': int,
                'nxdomain': int,
                'failed': int
            }
        """
        summary = {
            'total_validated': len(self._validation_metadata),
            'valid': 0,
            'valid_multiple_ips': 0,
            'mismatch': 0,
            'nxdomain': 0,
            'failed': 0,
            'validation_disabled': 0
        }

        for ip, metadata in self._validation_metadata.items():
            status = metadata.get('status', 'error')
            if status == 'valid':
                summary['valid'] += 1
            elif status == 'valid_multiple_ips':
                summary['valid_multiple_ips'] += 1
            elif status == 'mismatch':
                summary['mismatch'] += 1
            elif status == 'nxdomain':
                summary['nxdomain'] += 1
            elif status == 'validation_disabled':
                summary['validation_disabled'] += 1
            else:
                summary['failed'] += 1

        return summary


# Global resolver instance (can be configured by application)
_global_resolver: Optional[HostnameResolver] = None


def get_resolver() -> HostnameResolver:
    """
    Get the global hostname resolver instance

    Returns:
        Global HostnameResolver instance
    """
    global _global_resolver
    if _global_resolver is None:
        # Create default resolver in demo mode
        _global_resolver = HostnameResolver(demo_mode=True)
    return _global_resolver


def configure_resolver(demo_mode: bool = False,
                      enable_dns_lookup: bool = True,
                      enable_forward_dns: bool = True,
                      enable_bidirectional_validation: bool = True,
                      dc_server: Optional[str] = None,
                      dc_domain: Optional[str] = None,
                      filter_nonexistent: bool = True,
                      mark_nonexistent: bool = True) -> HostnameResolver:
    """
    Configure the global hostname resolver

    Args:
        demo_mode: Enable demo mode with synthetic hostnames
        enable_dns_lookup: Enable reverse DNS lookups (IP → hostname)
        enable_forward_dns: Enable forward DNS lookups (hostname → IP)
        enable_bidirectional_validation: Validate forward and reverse DNS match
        dc_server: Domain Controller server
        dc_domain: Domain name
        filter_nonexistent: If True, mark non-existent domains for filtering (default: True)
        mark_nonexistent: If True, show "server-not-found" for failed DNS lookups (default: True)

    Returns:
        Configured HostnameResolver instance
    """
    global _global_resolver
    _global_resolver = HostnameResolver(
        demo_mode=demo_mode,
        enable_dns_lookup=enable_dns_lookup,
        enable_forward_dns=enable_forward_dns,
        enable_bidirectional_validation=enable_bidirectional_validation,
        dc_server=dc_server,
        dc_domain=dc_domain,
        filter_nonexistent=filter_nonexistent,
        mark_nonexistent=mark_nonexistent
    )
    return _global_resolver


def resolve_hostname(ip_address: str, zone: Optional[str] = None) -> str:
    """
    Quick function to resolve hostname using global resolver

    Args:
        ip_address: IP address to resolve
        zone: Optional zone hint

    Returns:
        Resolved hostname
    """
    resolver = get_resolver()
    return resolver.resolve(ip_address, zone)
