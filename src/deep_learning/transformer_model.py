# -*- coding: utf-8 -*-
"""
Transformer Model for Temporal Traffic Analysis
================================================
Local PyTorch implementation - NO EXTERNAL APIs

Models temporal evolution of application communication patterns:
- Detect topology changes over time
- Predict future communication patterns
- Identify temporal anomalies
- Learn application lifecycle patterns
- Service chain evolution tracking

100% LOCAL TRAINING AND INFERENCE

Author: Enterprise Security Team
Version: 3.0 - Deep Learning Enhanced
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import math

logger = logging.getLogger(__name__)

# Try to import PyTorch (optional dependency)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install with: pip install torch")


class PositionalEncoding(nn.Module if TORCH_AVAILABLE else object):
    """
    Positional encoding for transformer

    Adds temporal position information to the input embeddings
    """

    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        """
        Args:
            d_model: Dimension of model embeddings
            max_len: Maximum sequence length
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for Transformer")

        super(PositionalEncoding, self).__init__()

        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor [batch_size, seq_len, d_model]

        Returns:
            x with positional encoding added
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module if TORCH_AVAILABLE else object):
    """
    Multi-head self-attention mechanism

    Allows the model to attend to different parts of the sequence
    """

    def __init__(self, d_model: int, num_heads: int = 8, dropout: float = 0.1):
        """
        Args:
            d_model: Dimension of model
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        super(MultiHeadAttention, self).__init__()

        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    def scaled_dot_product_attention(
        self,
        Q: torch.Tensor,
        K: torch.Tensor,
        V: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Scaled dot-product attention

        Returns:
            output: Attention output
            attention_weights: Attention weights for visualization
        """
        # Q, K, V: [batch_size, num_heads, seq_len, d_k]
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))

        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        output = torch.matmul(attention_weights, V)

        return output, attention_weights

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query, key, value: [batch_size, seq_len, d_model]
            mask: Optional attention mask

        Returns:
            output: [batch_size, seq_len, d_model]
            attention_weights: For visualization
        """
        batch_size = query.size(0)

        # Linear projections
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # Attention
        attn_output, attention_weights = self.scaled_dot_product_attention(Q, K, V, mask)

        # Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        # Final linear projection
        output = self.W_o(attn_output)

        return output, attention_weights


class FeedForward(nn.Module if TORCH_AVAILABLE else object):
    """
    Position-wise feed-forward network
    """

    def __init__(self, d_model: int, d_ff: int = 2048, dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            d_ff: Hidden dimension
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        super(FeedForward, self).__init__()

        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class TransformerEncoderLayer(nn.Module if TORCH_AVAILABLE else object):
    """
    Single transformer encoder layer

    Architecture:
    - Multi-head self-attention
    - Add & Norm
    - Feed-forward
    - Add & Norm
    """

    def __init__(self, d_model: int, num_heads: int = 8, d_ff: int = 2048, dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            num_heads: Number of attention heads
            d_ff: Feed-forward hidden dimension
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        super(TransformerEncoderLayer, self).__init__()

        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Input [batch_size, seq_len, d_model]
            mask: Optional attention mask

        Returns:
            output: [batch_size, seq_len, d_model]
            attention_weights: For visualization
        """
        # Self-attention
        attn_output, attention_weights = self.attention(x, x, x, mask)
        x = x + self.dropout1(attn_output)
        x = self.norm1(x)

        # Feed-forward
        ff_output = self.feed_forward(x)
        x = x + self.dropout2(ff_output)
        x = self.norm2(x)

        return x, attention_weights


