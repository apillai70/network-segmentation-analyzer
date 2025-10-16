#!/usr/bin/env python3
"""
Test DNS Validation and Multiple IP Support

This script demonstrates:
1. Forward DNS lookup (hostname → IP)
2. Reverse DNS lookup (IP → hostname)
3. Bidirectional DNS validation (forward + reverse match)
4. Multiple IP detection (VM + ESXi scenarios)
5. Validation metadata tracking
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.hostname_resolver import HostnameResolver, configure_resolver
import logging

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def test_basic_resolution():
    """Test basic hostname resolution"""
    print("\n" + "="*80)
    print("TEST 1: Basic Hostname Resolution (Demo Mode)")
    print("="*80)

    resolver = HostnameResolver(demo_mode=True)

    test_ips = [
        '10.100.160.214',  # Management
        '10.164.105.136',  # Web tier
        '10.164.116.100',  # Database
        '10.164.144.119',  # Cache
    ]

    for ip in test_ips:
        hostname = resolver.resolve(ip)
        print(f"  {ip:20} -> {hostname}")

    print(f"\nCache stats: {resolver.get_cache_stats()}")


def test_dns_validation():
    """Test bidirectional DNS validation"""
    print("\n" + "="*80)
    print("TEST 2: Bidirectional DNS Validation")
    print("="*80)

    # Create resolver with validation enabled
    resolver = HostnameResolver(
        demo_mode=False,
        enable_dns_lookup=True,
        enable_forward_dns=True,
        enable_bidirectional_validation=True
    )

    # Test with common DNS servers (should have valid DNS)
    test_cases = [
        ('8.8.8.8', 'Google DNS'),
        ('1.1.1.1', 'Cloudflare DNS'),
        ('192.168.1.1', 'Typical router IP - may not have DNS'),
    ]

    for ip, description in test_cases:
        print(f"\n{description} ({ip}):")
        validation = resolver.validate_bidirectional_dns(ip)

        print(f"  Status: {validation['status']}")
        print(f"  Valid: {validation['valid']}")

        if validation['reverse_hostname']:
            print(f"  Reverse DNS: {ip} -> {validation['reverse_hostname']}")

        if validation['forward_ip']:
            print(f"  Forward DNS: {validation['reverse_hostname']} -> {validation['forward_ip']}")

        if validation['forward_ips']:
            print(f"  All IPs: {validation['forward_ips']}")

        if validation['mismatch']:
            print(f"  Mismatch: {validation['mismatch']}")

    # Print validation summary
    print("\n" + "-"*80)
    summary = resolver.get_validation_summary()
    print("Validation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


def test_multiple_ips():
    """Test multiple IP detection and formatting"""
    print("\n" + "="*80)
    print("TEST 3: Multiple IP Detection (VM + ESXi)")
    print("="*80)

    resolver = HostnameResolver(
        demo_mode=False,
        enable_dns_lookup=True,
        enable_forward_dns=True,
        enable_bidirectional_validation=True
    )

    # Simulate multiple IPs for same hostname
    # In real scenario, this would be detected via gethostbyname_ex
    test_hostname = "test-server.example.com"
    resolver._multiple_ips[test_hostname] = ['10.0.1.100', '10.0.1.101']

    # Test formatting
    for ip in ['10.0.1.100', '10.0.1.101']:
        display = resolver.format_multiple_ips_display(test_hostname, ip)
        print(f"  {ip} -> {display}")

    # Check if hostname has multiple IPs
    print(f"\n  Has multiple IPs: {resolver.has_multiple_ips(test_hostname)}")
    print(f"  All IPs: {resolver.get_multiple_ips(test_hostname)}")


def test_resolve_with_display():
    """Test resolve_with_display with multiple IP support"""
    print("\n" + "="*80)
    print("TEST 4: Resolve with Display (with Multiple IPs)")
    print("="*80)

    resolver = HostnameResolver(demo_mode=True)

    # Test single IP
    ip1 = '10.164.105.136'
    hostname1, display1 = resolver.resolve_with_display(ip1, format='mermaid')
    print(f"\nSingle IP:")
    print(f"  IP: {ip1}")
    print(f"  Hostname: {hostname1}")
    print(f"  Display: {display1}")

    # Simulate multiple IPs
    test_hostname = "web-136"
    resolver._multiple_ips[test_hostname] = ['10.164.105.136', '10.164.105.137']

    hostname2, display2 = resolver.resolve_with_display('10.164.105.136', format='mermaid')
    print(f"\nMultiple IPs (VM + ESXi):")
    print(f"  IP: 10.164.105.136")
    print(f"  Hostname: {hostname2}")
    print(f"  Display: {display2}")


def test_validation_metadata():
    """Test validation metadata storage and retrieval"""
    print("\n" + "="*80)
    print("TEST 5: Validation Metadata Storage")
    print("="*80)

    resolver = HostnameResolver(
        demo_mode=False,
        enable_dns_lookup=True,
        enable_forward_dns=True,
        enable_bidirectional_validation=True
    )

    # Validate a few IPs
    test_ips = ['8.8.8.8', '1.1.1.1']

    for ip in test_ips:
        resolver.validate_bidirectional_dns(ip)

    # Retrieve metadata
    print("\nStored validation metadata:")
    for ip in test_ips:
        metadata = resolver.get_validation_metadata(ip)
        if metadata:
            print(f"\n  {ip}:")
            print(f"    Status: {metadata['status']}")
            print(f"    Valid: {metadata['valid']}")
            print(f"    Reverse: {metadata['reverse_hostname']}")
            print(f"    Forward IP: {metadata['forward_ip']}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DNS Validation and Multiple IP Support - Test Suite")
    print("="*80)

    try:
        test_basic_resolution()
        test_dns_validation()
        test_multiple_ips()
        test_resolve_with_display()
        test_validation_metadata()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
