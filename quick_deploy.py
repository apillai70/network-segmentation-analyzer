#!/usr/bin/env python3
"""
QUICK DEPLOYMENT SCRIPT
Run this immediately to analyze your network flows

Usage:
    python quick_deploy.py --data-dir ./flow_data --output-dir ./results
"""

import os
import sys
import argparse
import glob
from pathlib import Path

def setup_environment():
    """Install required packages"""
    print("[CONFIG] Setting up environment...")
    
    packages = [
        'pandas',
        'numpy', 
        'networkx',
        'scikit-learn',
        'torch',  # Optional, for PyTorch transformer
    ]
    
    import subprocess
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"  Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
    
    print("[OK] Environment ready")

def validate_csv_files(data_dir):
    """Validate CSV files exist and have required columns"""
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not csv_files:
        print(f"[ERROR] No CSV files found in {data_dir}")
        print("Expected format: app_1_flows.csv, app_2_flows.csv, ...")
        sys.exit(1)
    
    print(f"[OK] Found {len(csv_files)} CSV files")
    
    # Check first file for required columns
    import pandas as pd
    sample = pd.read_csv(csv_files[0], nrows=5)
    required_cols = ['source_ip', 'destination_ip', 'destination_port']
    
    missing = [col for col in required_cols if col not in sample.columns.str.lower()]
    
    if missing:
        print(f"[WARNING] Missing columns: {missing}")
        print(f"Available columns: {list(sample.columns)}")
        print("Will attempt to proceed with available columns...")
    
    return csv_files

