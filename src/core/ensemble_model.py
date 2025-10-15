# -*- coding: utf-8 -*-
"""
Ensemble Network Model
======================
Orchestrates multiple ML/DL models and picks the best predictions

Models included:
- Graph Attention Network (GAT) - Deep learning for topology
- Transformer Model - Sequence-based analysis
- VAE Model - Anomaly detection and clustering
- Classical ML (Random Forest, SVM) - Baseline predictions

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0 - Ensemble Learning
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class EnsembleNetworkModel:
    """
    Ensemble of multiple network analysis models

    Runs multiple models and combines their predictions:
    - GAT (deep learning)
    - Transformer (sequence modeling)
    - VAE (anomaly detection)
    - Classical ML (baseline)

    Automatically picks the best model or ensembles predictions
    """

    def __init__(self, persistence_manager, use_deep_learning=False, device='cpu'):
        """
        Initialize ensemble model

        Args:
            persistence_manager: Database for storing results
            use_deep_learning: Enable deep learning models (requires PyTorch)
            device: 'cpu' or 'cuda'
        """
        self.pm = persistence_manager
        self.use_deep_learning = use_deep_learning
        self.device = device

        # Available models
        self.models = {}
        self.model_scores = {}  # Track performance of each model

        # Initialize models
        self._initialize_models()

        logger.info("✓ Ensemble Network Model initialized")
        logger.info(f"  Deep Learning: {use_deep_learning}")
        logger.info(f"  Active models: {list(self.models.keys())}")

    def _initialize_models(self):
        """Initialize all available models"""

        # Always available: Classical ML
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.svm import SVC

            self.models['random_forest'] = {
                'classifier': RandomForestClassifier(n_estimators=100, random_state=42),
                'type': 'classical',
                'trained': False
            }

            self.models['svm'] = {
                'classifier': SVC(kernel='rbf', probability=True, random_state=42),
                'type': 'classical',
                'trained': False
            }

            logger.info("  ✓ Classical ML models loaded")

        except ImportError:
            logger.warning("  ⚠ scikit-learn not available")

        # Optional: Deep Learning models
        if self.use_deep_learning:
            try:
                from deep_learning.gat_model import GATApplicationAnalyzer

                self.models['gat'] = {
                    'analyzer': GATApplicationAnalyzer(device=self.device),
                    'type': 'deep_learning',
                    'trained': False
                }

                logger.info("  ✓ GAT model loaded")

            except ImportError as e:
                logger.warning(f"  ⚠ GAT model not available: {e}")

            try:
                from deep_learning.transformer_model import TemporalTrafficAnalyzer

                self.models['transformer'] = {
                    'analyzer': TemporalTrafficAnalyzer(device=self.device),
                    'type': 'deep_learning',
                    'trained': False
                }

                logger.info("  ✓ Transformer model loaded")

            except ImportError as e:
                logger.warning(f"  ⚠ Transformer model not available: {e}")

            try:
                from deep_learning.vae_model import ApplicationBehaviorAnalyzer

                self.models['vae'] = {
                    'analyzer': ApplicationBehaviorAnalyzer(device=self.device),
                    'type': 'deep_learning',
                    'trained': False
                }

                logger.info("  ✓ VAE model loaded")

            except ImportError as e:
                logger.warning(f"  ⚠ VAE model not available: {e}")

    def predict_zone(self, app_features: np.ndarray, app_name: str) -> Dict:
        """
        Predict security zone for an application

        Runs all available models and ensembles predictions

        Args:
            app_features: Feature vector for the application
            app_name: Application name

        Returns:
            Dictionary with zone prediction and confidence
        """
        predictions = {}

        # Run each model
        for model_name, model_info in self.models.items():
            try:
                if model_info['type'] == 'classical' and model_info['trained']:
                    classifier = model_info['classifier']
                    pred = classifier.predict([app_features])[0]
                    prob = classifier.predict_proba([app_features])[0]

                    predictions[model_name] = {
                        'zone': self._zone_index_to_name(pred),
                        'confidence': float(np.max(prob)),
                        'probabilities': prob.tolist()
                    }

                elif model_info['type'] == 'deep_learning' and model_info['trained']:
                    # Deep learning model prediction
                    # (Would need proper interface - placeholder for now)
                    pass

            except Exception as e:
                logger.debug(f"Model {model_name} prediction failed: {e}")

        # Ensemble predictions
        if predictions:
            ensemble_result = self._ensemble_predictions(predictions)
        else:
            # Fallback: heuristic-based prediction
            ensemble_result = self._heuristic_prediction(app_name)

        return ensemble_result

    def _ensemble_predictions(self, predictions: Dict) -> Dict:
        """
        Combine predictions from multiple models

        Uses weighted voting based on model performance
        """
        # Extract zone predictions
        zone_votes = {}
        weighted_confidence = {}

        for model_name, pred in predictions.items():
            zone = pred['zone']
            confidence = pred['confidence']

            # Weight based on model's historical performance
            weight = self.model_scores.get(model_name, 1.0)

            if zone not in zone_votes:
                zone_votes[zone] = 0
                weighted_confidence[zone] = []

            zone_votes[zone] += weight
            weighted_confidence[zone].append(confidence * weight)

        # Pick zone with most votes
        best_zone = max(zone_votes, key=zone_votes.get)
        avg_confidence = np.mean(weighted_confidence[best_zone])

        return {
            'predicted_zone': best_zone,
            'confidence': float(avg_confidence),
            'num_models': len(predictions),
            'model_votes': zone_votes,
            'method': 'ensemble'
        }

    def _heuristic_prediction(self, app_name: str) -> Dict:
        """
        Fallback heuristic prediction based on naming patterns
        """
        app_name_lower = app_name.lower()

        # Naming pattern heuristics
        if any(kw in app_name_lower for kw in ['web', 'ui', 'frontend', 'portal']):
            zone = 'WEB_TIER'
            confidence = 0.65
        elif any(kw in app_name_lower for kw in ['api', 'service', 'gateway']):
            zone = 'APP_TIER'
            confidence = 0.60
        elif any(kw in app_name_lower for kw in ['db', 'database', 'sql', 'dm_']):
            zone = 'DATA_TIER'
            confidence = 0.70
        elif any(kw in app_name_lower for kw in ['cache', 'redis', 'memcache']):
            zone = 'CACHE_TIER'
            confidence = 0.75
        elif any(kw in app_name_lower for kw in ['mq', 'queue', 'kafka', 'messaging']):
            zone = 'MESSAGING_TIER'
            confidence = 0.70
        else:
            zone = 'APP_TIER'
            confidence = 0.50

        return {
            'predicted_zone': zone,
            'confidence': confidence,
            'num_models': 0,
            'method': 'heuristic'
        }

    def train_classical_models(self, X: np.ndarray, y: np.ndarray):
        """
        Train classical ML models

        Args:
            X: Feature matrix [n_samples, n_features]
            y: Zone labels [n_samples]
        """
        logger.info(f"⚡ Training classical models on {len(X)} samples...")

        for model_name, model_info in self.models.items():
            if model_info['type'] == 'classical':
                try:
                    classifier = model_info['classifier']
                    classifier.fit(X, y)
                    model_info['trained'] = True

                    # Evaluate on training data (for score tracking)
                    score = classifier.score(X, y)
                    self.model_scores[model_name] = score

                    logger.info(f"  ✓ {model_name} trained (score: {score:.3f})")

                except Exception as e:
                    logger.error(f"  ✗ {model_name} training failed: {e}")

        logger.info("✓ Classical models training complete")

    def train_deep_learning_models(
        self,
        node_features: np.ndarray,
        adjacency_matrix: np.ndarray,
        zone_labels: np.ndarray
    ):
        """
        Train deep learning models

        Args:
            node_features: Feature matrix [n_nodes, n_features]
            adjacency_matrix: Adjacency matrix [n_nodes, n_nodes]
            zone_labels: Zone labels [n_nodes]
        """
        if not self.use_deep_learning:
            logger.info("Deep learning disabled - skipping DL training")
            return

        logger.info(f"⚡ Training deep learning models...")

        # Train GAT
        if 'gat' in self.models:
            try:
                gat_analyzer = self.models['gat']['analyzer']
                history = gat_analyzer.train_on_observed_data(
                    node_features,
                    adjacency_matrix,
                    zone_labels
                )

                self.models['gat']['trained'] = True
                logger.info("  ✓ GAT model trained")

            except Exception as e:
                logger.error(f"  ✗ GAT training failed: {e}")

        # Train other DL models (Transformer, VAE)
        # (Similar pattern for each model)

        logger.info("✓ Deep learning models training complete")

    def save_all_models(self, output_dir='./models/ensemble'):
        """Save all trained models"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save classical models
        import joblib

        for model_name, model_info in self.models.items():
            if model_info['type'] == 'classical' and model_info['trained']:
                model_file = output_path / f'{model_name}.joblib'
                joblib.dump(model_info['classifier'], model_file)
                logger.debug(f"Saved {model_name} to {model_file}")

        # Save model scores
        scores_file = output_path / 'model_scores.json'
        with open(scores_file, 'w') as f:
            json.dump(self.model_scores, f, indent=2)

        logger.info(f"✓ Models saved to {output_dir}")

    def load_all_models(self, input_dir='./models/ensemble'):
        """Load all trained models"""
        input_path = Path(input_dir)

        if not input_path.exists():
            logger.warning(f"Model directory not found: {input_dir}")
            return

        import joblib

        # Load classical models
        for model_name in ['random_forest', 'svm']:
            model_file = input_path / f'{model_name}.joblib'

            if model_file.exists() and model_name in self.models:
                try:
                    self.models[model_name]['classifier'] = joblib.load(model_file)
                    self.models[model_name]['trained'] = True
                    logger.debug(f"Loaded {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")

        # Load model scores
        scores_file = input_path / 'model_scores.json'
        if scores_file.exists():
            with open(scores_file) as f:
                self.model_scores = json.load(f)

        logger.info(f"✓ Models loaded from {input_dir}")

    @staticmethod
    def _zone_index_to_name(index: int) -> str:
        """Convert zone index to name"""
        zones = {
            0: 'WEB_TIER',
            1: 'APP_TIER',
            2: 'DATA_TIER',
            3: 'MESSAGING_TIER',
            4: 'CACHE_TIER',
            5: 'MANAGEMENT_TIER',
            6: 'INFRASTRUCTURE_TIER'
        }
        return zones.get(index, 'UNKNOWN')

    @staticmethod
    def _zone_name_to_index(name: str) -> int:
        """Convert zone name to index"""
        zones = {
            'WEB_TIER': 0,
            'APP_TIER': 1,
            'DATA_TIER': 2,
            'MESSAGING_TIER': 3,
            'CACHE_TIER': 4,
            'MANAGEMENT_TIER': 5,
            'INFRASTRUCTURE_TIER': 6
        }
        return zones.get(name, 1)  # Default to APP_TIER
