# -*- coding: utf-8 -*-
"""
Variational Autoencoder (VAE) for Application Behavior Fingerprinting
======================================================================
Local PyTorch implementation - NO EXTERNAL APIs

Learns compressed representations of application behavior patterns:
- Anomalous application detection
- Application clustering by behavior similarity
- Synthetic traffic pattern generation for testing
- Behavioral fingerprinting for zero-day app discovery

100% LOCAL TRAINING AND INFERENCE

Author: Enterprise Security Team
Version: 3.0 - Deep Learning Enhanced
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import pickle

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


class ApplicationBehaviorEncoder(nn.Module if TORCH_AVAILABLE else object):
    """
    Encoder network for VAE

    Maps high-dimensional application behavior to latent space
    Architecture: Input -> Hidden Layers -> mu, log_var
    """

    def __init__(self, input_dim: int = 128, hidden_dims: List[int] = None, latent_dim: int = 32):
        """
        Args:
            input_dim: Dimension of input features (behavior vectors)
            hidden_dims: List of hidden layer dimensions
            latent_dim: Dimension of latent space
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for VAE")

        super(ApplicationBehaviorEncoder, self).__init__()

        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Build encoder layers
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.LeakyReLU(0.2))
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)

        # Latent space parameters
        self.fc_mu = nn.Linear(prev_dim, latent_dim)
        self.fc_log_var = nn.Linear(prev_dim, latent_dim)

        logger.debug(f"Encoder initialized: {input_dim} -> {hidden_dims} -> {latent_dim}")

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through encoder

        Args:
            x: Input behavior vectors [batch_size, input_dim]

        Returns:
            mu: Mean of latent distribution [batch_size, latent_dim]
            log_var: Log variance of latent distribution [batch_size, latent_dim]
        """
        h = self.encoder(x)
        mu = self.fc_mu(h)
        log_var = self.fc_log_var(h)

        return mu, log_var


class ApplicationBehaviorDecoder(nn.Module if TORCH_AVAILABLE else object):
    """
    Decoder network for VAE

    Reconstructs application behavior from latent space
    Architecture: Latent -> Hidden Layers -> Output
    """

    def __init__(self, latent_dim: int = 32, hidden_dims: List[int] = None, output_dim: int = 128):
        """
        Args:
            latent_dim: Dimension of latent space
            hidden_dims: List of hidden layer dimensions (reversed from encoder)
            output_dim: Dimension of reconstructed output
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for VAE")

        super(ApplicationBehaviorDecoder, self).__init__()

        if hidden_dims is None:
            hidden_dims = [64, 128, 256]  # Reverse of encoder

        self.latent_dim = latent_dim
        self.output_dim = output_dim

        # Build decoder layers
        layers = []
        prev_dim = latent_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.LeakyReLU(0.2))
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        self.decoder = nn.Sequential(*layers)

        # Output layer
        self.fc_output = nn.Linear(prev_dim, output_dim)

        logger.debug(f"Decoder initialized: {latent_dim} -> {hidden_dims} -> {output_dim}")

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through decoder

        Args:
            z: Latent vectors [batch_size, latent_dim]

        Returns:
            reconstructed: Reconstructed behavior vectors [batch_size, output_dim]
        """
        h = self.decoder(z)
        reconstructed = self.fc_output(h)

        return reconstructed


class ApplicationBehaviorVAE(nn.Module if TORCH_AVAILABLE else object):
    """
    Variational Autoencoder for Application Behavior

    Key Features:
    - Learn compressed behavior representations
    - Detect anomalous applications (high reconstruction error)
    - Generate synthetic traffic patterns
    - Cluster applications by behavior similarity
    - Identify zero-day applications

    Architecture:
    - Encoder: Maps behavior -> latent distribution (mu, log_var)
    - Reparameterization: Sample from latent distribution
    - Decoder: Maps latent sample -> reconstructed behavior

    Loss = Reconstruction Loss + KL Divergence
    """

    def __init__(
        self,
        input_dim: int = 128,
        latent_dim: int = 32,
        hidden_dims: List[int] = None,
        beta: float = 1.0
    ):
        """
        Args:
            input_dim: Dimension of input behavior vectors
            latent_dim: Dimension of latent space
            hidden_dims: Hidden layer dimensions for encoder
            beta: Weight for KL divergence term (beta-VAE)
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for VAE")

        super(ApplicationBehaviorVAE, self).__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.beta = beta

        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        # Build encoder and decoder
        self.encoder = ApplicationBehaviorEncoder(input_dim, hidden_dims, latent_dim)
        self.decoder = ApplicationBehaviorDecoder(latent_dim, list(reversed(hidden_dims)), input_dim)

        # Initialize weights
        self._init_weights()

        logger.info(f"VAE initialized (input: {input_dim}, latent: {latent_dim}, beta: {beta})")

    def _init_weights(self):
        """Initialize model weights"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        """
        Reparameterization trick: z = mu + sigma * epsilon

        Args:
            mu: Mean of latent distribution
            log_var: Log variance of latent distribution

        Returns:
            z: Sampled latent vector
        """
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        z = mu + eps * std

        return z

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass through VAE

        Args:
            x: Input behavior vectors [batch_size, input_dim]

        Returns:
            reconstructed: Reconstructed behavior [batch_size, input_dim]
            mu: Latent mean [batch_size, latent_dim]
            log_var: Latent log variance [batch_size, latent_dim]
        """
        # Encode
        mu, log_var = self.encoder(x)

        # Sample from latent distribution
        z = self.reparameterize(mu, log_var)

        # Decode
        reconstructed = self.decoder(z)

        return reconstructed, mu, log_var

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode input to latent space (deterministic - using mean)

        Args:
            x: Input behavior vectors

        Returns:
            z: Latent vectors (using mu only)
        """
        mu, _ = self.encoder(x)
        return mu

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """
        Decode latent vectors to behavior space

        Args:
            z: Latent vectors

        Returns:
            reconstructed: Reconstructed behavior vectors
        """
        return self.decoder(z)

    def generate(self, num_samples: int, device: str = 'cpu') -> torch.Tensor:
        """
        Generate synthetic application behaviors by sampling from latent space

        Args:
            num_samples: Number of samples to generate
            device: Device to generate on

        Returns:
            generated: Generated behavior vectors
        """
        self.eval()
        with torch.no_grad():
            # Sample from standard normal distribution
            z = torch.randn(num_samples, self.latent_dim).to(device)

            # Decode to behavior space
            generated = self.decoder(z)

        return generated

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute reconstruction error for anomaly detection

        Args:
            x: Input behavior vectors

        Returns:
            errors: Reconstruction error per sample
        """
        self.eval()
        with torch.no_grad():
            reconstructed, _, _ = self.forward(x)

            # MSE per sample
            errors = torch.mean((x - reconstructed) ** 2, dim=1)

        return errors


