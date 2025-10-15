#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow Filtering Utility
======================
Filter network flows based on DNS resolution status.

Filters out flows where BOTH source AND destination have non-existent DNS entries (NXDOMAIN).
This helps clean up reports and visualizations by removing stale/invalid traffic.

Author: Enterprise Security Team
Version: 1.0
"""

import logging
from typing import List, Tuple, Dict
from collections import Counter

logger = logging.getLogger(__name__)


def filter_flows_by_dns_status(
    flow_records: List,
    hostname_resolver,
    filter_nonexistent: bool = True
) -> Tuple[List, Dict]:
    """
    Filter network flows based on DNS resolution status

    Removes flows where BOTH source AND destination are non-existent domains (NXDOMAIN).
    This is conservative - flows with only ONE non-existent endpoint are kept.

    Args:
        flow_records: List of FlowRecord objects
        hostname_resolver: HostnameResolver instance (must have filter_nonexistent enabled)
        filter_nonexistent: If True, filter flows with both IPs non-existent (default: True)

    Returns:
        Tuple of (filtered_flows, statistics_dict)

    Example:
        >>> from src.utils.hostname_resolver import HostnameResolver
        >>> resolver = HostnameResolver(demo_mode=False, filter_nonexistent=True)
        >>> filtered_flows, stats = filter_flows_by_dns_status(all_flows, resolver)
        >>> print(f"Kept {stats['flows_kept']} flows, filtered {stats['flows_filtered']}")
    """

    if not filter_nonexistent:
        # Filtering disabled - return all flows
        return flow_records, {
            'total_flows': len(flow_records),
            'flows_kept': len(flow_records),
            'flows_filtered': 0,
            'filter_percentage': 0.0,
            'filtering_enabled': False
        }

    if not hostname_resolver:
        logger.warning("No hostname resolver provided - returning all flows unfiltered")
        return flow_records, {
            'total_flows': len(flow_records),
            'flows_kept': len(flow_records),
            'flows_filtered': 0,
            'filter_percentage': 0.0,
            'filtering_enabled': False,
            'warning': 'No resolver provided'
        }

    # Step 1: Resolve all hostnames (this marks non-existent IPs internally)
    logger.info(f"Resolving hostnames for {len(flow_records)} flows...")

    for record in flow_records:
        # Resolve source and destination (this populates the non-existent IPs set)
        if hasattr(record, 'src_ip') and record.src_ip:
            hostname_resolver.resolve(record.src_ip)
        if hasattr(record, 'dst_ip') and record.dst_ip:
            hostname_resolver.resolve(record.dst_ip)

    # Step 2: Filter flows
    logger.info(f"Filtering flows where both IPs are non-existent...")

    filtered_flows = []
    filtered_count = 0
    filter_reasons = Counter()

    for record in flow_records:
        src_ip = getattr(record, 'src_ip', None)
        dst_ip = getattr(record, 'dst_ip', None)

        # Skip records with missing IPs
        if not src_ip or not dst_ip:
            filter_reasons['missing_ip'] += 1
            filtered_count += 1
            continue

        # Check if flow should be filtered
        if hostname_resolver.should_filter_flow(src_ip, dst_ip):
            filter_reasons['both_nonexistent'] += 1
            filtered_count += 1
            logger.debug(f"Filtered flow: {src_ip} -> {dst_ip} (both non-existent)")
            continue

        # Keep this flow
        filtered_flows.append(record)

    # Step 3: Calculate statistics
    total_flows = len(flow_records)
    flows_kept = len(filtered_flows)
    filter_percentage = (filtered_count / max(total_flows, 1)) * 100

    stats = {
        'total_flows': total_flows,
        'flows_kept': flows_kept,
        'flows_filtered': filtered_count,
        'filter_percentage': filter_percentage,
        'filtering_enabled': True,
        'filter_reasons': dict(filter_reasons),
        'nonexistent_ips_found': hostname_resolver.get_nonexistent_count()
    }

    # Log summary
    logger.info(f"✓ Flow filtering complete:")
    logger.info(f"  Total flows: {total_flows:,}")
    logger.info(f"  Flows kept: {flows_kept:,}")
    logger.info(f"  Flows filtered: {filtered_count:,} ({filter_percentage:.1f}%)")
    logger.info(f"  Non-existent IPs found: {stats['nonexistent_ips_found']}")

    if filter_reasons:
        logger.info(f"  Filter reasons:")
        for reason, count in filter_reasons.items():
            logger.info(f"    - {reason}: {count}")

    return filtered_flows, stats


def apply_filtering_to_records(
    flow_records: List,
    hostname_resolver,
    filter_enabled: bool = True,
    log_stats: bool = True
) -> List:
    """
    Convenience function to filter flows and return only the filtered records

    This is a simplified version that just returns the filtered flows without statistics.
    Use filter_flows_by_dns_status() if you need detailed statistics.

    Args:
        flow_records: List of FlowRecord objects
        hostname_resolver: HostnameResolver instance
        filter_enabled: If True, apply filtering (default: True)
        log_stats: If True, log statistics (default: True)

    Returns:
        List of filtered FlowRecord objects

    Example:
        >>> from src.utils.hostname_resolver import HostnameResolver
        >>> resolver = HostnameResolver(demo_mode=False, filter_nonexistent=True)
        >>> clean_flows = apply_filtering_to_records(all_flows, resolver)
    """

    filtered_flows, stats = filter_flows_by_dns_status(
        flow_records,
        hostname_resolver,
        filter_nonexistent=filter_enabled
    )

    if log_stats and filter_enabled:
        logger.info(f"Filtered {stats['flows_filtered']} flows ({stats['filter_percentage']:.1f}%)")

    return filtered_flows


def get_filtering_summary(hostname_resolver) -> Dict:
    """
    Get summary of filtering status from hostname resolver

    Args:
        hostname_resolver: HostnameResolver instance

    Returns:
        Dictionary with filtering statistics

    Example:
        >>> summary = get_filtering_summary(resolver)
        >>> print(f"Non-existent IPs: {summary['nonexistent_ips']}")
    """

    if not hostname_resolver:
        return {
            'filtering_enabled': False,
            'error': 'No resolver provided'
        }

    cache_stats = hostname_resolver.get_cache_stats()

    return {
        'filtering_enabled': hostname_resolver.filter_nonexistent,
        'marking_enabled': hostname_resolver.mark_nonexistent,
        'nonexistent_ips': hostname_resolver.get_nonexistent_count(),
        'cached_hostnames': cache_stats.get('cached_hostnames', 0),
        'provided_hostnames': cache_stats.get('provided_hostnames', 0),
    }


# Convenience function for batch processing
def should_enable_filtering(command_line_flag: bool = None, default: bool = True) -> bool:
    """
    Determine if filtering should be enabled based on configuration

    Args:
        command_line_flag: Flag from command line (None if not specified)
        default: Default value if flag not specified (default: True)

    Returns:
        Boolean indicating if filtering should be enabled
    """

    if command_line_flag is not None:
        return command_line_flag

    return default
