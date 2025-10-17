# -*- coding: utf-8 -*-
"""
Graph Attention Network (GAT) for Application Topology
=======================================================
Local PyTorch implementation - NO EXTERNAL APIs

Discovers application-level relationships beyond network flows:
- Service-to-service dependencies
- Critical application clusters
- Attention-based importance scoring
- Microservice communication patterns

100% LOCAL TRAINING AND INFERENCE

Author: Enterprise Security Team
Version: 3.0 - Deep Learning Enhanced
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Try to import PyTorch (optional dependency)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install with: pip install torch")


class GraphAttentionLayer(nn.Module if TORCH_AVAILABLE else object):
    """
    Single Graph Attention Layer with multi-head attention

    Learns which application connections are important using attention mechanism
    """

    def __init__(self, in_features: int, out_features: int, num_heads: int = 8, dropout: float = 0.2):
        """
        Args:
            in_features: Input feature dimension
            out_features: Output feature dimension per head
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for GAT")

        super(GraphAttentionLayer, self).__init__()

        self.in_features = in_features
        self.out_features = out_features
        self.num_heads = num_heads
        self.dropout = dropout

        # Linear transformations for each head
        self.W = nn.ModuleList([
            nn.Linear(in_features, out_features, bias=False)
            for _ in range(num_heads)
        ])

        # Attention mechanisms for each head
        self.attention = nn.ModuleList([
            nn.Linear(2 * out_features, 1, bias=False)
            for _ in range(num_heads)
        ])

        self.leaky_relu = nn.LeakyReLU(0.2)
        self.dropout_layer = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GAT layer

        Args:
            x: Node features [num_nodes, in_features]
            adj: Adjacency matrix [num_nodes, num_nodes]

        Returns:
            Updated node features [num_nodes, out_features * num_heads]
        """
        num_nodes = x.size(0)
        outputs = []

        for head_idx in range(self.num_heads):
            # Linear transformation
            h = self.W[head_idx](x)  # [num_nodes, out_features]

            # Compute attention coefficients
            # Repeat h for all pairs (i, j)
            h_i = h.repeat(1, num_nodes).view(num_nodes * num_nodes, self.out_features)
            h_j = h.repeat(num_nodes, 1)

            # Concatenate h_i and h_j
            concat_h = torch.cat([h_i, h_j], dim=1)  # [num_nodes * num_nodes, 2 * out_features]

            # Attention scores
            e = self.leaky_relu(self.attention[head_idx](concat_h))  # [num_nodes * num_nodes, 1]
            e = e.view(num_nodes, num_nodes)  # [num_nodes, num_nodes]

            # Mask attention scores with adjacency matrix
            e = e.masked_fill(adj == 0, float('-inf'))

            # Softmax to get attention weights
            alpha = F.softmax(e, dim=1)  # [num_nodes, num_nodes]
            alpha = self.dropout_layer(alpha)

            # Weighted aggregation
            h_prime = torch.matmul(alpha, h)  # [num_nodes, out_features]

            outputs.append(h_prime)

        # Concatenate all heads
        output = torch.cat(outputs, dim=1)  # [num_nodes, out_features * num_heads]

        return output


class ApplicationTopologyGAT(nn.Module if TORCH_AVAILABLE else object):
    """
    Multi-layer Graph Attention Network for application topology discovery

    Architecture:
    - Input: Node features (app metadata, network stats)
    - GAT Layer 1: 64 -> 128 features, 8 heads
    - GAT Layer 2: 128*8 -> 64 features, 4 heads
    - GAT Layer 3: 64*4 -> 32 features, 1 head
    - Output: Application embeddings for clustering/classification
    """

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128, output_dim: int = 32, num_zones: int = 7):
        """
        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            output_dim: Output embedding dimension
            num_zones: Number of security zones to classify
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for GAT")

        super(ApplicationTopologyGAT, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_zones = num_zones

        # GAT layers
        self.gat1 = GraphAttentionLayer(input_dim, hidden_dim, num_heads=8, dropout=0.2)
        self.gat2 = GraphAttentionLayer(hidden_dim * 8, 64, num_heads=4, dropout=0.2)
        self.gat3 = GraphAttentionLayer(64 * 4, output_dim, num_heads=1, dropout=0.2)

        # Classification head for zone prediction
        self.classifier = nn.Sequential(
            nn.Linear(output_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_zones)
        )

        # Initialize weights
        self._init_weights()

        logger.info(f"[OK] GAT model initialized (input: {input_dim}, output: {output_dim}, zones: {num_zones})")

    def _init_weights(self):
        """Initialize model weights"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass

        Args:
            x: Node features [num_nodes, input_dim]
            adj: Adjacency matrix [num_nodes, num_nodes]

        Returns:
            embeddings: Node embeddings [num_nodes, output_dim]
            zone_logits: Zone classification logits [num_nodes, num_zones]
        """
        # GAT layers
        h = F.elu(self.gat1(x, adj))
        h = F.elu(self.gat2(h, adj))
        embeddings = self.gat3(h, adj)  # Final embeddings

        # Zone classification
        zone_logits = self.classifier(embeddings)

        return embeddings, zone_logits

    def get_attention_weights(self, x: torch.Tensor, adj: torch.Tensor) -> List[torch.Tensor]:
        """
        Extract attention weights for visualization

        Returns:
            List of attention weight matrices for each layer
        """
        # This would require modifications to store attention weights during forward pass
        # Simplified version: return adjacency-based importance
        return [adj]

    def predict_zones(self, x: torch.Tensor, adj: torch.Tensor) -> np.ndarray:
        """
        Predict security zones for applications

        Returns:
            zone_predictions: Array of zone indices [num_nodes]
        """
        self.eval()
        with torch.no_grad():
            _, zone_logits = self.forward(x, adj)
            zone_predictions = torch.argmax(zone_logits, dim=1)

        return zone_predictions.cpu().numpy()

    def get_embeddings(self, x: torch.Tensor, adj: torch.Tensor) -> np.ndarray:
        """
        Get application embeddings

        Returns:
            embeddings: Array of embeddings [num_nodes, output_dim]
        """
        self.eval()
        with torch.no_grad():
            embeddings, _ = self.forward(x, adj)

        return embeddings.cpu().numpy()


class GATTrainer:
    """
    Trainer for GAT model - handles training loop, validation, checkpointing
    """

    def __init__(self, model: ApplicationTopologyGAT, learning_rate: float = 0.001, device: str = 'cpu'):
        """
        Args:
            model: GAT model to train
            learning_rate: Learning rate for optimizer
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)
        self.criterion = nn.CrossEntropyLoss()

        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }

        logger.info(f"[OK] GAT Trainer initialized (device: {device})")

    def train_epoch(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        labels: torch.Tensor,
        train_mask: torch.Tensor
    ) -> Tuple[float, float]:
        """
        Train for one epoch

        Args:
            x: Node features
            adj: Adjacency matrix
            labels: Zone labels for supervised learning
            train_mask: Boolean mask for training nodes

        Returns:
            loss, accuracy
        """
        self.model.train()

        # Move to device
        x = x.to(self.device)
        adj = adj.to(self.device)
        labels = labels.to(self.device)
        train_mask = train_mask.to(self.device)

        # Forward pass
        self.optimizer.zero_grad()
        embeddings, zone_logits = self.model(x, adj)

        # Loss only on training nodes
        loss = self.criterion(zone_logits[train_mask], labels[train_mask])

        # Backward pass
        loss.backward()
        self.optimizer.step()

        # Calculate accuracy
        predictions = torch.argmax(zone_logits[train_mask], dim=1)
        accuracy = (predictions == labels[train_mask]).float().mean().item()

        return loss.item(), accuracy

    def validate(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        labels: torch.Tensor,
        val_mask: torch.Tensor
    ) -> Tuple[float, float]:
        """
        Validate model

        Returns:
            val_loss, val_accuracy
        """
        self.model.eval()

        with torch.no_grad():
            x = x.to(self.device)
            adj = adj.to(self.device)
            labels = labels.to(self.device)
            val_mask = val_mask.to(self.device)

            embeddings, zone_logits = self.model(x, adj)

            loss = self.criterion(zone_logits[val_mask], labels[val_mask])

            predictions = torch.argmax(zone_logits[val_mask], dim=1)
            accuracy = (predictions == labels[val_mask]).float().mean().item()

        return loss.item(), accuracy

    def train(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        labels: torch.Tensor,
        train_mask: torch.Tensor,
        val_mask: torch.Tensor,
        epochs: int = 200,
        early_stopping_patience: int = 20,
        checkpoint_path: Optional[str] = None
    ) -> Dict:
        """
        Full training loop

        Args:
            epochs: Number of training epochs
            early_stopping_patience: Stop if no improvement for N epochs
            checkpoint_path: Path to save best model

        Returns:
            Training history dictionary
        """
        logger.info(f"🔥 Training GAT model for {epochs} epochs...")

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # Train
            train_loss, train_acc = self.train_epoch(x, adj, labels, train_mask)

            # Validate
            val_loss, val_acc = self.validate(x, adj, labels, val_mask)

            # Record history
            self.training_history['train_loss'].append(train_loss)
            self.training_history['val_loss'].append(val_loss)
            self.training_history['train_acc'].append(train_acc)
            self.training_history['val_acc'].append(val_acc)

            # Logging
            if epoch % 10 == 0:
                logger.info(f"  Epoch {epoch:3d}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, "
                          f"train_acc={train_acc:.4f}, val_acc={val_acc:.4f}")

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0

                # Save checkpoint
                if checkpoint_path:
                    self.save_checkpoint(checkpoint_path)
            else:
                patience_counter += 1

            if patience_counter >= early_stopping_patience:
                logger.info(f"  Early stopping at epoch {epoch}")
                break

        logger.info(f"[OK] Training complete! Best val_loss: {best_val_loss:.4f}")

        return self.training_history

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_history': self.training_history
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)

        logger.debug(f"Checkpoint saved: {path}")

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_history = checkpoint.get('training_history', self.training_history)

        logger.info(f"[OK] Checkpoint loaded: {path}")


class GATApplicationAnalyzer:
    """
    High-level interface for using GAT to analyze application topology

    Integrates with existing network analysis pipeline
    """

    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        """
        Args:
            model_path: Path to pre-trained model (optional)
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. GAT analysis will be limited.")
            self.model = None
            self.trainer = None
            return

        # Initialize or load model
        if model_path and Path(model_path).exists():
            self.model = self._load_model(model_path, device)
        else:
            self.model = ApplicationTopologyGAT()

        self.trainer = GATTrainer(self.model, device=device) if self.model else None

        # Zone mapping
        self.zone_mapping = {
            0: 'WEB_TIER',
            1: 'APP_TIER',
            2: 'DATA_TIER',
            3: 'MESSAGING_TIER',
            4: 'CACHE_TIER',
            5: 'MANAGEMENT_TIER',
            6: 'INFRASTRUCTURE_TIER'
        }

        logger.info("[OK] GAT Application Analyzer initialized")

    def analyze_topology(
        self,
        node_features: np.ndarray,
        adjacency_matrix: np.ndarray,
        node_names: List[str]
    ) -> Dict:
        """
        Analyze application topology using GAT

        Args:
            node_features: Feature matrix [num_nodes, feature_dim]
            adjacency_matrix: Adjacency matrix [num_nodes, num_nodes]
            node_names: List of application names

        Returns:
            Analysis results with zone predictions and embeddings
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("GAT analysis not available")
            return {}

        logger.info(f"[SEARCH] Analyzing topology with GAT ({len(node_names)} applications)...")

        # Convert to tensors
        x = torch.FloatTensor(node_features)
        adj = torch.FloatTensor(adjacency_matrix)

        # Get predictions
        zone_predictions = self.model.predict_zones(x, adj)
        embeddings = self.model.get_embeddings(x, adj)

        # Build results
        results = {
            'applications': {},
            'clusters': self._identify_clusters(embeddings, node_names),
            'critical_connections': self._identify_critical_connections(adjacency_matrix, node_names)
        }

        for i, app_name in enumerate(node_names):
            zone_idx = zone_predictions[i]
            results['applications'][app_name] = {
                'predicted_zone': self.zone_mapping.get(zone_idx, 'UNKNOWN'),
                'zone_confidence': 0.85,  # TODO: Extract from softmax probabilities
                'embedding': embeddings[i].tolist(),
                'centrality': float(np.sum(adjacency_matrix[i]))
            }

        logger.info(f"[OK] GAT analysis complete")

        return results

    def train_on_observed_data(
        self,
        node_features: np.ndarray,
        adjacency_matrix: np.ndarray,
        zone_labels: np.ndarray,
        train_ratio: float = 0.8
    ) -> Dict:
        """
        Train GAT on observed application data

        Args:
            node_features: Feature matrix
            adjacency_matrix: Adjacency matrix
            zone_labels: Ground truth zone labels
            train_ratio: Ratio of data for training

        Returns:
            Training results
        """
        if not TORCH_AVAILABLE or self.trainer is None:
            logger.warning("GAT training not available")
            return {}

        logger.info("🔥 Training GAT on observed data...")

        # Convert to tensors
        x = torch.FloatTensor(node_features)
        adj = torch.FloatTensor(adjacency_matrix)
        labels = torch.LongTensor(zone_labels)

        # Create train/val masks
        num_nodes = len(node_features)
        train_size = int(num_nodes * train_ratio)

        indices = np.random.permutation(num_nodes)
        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool)

        train_mask[indices[:train_size]] = True
        val_mask[indices[train_size:]] = True

        # Train
        history = self.trainer.train(
            x, adj, labels, train_mask, val_mask,
            epochs=200,
            checkpoint_path='./models/gat_checkpoint.pt'
        )

        return history

    def _identify_clusters(self, embeddings: np.ndarray, node_names: List[str]) -> List[Dict]:
        """Identify application clusters using embeddings"""
        # Simple k-means clustering
        from sklearn.cluster import KMeans

        n_clusters = min(5, len(embeddings))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        clusters = []
        for i in range(n_clusters):
            cluster_apps = [node_names[j] for j in range(len(node_names)) if cluster_labels[j] == i]
            clusters.append({
                'cluster_id': i,
                'applications': cluster_apps,
                'size': len(cluster_apps)
            })

        return clusters

    def _identify_critical_connections(self, adj_matrix: np.ndarray, node_names: List[str]) -> List[Dict]:
        """Identify critical connections (high traffic/importance)"""
        critical = []

        # Find top connections by weight
        for i in range(len(node_names)):
            for j in range(i + 1, len(node_names)):
                weight = adj_matrix[i, j] + adj_matrix[j, i]
                if weight > np.percentile(adj_matrix, 90):  # Top 10%
                    critical.append({
                        'source': node_names[i],
                        'target': node_names[j],
                        'weight': float(weight),
                        'importance': 'HIGH'
                    })

        return sorted(critical, key=lambda x: x['weight'], reverse=True)[:20]  # Top 20

    def _load_model(self, path: str, device: str) -> ApplicationTopologyGAT:
        """Load pre-trained model"""
        model = ApplicationTopologyGAT()
        checkpoint = torch.load(path, map_location=torch.device(device))
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        logger.info(f"[OK] Pre-trained GAT model loaded from {path}")

        return model

    def export_analysis(self, results: Dict, output_path: str):
        """Export analysis results to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        logger.info(f"[OK] GAT analysis exported to {output_path}")
