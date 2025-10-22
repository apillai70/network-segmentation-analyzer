#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Analysis Demo - Shortest Path & Gap Analysis
===================================================
Demonstrates in-memory graph analysis WITHOUT Graph DB

Requirements:
    pip install networkx

Usage:
    python run_graph_analysis.py

Author: Network Security Team
"""

import sys
import codecs
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.parser import parse_network_logs
from src.graph_analyzer import GraphAnalyzer
from src.path_visualizer import PathVisualizer

def main():
    print("="*70)
    print("NETWORK GRAPH ANALYSIS - In-Memory (No Graph DB Required)")
    print("="*70)
    print()

    # Step 1: Parse network flows
    print("[1/5] Parsing network flows from CSV files...")
    parser = parse_network_logs('data/input')
    print(f"  ✓ Loaded {len(parser.records)} flow records")
    print()

    # Step 2: Build in-memory graph
    print("[2/5] Building in-memory network graph...")
    analyzer = GraphAnalyzer(parser.records)
    print(f"  ✓ Graph built: {analyzer.graph.number_of_nodes()} nodes, "
          f"{analyzer.graph.number_of_edges()} edges")
    print()

    # Step 3: Calculate network metrics
    print("[3/5] Calculating centrality metrics...")
    metrics = analyzer.calculate_centrality_metrics()

    # Find top 5 most critical nodes
    top_critical = sorted(
        metrics.items(),
        key=lambda x: x[1]['betweenness_centrality'],
        reverse=True
    )[:5]

    print("  Top 5 Critical Nodes (highest betweenness centrality):")
    for ip, m in top_critical:
        hostname = m['hostname'] or 'Unknown'
        print(f"    • {ip:15s} ({hostname:30s}) - "
              f"Betweenness: {m['betweenness_centrality']:.4f}")
    print()

    # Step 4: Shortest Path Analysis
    print("[4/5] Finding shortest paths...")

    # Example 1: Find path between first and last flow
    if len(parser.records) > 0:
        source = parser.records[0].src_ip
        target = parser.records[-1].dst_ip

        print(f"  Example: {source} → {target}")

        path_result = analyzer.find_shortest_path(source, target)

        if path_result:
            print(f"    ✓ Path found: {path_result['path_length']} hops")
            print(f"      Path: {' → '.join(path_result['path'][:5])}", end='')
            if len(path_result['path']) > 5:
                print(f" ... ({len(path_result['path'])} total nodes)")
            else:
                print()

            # Generate visualization
            visualizer = PathVisualizer(analyzer)
            html_path = visualizer.visualize_shortest_path(source, target)
            print(f"      📊 Visualization: {html_path}")

            # Find all paths
            all_paths = analyzer.find_all_paths(source, target, max_depth=5)
            if len(all_paths) > 1:
                print(f"      ℹ️  Found {len(all_paths)} total paths")
                multi_path_html = visualizer.visualize_all_paths(source, target)
                print(f"      📊 All paths: {multi_path_html}")
        else:
            print(f"    ✗ No path exists between these nodes")

    print()

    # Step 5: Gap Analysis
    print("[5/5] Performing gap analysis...")

    # Define expected topology (customize for your network)
    expected_topology = {}

    # Example: All WEB tier should connect to APP tier
    web_nodes = [ip for ip, meta in analyzer.node_metadata.items()
                 if ip.startswith('10.164.105.')]
    app_nodes = [ip for ip, meta in analyzer.node_metadata.items()
                 if ip.startswith('10.100.246.') or ip.startswith('10.165.116.')]

    if web_nodes and app_nodes:
        # Take first 3 of each for demo
        expected_topology['WEB_to_APP'] = [
            (web, app) for web in web_nodes[:3] for app in app_nodes[:3]
        ]

    if expected_topology:
        gaps = analyzer.analyze_gaps(expected_topology)

        if gaps:
            print(f"  ⚠️  Found {len(gaps)} topology gaps:")
            for gap in gaps[:5]:  # Show first 5
                print(f"    • {gap['gap_type']}: {gap['source_ip']} → {gap['destination_ip']} "
                      f"[{gap['severity']}]")

            if len(gaps) > 5:
                print(f"    ... and {len(gaps)-5} more gaps")

            # Generate gap visualization
            visualizer = PathVisualizer(analyzer)
            gap_html = visualizer.visualize_gaps(gaps)
            print(f"    📊 Gap report: {gap_html}")
        else:
            print("  ✓ No topology gaps found!")
    else:
        print("  ℹ️  No expected topology defined (customize in script)")

    print()

    # Step 6: Policy Violations (Example)
    print("[BONUS] Checking security policies...")

    # Example policy: WEB tier should NOT connect directly to DATABASE tier
    policies = [
        {
            'name': 'No direct WEB to DATABASE access',
            'source_tier': 'WEB',
            'destination_tier': 'DATABASE',
            'action': 'DENY'
        }
    ]

    violations = analyzer.detect_policy_violations(policies)

    if violations:
        print(f"  ⚠️  Found {len(violations)} policy violations:")
        for violation in violations[:3]:
            print(f"    • {violation['policy_name']}")
            print(f"      {violation['source_ip']} → {violation['destination_ip']}")
            print(f"      Protocols: {', '.join(violation['protocols'])}")
    else:
        print("  ✓ No policy violations detected!")

    print()
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print()
    print("📁 Output Files:")
    print("  • outputs/graph_analysis/network_graph.json")
    print("  • outputs/visualizations/shortest_path.html")
    print("  • outputs/visualizations/all_paths.html")
    print("  • outputs/visualizations/gap_analysis.html")
    print()
    print("💡 Open the HTML files in your browser for interactive visualization!")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
