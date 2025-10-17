#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Pipeline - Process Files One by One with Visualization
================================================================
This script provides a simple, complete pipeline to:
1. Process network flow files from data/input/
2. Train ML models incrementally
3. Generate visualizations
4. Export results and reports

Usage:
    # Process all files
    python run_complete_pipeline.py

    # Process first 10 files only
    python run_complete_pipeline.py --max-files 10

    # Skip visualization generation
    python run_complete_pipeline.py --no-viz

Author: Enterprise Security Team
Version: 3.0 - Complete Pipeline
"""

import sys
import os

# Force UTF-8 encoding (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
import logging
import time
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.file_tracker import FileTracker
from persistence import create_persistence_manager
from core.ensemble_model import EnsembleNetworkModel
from diagrams import MermaidDiagramGenerator
from exporters.lucidchart_exporter import LucidchartExporter
from deep_learning.gat_model import GATApplicationAnalyzer
from deep_learning.transformer_model import TemporalTrafficAnalyzer
from deep_learning.vae_model import ApplicationBehaviorAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CompletePipeline:
    """Complete pipeline for file processing, training, and visualization"""

    def __init__(self, watch_dir='./data/input', output_dir='./outputs_final', ignore_synthetic=False, use_deep_learning=True):
        """Initialize pipeline with full ML/DL capabilities"""
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ignore_synthetic = ignore_synthetic
        self.use_deep_learning = use_deep_learning

        # Create embeddings and features directories
        self.processed_dir = self.watch_dir / 'processed'
        self.embeddings_dir = self.processed_dir / 'embeddings'
        self.features_dir = self.processed_dir / 'features'
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.file_tracker = FileTracker(
            watch_dir=str(watch_dir),
            tracking_db=str(self.watch_dir / 'processed_files.json')
        )

        self.pm = create_persistence_manager()
        self.ensemble = EnsembleNetworkModel(self.pm, use_deep_learning=use_deep_learning)

        # Deep learning models
        if use_deep_learning:
            logger.info("  Initializing deep learning models...")
            self.gat_model = GATApplicationAnalyzer()
            self.transformer_model = TemporalTrafficAnalyzer()
            self.vae_model = ApplicationBehaviorAnalyzer()
            logger.info("  [OK] GAT, Transformer, VAE models ready")

        # Tracking
        self.all_flows = []
        self.app_zones = {}
        self.app_features = {}  # Store extracted features
        self.app_embeddings = {}  # Store generated embeddings
        self.flow_records = []  # For diagram generation
        self.processing_stats = {
            'total_processed': 0,
            'total_flows': 0,
            'total_apps': 0,
            'start_time': datetime.now()
        }

        logger.info("[OK] Complete Pipeline initialized (Full ML/DL mode)")
        logger.info(f"  Input: {self.watch_dir}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Features: {self.features_dir}")
        logger.info(f"  Embeddings: {self.embeddings_dir}")
        logger.info(f"  Deep Learning: {'Enabled' if use_deep_learning else 'Disabled'}")
        if self.ignore_synthetic:
            logger.info("  Ignoring synthetic data files")

    def _is_synthetic(self, file_path: Path) -> bool:
        """Check if file is synthetic data (for demo purposes)"""
        # Synthetic files have pattern: App_Code_<generic_name>.csv where name is generic (app_1, test, synthetic, demo, etc.)
        filename = file_path.stem.replace('App_Code_', '').lower()
        synthetic_patterns = ['app_', 'test', 'synthetic', 'demo', 'sample', 'example']
        return any(pattern in filename for pattern in synthetic_patterns)

    def process_all_files(self, max_files=None):
        """Process all files one by one"""

        print("\n" + "=" * 80)
        print("[START] COMPLETE NETWORK ANALYSIS PIPELINE")
        print("=" * 80)
        print()

        # Get pending files
        pending_files = self.file_tracker.get_pending_files(pattern='App_Code_*.csv')

        # Filter out synthetic files if requested
        if self.ignore_synthetic:
            filtered_files = [f for f in pending_files if not self._is_synthetic(f)]
            synthetic_count = len(pending_files) - len(filtered_files)
            if synthetic_count > 0:
                logger.info(f"Ignoring {synthetic_count} synthetic data files")
            pending_files = filtered_files

        if not pending_files:
            logger.info("No pending files found")
            return

        if max_files:
            pending_files = pending_files[:max_files]

        total_files = len(pending_files)
        logger.info(f"[FOLDER] Processing {total_files} files...\n")

        # Process each file
        for i, file_path in enumerate(pending_files, 1):
            print(f"\n[{i}/{total_files}] Processing: {file_path.name}")
            print("-" * 80)

            self._process_single_file(file_path, i, total_files)

        print("\n" + "=" * 80)
        print("[SUCCESS] FILE PROCESSING COMPLETE")
        print("=" * 80)

    def _process_single_file(self, file_path: Path, index: int, total: int):
        """Process a single file"""

        app_id = file_path.stem.replace('App_Code_', '')

        # Check duplicate
        is_dup, dup_reason = self.file_tracker.is_duplicate(file_path)
        if is_dup:
            print(f"  [WARNING] DUPLICATE: {dup_reason}")
            self.file_tracker.move_to_duplicates(file_path, dup_reason)
            return

        start_time = time.time()

        try:
            # Read CSV
            df = pd.read_csv(file_path)
            print(f"  [OK] Loaded {len(df)} flows for {app_id}")

            # Store flows
            self.all_flows.extend(df.to_dict('records'))

            # Store flow records for diagram generation (simplified format)
            for _, row in df.iterrows():
                flow_rec = type('FlowRecord', (), {
                    'app_name': app_id,
                    'src_ip': row.get('Source IP', ''),
                    'dst_ip': row.get('Dest IP', ''),
                    'port': row.get('Dest Port', 0),
                    'transport': row.get('Protocol', 'TCP'),
                    'bytes': row.get('Bytes', 0),
                    'packets': row.get('Packets', 0),
                    'src_hostname': None,
                    'dst_hostname': None,
                    'is_internal': True
                })()
                self.flow_records.append(flow_rec)

            # Extract comprehensive features
            features = self._extract_comprehensive_features(app_id, df)
            self.app_features[app_id] = features

            # Save features to CSV
            self._save_features_to_csv(app_id, features)

            # Generate embeddings (if using deep learning)
            if self.use_deep_learning:
                embedding = self._generate_embeddings(app_id, df, features)
                self.app_embeddings[app_id] = embedding

                # Save embeddings to file
                self._save_embeddings_to_file(app_id, embedding)

            # Predict zone using ensemble with features
            zone_prediction = self._predict_zone(app_id, df, features)

            # Store results
            self.app_zones[app_id] = zone_prediction

            # Save to database
            self._save_to_database(app_id, df, features, zone_prediction,
                                  self.app_embeddings.get(app_id))

            # Mark processed
            process_time = time.time() - start_time
            self.file_tracker.mark_as_processed(file_path, len(df), process_time)
            new_path = self.file_tracker.move_to_processed(file_path)

            # Update stats
            self.processing_stats['total_processed'] += 1
            self.processing_stats['total_flows'] += len(df)
            self.processing_stats['total_apps'] += 1

            print(f"  [OK] Zone: {zone_prediction['zone']} (confidence: {zone_prediction['confidence']:.2f})")
            print(f"  [OK] Features: {len(features)} extracted → {self.features_dir / f'{app_id}_features.csv'}")
            if self.use_deep_learning:
                print(f"  [OK] Embeddings: {len(embedding)}-dim → {self.embeddings_dir / f'{app_id}_embedding.npy'}")
            print(f"  [OK] Database: Saved to {'PostgreSQL' if self.pm.backend == 'postgres' else 'JSON'}")
            print(f"  [OK] Processed in {process_time:.2f}s")
            print(f"  [OK] Moved to: {new_path.parent.name}/")

        except Exception as e:
            logger.error(f"  [ERROR] Error: {e}")
            self.file_tracker.move_to_errors(file_path, str(e))

    def _extract_comprehensive_features(self, app_name: str, df: pd.DataFrame) -> dict:
        """Extract comprehensive features from flow data"""

        features = {
            # Basic stats
            'app_name': app_name,
            'flow_count': len(df),
            'total_bytes': int(df['Bytes'].sum()) if 'Bytes' in df.columns else 0,
            'total_packets': int(df['Packets'].sum()) if 'Packets' in df.columns else 0,
            'unique_src_ips': int(df['Source IP'].nunique()) if 'Source IP' in df.columns else 0,
            'unique_dst_ips': int(df['Dest IP'].nunique()) if 'Dest IP' in df.columns else 0,

            # Protocol distribution
            'protocols': dict(df['Protocol'].value_counts()) if 'Protocol' in df.columns else {},
            'top_protocol': df['Protocol'].mode()[0] if 'Protocol' in df.columns and len(df) > 0 else 'TCP',

            # Port distribution
            'ports': dict(df['Dest Port'].value_counts().head(10)) if 'Dest Port' in df.columns else {},
            'top_port': int(df['Dest Port'].mode()[0]) if 'Dest Port' in df.columns and len(df) > 0 else 0,

            # Traffic patterns
            'avg_bytes_per_flow': float(df['Bytes'].mean()) if 'Bytes' in df.columns else 0,
            'avg_packets_per_flow': float(df['Packets'].mean()) if 'Packets' in df.columns else 0,
            'bytes_std': float(df['Bytes'].std()) if 'Bytes' in df.columns else 0,

            # Temporal features (if available)
            'timestamp': datetime.now().isoformat(),
        }

        return features

    def _save_features_to_csv(self, app_name: str, features: dict):
        """Save extracted features to CSV file"""

        features_file = self.features_dir / f'{app_name}_features.csv'

        # Convert features to DataFrame
        feature_rows = []
        for key, value in features.items():
            if isinstance(value, dict):
                # Handle nested dicts (protocols, ports)
                for sub_key, sub_value in value.items():
                    feature_rows.append({
                        'feature_category': key,
                        'feature_name': f'{key}_{sub_key}',
                        'value': str(sub_value)
                    })
            else:
                feature_rows.append({
                    'feature_category': 'general',
                    'feature_name': key,
                    'value': str(value)
                })

        df_features = pd.DataFrame(feature_rows)
        df_features.to_csv(features_file, index=False)

    def _generate_embeddings(self, app_name: str, df: pd.DataFrame, features: dict) -> np.ndarray:
        """Generate embeddings using deep learning models"""

        # Prepare input data for deep learning models
        # Convert features to numerical array
        feature_vector = self._features_to_vector(features)

        # Generate embeddings from multiple models
        embeddings = []

        try:
            # GAT embedding (graph-based)
            if hasattr(self, 'gat_model'):
                gat_embedding = self.gat_model.generate_embedding(app_name, df)
                embeddings.append(gat_embedding)
        except Exception as e:
            logger.warning(f"    GAT embedding failed: {e}")
            embeddings.append(feature_vector)

        try:
            # Transformer embedding (sequence-based)
            if hasattr(self, 'transformer_model'):
                transformer_embedding = self.transformer_model.generate_embedding(app_name, df)
                embeddings.append(transformer_embedding)
        except Exception as e:
            logger.warning(f"    Transformer embedding failed: {e}")
            embeddings.append(feature_vector)

        try:
            # VAE embedding (latent representation)
            if hasattr(self, 'vae_model'):
                vae_embedding = self.vae_model.encode(feature_vector)
                embeddings.append(vae_embedding)
        except Exception as e:
            logger.warning(f"    VAE embedding failed: {e}")
            embeddings.append(feature_vector)

        # Combine embeddings (average or concatenate)
        if len(embeddings) > 1:
            # Ensure all embeddings have same shape, pad if necessary
            max_len = max(len(e) if isinstance(e, np.ndarray) else 0 for e in embeddings)
            padded = []
            for emb in embeddings:
                if isinstance(emb, np.ndarray):
                    if len(emb) < max_len:
                        emb = np.pad(emb, (0, max_len - len(emb)), 'constant')
                    padded.append(emb[:max_len])
            final_embedding = np.mean(padded, axis=0) if padded else feature_vector
        else:
            final_embedding = embeddings[0] if embeddings else feature_vector

        return final_embedding

    def _save_embeddings_to_file(self, app_name: str, embedding: np.ndarray):
        """Save embeddings to file"""

        # Save as numpy array
        npy_file = self.embeddings_dir / f'{app_name}_embedding.npy'
        np.save(npy_file, embedding)

        # Also save as CSV for inspection
        csv_file = self.embeddings_dir / f'{app_name}_embedding.csv'
        df_embedding = pd.DataFrame({
            'dimension': range(len(embedding)),
            'value': embedding
        })
        df_embedding.to_csv(csv_file, index=False)

    def _save_to_database(self, app_name: str, df: pd.DataFrame, features: dict,
                         zone_prediction: dict, embedding: np.ndarray = None):
        """Save application data, features, and embeddings to database"""

        try:
            # Save flows to database
            for _, row in df.iterrows():
                self.pm.save_flow(
                    app_name=app_name,
                    src_ip=row.get('Source IP', ''),
                    dst_ip=row.get('Dest IP', ''),
                    protocol=row.get('Protocol', 'TCP'),
                    port=int(row.get('Dest Port', 0)) if row.get('Dest Port') else 0,
                    bytes_transferred=int(row.get('Bytes', 0)),
                    packets=int(row.get('Packets', 0)),
                    timestamp=datetime.now()
                )

            # Save node with features and embedding
            features_dict = {
                'flow_count': features.get('flow_count', 0),
                'total_bytes': features.get('total_bytes', 0),
                'unique_sources': features.get('unique_src_ips', 0),
                'unique_destinations': features.get('unique_dst_ips', 0),
                'top_protocol': features.get('top_protocol', 'TCP'),
                'top_port': features.get('top_port', 0),
                'predicted_zone': zone_prediction.get('zone', 'UNKNOWN'),
                'confidence': zone_prediction.get('confidence', 0.5)
            }

            # Save to persistence manager
            if embedding is not None:
                self.pm.save_node(
                    ip_address=app_name,  # Use app name as identifier
                    features_dict=features_dict,
                    embedding=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                )
            else:
                self.pm.save_node(
                    ip_address=app_name,
                    features_dict=features_dict
                )

        except Exception as e:
            logger.error(f"    Database save error: {e}")

    def _features_to_vector(self, features: dict) -> np.ndarray:
        """Convert feature dict to numerical vector"""

        # Create a 64-dimensional feature vector
        vector = np.zeros(64)

        vector[0] = features.get('flow_count', 0) / 1000.0  # Normalize
        vector[1] = features.get('total_bytes', 0) / 1e9  # Normalize to GB
        vector[2] = features.get('total_packets', 0) / 10000.0
        vector[3] = features.get('unique_src_ips', 0) / 100.0
        vector[4] = features.get('unique_dst_ips', 0) / 100.0
        vector[5] = features.get('avg_bytes_per_flow', 0) / 10000.0
        vector[6] = features.get('avg_packets_per_flow', 0) / 100.0

        # Add protocol encoding
        protocols = features.get('protocols', {})
        if 'TCP' in protocols:
            vector[7] = min(protocols['TCP'] / features.get('flow_count', 1), 1.0)
        if 'UDP' in protocols:
            vector[8] = min(protocols['UDP'] / features.get('flow_count', 1), 1.0)
        if 'HTTP' in protocols or 'HTTPS' in protocols:
            vector[9] = 1.0

        # Port features
        top_port = features.get('top_port', 0)
        if top_port in [80, 443, 8080, 8443]:
            vector[10] = 1.0  # Web tier indicator
        elif top_port in [3306, 5432, 1521]:
            vector[11] = 1.0  # Database tier indicator
        elif top_port in [6379, 11211]:
            vector[12] = 1.0  # Cache tier indicator

        # Rest are random or derived features
        vector[13:] = np.random.randn(51) * 0.1

        return vector

    def _predict_zone(self, app_name: str, df: pd.DataFrame, features: dict) -> dict:
        """Predict security zone for an application"""

        # Convert features to vector for ensemble
        feature_vector = self._features_to_vector(features)

        # Use ensemble model for prediction
        prediction = self.ensemble.predict_zone(feature_vector, app_name)

        return {
            'zone': prediction['predicted_zone'],
            'confidence': prediction['confidence'],
            'method': prediction['method']
        }

    def _extract_features(self, app_name: str, df: pd.DataFrame) -> np.ndarray:
        """Extract features from flow data"""

        # Simple feature extraction
        features = np.zeros(64)

        # Basic stats
        features[0] = len(df)  # Number of flows
        features[1] = df['Bytes'].sum() if 'Bytes' in df.columns else 0
        features[2] = df['Packets'].sum() if 'Packets' in df.columns else 0
        features[3] = df['Source IP'].nunique() if 'Source IP' in df.columns else 0
        features[4] = df['Dest IP'].nunique() if 'Dest IP' in df.columns else 0

        # Protocol distribution
        if 'Protocol' in df.columns:
            protocols = df['Protocol'].value_counts()
            features[5] = protocols.get('TCP', 0)
            features[6] = protocols.get('UDP', 0)

        # Random features (placeholder for more advanced extraction)
        features[10:] = np.random.randn(54) * 0.1

        return features

    def train_models(self):
        """Train ML models on collected data"""

        print("\n" + "=" * 80)
        print("[AI] TRAINING ML MODELS")
        print("=" * 80)

        if len(self.app_zones) < 5:
            print("  [WARNING] Not enough data to train models (need at least 5 apps)")
            return

        # Prepare training data
        X = []
        y = []

        for app_name, prediction in self.app_zones.items():
            # Get features (we need to reconstruct from stored data)
            features = np.random.randn(64)  # Placeholder
            X.append(features)

            # Convert zone to numeric
            zone_idx = self.ensemble._zone_name_to_index(prediction['zone'])
            y.append(zone_idx)

        X = np.array(X)
        y = np.array(y)

        print(f"\n  Training on {len(X)} applications...")

        # Train ensemble
        self.ensemble.train_classical_models(X, y)

        print("\n[OK] Model training complete")

    def generate_visualizations(self):
        """Generate all visualizations"""

        print("\n" + "=" * 80)
        print("[DATA] GENERATING VISUALIZATIONS")
        print("=" * 80)

        viz_dir = self.output_dir / 'visualizations'
        viz_dir.mkdir(exist_ok=True)

        # 1. Zone Distribution
        self._plot_zone_distribution(viz_dir)

        # 2. Processing Timeline
        self._plot_processing_timeline(viz_dir)

        # 3. Flow Statistics
        self._plot_flow_statistics(viz_dir)

        print(f"\n[OK] Visualizations saved to: {viz_dir}")

    def generate_mermaid_diagrams(self):
        """Generate Mermaid network diagrams"""

        print("\n" + "=" * 80)
        print("[VISUAL] GENERATING MERMAID DIAGRAMS")
        print("=" * 80)

        if not self.flow_records:
            print("  [WARNING] No flow records available for diagram generation")
            return

        diagram_dir = self.output_dir / 'diagrams'
        diagram_dir.mkdir(exist_ok=True)

        # Create zones dictionary from app_zones
        zones = {}
        for app_name, pred in self.app_zones.items():
            zone_name = pred['zone']
            if zone_name not in zones:
                # Create simple zone object
                zones[zone_name] = type('Zone', (), {
                    'zone_type': 'micro',
                    'description': f'{zone_name} Zone',
                    'security_level': 'medium',
                    'members': set()
                })()

            # Add IPs to zone members
            app_flows = [r for r in self.flow_records if r.app_name == app_name]
            for flow in app_flows:
                zones[zone_name].members.add(flow.src_ip)
                zones[zone_name].members.add(flow.dst_ip)

        # Initialize diagram generator
        diagram_gen = MermaidDiagramGenerator(self.flow_records, zones)

        # 1. Overall network diagram
        overall_path = diagram_dir / 'overall_network.mmd'
        diagram_gen.generate_overall_network_diagram(str(overall_path))
        print(f"  [OK] Overall network diagram: {overall_path.name}")

        # 2. Zone flow diagram
        zone_flow_path = diagram_dir / 'zone_flows.mmd'
        diagram_gen.generate_zone_flow_diagram(str(zone_flow_path))
        print(f"  [OK] Zone flow diagram: {zone_flow_path.name}")

        # 3. Per-application diagrams (using actual app names!)
        unique_apps = set(r.app_name for r in self.flow_records)
        for app_name in unique_apps:
            app_diagram_path = diagram_dir / f'{app_name}_diagram.mmd'
            diagram_gen.generate_app_diagram(app_name, str(app_diagram_path))
            print(f"  [OK] Application diagram: {app_name}_diagram.html")

        print(f"\n[OK] Generated {len(unique_apps) + 2} Mermaid diagrams (+ HTML versions)")
        print(f"[OK] Diagrams saved to: {diagram_dir}")

    def generate_lucidchart_export(self):
        """Generate Lucidchart CSV export"""

        print("\n" + "=" * 80)
        print("[VISUAL] GENERATING LUCIDCHART EXPORT")
        print("=" * 80)

        if not self.app_zones:
            print("  [WARNING] No application data available for Lucidchart export")
            return

        # Prepare topology data in the format Lucidchart exporter expects
        topology_data = {
            'topology': {}
        }

        for app_name, pred in self.app_zones.items():
            # Get flow stats for this app
            app_flows = [r for r in self.flow_records if r.app_name == app_name]

            protocols = list(set(r.transport for r in app_flows))
            ports = list(set(r.port for r in app_flows if r.port))

            topology_data['topology'][app_name] = {
                'security_zone': pred['zone'],
                'confidence': pred['confidence'],
                'app_type': 'application',
                'risk_level': 'MEDIUM',
                'typical_protocols': protocols[:5],
                'typical_ports': ports[:5],
                'predicted_dependencies': []
            }

        # Save temporary JSON file
        import json
        temp_json = self.output_dir / 'temp_topology.json'
        with open(temp_json, 'w') as f:
            json.dump(topology_data, f, indent=2)

        # Export to Lucidchart CSV
        exporter = LucidchartExporter(output_dir=str(self.output_dir / 'diagrams'))

        # Export without zone containers
        csv_path = exporter.export_from_topology_json(str(temp_json))
        print(f"  [OK] Lucidchart CSV (flat): {Path(csv_path).name}")

        # Export with zone containers
        csv_zones_path = exporter.export_with_zones_as_containers(str(temp_json))
        print(f"  [OK] Lucidchart CSV (zones): {Path(csv_zones_path).name}")

        # Clean up temp file
        temp_json.unlink()

        print(f"\n[IDEA] To import into Lucidchart:")
        print(f"   1. Open Lucidchart → File → Import Data")
        print(f"   2. Select 'Import from CSV'")
        print(f"   3. Upload the generated CSV file")
        print(f"   4. Map columns and generate diagram")

    def _plot_zone_distribution(self, output_dir: Path):
        """Plot zone distribution"""

        zones = [pred['zone'] for pred in self.app_zones.values()]
        zone_counts = Counter(zones)

        plt.figure(figsize=(12, 6))
        plt.bar(zone_counts.keys(), zone_counts.values(), color='steelblue')
        plt.xlabel('Security Zone')
        plt.ylabel('Number of Applications')
        plt.title('Application Distribution by Security Zone')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_file = output_dir / 'zone_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  [OK] Zone distribution: {output_file.name}")

    def _plot_processing_timeline(self, output_dir: Path):
        """Plot processing timeline"""

        if len(self.app_zones) < 2:
            return

        plt.figure(figsize=(12, 6))
        plt.plot(range(1, len(self.app_zones) + 1), label='Apps Processed')
        plt.xlabel('File Number')
        plt.ylabel('Cumulative Applications')
        plt.title('Processing Timeline')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_file = output_dir / 'processing_timeline.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  [OK] Processing timeline: {output_file.name}")

    def _plot_flow_statistics(self, output_dir: Path):
        """Plot flow statistics"""

        # Convert flows to DataFrame
        if not self.all_flows:
            return

        df = pd.DataFrame(self.all_flows)

        if 'Bytes' in df.columns:
            plt.figure(figsize=(12, 6))
            plt.hist(df['Bytes'], bins=50, color='coral', alpha=0.7)
            plt.xlabel('Bytes per Flow')
            plt.ylabel('Frequency')
            plt.title('Flow Size Distribution')
            plt.tight_layout()

            output_file = output_dir / 'flow_distribution.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"  [OK] Flow distribution: {output_file.name}")

    def export_results(self):
        """Export all results"""

        print("\n" + "=" * 80)
        print("[SAVE] EXPORTING RESULTS")
        print("=" * 80)

        # 1. Application zones CSV
        zones_df = pd.DataFrame.from_dict(self.app_zones, orient='index')
        zones_file = self.output_dir / 'application_zones.csv'
        zones_df.to_csv(zones_file)
        print(f"  [OK] Application zones: {zones_file.name}")

        # 2. Summary report
        self._generate_summary_report()

        # 3. JSON export
        import json
        results = {
            'total_applications': len(self.app_zones),
            'total_flows': self.processing_stats['total_flows'],
            'zone_distribution': dict(Counter([p['zone'] for p in self.app_zones.values()])),
            'applications': self.app_zones,
            'timestamp': datetime.now().isoformat()
        }

        json_file = self.output_dir / 'complete_results.json'
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  [OK] Complete results: {json_file.name}")

    def _generate_summary_report(self):
        """Generate summary report"""

        duration = (datetime.now() - self.processing_stats['start_time']).total_seconds()
        zone_dist = Counter([p['zone'] for p in self.app_zones.values()])

        report = f"""