class TrafficPatternTransformer(nn.Module if TORCH_AVAILABLE else object):
    """
    Transformer model for temporal traffic pattern analysis

    Key Features:
    - Learn temporal dependencies in traffic patterns
    - Predict future communication patterns
    - Detect topology changes
    - Identify periodic patterns
    - Anomaly detection in temporal domain

    Architecture:
    - Input Embedding + Positional Encoding
    - N x Transformer Encoder Layers
    - Prediction Head (for next-step prediction)
    - Classification Head (for pattern classification)
    """

    def __init__(
        self,
        input_dim: int = 64,
        d_model: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        d_ff: int = 1024,
        max_seq_len: int = 1000,
        num_classes: int = 10,
        dropout: float = 0.1
    ):
        """
        Args:
            input_dim: Dimension of input features (per time step)
            d_model: Dimension of model embeddings
            num_heads: Number of attention heads
            num_layers: Number of transformer layers
            d_ff: Dimension of feed-forward hidden layer
            max_seq_len: Maximum sequence length
            num_classes: Number of pattern classes
            dropout: Dropout probability
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for Transformer")

        super(TrafficPatternTransformer, self).__init__()

        self.input_dim = input_dim
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers

        # Input embedding
        self.input_embedding = nn.Linear(input_dim, d_model)

        # Positional encoding
        self.pos_encoding = PositionalEncoding(d_model, max_seq_len, dropout)

        # Transformer encoder layers
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

        # Prediction head (for next-step prediction)
        self.prediction_head = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, input_dim)
        )

        # Classification head (for pattern classification)
        self.classification_head = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, num_classes)
        )

        # Change detection head (for topology changes)
        self.change_detection_head = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, 1),
            nn.Sigmoid()
        )

        # Initialize weights
        self._init_weights()

        logger.info(
            f"Transformer initialized (d_model: {d_model}, layers: {num_layers}, heads: {num_heads})"
        )

    def _init_weights(self):
        """Initialize model weights"""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        return_attention: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through transformer

        Args:
            x: Input sequence [batch_size, seq_len, input_dim]
            mask: Optional attention mask
            return_attention: Whether to return attention weights

        Returns:
            Dictionary with predictions, classifications, and change scores
        """
        # Input embedding + positional encoding
        x = self.input_embedding(x)  # [batch_size, seq_len, d_model]
        x = self.pos_encoding(x)

        # Store attention weights if requested
        attention_weights = [] if return_attention else None

        # Pass through encoder layers
        for layer in self.encoder_layers:
            x, attn = layer(x, mask)
            if return_attention:
                attention_weights.append(attn)

        # Get outputs from different heads
        # For prediction: use last time step
        last_hidden = x[:, -1, :]  # [batch_size, d_model]

        predictions = self.prediction_head(last_hidden)  # [batch_size, input_dim]
        classifications = self.classification_head(last_hidden)  # [batch_size, num_classes]
        change_scores = self.change_detection_head(last_hidden)  # [batch_size, 1]

        outputs = {
            'predictions': predictions,
            'classifications': classifications,
            'change_scores': change_scores.squeeze(-1),
            'hidden_states': x
        }

        if return_attention:
            outputs['attention_weights'] = attention_weights

        return outputs

    def predict_next_step(self, x: torch.Tensor) -> torch.Tensor:
        """
        Predict next time step in sequence

        Args:
            x: Input sequence [batch_size, seq_len, input_dim]

        Returns:
            Predicted next step [batch_size, input_dim]
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            return outputs['predictions']

    def detect_topology_change(self, x: torch.Tensor) -> torch.Tensor:
        """
        Detect if topology change occurred

        Args:
            x: Input sequence [batch_size, seq_len, input_dim]

        Returns:
            Change probability [batch_size]
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            return outputs['change_scores']

    def classify_pattern(self, x: torch.Tensor) -> torch.Tensor:
        """
        Classify traffic pattern

        Args:
            x: Input sequence [batch_size, seq_len, input_dim]

        Returns:
            Pattern class logits [batch_size, num_classes]
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            return outputs['classifications']


class TemporalTrafficDataset(Dataset if TORCH_AVAILABLE else object):
    """Dataset for temporal traffic sequences"""

    def __init__(
        self,
        sequences: np.ndarray,
        labels: Optional[np.ndarray] = None,
        change_labels: Optional[np.ndarray] = None
    ):
        """
        Args:
            sequences: Traffic sequences [num_samples, seq_len, input_dim]
            labels: Optional pattern labels [num_samples]
            change_labels: Optional change detection labels [num_samples]
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels) if labels is not None else None
        self.change_labels = torch.FloatTensor(change_labels) if change_labels is not None else None

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = {'sequence': self.sequences[idx]}

        if self.labels is not None:
            item['label'] = self.labels[idx]

        if self.change_labels is not None:
            item['change_label'] = self.change_labels[idx]

        return item


