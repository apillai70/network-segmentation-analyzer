#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threat Surface Analysis Demo
=============================
Demonstrates attack path discovery and threat surface analysis

Requirements:
    pip install networkx

Usage:
    python run_threat_analysis.py

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
from src.threat_surface_analyzer import ThreatSurfaceAnalyzer


def main():
    print("="*70)
    print("THREAT SURFACE ANALYSIS - Attack Path Discovery")
    print("="*70)
    print()

    # Step 1: Parse network flows
    print("[1/4] Parsing network flows from CSV files...")
    parser = parse_network_logs('data/input')
    print(f"   Loaded {len(parser.records)} flow records")
    print()

    # Step 2: Build in-memory graph
    print("[2/4] Building network graph...")
    graph_analyzer = GraphAnalyzer(parser.records)
    print(f"   Graph built: {graph_analyzer.graph.number_of_nodes()} nodes, "
          f"{graph_analyzer.graph.number_of_edges()} edges")
    print()

    # Step 3: Perform threat surface analysis
    print("[3/4] Analyzing threat surface...")
    print("  This may take 30-60 seconds for large networks...")

    threat_analyzer = ThreatSurfaceAnalyzer(graph_analyzer)
    results = threat_analyzer.analyze_attack_surface()

    print(f"   Analysis complete!")
    print()

    # Step 4: Display results
    print("[4/4] Threat Surface Analysis Results")
    print("="*70)
    print()

    # Summary
    summary = results['summary']
    print("SUMMARY:")
    print(f"  • Total Attack Paths Found: {summary['total_attack_paths']}")
    print(f"  • High-Exposure Nodes: {summary['exposed_nodes']}")
    print(f"  • Critical Assets at Risk: {summary['critical_assets_at_risk']}")
    print(f"  • Average Attack Distance: {summary['avg_attack_distance']:.1f} hops")
    print(f"  • High-Threat Nodes: {summary['high_threat_nodes']}")
    print()

    # Top 5 Most Critical Attack Paths
    if results['attack_paths']:
        print("TOP 5 MOST CRITICAL ATTACK PATHS:")
        print("-"*70)
        for i, path in enumerate(results['attack_paths'][:5], 1):
            print(f"\n  {i}. {path['source_tier']} -> {path['target_tier']} "
                  f"[{path['risk_level']}]")
            print(f"     Source: {path['source']}")
            print(f"     Target: {path['target']}")
            print(f"     Path Length: {path['path_length']} hops")
            print(f"     Attack Vector: {path['attack_vector']}")

            # Show path (limit to first 4 nodes if long)
            path_display = ' -> '.join(path['path'][:4])
            if len(path['path']) > 4:
                path_display += f' ... -> {path["path"][-1]}'
            print(f"     Route: {path_display}")
        print()

    # High Exposure Nodes
    high_exposure = [
        (ip, data) for ip, data in results['exposure_analysis'].items()
        if data['exposure_level'] in ['CRITICAL', 'HIGH']
    ]

    if high_exposure:
        print(f"HIGH EXPOSURE NODES ({len(high_exposure)} total):")
        print("-"*70)

        # Sort by exposure score
        high_exposure.sort(key=lambda x: x[1]['exposure_score'], reverse=True)

        for i, (ip, data) in enumerate(high_exposure[:10], 1):
            hostname = graph_analyzer.node_metadata.get(ip, {}).get('hostname', 'Unknown')
            print(f"\n  {i}. {ip} ({hostname})")
            print(f"     Tier: {data['tier']}")
            print(f"     Exposure Level: {data['exposure_level']}")
            print(f"     Exposure Score: {data['exposure_score']:.1f}/10")
            print(f"     Is Internal: {data['is_internal']}")
            print(f"     External Access: {data['has_external_access']}")
            print(f"     Connections: {data['in_degree']} in, {data['out_degree']} out")

        if len(high_exposure) > 10:
            print(f"\n  ... and {len(high_exposure)-10} more high-exposure nodes")
        print()

    # Critical Chokepoints
    if results['critical_chokepoints']:
        print(f"CRITICAL CHOKEPOINTS ({len(results['critical_chokepoints'])} total):")
        print("-"*70)
        print("  Nodes whose removal would block significant attack paths:")
        print()

        for i, choke in enumerate(results['critical_chokepoints'][:5], 1):
            hostname = choke['hostname'] or 'Unknown'
            print(f"  {i}. {choke['ip']} ({hostname})")
            print(f"     Tier: {choke['tier']}")
            print(f"     Betweenness Centrality: {choke['betweenness']}")
            print(f"     Paths Blocked if Removed: {choke['paths_blocked']}")
            print(f"     Attack Surface Reduction: {choke['reduction_percentage']:.1f}%")
            print(f"     Mitigation Priority: {choke['mitigation_priority']}")
            print()

    # Mitigation Recommendations
    if results['mitigation_recommendations']:
        print("MITIGATION RECOMMENDATIONS:")
        print("="*70)

        for i, mitigation in enumerate(results['mitigation_recommendations'], 1):
            print(f"\n{i}. [{mitigation['priority']}] {mitigation['title']}")
            print(f"   Category: {mitigation['category']}")
            print(f"   Description: {mitigation['description']}")
            print(f"   Implementation: {mitigation['implementation']}")
            print(f"   Impact: {mitigation['impact']}")

            if mitigation.get('affected_nodes'):
                affected_count = len(mitigation['affected_nodes'])
                print(f"   Affected Nodes: {affected_count}")

                # Show first 3 affected nodes
                for node_ip in mitigation['affected_nodes'][:3]:
                    hostname = graph_analyzer.node_metadata.get(node_ip, {}).get('hostname', 'Unknown')
                    print(f"     • {node_ip} ({hostname})")

                if affected_count > 3:
                    print(f"     ... and {affected_count-3} more nodes")
        print()

    # Export results
    print("="*70)
    print("EXPORTING RESULTS...")
    print("="*70)

    output_dir = Path('outputs/threat_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    threat_analyzer.export_analysis(str(output_dir / 'threat_surface_analysis.json'))

    print()
    print('Output Files:')
    print(f"  * {output_dir / 'threat_surface_analysis.json'}")
    print()

    # Risk Score Distribution
    print("THREAT SCORE DISTRIBUTION:")
    print("-"*70)

    threat_scores = results['threat_scores']

    critical_nodes = sum(1 for s in threat_scores.values() if s >= 8.0)
    high_nodes = sum(1 for s in threat_scores.values() if 6.0 <= s < 8.0)
    medium_nodes = sum(1 for s in threat_scores.values() if 4.0 <= s < 6.0)
    low_nodes = sum(1 for s in threat_scores.values() if s < 4.0)

    total_nodes = len(threat_scores)

    print(f"  Critical (8.0-10.0): {critical_nodes:4d} nodes ({critical_nodes/total_nodes*100:5.1f}%)")
    print(f"  High     (6.0-7.9):  {high_nodes:4d} nodes ({high_nodes/total_nodes*100:5.1f}%)")
    print(f"  Medium   (4.0-5.9):  {medium_nodes:4d} nodes ({medium_nodes/total_nodes*100:5.1f}%)")
    print(f"  Low      (0.0-3.9):  {low_nodes:4d} nodes ({low_nodes/total_nodes*100:5.1f}%)")
    print()

    # Top 10 Highest Threat Scores
    print("TOP 10 HIGHEST THREAT SCORES:")
    print("-"*70)

    top_threats = sorted(threat_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    for i, (ip, score) in enumerate(top_threats, 1):
        hostname = graph_analyzer.node_metadata.get(ip, {}).get('hostname', 'Unknown')
        tier = graph_analyzer._classify_node_tier(ip)
        exposure = results['exposure_analysis'].get(ip, {})

        print(f"  {i:2d}. {ip:15s} ({hostname:30s})")
        print(f"      Threat Score: {score:.2f}/10.0")
        print(f"      Tier: {tier}")
        print(f"      Exposure Level: {exposure.get('exposure_level', 'UNKNOWN')}")
        print()

    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print()
    print("=� Next Steps:")
    print("  1. Review mitigation recommendations (prioritize CRITICAL and HIGH)")
    print("  2. Investigate high-exposure nodes for unnecessary external access")
    print("  3. Harden critical chokepoints (enable MFA, IDS/IPS)")
    print("  4. Block direct external � critical asset paths")
    print("  5. Implement network segmentation to reduce attack surface")
    print()
    print("=� For interactive visualization, run:")
    print("     python run_graph_analysis.py")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nL Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
