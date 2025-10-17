"""
==============================================================================
SYSTEM VERIFICATION SCRIPT
Save as: verify_system.py
Run: python verify_system.py
==============================================================================
"""
import sys
import importlib

def verify_installation():
    """Verify all components are properly installed"""
    
    print("="*60)
    print("ENTERPRISE NETWORK ANALYSIS - SYSTEM VERIFICATION")
    print("="*60)
    
    required_packages = {
        'pandas': '1.5.0',
        'numpy': '1.23.0',
        'networkx': '2.8.0',
        'sklearn': '1.1.0'
    }
    
    optional_packages = {
        'torch': '2.0.0',
        'matplotlib': '3.5.0'
    }
    
    print("\n[STEP] Checking Required Packages...")
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            if package == 'sklearn':
                module = importlib.import_module('sklearn')
            else:
                module = importlib.import_module(package)
            
            version = getattr(module, '__version__', 'unknown')
            print(f"  [OK] {package}: {version}")
        except ImportError:
            print(f"  [ERROR] {package}: NOT INSTALLED")
            all_ok = False
    
    print("\n[STEP] Checking Optional Packages...")
    for package, min_version in optional_packages.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"  [OK] {package}: {version}")
        except ImportError:
            print(f"  [WARNING] {package}: Not installed (optional)")
    
    if not all_ok:
        print("\n[ERROR] MISSING REQUIRED PACKAGES")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n[SUCCESS] All required packages installed!")
    
    # Test imports from main system
    print("\n[CONFIG] Testing System Components...")
    
    try:
        print("  Testing GNN...")
        from enterprise_network_analyzer import GraphNeuralNetwork
        gnn = GraphNeuralNetwork(input_dim=10, hidden_dim=8, output_dim=4, num_layers=2)
        print("  [OK] GNN initialized")
        
        print("  Testing RL Agent...")
        from enterprise_network_analyzer import SegmentationRLAgent
        agent = SegmentationRLAgent(state_dim=4, action_dim=5)
        print("  [OK] RL Agent initialized")
        
        print("  Testing Time-Series Analyzer...")
        from enterprise_network_analyzer import TimeSeriesAnalyzer
        ts = TimeSeriesAnalyzer()
        print("  [OK] Time-Series Analyzer initialized")
        
        print("  Testing Federated Learning...")
        from enterprise_network_analyzer import FederatedLearningCoordinator
        fl = FederatedLearningCoordinator(num_clients=2)
        print("  [OK] Federated Learning initialized")
        
        print("  Testing AutoML...")
        from enterprise_network_analyzer import AutoMLPipeline
        automl = AutoMLPipeline()
        print("  [OK] AutoML initialized")
        
        print("\n[SUCCESS] All components working!")
        
    except Exception as e:
        print(f"\n[ERROR] Component test failed: {e}")
        return False
    
    # Create sample data and test pipeline
    print("\n🧪 Running End-to-End Test...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample flow data
        sample_data = pd.DataFrame({
            'source_ip': ['10.0.1.' + str(i % 10) for i in range(100)],
            'destination_ip': ['10.0.2.' + str(i % 5) for i in range(100)],
            'source_port': np.random.randint(30000, 60000, 100),
            'destination_port': [[80, 443, 3306, 5432, 9092][i % 5] for i in range(100)],
            'protocol': ['TCP'] * 100
        })
        
        # Save sample file
        sample_data.to_csv('test_flow_data.csv', index=False)
        print("  [OK] Created test data")
        
        # Test loading
        from enterprise_network_analyzer import EnterpriseNetworkAnalyzer
        analyzer = EnterpriseNetworkAnalyzer()
        analyzer.load_data(['test_flow_data.csv'])
        print(f"  [OK] Loaded {len(analyzer.flows_df)} flows")
        
        # Test graph building
        node_features, adj_matrix, node_list = analyzer.prepare_graph_data()
        print(f"  [OK] Built graph with {len(node_list)} nodes")
        
        # Quick GNN test
        gnn = GraphNeuralNetwork(
            input_dim=node_features.shape[1],
            hidden_dim=16,
            output_dim=8,
            num_layers=2
        )
        embeddings = gnn.train(node_features, adj_matrix, labels=None, epochs=5)
        print(f"  [OK] GNN generated embeddings: {embeddings.shape}")
        
        # Clean up
        import os
        os.remove('test_flow_data.csv')
        print("  [OK] Cleaned up test files")
        
        print("\n[SUCCESS] END-TO-END TEST PASSED!")
        
    except Exception as e:
        print(f"\n[ERROR] End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("[SUCCESS] SYSTEM VERIFICATION COMPLETE - ALL TESTS PASSED!")
    print("="*60)
    print("\nYou're ready to analyze your network flows!")
    print("\nNext step:")
    print("  python quick_deploy.py --data-dir ./flow_data --mode fast")
    
    return True

if __name__ == '__main__':
    success = verify_installation()
    sys.exit(0 if success else 1)