class TransformerTrainer:
    """
    Trainer for Transformer model - handles training loop, validation, checkpointing
    """

    def __init__(
        self,
        model: TrafficPatternTransformer,
        learning_rate: float = 0.0001,
        device: str = 'cpu'
    ):
        """
        Args:
            model: Transformer model to train
            learning_rate: Learning rate for optimizer
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)

        self.optimizer = torch.optim.AdamW(
            model.parameters(), lr=learning_rate, weight_decay=0.01
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=100, eta_min=1e-6
        )

        # Loss functions
        self.prediction_criterion = nn.MSELoss()
        self.classification_criterion = nn.CrossEntropyLoss()
        self.change_detection_criterion = nn.BCELoss()

        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_pred_loss': [],
            'train_class_loss': [],
            'train_change_loss': [],
            'val_pred_loss': [],
            'val_class_loss': [],
            'val_change_loss': []
        }

        logger.info(f"Transformer Trainer initialized (device: {device})")

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> Tuple[float, float, float, float]:
        """
        Train for one epoch

        Returns:
            avg_total_loss, avg_pred_loss, avg_class_loss, avg_change_loss
        """
        self.model.train()

        total_loss = 0.0
        total_pred = 0.0
        total_class = 0.0
        total_change = 0.0
        num_batches = 0

        for batch in train_loader:
            sequences = batch['sequence'].to(self.device)

            # Create next-step targets
            input_seq = sequences[:, :-1, :]  # All but last
            target_next = sequences[:, -1, :]  # Last step

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(input_seq)

            # Prediction loss
            pred_loss = self.prediction_criterion(outputs['predictions'], target_next)

            # Classification loss (if labels available)
            class_loss = torch.tensor(0.0).to(self.device)
            if 'label' in batch:
                labels = batch['label'].to(self.device)
                class_loss = self.classification_criterion(outputs['classifications'], labels)

            # Change detection loss (if labels available)
            change_loss = torch.tensor(0.0).to(self.device)
            if 'change_label' in batch:
                change_labels = batch['change_label'].to(self.device)
                change_loss = self.change_detection_criterion(
                    outputs['change_scores'], change_labels
                )

            # Combined loss
            loss = pred_loss + 0.5 * class_loss + 0.3 * change_loss

            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            # Accumulate losses
            total_loss += loss.item()
            total_pred += pred_loss.item()
            total_class += class_loss.item()
            total_change += change_loss.item()
            num_batches += 1

        # Average losses
        avg_loss = total_loss / num_batches
        avg_pred = total_pred / num_batches
        avg_class = total_class / num_batches
        avg_change = total_change / num_batches

        return avg_loss, avg_pred, avg_class, avg_change

    def validate(
        self,
        val_loader: DataLoader
    ) -> Tuple[float, float, float, float]:
        """
        Validate model

        Returns:
            avg_total_loss, avg_pred_loss, avg_class_loss, avg_change_loss
        """
        self.model.eval()

        total_loss = 0.0
        total_pred = 0.0
        total_class = 0.0
        total_change = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                sequences = batch['sequence'].to(self.device)

                input_seq = sequences[:, :-1, :]
                target_next = sequences[:, -1, :]

                outputs = self.model(input_seq)

                pred_loss = self.prediction_criterion(outputs['predictions'], target_next)

                class_loss = torch.tensor(0.0).to(self.device)
                if 'label' in batch:
                    labels = batch['label'].to(self.device)
                    class_loss = self.classification_criterion(outputs['classifications'], labels)

                change_loss = torch.tensor(0.0).to(self.device)
                if 'change_label' in batch:
                    change_labels = batch['change_label'].to(self.device)
                    change_loss = self.change_detection_criterion(
                        outputs['change_scores'], change_labels
                    )

                loss = pred_loss + 0.5 * class_loss + 0.3 * change_loss

                total_loss += loss.item()
                total_pred += pred_loss.item()
                total_class += class_loss.item()
                total_change += change_loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        avg_pred = total_pred / num_batches
        avg_class = total_class / num_batches
        avg_change = total_change / num_batches

        return avg_loss, avg_pred, avg_class, avg_change

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100,
        early_stopping_patience: int = 15,
        checkpoint_path: Optional[str] = None
    ) -> Dict:
        """
        Full training loop

        Returns:
            Training history dictionary
        """
        logger.info(f"Training Transformer model for {epochs} epochs...")

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # Train
            train_loss, train_pred, train_class, train_change = self.train_epoch(
                train_loader, epoch
            )

            # Validate
            val_loss, val_pred, val_class, val_change = self.validate(val_loader)

            # Update learning rate
            self.scheduler.step()

            # Record history
            self.training_history['train_loss'].append(train_loss)
            self.training_history['train_pred_loss'].append(train_pred)
            self.training_history['train_class_loss'].append(train_class)
            self.training_history['train_change_loss'].append(train_change)
            self.training_history['val_loss'].append(val_loss)
            self.training_history['val_pred_loss'].append(val_pred)
            self.training_history['val_class_loss'].append(val_class)
            self.training_history['val_change_loss'].append(val_change)

            # Logging
            if epoch % 5 == 0 or epoch == epochs - 1:
                logger.info(
                    f"  Epoch {epoch:3d}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, "
                    f"lr={self.scheduler.get_last_lr()[0]:.6f}"
                )

            # Early stopping and checkpointing
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0

                if checkpoint_path:
                    self.save_checkpoint(checkpoint_path)
            else:
                patience_counter += 1

            if patience_counter >= early_stopping_patience:
                logger.info(f"  Early stopping at epoch {epoch}")
                break

        logger.info(f"Training complete! Best val_loss: {best_val_loss:.4f}")

        return self.training_history

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'training_history': self.training_history,
            'model_config': {
                'input_dim': self.model.input_dim,
                'd_model': self.model.d_model,
                'num_heads': self.model.num_heads,
                'num_layers': self.model.num_layers
            }
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)

        logger.debug(f"Checkpoint saved: {path}")

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.training_history = checkpoint.get('training_history', self.training_history)

        logger.info(f"Checkpoint loaded: {path}")


class TemporalTrafficAnalyzer:
    """
    High-level interface for temporal traffic analysis using Transformer

    Key Capabilities:
    1. Predict future communication patterns
    2. Detect topology changes
    3. Identify periodic patterns
    4. Temporal anomaly detection
    5. Service lifecycle analysis
    """

    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        """
        Args:
            model_path: Path to pre-trained Transformer model (optional)
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. Transformer analysis will be limited.")
            self.model = None
            self.trainer = None
            return

        self.device = device

        # Initialize or load model
        if model_path and Path(model_path).exists():
            self.model, self.trainer = self._load_model(model_path, device)
        else:
            self.model = None
            self.trainer = None

        logger.info("Temporal Traffic Analyzer initialized")

    def predict_future_patterns(
        self,
        traffic_sequences: np.ndarray,
        num_steps: int = 5
    ) -> np.ndarray:
        """
        Predict future traffic patterns

        Args:
            traffic_sequences: Historical traffic [num_sequences, seq_len, input_dim]
            num_steps: Number of future steps to predict

        Returns:
            Predicted future patterns [num_sequences, num_steps, input_dim]
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("Transformer not available for prediction")
            return np.array([])

        logger.info(f"Predicting {num_steps} future steps...")

        predictions = []
        current_seq = torch.FloatTensor(traffic_sequences).to(self.device)

        self.model.eval()
        with torch.no_grad():
            for _ in range(num_steps):
                # Predict next step
                next_step = self.model.predict_next_step(current_seq)

                # Store prediction
                predictions.append(next_step.cpu().numpy())

                # Update sequence (sliding window)
                current_seq = torch.cat([
                    current_seq[:, 1:, :],
                    next_step.unsqueeze(1)
                ], dim=1)

        predictions = np.array(predictions).transpose(1, 0, 2)  # [num_seq, num_steps, input_dim]

        logger.info("Future prediction complete")

        return predictions

    def detect_topology_changes(
        self,
        traffic_sequences: np.ndarray,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Detect topology changes in traffic patterns

        Args:
            traffic_sequences: Traffic sequences [num_sequences, seq_len, input_dim]
            threshold: Change detection threshold

        Returns:
            List of detected changes with details
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("Transformer not available for change detection")
            return []

        logger.info(f"Detecting topology changes in {len(traffic_sequences)} sequences...")

        x = torch.FloatTensor(traffic_sequences).to(self.device)
        change_scores = self.model.detect_topology_change(x).cpu().numpy()

        changes = []
        for i, score in enumerate(change_scores):
            if score > threshold:
                changes.append({
                    'sequence_id': i,
                    'change_score': float(score),
                    'severity': 'HIGH' if score > 0.8 else 'MEDIUM',
                    'timestamp': i  # Could map to actual timestamp
                })

        changes.sort(key=lambda x: x['change_score'], reverse=True)

        logger.info(f"Detected {len(changes)} topology changes")

        return changes

    def analyze_temporal_patterns(
        self,
        traffic_sequences: np.ndarray,
        pattern_names: List[str] = None
    ) -> Dict:
        """
        Analyze and classify temporal patterns

        Args:
            traffic_sequences: Traffic sequences [num_sequences, seq_len, input_dim]
            pattern_names: Optional names for pattern classes

        Returns:
            Pattern analysis results
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("Transformer not available for pattern analysis")
            return {}

        logger.info(f"Analyzing temporal patterns in {len(traffic_sequences)} sequences...")

        x = torch.FloatTensor(traffic_sequences).to(self.device)
        classifications = self.model.classify_pattern(x).cpu().numpy()
        pattern_ids = np.argmax(classifications, axis=1)

        # Default pattern names if not provided
        if pattern_names is None:
            pattern_names = [f"Pattern_{i}" for i in range(classifications.shape[1])]

        # Organize results
        patterns = {}
        for i in range(len(pattern_names)):
            mask = pattern_ids == i
            patterns[pattern_names[i]] = {
                'count': int(np.sum(mask)),
                'percentage': float(np.mean(mask) * 100),
                'avg_confidence': float(np.mean(classifications[mask, i])) if np.any(mask) else 0.0
            }

        logger.info("Temporal pattern analysis complete")

        return {
            'patterns': patterns,
            'pattern_assignments': pattern_ids.tolist(),
            'confidence_scores': classifications.tolist()
        }

    def _load_model(self, path: str, device: str) -> Tuple:
        """Load pre-trained Transformer model"""
        checkpoint = torch.load(path, map_location=torch.device(device))

        config = checkpoint['model_config']
        model = TrafficPatternTransformer(
            input_dim=config['input_dim'],
            d_model=config['d_model'],
            num_heads=config['num_heads'],
            num_layers=config['num_layers']
        )
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        trainer = TransformerTrainer(model, device=device)
        trainer.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        trainer.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        trainer.training_history = checkpoint.get('training_history', trainer.training_history)

        logger.info(f"Pre-trained Transformer model loaded from {path}")

        return model, trainer

    def export_analysis(self, results: Dict, output_path: str):
        """Export analysis results to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Temporal analysis exported to {output_path}")
