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
from typing import Optional, Dict, Tuple
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
                 dc_server: Optional[str] = None,
                 dc_domain: Optional[str] = None,
                 timeout: float = 2.0,
                 filter_nonexistent: bool = True,
                 mark_nonexistent: bool = True):
        """
        Args:
            demo_mode: If True, generate synthetic hostnames instead of DNS lookups
            enable_dns_lookup: Enable reverse DNS lookups
            dc_server: Domain Controller server address (e.g., "dc1.company.com")
            dc_domain: Domain name (e.g., "company.local")
            timeout: DNS lookup timeout in seconds
            filter_nonexistent: If True, mark non-existent domains for filtering (default: True)
            mark_nonexistent: If True, show "server-not-found" for failed DNS lookups (default: True)
        """
        self.demo_mode = demo_mode
        self.enable_dns_lookup = enable_dns_lookup
        self.dc_server = dc_server
        self.dc_domain = dc_domain
        self.timeout = timeout
        self.filter_nonexistent = filter_nonexistent
        self.mark_nonexistent = mark_nonexistent

        # Cache for resolved hostnames
        self._cache: Dict[str, str] = {}

        # Provided hostnames (from CSV or other sources)
        self._provided_hostnames: Dict[str, str] = {}

        # Track non-existent domains
        self._nonexistent_ips: set = set()

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
            ip_address: IP address to resolve
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
        """
        hostname = self.resolve(ip_address, zone)

        if hostname and hostname != ip_address:
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

        # Determine hostname prefix based on zone
        prefix = self._get_zone_prefix(zone)

        # Generate hostname patterns based on IP subnet
        if ip_address.startswith('10.100.160.'):
            # Management subnet
            hostname = f"mgmt-{prefix}-{last_octet}"
        elif ip_address.startswith('10.100.246.'):
            # Application subnet
            hostname = f"app-{prefix}-{last_octet}"
        elif ip_address.startswith('10.164.105.'):
            # Web tier subnet
            hostname = f"web-{prefix}-{last_octet}"
        elif ip_address.startswith('10.164.116.'):
            # Database subnet
            hostname = f"db-{prefix}-{last_octet}"
        elif ip_address.startswith('10.164.144.'):
            # Cache/Redis subnet
            hostname = f"cache-{prefix}-{last_octet}"
        elif ip_address.startswith('10.164.145.'):
            # Message queue subnet
            hostname = f"mq-{prefix}-{last_octet}"
        elif ip_address.startswith('10.165.116.'):
            # API subnet
            hostname = f"api-{prefix}-{last_octet}"
        elif ip_address.startswith('2001:db8:'):
            # IPv6 - use different pattern
            hostname = f"ipv6-{prefix}-{last_octet}"
        else:
            # Generic pattern
            hostname = f"{prefix}-server-{last_octet}"

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
        logger.info("Hostname resolution cache cleared")


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
                      dc_server: Optional[str] = None,
                      dc_domain: Optional[str] = None,
                      filter_nonexistent: bool = True,
                      mark_nonexistent: bool = True) -> HostnameResolver:
    """
    Configure the global hostname resolver

    Args:
        demo_mode: Enable demo mode with synthetic hostnames
        enable_dns_lookup: Enable reverse DNS lookups
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
