#!/usr/bin/env python3
"""Network Segmentation Analyzer - Main entry point."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parsers import ExtrahopParser, DynatraceParser, SplunkParser
from topology import NetworkTopology


def main():
    """Main function to run the network segmentation analyzer."""
    parser = argparse.ArgumentParser(
        description='Network Segmentation Analyzer - Analyze network topology from monitoring logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Extrahop logs
  python analyzer.py extrahop logs/extrahop.log

  # Analyze Dynatrace logs
  python analyzer.py dynatrace logs/dynatrace.log

  # Analyze Splunk logs
  python analyzer.py splunk logs/splunk.log
  
  # Analyze with custom output
  python analyzer.py extrahop logs/extrahop.log -o custom_topology.png
        """
    )
    
    parser.add_argument(
        'source',
        choices=['extrahop', 'dynatrace', 'splunk'],
        help='Monitoring application source'
    )
    
    parser.add_argument(
        'logfile',
        help='Path to the log file'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='network_topology.png',
        help='Output file for topology visualization (default: network_topology.png)'
    )
    
    parser.add_argument(
        '-r', '--report',
        default='network_report.txt',
        help='Output file for text report (default: network_report.txt)'
    )
    
    args = parser.parse_args()
    
    # Check if log file exists
    if not Path(args.logfile).exists():
        print(f"Error: Log file not found: {args.logfile}")
        return 1
    
    # Select appropriate parser
    print(f"Analyzing {args.source} logs from: {args.logfile}")
    print("-" * 60)
    
    if args.source == 'extrahop':
        log_parser = ExtrahopParser(args.logfile)
    elif args.source == 'dynatrace':
        log_parser = DynatraceParser(args.logfile)
    elif args.source == 'splunk':
        log_parser = SplunkParser(args.logfile)
    else:
        print(f"Error: Unknown source: {args.source}")
        return 1
    
    # Parse logs
    connections = log_parser.parse()
    print(f"Parsed {len(connections)} connections")
    
    if not connections:
        print("Warning: No connections found in log file")
        return 0
    
    # Build topology
    topology = NetworkTopology()
    topology.add_connections(connections)
    
    # Generate report
    report = topology.generate_report()
    print(report)
    
    # Save report to file
    with open(args.report, 'w') as f:
        f.write(report)
    print(f"Report saved to: {args.report}")
    
    # Visualize topology
    topology.visualize(args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
