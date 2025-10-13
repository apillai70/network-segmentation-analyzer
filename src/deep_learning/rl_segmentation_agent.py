# -*- coding: utf-8 -*-
"""
Reinforcement Learning Agent for Optimal Network Segmentation
==============================================================
Local PyTorch implementation - NO EXTERNAL APIs

RL agent learns optimal segmentation policies:
- Balance security vs operational complexity
- Minimize attack surface
- Maximize network performance
- Learn from network topology and traffic patterns
- Adaptive segmentation based on evolving threats

100% LOCAL TRAINING AND INFERENCE

Uses Deep Q-Learning (DQN) and Policy Gradient methods

Author: Enterprise Security Team
Version: 3.0 - Deep Learning Enhanced
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import deque, namedtuple
import json
import random

logger = logging.getLogger(__name__)

# Try to import PyTorch (optional dependency)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install with: pip install torch")

# Experience tuple for replay buffer
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


class SegmentationNetwork(nn.Module if TORCH_AVAILABLE else object):
    """
    Deep Q-Network for segmentation policy

    Learns Q-values for different segmentation actions
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: List[int] = None
    ):
        """
        Args:
            state_dim: Dimension of network state representation
            action_dim: Number of possible segmentation actions
            hidden_dims: Hidden layer dimensions
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for RL")

        super(SegmentationNetwork, self).__init__()

        if hidden_dims is None:
            hidden_dims = [256, 256, 128]

        # Build network
        layers = []
        prev_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        self.feature_extractor = nn.Sequential(*layers)

        # Dueling DQN architecture
        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(prev_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(prev_dim, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )

        logger.debug(f"SegmentationNetwork initialized: state_dim={state_dim}, action_dim={action_dim}")

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass - compute Q-values

        Args:
            state: Network state [batch_size, state_dim]

        Returns:
            q_values: Q-values for each action [batch_size, action_dim]
        """
        features = self.feature_extractor(state)

        value = self.value_stream(features)
        advantage = self.advantage_stream(features)

        # Combine value and advantage: Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))

        return q_values