def run_fast_analysis(csv_files, output_dir):
    """Run optimized analysis for quick results"""
    print("\n[START] Starting Fast Analysis Mode...")
    print("="*60)
    
    # Import the main analyzer
    from enterprise_network_analyzer import EnterpriseNetworkAnalyzer
    
    analyzer = EnterpriseNetworkAnalyzer()
    
    # Load data (limit to first 50 apps for speed)
    print(f"\n[FOLDER] Loading up to 50 applications for quick analysis...")
    analyzer.load_data(csv_files[:50])

    # Run analysis with reduced iterations for speed
    print("\n[START] Running optimized analysis pipeline...")
    
    # GNN with fewer epochs
    print("  1/5 Training GNN (20 epochs)...")
    node_features, adj_matrix, node_list = analyzer.prepare_graph_data()
    
    from enterprise_network_analyzer import GraphNeuralNetwork
    analyzer.gnn = GraphNeuralNetwork(
        input_dim=64,
        hidden_dim=64,  # Reduced
        output_dim=16,  # Reduced
        num_layers=2   # Reduced
    )
    embeddings = analyzer.gnn.train(node_features, adj_matrix, labels=None, epochs=20)
    
    # RL with fewer episodes
    print("  2/5 Training RL Agent (30 episodes)...")
    for i, node_id in enumerate(node_list):
        analyzer.nodes[node_id]['features'] = embeddings[i]
    
    from enterprise_network_analyzer import SegmentationRLAgent
    analyzer.rl_agent = SegmentationRLAgent(state_dim=16, action_dim=7)
    rewards = analyzer.rl_agent.train(analyzer.nodes, analyzer.graph, episodes=30)
    
    # Time-series analysis
    print("  3/5 Analyzing time-series patterns...")
    flows_with_time = analyzer.timeseries.extract_temporal_features(analyzer.flows_df)
    anomalies = analyzer.timeseries.detect_anomalies(flows_with_time)
    
    # Federated learning
    print("  4/5 Running federated learning (5 rounds)...")
    import numpy as np
    data_splits = np.array_split(analyzer.flows_df, 3)
    
    from enterprise_network_analyzer import FederatedLearningCoordinator
    analyzer.federated = FederatedLearningCoordinator(num_clients=3)
    analyzer.federated.initialize_clients(data_splits)
    global_model = analyzer.federated.train_federated(rounds=5)
    
    # AutoML
    print("  5/5 Running AutoML pipeline...")
    X = flows_with_time.select_dtypes(include=[np.number]).fillna(0)
    y = np.random.randint(0, 5, size=len(X))
    automl_results = analyzer.automl.run_auto_pipeline(X, y, task='clustering')
    
    # Generate report
    print("\n[DATA] Generating reports...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    import json
    from datetime import datetime
    
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'apps_analyzed': len(csv_files[:50]),
            'total_flows': len(analyzer.flows_df),
            'analysis_mode': 'FAST'
        },
        'gnn': {
            'nodes': len(node_list),
            'embedding_dim': 16
        },
        'rl': {
            'final_avg_reward': float(np.mean(rewards[-10:])),
            'zones_assigned': len(analyzer.rl_agent.get_optimal_policy(analyzer.nodes))
        },
        'timeseries': {
            'anomalies_detected': len(anomalies)
        },
        'federated': {
            'clients': 3,
            'rounds': 5
        },
        'automl': automl_results
    }
    
    # Save report
    report_path = os.path.join(output_dir, 'quick_analysis_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Save node assignments
    policy = analyzer.rl_agent.get_optimal_policy(analyzer.nodes)
    zone_names = ['WEB_TIER', 'DATA_TIER', 'MESSAGING', 'INFRASTRUCTURE', 
                  'APP_TIER', 'DMZ', 'MANAGEMENT']
    
    assignments = []
    for node_id, zone_idx in policy.items():
        assignments.append({
            'ip': node_id,
            'zone': zone_names[zone_idx],
            'zone_id': int(zone_idx)
        })
    
    import pandas as pd
    assignments_df = pd.DataFrame(assignments)
    assignments_path = os.path.join(output_dir, 'zone_assignments.csv')
    assignments_df.to_csv(assignments_path, index=False)
    
    # Save anomalies
    if anomalies:
        anomalies_df = pd.DataFrame(anomalies)
        anomalies_path = os.path.join(output_dir, 'temporal_anomalies.csv')
        anomalies_df.to_csv(anomalies_path, index=False)
    
    print("\n[SUCCESS] ANALYSIS COMPLETE!")
    print("="*60)
    print(f"[FOLDER] Results saved to: {output_dir}/")
    print(f"  - quick_analysis_report.json")
    print(f"  - zone_assignments.csv")
    print(f"  - temporal_anomalies.csv")
    print(f"\n[DATA] Summary:")
    print(f"  Apps Analyzed: {len(csv_files[:50])}")
    print(f"  Network Nodes: {len(node_list)}")
    print(f"  RL Avg Reward: {np.mean(rewards[-10:]):.2f}")
    print(f"  Anomalies: {len(anomalies)}")
    
    return report

def run_full_analysis(csv_files, output_dir):
    """Run complete analysis with all 135 apps"""
    print("\n[START] Starting Full Analysis Mode (ALL 135 apps)...")
    print("[WARNING] This will take 30-60 minutes")
    print("="*60)
    
    from enterprise_network_analyzer import EnterpriseNetworkAnalyzer
    
    analyzer = EnterpriseNetworkAnalyzer()
    analyzer.load_data(csv_files)
    results = analyzer.run_complete_analysis()
    
    print(f"\n[SUCCESS] Full analysis complete!")
    print(f"[FOLDER] Report: enterprise_network_analysis_report.json")
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Quick deployment for enterprise network analysis'
    )
    parser.add_argument(
        '--data-dir',
        default='./flow_data',
        help='Directory containing CSV flow files'
    )
    parser.add_argument(
        '--output-dir',
        default='./results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--mode',
        choices=['fast', 'full'],
        default='fast',
        help='Analysis mode: fast (50 apps, 5 min) or full (135 apps, 60 min)'
    )
    parser.add_argument(
        '--skip-setup',
        action='store_true',
        help='Skip environment setup'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("ENTERPRISE NETWORK ANALYSIS - QUICK DEPLOY")
    print("="*60)
    
    # Setup
    if not args.skip_setup:
        setup_environment()
    
    # Validate data
    csv_files = validate_csv_files(args.data_dir)
    
    # Run analysis
    if args.mode == 'fast':
        report = run_fast_analysis(csv_files, args.output_dir)
    else:
        report = run_full_analysis(csv_files, args.output_dir)
    
    print("\n[SUCCESS] DEPLOYMENT SUCCESSFUL!")
    print(f"Next steps:")
    print(f"  1. Review {args.output_dir}/quick_analysis_report.json")
    print(f"  2. Check {args.output_dir}/zone_assignments.csv for segmentation")
    print(f"  3. Investigate anomalies in {args.output_dir}/temporal_anomalies.csv")

if __name__ == '__main__':
    main()