def vae_loss_function(
    reconstructed: torch.Tensor,
    x: torch.Tensor,
    mu: torch.Tensor,
    log_var: torch.Tensor,
    beta: float = 1.0
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    VAE loss function: Reconstruction Loss + Beta * KL Divergence

    Args:
        reconstructed: Reconstructed data
        x: Original data
        mu: Latent mean
        log_var: Latent log variance
        beta: Weight for KL term (beta-VAE for disentanglement)

    Returns:
        total_loss: Combined loss
        recon_loss: Reconstruction loss (MSE)
        kl_loss: KL divergence loss
    """
    # Reconstruction loss (MSE)
    recon_loss = F.mse_loss(reconstructed, x, reduction='mean')

    # KL divergence loss
    # KL(N(mu, sigma) || N(0, 1)) = -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
    kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=1)
    kl_loss = torch.mean(kl_loss)

    # Total loss
    total_loss = recon_loss + beta * kl_loss

    return total_loss, recon_loss, kl_loss


class BehaviorDataset(Dataset if TORCH_AVAILABLE else object):
    """Dataset for application behavior vectors"""

    def __init__(self, behavior_vectors: np.ndarray, app_names: List[str] = None):
        """
        Args:
            behavior_vectors: Array of behavior vectors [num_apps, feature_dim]
            app_names: Optional list of application names
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        self.data = torch.FloatTensor(behavior_vectors)
        self.app_names = app_names or [f"app_{i}" for i in range(len(behavior_vectors))]

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return self.data[idx]


class VAETrainer:
    """
    Trainer for VAE model - handles training loop, validation, checkpointing
    """

    def __init__(
        self,
        model: ApplicationBehaviorVAE,
        learning_rate: float = 0.001,
        device: str = 'cpu'
    ):
        """
        Args:
            model: VAE model to train
            learning_rate: Learning rate for optimizer
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")

        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=10, verbose=True
        )

        self.training_history = {
            'train_loss': [],
            'train_recon_loss': [],
            'train_kl_loss': [],
            'val_loss': [],
            'val_recon_loss': [],
            'val_kl_loss': []
        }

        logger.info(f"VAE Trainer initialized (device: {device})")

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> Tuple[float, float, float]:
        """
        Train for one epoch

        Returns:
            avg_loss, avg_recon_loss, avg_kl_loss
        """
        self.model.train()

        total_loss = 0.0
        total_recon = 0.0
        total_kl = 0.0
        num_batches = 0

        for batch in train_loader:
            x = batch.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            reconstructed, mu, log_var = self.model(x)

            # Compute loss
            loss, recon_loss, kl_loss = vae_loss_function(
                reconstructed, x, mu, log_var, beta=self.model.beta
            )

            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            # Accumulate losses
            total_loss += loss.item()
            total_recon += recon_loss.item()
            total_kl += kl_loss.item()
            num_batches += 1

        # Average losses
        avg_loss = total_loss / num_batches
        avg_recon = total_recon / num_batches
        avg_kl = total_kl / num_batches

        return avg_loss, avg_recon, avg_kl

    def validate(
        self,
        val_loader: DataLoader
    ) -> Tuple[float, float, float]:
        """
        Validate model

        Returns:
            avg_loss, avg_recon_loss, avg_kl_loss
        """
        self.model.eval()

        total_loss = 0.0
        total_recon = 0.0
        total_kl = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                x = batch.to(self.device)

                # Forward pass
                reconstructed, mu, log_var = self.model(x)

                # Compute loss
                loss, recon_loss, kl_loss = vae_loss_function(
                    reconstructed, x, mu, log_var, beta=self.model.beta
                )

                total_loss += loss.item()
                total_recon += recon_loss.item()
                total_kl += kl_loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        avg_recon = total_recon / num_batches
        avg_kl = total_kl / num_batches

        return avg_loss, avg_recon, avg_kl

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

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of training epochs
            early_stopping_patience: Stop if no improvement for N epochs
            checkpoint_path: Path to save best model

        Returns:
            Training history dictionary
        """
        logger.info(f"Training VAE model for {epochs} epochs...")

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # Train
            train_loss, train_recon, train_kl = self.train_epoch(train_loader, epoch)

            # Validate
            val_loss, val_recon, val_kl = self.validate(val_loader)

            # Update learning rate
            self.scheduler.step(val_loss)

            # Record history
            self.training_history['train_loss'].append(train_loss)
            self.training_history['train_recon_loss'].append(train_recon)
            self.training_history['train_kl_loss'].append(train_kl)
            self.training_history['val_loss'].append(val_loss)
            self.training_history['val_recon_loss'].append(val_recon)
            self.training_history['val_kl_loss'].append(val_kl)

            # Logging
            if epoch % 5 == 0 or epoch == epochs - 1:
                logger.info(
                    f"  Epoch {epoch:3d}: train_loss={train_loss:.4f} "
                    f"(recon={train_recon:.4f}, kl={train_kl:.4f}), "
                    f"val_loss={val_loss:.4f} (recon={val_recon:.4f}, kl={val_kl:.4f})"
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
                'latent_dim': self.model.latent_dim,
                'beta': self.model.beta
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


class ApplicationBehaviorAnalyzer:
    """
    High-level interface for using VAE to analyze application behaviors

    Key Capabilities:
    1. Anomaly Detection: Identify applications with unusual behavior
    2. Behavior Clustering: Group similar applications
    3. Fingerprinting: Create unique behavior signatures
    4. Synthetic Generation: Generate test traffic patterns
    """

    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        """
        Args:
            model_path: Path to pre-trained VAE model (optional)
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. VAE analysis will be limited.")
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

        # Statistics for anomaly detection
        self.reconstruction_threshold = None
        self.latent_stats = None

        logger.info("Application Behavior Analyzer initialized")

    def train_on_behaviors(
        self,
        behavior_vectors: np.ndarray,
        app_names: List[str],
        val_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
        latent_dim: int = 32,
        checkpoint_path: str = './models/vae_checkpoint.pt'
    ) -> Dict:
        """
        Train VAE on observed application behaviors

        Args:
            behavior_vectors: Behavior feature vectors [num_apps, feature_dim]
            app_names: List of application names
            val_split: Validation split ratio
            epochs: Number of training epochs
            batch_size: Batch size for training
            latent_dim: Dimension of latent space
            checkpoint_path: Path to save model

        Returns:
            Training history
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available")
            return {}

        logger.info(f"Training VAE on {len(behavior_vectors)} applications...")

        # Create dataset
        dataset = BehaviorDataset(behavior_vectors, app_names)

        # Split train/val
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size]
        )

        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Initialize model and trainer
        input_dim = behavior_vectors.shape[1]
        self.model = ApplicationBehaviorVAE(
            input_dim=input_dim,
            latent_dim=latent_dim,
            beta=1.0
        )
        self.trainer = VAETrainer(self.model, learning_rate=0.001, device=self.device)

        # Train
        history = self.trainer.train(
            train_loader, val_loader,
            epochs=epochs,
            checkpoint_path=checkpoint_path
        )

        # Compute statistics for anomaly detection
        self._compute_statistics(behavior_vectors)

        logger.info("VAE training complete")

        return history

    def detect_anomalies(
        self,
        behavior_vectors: np.ndarray,
        app_names: List[str],
        threshold_percentile: float = 95.0
    ) -> List[Dict]:
        """
        Detect anomalous applications based on reconstruction error

        Args:
            behavior_vectors: Behavior vectors to check
            app_names: Application names
            threshold_percentile: Percentile for anomaly threshold

        Returns:
            List of anomalous applications with details
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("VAE not available for anomaly detection")
            return []

        logger.info(f"Detecting anomalies in {len(behavior_vectors)} applications...")

        # Convert to tensor
        x = torch.FloatTensor(behavior_vectors).to(self.device)

        # Compute reconstruction errors
        errors = self.model.reconstruction_error(x).cpu().numpy()

        # Determine threshold
        if self.reconstruction_threshold is None:
            threshold = np.percentile(errors, threshold_percentile)
        else:
            threshold = self.reconstruction_threshold

        # Find anomalies
        anomalies = []
        for i, (app_name, error) in enumerate(zip(app_names, errors)):
            if error > threshold:
                anomalies.append({
                    'app_name': app_name,
                    'reconstruction_error': float(error),
                    'threshold': float(threshold),
                    'anomaly_score': float(error / threshold),
                    'severity': 'HIGH' if error > threshold * 1.5 else 'MEDIUM'
                })

        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)

        logger.info(f"Found {len(anomalies)} anomalous applications")

        return anomalies

    def cluster_applications(
        self,
        behavior_vectors: np.ndarray,
        app_names: List[str],
        n_clusters: int = 5
    ) -> Dict:
        """
        Cluster applications by behavior similarity using latent representations

        Args:
            behavior_vectors: Behavior vectors
            app_names: Application names
            n_clusters: Number of clusters

        Returns:
            Clustering results
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("VAE not available for clustering")
            return {}

        logger.info(f"Clustering {len(behavior_vectors)} applications...")

        # Encode to latent space
        x = torch.FloatTensor(behavior_vectors).to(self.device)
        latent = self.model.encode(x).cpu().numpy()

        # K-means clustering in latent space
        from sklearn.cluster import KMeans

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(latent)

        # Organize results
        clusters = {}
        for i in range(n_clusters):
            cluster_apps = [app_names[j] for j in range(len(app_names)) if cluster_labels[j] == i]
            clusters[f'cluster_{i}'] = {
                'applications': cluster_apps,
                'size': len(cluster_apps),
                'centroid': kmeans.cluster_centers_[i].tolist()
            }

        logger.info(f"Clustering complete: {n_clusters} clusters")

        return {
            'clusters': clusters,
            'cluster_labels': cluster_labels.tolist(),
            'latent_representations': latent.tolist()
        }

    def generate_synthetic_behaviors(
        self,
        num_samples: int = 100,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate synthetic application behavior patterns for testing

        Args:
            num_samples: Number of synthetic patterns to generate
            save_path: Optional path to save generated patterns

        Returns:
            Generated behavior vectors
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("VAE not available for generation")
            return np.array([])

        logger.info(f"Generating {num_samples} synthetic behavior patterns...")

        # Generate samples
        generated = self.model.generate(num_samples, device=self.device)
        generated_np = generated.cpu().numpy()

        # Save if requested
        if save_path:
            output_path = Path(save_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(output_path, generated_np)
            logger.info(f"Synthetic patterns saved to {save_path}")

        logger.info(f"Generation complete")

        return generated_np

    def get_behavior_fingerprint(
        self,
        behavior_vector: np.ndarray
    ) -> Dict:
        """
        Create a unique fingerprint for an application's behavior

        Args:
            behavior_vector: Behavior feature vector

        Returns:
            Fingerprint dictionary
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.warning("VAE not available for fingerprinting")
            return {}

        # Encode to latent space
        x = torch.FloatTensor(behavior_vector).unsqueeze(0).to(self.device)
        latent = self.model.encode(x).cpu().numpy()[0]

        # Compute reconstruction error
        error = self.model.reconstruction_error(x).cpu().numpy()[0]

        fingerprint = {
            'latent_representation': latent.tolist(),
            'reconstruction_quality': float(1.0 / (1.0 + error)),
            'is_anomalous': bool(error > self.reconstruction_threshold) if self.reconstruction_threshold else False,
            'fingerprint_hash': hash(tuple(latent.round(3)))
        }

        return fingerprint

    def _compute_statistics(self, behavior_vectors: np.ndarray):
        """Compute statistics for anomaly detection"""
        if self.model is None:
            return

        x = torch.FloatTensor(behavior_vectors).to(self.device)

        # Reconstruction errors
        errors = self.model.reconstruction_error(x).cpu().numpy()
        self.reconstruction_threshold = np.percentile(errors, 95)

        # Latent space statistics
        latent = self.model.encode(x).cpu().numpy()
        self.latent_stats = {
            'mean': np.mean(latent, axis=0),
            'std': np.std(latent, axis=0)
        }

        logger.debug(f"Statistics computed: threshold={self.reconstruction_threshold:.4f}")

    def _load_model(self, path: str, device: str) -> Tuple:
        """Load pre-trained VAE model"""
        checkpoint = torch.load(path, map_location=torch.device(device))

        config = checkpoint['model_config']
        model = ApplicationBehaviorVAE(
            input_dim=config['input_dim'],
            latent_dim=config['latent_dim'],
            beta=config['beta']
        )
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        trainer = VAETrainer(model, device=device)
        trainer.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        trainer.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        trainer.training_history = checkpoint.get('training_history', trainer.training_history)

        logger.info(f"Pre-trained VAE model loaded from {path}")

        return model, trainer

    def export_analysis(self, results: Dict, output_path: str):
        """Export analysis results to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        logger.info(f"VAE analysis exported to {output_path}")