class PolicyNetwork(nn.Module if TORCH_AVAILABLE else object):
    """
    Policy network for Policy Gradient methods

    Outputs probability distribution over actions
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: List[int] = None
    ):
        """
        Args:
            state_dim: Dimension of network state representation
            action_dim: Number of possible segmentation actions
            hidden_dims: Hidden layer dimensions
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for RL")

        super(PolicyNetwork, self).__init__()

        if hidden_dims is None:
            hidden_dims = [256, 256, 128]

        # Build network
        layers = []
        prev_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, action_dim))
        layers.append(nn.Softmax(dim=-1))

        self.network = nn.Sequential(*layers)

        logger.debug(f"PolicyNetwork initialized: state_dim={state_dim}, action_dim={action_dim}")

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass - compute action probabilities

        Args:
            state: Network state [batch_size, state_dim]

        Returns:
            action_probs: Probability distribution [batch_size, action_dim]
        """
        return self.network(state)


class ReplayBuffer:
    """
    Experience replay buffer for DQN

    Stores and samples experiences for training
    """

    def __init__(self, capacity: int = 10000):
        """
        Args:
            capacity: Maximum buffer size
        """
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """Add experience to buffer"""
        experience = Experience(state, action, reward, next_state, done)
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch of experiences"""
        return random.sample(self.buffer, batch_size)

    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    """
    Deep Q-Network agent for segmentation optimization

    Uses:
    - Dueling DQN architecture
    - Double DQN for stability
    - Experience replay
    - Target network
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.0001,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 10000,
        device: str = 'cpu'
    ):
        """
        Args:
            state_dim: State dimension
            action_dim: Number of actions
            learning_rate: Learning rate
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay: Epsilon decay rate
            buffer_capacity: Replay buffer capacity
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for DQN")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.device = torch.device(device)

        # Q-network and target network
        self.q_network = SegmentationNetwork(state_dim, action_dim).to(self.device)
        self.target_network = SegmentationNetwork(state_dim, action_dim).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()

        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        # Replay buffer
        self.replay_buffer = ReplayBuffer(buffer_capacity)

        # Training metrics
        self.training_history = {
            'episode_rewards': [],
            'episode_lengths': [],
            'loss': [],
            'epsilon': []
        }

        logger.info(f"DQN Agent initialized (state_dim: {state_dim}, action_dim: {action_dim})")

    def select_action(self, state: np.ndarray, eval_mode: bool = False) -> int:
        """
        Select action using epsilon-greedy policy

        Args:
            state: Current state
            eval_mode: If True, no exploration (greedy)

        Returns:
            Selected action index
        """
        # Exploration
        if not eval_mode and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        # Exploitation
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor)
            return q_values.argmax(dim=1).item()

    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def update(self, batch_size: int = 64) -> Optional[float]:
        """
        Update Q-network using experience replay

        Args:
            batch_size: Batch size for training

        Returns:
            Loss value (None if buffer too small)
        """
        if len(self.replay_buffer) < batch_size:
            return None

        # Sample batch
        experiences = self.replay_buffer.sample(batch_size)
        batch = Experience(*zip(*experiences))

        # Convert to tensors
        state_batch = torch.FloatTensor(np.array(batch.state)).to(self.device)
        action_batch = torch.LongTensor(batch.action).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)
        next_state_batch = torch.FloatTensor(np.array(batch.next_state)).to(self.device)
        done_batch = torch.FloatTensor(batch.done).to(self.device)

        # Current Q-values
        current_q_values = self.q_network(state_batch).gather(1, action_batch).squeeze(1)

        # Double DQN: use Q-network to select action, target network to evaluate
        with torch.no_grad():
            next_actions = self.q_network(next_state_batch).argmax(dim=1, keepdim=True)
            next_q_values = self.target_network(next_state_batch).gather(1, next_actions).squeeze(1)
            target_q_values = reward_batch + (1 - done_batch) * self.gamma * next_q_values

        # Compute loss
        loss = F.mse_loss(current_q_values, target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        self.optimizer.step()

        return loss.item()

    def update_target_network(self):
        """Update target network with Q-network weights"""
        self.target_network.load_state_dict(self.q_network.state_dict())

    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save(self, path: str):
        """Save agent checkpoint"""
        checkpoint = {
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_history': self.training_history,
            'epsilon': self.epsilon,
            'config': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'gamma': self.gamma
            }
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)

        logger.info(f"DQN agent saved: {path}")

    def load(self, path: str):
        """Load agent checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)

        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_history = checkpoint.get('training_history', self.training_history)
        self.epsilon = checkpoint.get('epsilon', self.epsilon)

        logger.info(f"DQN agent loaded: {path}")


class SegmentationEnvironment:
    """
    Environment for network segmentation RL

    Defines:
    - State: Network topology, traffic patterns, security metrics
    - Actions: Segmentation decisions (zone assignments, ACLs, etc.)
    - Rewards: Security improvement, performance impact, complexity cost
    """

    def __init__(
        self,
        network_topology: Dict,
        traffic_data: Dict,
        security_requirements: Dict
    ):
        """
        Args:
            network_topology: Network graph and application metadata
            traffic_data: Traffic patterns and statistics
            security_requirements: Security policies and constraints
        """
        self.topology = network_topology
        self.traffic = traffic_data
        self.security = security_requirements

        # State representation
        self.state_dim = self._compute_state_dim()

        # Action space: zone assignment for each application
        self.num_zones = len(security_requirements.get('zones', []))
        self.num_apps = len(network_topology.get('applications', []))
        self.action_dim = self.num_apps * self.num_zones

        # Current state
        self.current_state = None
        self.current_segmentation = None

        logger.info(
            f"Segmentation Environment initialized "
            f"(state_dim: {self.state_dim}, action_dim: {self.action_dim})"
        )

    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state

        Returns:
            Initial state
        """
        # Random initial segmentation
        self.current_segmentation = {
            app: random.randint(0, self.num_zones - 1)
            for app in self.topology.get('applications', [])
        }

        self.current_state = self._compute_state()

        return self.current_state

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return next state, reward, done, info

        Args:
            action: Action index (app_idx * num_zones + zone_idx)

        Returns:
            next_state, reward, done, info
        """
        # Decode action
        app_idx = action // self.num_zones
        zone_idx = action % self.num_zones

        # Apply action (move app to zone)
        apps = list(self.topology.get('applications', []))
        if app_idx < len(apps):
            self.current_segmentation[apps[app_idx]] = zone_idx

        # Compute next state
        next_state = self._compute_state()

        # Compute reward
        reward = self._compute_reward()

        # Check if done (could be based on episode length or convergence)
        done = False  # Continuous task

        # Additional info
        info = {
            'security_score': self._compute_security_score(),
            'performance_score': self._compute_performance_score(),
            'complexity_score': self._compute_complexity_score()
        }

        self.current_state = next_state

        return next_state, reward, done, info

    def _compute_state(self) -> np.ndarray:
        """
        Compute state representation from current segmentation

        State includes:
        - Zone assignments (one-hot encoded)
        - Cross-zone traffic volume
        - Security violations count
        - Network complexity metrics
        """
        state_components = []

        # Zone assignments (one-hot)
        apps = list(self.topology.get('applications', []))
        for app in apps:
            zone = self.current_segmentation.get(app, 0)
            one_hot = [0] * self.num_zones
            one_hot[zone] = 1
            state_components.extend(one_hot)

        # Cross-zone traffic
        cross_zone_traffic = self._compute_cross_zone_traffic()
        state_components.append(cross_zone_traffic)

        # Security violations
        violations = self._compute_security_violations()
        state_components.append(violations)

        # Complexity
        complexity = self._compute_complexity_score()
        state_components.append(complexity)

        return np.array(state_components, dtype=np.float32)

    def _compute_state_dim(self) -> int:
        """Compute state dimension"""
        num_apps = len(self.topology.get('applications', []))
        num_zones = len(self.security.get('zones', []))

        # Zone assignments (one-hot) + cross-zone traffic + violations + complexity
        return num_apps * num_zones + 3

    def _compute_reward(self) -> float:
        """
        Compute reward for current segmentation

        Reward = Security Score - Performance Penalty - Complexity Penalty
        """
        security_score = self._compute_security_score()
        performance_penalty = self._compute_performance_penalty()
        complexity_penalty = self._compute_complexity_penalty()

        reward = security_score - 0.3 * performance_penalty - 0.2 * complexity_penalty

        return reward

    def _compute_security_score(self) -> float:
        """Compute security score (0-1, higher is better)"""
        # Simplified: fewer cross-zone connections = better security
        violations = self._compute_security_violations()
        max_violations = len(self.topology.get('connections', []))

        if max_violations == 0:
            return 1.0

        return 1.0 - min(violations / max_violations, 1.0)

    def _compute_performance_score(self) -> float:
        """Compute performance score (0-1, higher is better)"""
        # Simplified: minimize cross-zone traffic
        cross_zone_traffic = self._compute_cross_zone_traffic()
        total_traffic = sum(self.traffic.get('volumes', {}).values()) or 1.0

        return 1.0 - min(cross_zone_traffic / total_traffic, 1.0)

    def _compute_complexity_score(self) -> float:
        """Compute complexity score (0-1, higher is better)"""
        # Simplified: fewer zones used = lower complexity
        zones_used = len(set(self.current_segmentation.values()))

        return 1.0 - (zones_used / self.num_zones)

    def _compute_performance_penalty(self) -> float:
        """Compute performance penalty (0-1, higher is worse)"""
        return 1.0 - self._compute_performance_score()

    def _compute_complexity_penalty(self) -> float:
        """Compute complexity penalty (0-1, higher is worse)"""
        return 1.0 - self._compute_complexity_score()

    def _compute_cross_zone_traffic(self) -> float:
        """Compute cross-zone traffic volume"""
        cross_zone = 0.0

        for conn in self.topology.get('connections', []):
            src = conn.get('source')
            dst = conn.get('destination')
            volume = self.traffic.get('volumes', {}).get(f"{src}->{dst}", 0)

            if self.current_segmentation.get(src) != self.current_segmentation.get(dst):
                cross_zone += volume

        return cross_zone

    def _compute_security_violations(self) -> int:
        """Count security violations"""
        violations = 0

        # Check policy violations
        for policy in self.security.get('policies', []):
            src_zone = policy.get('source_zone')
            dst_zone = policy.get('destination_zone')
            allowed = policy.get('allowed', True)

            # Count connections violating policy
            for conn in self.topology.get('connections', []):
                src = conn.get('source')
                dst = conn.get('destination')

                src_assigned = self.current_segmentation.get(src)
                dst_assigned = self.current_segmentation.get(dst)

                if src_assigned == src_zone and dst_assigned == dst_zone and not allowed:
                    violations += 1

        return violations


class RLSegmentationOptimizer:
    """
    High-level interface for RL-based segmentation optimization

    Orchestrates training and inference for optimal segmentation policies
    """

    def __init__(
        self,
        network_topology: Dict,
        traffic_data: Dict,
        security_requirements: Dict,
        agent_type: str = 'dqn',
        device: str = 'cpu'
    ):
        """
        Args:
            network_topology: Network topology data
            traffic_data: Traffic patterns
            security_requirements: Security constraints
            agent_type: 'dqn' or 'policy_gradient'
            device: 'cpu' or 'cuda'
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. RL optimization will be limited.")
            self.agent = None
            self.env = None
            return

        # Create environment
        self.env = SegmentationEnvironment(
            network_topology, traffic_data, security_requirements
        )

        # Create agent
        if agent_type == 'dqn':
            self.agent = DQNAgent(
                state_dim=self.env.state_dim,
                action_dim=self.env.action_dim,
                device=device
            )
        else:
            # Future: implement policy gradient
            raise NotImplementedError("Policy gradient not yet implemented")

        self.device = device

        logger.info(f"RL Segmentation Optimizer initialized (agent: {agent_type})")

    def train(
        self,
        num_episodes: int = 1000,
        max_steps_per_episode: int = 100,
        batch_size: int = 64,
        target_update_freq: int = 10,
        checkpoint_path: str = './models/rl_agent.pt'
    ) -> Dict:
        """
        Train RL agent

        Args:
            num_episodes: Number of training episodes
            max_steps_per_episode: Maximum steps per episode
            batch_size: Batch size for updates
            target_update_freq: Frequency to update target network
            checkpoint_path: Path to save checkpoints

        Returns:
            Training history
        """
        if not TORCH_AVAILABLE or self.agent is None:
            logger.warning("RL agent not available")
            return {}

        logger.info(f"Training RL agent for {num_episodes} episodes...")

        for episode in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0
            episode_length = 0

            for step in range(max_steps_per_episode):
                # Select action
                action = self.agent.select_action(state)

                # Execute action
                next_state, reward, done, info = self.env.step(action)

                # Store experience
                self.agent.store_experience(state, action, reward, next_state, done)

                # Update agent
                loss = self.agent.update(batch_size)

                # Update metrics
                episode_reward += reward
                episode_length += 1

                state = next_state

                if done:
                    break

            # Update target network
            if episode % target_update_freq == 0:
                self.agent.update_target_network()

            # Decay epsilon
            self.agent.decay_epsilon()

            # Record episode
            self.agent.training_history['episode_rewards'].append(episode_reward)
            self.agent.training_history['episode_lengths'].append(episode_length)
            self.agent.training_history['epsilon'].append(self.agent.epsilon)

            # Logging
            if episode % 50 == 0:
                avg_reward = np.mean(self.agent.training_history['episode_rewards'][-50:])
                logger.info(
                    f"  Episode {episode}: avg_reward={avg_reward:.2f}, "
                    f"epsilon={self.agent.epsilon:.3f}"
                )

            # Save checkpoint
            if episode % 100 == 0 and episode > 0:
                self.agent.save(checkpoint_path)

        logger.info("Training complete!")

        return self.agent.training_history

    def optimize_segmentation(self) -> Dict:
        """
        Find optimal segmentation using trained agent

        Returns:
            Optimal segmentation policy
        """
        if not TORCH_AVAILABLE or self.agent is None:
            logger.warning("RL agent not available")
            return {}

        logger.info("Finding optimal segmentation...")

        state = self.env.reset()

        # Run greedy policy
        for _ in range(100):  # Max steps
            action = self.agent.select_action(state, eval_mode=True)
            next_state, reward, done, info = self.env.step(action)
            state = next_state

            if done:
                break

        # Get final segmentation
        optimal_segmentation = {
            'zone_assignments': self.env.current_segmentation,
            'security_score': info['security_score'],
            'performance_score': info['performance_score'],
            'complexity_score': info['complexity_score']
        }

        logger.info(
            f"Optimal segmentation found: security={info['security_score']:.2f}, "
            f"performance={info['performance_score']:.2f}, "
            f"complexity={info['complexity_score']:.2f}"
        )

        return optimal_segmentation

    def export_policy(self, output_path: str):
        """Export learned policy"""
        if not TORCH_AVAILABLE or self.agent is None:
            logger.warning("RL agent not available")
            return

        optimal_seg = self.optimize_segmentation()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimal_seg, f, indent=2)

        logger.info(f"Policy exported to {output_path}")