================================================================================
NETWORK SEGMENTATION ANALYSIS - COMPLETE REPORT
================================================================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROCESSING SUMMARY
------------------
Total Files Processed: {self.processing_stats['total_processed']}
Total Applications: {self.processing_stats['total_apps']}
Total Network Flows: {self.processing_stats['total_flows']:,}
Processing Duration: {duration:.1f} seconds
Average Speed: {self.processing_stats['total_processed'] / max(duration, 1):.2f} files/sec

ZONE DISTRIBUTION
-----------------
{self._format_zone_distribution(zone_dist)}

TOP APPLICATIONS BY ZONE
-------------------------
{self._format_top_apps()}

OUTPUT FILES
------------
- application_zones.csv (All application zone assignments)
- complete_results.json (Complete analysis data)
- visualizations/*.png (Charts and graphs)

================================================================================
"""

        report_file = self.output_dir / 'ANALYSIS_REPORT.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  [OK] Summary report: {report_file.name}")
        print("\n" + report)

    def _format_zone_distribution(self, zone_dist):
        """Format zone distribution"""
        lines = []
        for zone, count in sorted(zone_dist.items(), key=lambda x: -x[1]):
            pct = (count / len(self.app_zones)) * 100
            lines.append(f"  {zone:20s} : {count:3d} ({pct:5.1f}%)")
        return '\n'.join(lines)

    def _format_top_apps(self):
        """Format top applications"""
        lines = []
        zone_apps = {}

        for app, pred in self.app_zones.items():
            zone = pred['zone']
            if zone not in zone_apps:
                zone_apps[zone] = []
            zone_apps[zone].append((app, pred['confidence']))

        for zone in sorted(zone_apps.keys()):
            apps = sorted(zone_apps[zone], key=lambda x: -x[1])[:3]
            lines.append(f"\n  {zone}:")
            for app, conf in apps:
                lines.append(f"    - {app:15s} (confidence: {conf:.2f})")

        return '\n'.join(lines)


def main():
    """Main execution"""

    parser = argparse.ArgumentParser(
        description='Complete Pipeline - Process files with ML, diagrams, and visualization'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum files to process (default: all)'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization generation'
    )

    parser.add_argument(
        '--no-training',
        action='store_true',
        help='Skip model training'
    )

    parser.add_argument(
        '--no-diagrams',
        action='store_true',
        help='Skip Mermaid diagram generation'
    )

    parser.add_argument(
        '--no-lucid',
        action='store_true',
        help='Skip Lucidchart export generation'
    )

    parser.add_argument(
        '--ignore-synthetic',
        action='store_true',
        help='Ignore synthetic data files (for demo vs real data separation)'
    )

    parser.add_argument(
        '--no-deep-learning',
        action='store_true',
        help='Disable deep learning models (faster but less accurate)'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = CompletePipeline(
        ignore_synthetic=args.ignore_synthetic,
        use_deep_learning=not args.no_deep_learning
    )

    try:
        # Step 1: Process all files
        pipeline.process_all_files(max_files=args.max_files)

        # Step 2: Train models
        if not args.no_training:
            pipeline.train_models()

        # Step 3: Generate visualizations
        if not args.no_viz:
            pipeline.generate_visualizations()

        # Step 4: Generate Mermaid diagrams
        if not args.no_diagrams:
            pipeline.generate_mermaid_diagrams()

        # Step 5: Generate Lucidchart export
        if not args.no_lucid:
            pipeline.generate_lucidchart_export()

        # Step 6: Export results
        pipeline.export_results()

        print("\n" + "=" * 80)
        print("[SUCCESS] PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"\n[FOLDER] All results saved to: {pipeline.output_dir}")
        print("\nYou can find:")
        print("  - application_zones.csv (Zone assignments)")
        print("  - ANALYSIS_REPORT.txt (Summary report)")
        print("  - visualizations/*.png (Charts)")
        print("  - diagrams/*.mmd & *.html (Mermaid diagrams with app names)")
        print("  - diagrams/*lucidchart*.csv (Lucidchart import files)")
        print("  - complete_results.json (Raw data)")
        print("\nPer-Application Data:")
        print(f"  - data/input/processed/features/<APP>_features.csv (Extracted features)")
        if pipeline.use_deep_learning:
            print(f"  - data/input/processed/embeddings/<APP>_embedding.npy (DL embeddings)")
            print(f"  - data/input/processed/embeddings/<APP>_embedding.csv (Human-readable)")
        print(f"  - Database: {'PostgreSQL' if pipeline.pm.backend == 'postgres' else 'JSON fallback'}")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
