"""
Network Threat Surface Analyzer
================================
Analyzes attack paths, exposure points, and threat surface area
without requiring a Graph Database.

Features:
- Attack path discovery (Internet → Critical Assets)
- Exposure scoring for all nodes
- What-if scenario analysis
- Threat surface reduction recommendations
- Attack chain visualization

Author: Network Security Team
Version: 1.0
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class ThreatSurfaceAnalyzer:
    """
    Analyzes network threat surface using graph analysis
    Identifies attack paths and provides mitigation recommendations
    """

    # Tier risk scores (1-10 scale)
    TIER_RISK_SCORES = {
        'WEB': 8,              # High risk (internet-facing)
        'LOADBALANCER': 9,     # Very high (entry point)
        'APP': 5,              # Medium (internal logic)
        'DATABASE': 10,        # Critical (data at rest)
        'CACHE': 4,            # Medium-low (temporary data)
        'QUEUE': 6,            # Medium (message passing)
        'MANAGEMENT': 7,       # High (admin access)
        'UNKNOWN': 3           # Low (unclassified)
    }

    # Critical asset types (highest priority to protect)
    CRITICAL_TIERS = {'DATABASE', 'QUEUE', 'MANAGEMENT'}

    # External-facing tiers (entry points for attacks)
    EXTERNAL_TIERS = {'WEB', 'LOADBALANCER'}

    def __init__(self, graph_analyzer):
        """
        Initialize with GraphAnalyzer instance

        Args:
            graph_analyzer: GraphAnalyzer with network flow data
        """
        self.analyzer = graph_analyzer
        self.attack_paths = []
        self.exposure_scores = {}
        self.threat_scores = {}

        logger.info("ThreatSurfaceAnalyzer initialized")

    def analyze_attack_surface(self) -> Dict:
        """
        Perform comprehensive threat surface analysis

        Returns:
            Dict with all analysis results
        """
        logger.info("Starting comprehensive threat surface analysis...")

        results = {
            'attack_paths': self._discover_attack_paths(),
            'exposure_analysis': self._analyze_exposure(),
            'threat_scores': self._calculate_threat_scores(),
            'critical_chokepoints': self._identify_chokepoints(),
            'mitigation_recommendations': self._generate_mitigations(),
            'summary': {}
        }

        # Generate summary
        results['summary'] = {
            'total_attack_paths': len(results['attack_paths']),
            'exposed_nodes': len([s for s in results['exposure_analysis'].values() if s['exposure_level'] == 'HIGH']),
            'critical_assets_at_risk': len([p for p in results['attack_paths'] if p['target_tier'] in self.CRITICAL_TIERS]),
            'avg_attack_distance': sum(p['path_length'] for p in results['attack_paths']) / max(len(results['attack_paths']), 1),
            'high_threat_nodes': len([s for s in results['threat_scores'].values() if s >= 7.0])
        }

        logger.info(f"  [OK] Analysis complete: {results['summary']['total_attack_paths']} attack paths found")
        return results

    def _discover_attack_paths(self) -> List[Dict]:
        """
        Discover all attack paths from external nodes to critical assets

        Returns:
            List of attack path dictionaries
        """
        logger.info("  Discovering attack paths (Internet → Critical Assets)...")

        attack_paths = []

        # Identify external-facing nodes
        external_nodes = []
        for ip in self.analyzer.graph.nodes():
            tier = self.analyzer._classify_node_tier(ip)
            is_internal = self.analyzer.node_metadata.get(ip, {}).get('is_internal', True)

            if tier in self.EXTERNAL_TIERS or not is_internal:
                external_nodes.append(ip)

        # Identify critical assets
        critical_nodes = []
        for ip in self.analyzer.graph.nodes():
            tier = self.analyzer._classify_node_tier(ip)
            if tier in self.CRITICAL_TIERS:
                critical_nodes.append(ip)

        logger.info(f"    Found {len(external_nodes)} external nodes, {len(critical_nodes)} critical assets")

        # Find all paths from external → critical
        for ext_ip in external_nodes[:50]:  # Limit to avoid timeout
            for crit_ip in critical_nodes[:20]:
                paths = self.analyzer.find_all_paths(ext_ip, crit_ip, max_depth=6)

                for path in paths[:10]:  # Limit paths per pair
                    attack_paths.append({
                        'source': ext_ip,
                        'source_tier': self.analyzer._classify_node_tier(ext_ip),
                        'target': crit_ip,
                        'target_tier': self.analyzer._classify_node_tier(crit_ip),
                        'path': path,
                        'path_length': len(path) - 1,
                        'risk_level': self._assess_path_risk(path),
                        'attack_vector': self._identify_attack_vector(path)
                    })

        # Sort by risk
        attack_paths.sort(key=lambda x: (
            self.TIER_RISK_SCORES.get(x['target_tier'], 5),
            -x['path_length']  # Shorter paths = higher risk
        ), reverse=True)

        logger.info(f"    [OK] Discovered {len(attack_paths)} attack paths")
        return attack_paths

    def _analyze_exposure(self) -> Dict[str, Dict]:
        """
        Analyze exposure level for each node

        Returns:
            Dict mapping IP → exposure analysis
        """
        logger.info("  Analyzing node exposure levels...")

        exposure_analysis = {}

        for ip in self.analyzer.graph.nodes():
            tier = self.analyzer._classify_node_tier(ip)
            is_internal = self.analyzer.node_metadata.get(ip, {}).get('is_internal', True)

            # Calculate exposure factors
            in_degree = self.analyzer.graph.in_degree(ip)
            out_degree = self.analyzer.graph.out_degree(ip)

            # Check if directly accessible from external
            has_external_access = False
            for predecessor in self.analyzer.graph.predecessors(ip):
                pred_internal = self.analyzer.node_metadata.get(predecessor, {}).get('is_internal', True)
                if not pred_internal:
                    has_external_access = True
                    break

            # Calculate exposure score
            exposure_score = 0

            if not is_internal:
                exposure_score += 10  # External node = max exposure
            elif has_external_access:
                exposure_score += 7   # One hop from external
            elif tier in self.EXTERNAL_TIERS:
                exposure_score += 6   # Internet-facing tier

            # Add connectivity factor
            exposure_score += min(out_degree / 10, 3)  # Max +3 for connectivity

            # Determine exposure level
            if exposure_score >= 8:
                exposure_level = 'CRITICAL'
            elif exposure_score >= 6:
                exposure_level = 'HIGH'
            elif exposure_score >= 4:
                exposure_level = 'MEDIUM'
            else:
                exposure_level = 'LOW'

            exposure_analysis[ip] = {
                'exposure_score': round(exposure_score, 2),
                'exposure_level': exposure_level,
                'tier': tier,
                'is_internal': is_internal,
                'has_external_access': has_external_access,
                'in_degree': in_degree,
                'out_degree': out_degree
            }

        logger.info(f"    [OK] Analyzed exposure for {len(exposure_analysis)} nodes")
        return exposure_analysis

    def _calculate_threat_scores(self) -> Dict[str, float]:
        """
        Calculate comprehensive threat score for each node

        Returns:
            Dict mapping IP → threat score (0-10)
        """
        logger.info("  Calculating threat scores...")

        threat_scores = {}
        metrics = self.analyzer.calculate_centrality_metrics()

        for ip in self.analyzer.graph.nodes():
            tier = self.analyzer._classify_node_tier(ip)

            # Base score from tier
            base_score = self.TIER_RISK_SCORES.get(tier, 5)

            # Centrality multiplier (high betweenness = on many attack paths)
            centrality = metrics[ip]['betweenness_centrality']
            centrality_multiplier = 1 + (centrality * 10)

            # Exposure multiplier
            exposure_data = self.exposure_scores.get(ip, {})
            exposure_multiplier = 1 + (exposure_data.get('exposure_score', 0) / 20)

            # Calculate final score
            threat_score = base_score * centrality_multiplier * exposure_multiplier
            threat_score = min(threat_score, 10.0)  # Cap at 10

            threat_scores[ip] = round(threat_score, 2)

        logger.info(f"    [OK] Calculated threat scores for {len(threat_scores)} nodes")
        return threat_scores

    def _identify_chokepoints(self) -> List[Dict]:
        """
        Identify critical chokepoints (single points of failure/entry)

        Returns:
            List of chokepoint dictionaries
        """
        logger.info("  Identifying critical chokepoints...")

        chokepoints = []
        metrics = self.analyzer.calculate_centrality_metrics()

        # Find nodes with high betweenness (many paths pass through them)
        high_betweenness = sorted(
            [(ip, m['betweenness_centrality']) for ip, m in metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:20]

        for ip, betweenness in high_betweenness:
            if betweenness > 0.01:  # Significant chokepoint
                # Calculate impact of removing this node
                impact = self._calculate_removal_impact(ip)

                chokepoints.append({
                    'ip': ip,
                    'hostname': self.analyzer.node_metadata.get(ip, {}).get('hostname', ''),
                    'tier': self.analyzer._classify_node_tier(ip),
                    'betweenness': round(betweenness, 4),
                    'paths_blocked': impact['paths_blocked'],
                    'reduction_percentage': impact['reduction_percentage'],
                    'mitigation_priority': 'HIGH' if impact['reduction_percentage'] > 50 else 'MEDIUM'
                })

        logger.info(f"    [OK] Identified {len(chokepoints)} critical chokepoints")
        return chokepoints

    def _generate_mitigations(self) -> List[Dict]:
        """
        Generate mitigation recommendations

        Returns:
            List of mitigation dictionaries
        """
        logger.info("  Generating mitigation recommendations...")

        mitigations = []

        # Recommendation 1: Isolate high-risk external-facing nodes
        high_exposure = [ip for ip, data in self.exposure_scores.items()
                        if data['exposure_level'] in ['CRITICAL', 'HIGH']]

        if high_exposure:
            mitigations.append({
                'priority': 'HIGH',
                'category': 'Network Segmentation',
                'title': 'Isolate High-Exposure Nodes',
                'description': f'Isolate {len(high_exposure)} nodes with high external exposure',
                'affected_nodes': high_exposure[:10],
                'implementation': 'Add firewall rules to restrict inbound traffic to these nodes',
                'impact': f'Reduces attack surface by limiting entry points'
            })

        # Recommendation 2: Block direct external → critical asset paths
        direct_paths = [p for p in self.attack_paths if p['path_length'] <= 2]

        if direct_paths:
            mitigations.append({
                'priority': 'CRITICAL',
                'category': 'Access Control',
                'title': 'Block Direct External Access to Critical Assets',
                'description': f'Found {len(direct_paths)} direct paths from external to critical assets',
                'affected_nodes': list(set([p['target'] for p in direct_paths])),
                'implementation': 'Implement DMZ and require traffic to pass through application tier',
                'impact': f'Eliminates {len(direct_paths)} high-risk attack paths'
            })

        # Recommendation 3: Harden chokepoints
        critical_choke = [c for c in self._identify_chokepoints()
                         if c['mitigation_priority'] == 'HIGH']

        if critical_choke:
            mitigations.append({
                'priority': 'HIGH',
                'category': 'System Hardening',
                'title': 'Harden Critical Chokepoints',
                'description': f'Secure {len(critical_choke)} nodes that control access to many systems',
                'affected_nodes': [c['ip'] for c in critical_choke],
                'implementation': 'Enable MFA, restrict privileged access, implement IDS/IPS',
                'impact': f'Protects nodes that block {sum(c["paths_blocked"] for c in critical_choke)} attack paths'
            })

        # Recommendation 4: Add redundancy to single points of failure
        single_points = [c for c in self._identify_chokepoints()
                        if c['reduction_percentage'] > 80]

        if single_points:
            mitigations.append({
                'priority': 'MEDIUM',
                'category': 'Resilience',
                'title': 'Add Redundancy to Single Points of Failure',
                'description': f'Found {len(single_points)} nodes whose removal blocks >80% of attack paths',
                'affected_nodes': [c['ip'] for c in single_points],
                'implementation': 'Deploy redundant systems with load balancing',
                'impact': 'Improves both security (distributed attack surface) and availability'
            })

        logger.info(f"    [OK] Generated {len(mitigations)} mitigation recommendations")
        return mitigations

    def _assess_path_risk(self, path: List[str]) -> str:
        """Assess risk level of an attack path"""
        if len(path) <= 2:
            return 'CRITICAL'  # Direct access
        elif len(path) <= 3:
            return 'HIGH'      # One intermediary
        elif len(path) <= 4:
            return 'MEDIUM'    # Two intermediaries
        else:
            return 'LOW'       # Multiple hops

    def _identify_attack_vector(self, path: List[str]) -> str:
        """Identify attack vector type"""
        if len(path) < 2:
            return 'Unknown'

        source_tier = self.analyzer._classify_node_tier(path[0])
        target_tier = self.analyzer._classify_node_tier(path[-1])

        if source_tier in self.EXTERNAL_TIERS and target_tier == 'DATABASE':
            return 'External → Database (SQL Injection, Data Exfiltration)'
        elif source_tier in self.EXTERNAL_TIERS and target_tier == 'APP':
            return 'External → Application (Code Injection, RCE)'
        elif source_tier == 'WEB' and target_tier == 'MANAGEMENT':
            return 'Web → Management (Privilege Escalation)'
        else:
            return f'{source_tier} → {target_tier} (Lateral Movement)'

    def _calculate_removal_impact(self, node_ip: str) -> Dict:
        """Calculate impact of removing a node (what-if analysis)"""
        # Sample attack paths to estimate impact
        sample_external = list(self.analyzer.graph.nodes())[:10]
        sample_critical = [ip for ip in self.analyzer.graph.nodes()
                          if self.analyzer._classify_node_tier(ip) in self.CRITICAL_TIERS][:10]

        paths_before = 0
        paths_after = 0

        for ext in sample_external:
            for crit in sample_critical:
                paths = self.analyzer.find_all_paths(ext, crit, max_depth=5)
                paths_before += len(paths)

                # Count paths not using this node
                paths_filtered = [p for p in paths if node_ip not in p]
                paths_after += len(paths_filtered)

        paths_blocked = paths_before - paths_after
        reduction_pct = (paths_blocked / max(paths_before, 1)) * 100

        return {
            'paths_blocked': paths_blocked,
            'paths_before': paths_before,
            'paths_after': paths_after,
            'reduction_percentage': round(reduction_pct, 1)
        }

    def export_analysis(self, output_path: str):
        """
        Export threat surface analysis to JSON

        Args:
            output_path: Path to save JSON file
        """
        logger.info(f"Exporting threat surface analysis: {output_path}")

        results = self.analyze_attack_surface()

        # Convert to JSON-serializable format
        export_data = {
            'summary': results['summary'],
            'attack_paths': results['attack_paths'][:100],  # Limit for file size
            'high_exposure_nodes': [
                {'ip': ip, **data}
                for ip, data in results['exposure_analysis'].items()
                if data['exposure_level'] in ['CRITICAL', 'HIGH']
            ],
            'high_threat_nodes': [
                {'ip': ip, 'threat_score': score}
                for ip, score in results['threat_scores'].items()
                if score >= 7.0
            ],
            'chokepoints': results['critical_chokepoints'],
            'mitigations': results['mitigation_recommendations']
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"  [OK] Analysis exported: {output_path}")


if __name__ == '__main__':
    print("Threat Surface Analyzer - Use from main pipeline")
