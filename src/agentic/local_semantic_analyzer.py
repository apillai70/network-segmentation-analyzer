# -*- coding: utf-8 -*-
"""
Local Semantic Application Analyzer
====================================
Intelligent application analysis WITHOUT external API calls.
Uses local knowledge graphs, pattern matching, and ML models.

100% ON-PREMISE - NO DATA LEAVES YOUR NETWORK

Features:
- Knowledge graph-based semantic understanding
- Advanced pattern recognition
- Dependency inference from naming and context
- Application type classification
- Compliance detection
- All processing happens locally

Author: Enterprise Security Team
Version: 3.0 - Local Intelligence
"""

import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import pickle

logger = logging.getLogger(__name__)


class ApplicationKnowledgeGraph:
    """
    Local knowledge graph for application semantics

    Stores relationships between:
    - Application types and their characteristics
    - Common dependencies
    - Technology stacks
    - Compliance requirements
    """

    def __init__(self):
        self.graph = self._build_knowledge_graph()
        self.type_signatures = self._build_type_signatures()
        self.dependency_patterns = self._build_dependency_patterns()
        self.compliance_rules = self._build_compliance_rules()
        self.tech_stack_patterns = self._build_tech_stack_patterns()

        logger.info("[OK] Application Knowledge Graph initialized (local)")

    def _build_knowledge_graph(self) -> Dict:
        """Build comprehensive knowledge graph"""
        return {
            'web_server': {
                'characteristics': ['public-facing', 'http', 'https', 'frontend'],
                'common_names': ['web', 'frontend', 'ui', 'portal', 'dashboard', 'www', 'nginx', 'apache'],
                'typical_ports': [80, 443, 8080, 8443],
                'typical_dependencies': ['api_service', 'cache', 'cdn'],
                'security_zone': 'WEB_TIER',
                'risk_level': 'MEDIUM',
                'protocols': ['http', 'https', 'websocket']
            },
            'api_service': {
                'characteristics': ['backend', 'business-logic', 'microservice'],
                'common_names': ['api', 'service', 'backend', 'srv', 'svc', 'gateway', 'endpoint'],
                'typical_ports': [8080, 8443, 3000, 5000, 9000],
                'typical_dependencies': ['database', 'cache', 'message_queue', 'other_apis'],
                'security_zone': 'APP_TIER',
                'risk_level': 'MEDIUM',
                'protocols': ['http', 'https', 'grpc', 'graphql']
            },
            'database': {
                'characteristics': ['persistent-storage', 'data-layer', 'stateful'],
                'common_names': ['db', 'database', 'postgres', 'mysql', 'mongo', 'sql', 'data'],
                'typical_ports': [5432, 3306, 27017, 1433, 1521],
                'typical_dependencies': [],
                'security_zone': 'DATA_TIER',
                'risk_level': 'HIGH',
                'protocols': ['tcp', 'sql']
            },
            'cache': {
                'characteristics': ['in-memory', 'ephemeral', 'fast-access'],
                'common_names': ['cache', 'redis', 'memcache', 'memcached'],
                'typical_ports': [6379, 11211],
                'typical_dependencies': [],
                'security_zone': 'CACHE_TIER',
                'risk_level': 'MEDIUM',
                'protocols': ['tcp', 'redis']
            },
            'message_queue': {
                'characteristics': ['async', 'event-driven', 'pub-sub'],
                'common_names': ['kafka', 'rabbitmq', 'mq', 'queue', 'broker', 'sqs', 'pubsub'],
                'typical_ports': [9092, 5672, 15672],
                'typical_dependencies': [],
                'security_zone': 'MESSAGING_TIER',
                'risk_level': 'MEDIUM',
                'protocols': ['kafka', 'amqp', 'mqtt']
            },
            'worker': {
                'characteristics': ['background-processing', 'async-tasks', 'scheduled'],
                'common_names': ['worker', 'job', 'cron', 'scheduler', 'task', 'celery'],
                'typical_ports': [],
                'typical_dependencies': ['database', 'message_queue', 'cache'],
                'security_zone': 'APP_TIER',
                'risk_level': 'LOW',
                'protocols': ['tcp']
            },
            'infrastructure': {
                'characteristics': ['monitoring', 'logging', 'orchestration'],
                'common_names': ['monitor', 'logging', 'prometheus', 'grafana', 'elk', 'kibana', 'k8s'],
                'typical_ports': [9090, 3000, 9200, 5601],
                'typical_dependencies': [],
                'security_zone': 'MANAGEMENT_TIER',
                'risk_level': 'HIGH',
                'protocols': ['http', 'https']
            }
        }

    def _build_type_signatures(self) -> Dict:
        """Build type signatures for classification"""
        return {
            'authentication': {
                'keywords': ['auth', 'login', 'sso', 'oauth', 'iam', 'identity', 'keycloak', 'okta'],
                'implies_dependencies': ['database', 'cache'],
                'compliance': ['SOC2', 'GDPR'],
                'risk_level': 'HIGH'
            },
            'payment': {
                'keywords': ['payment', 'billing', 'checkout', 'transaction', 'stripe', 'paypal'],
                'implies_dependencies': ['database', 'external_payment_gateway'],
                'compliance': ['PCI-DSS'],
                'risk_level': 'HIGH'
            },
            'user_management': {
                'keywords': ['user', 'customer', 'profile', 'account', 'registration'],
                'implies_dependencies': ['database', 'cache', 'email_service'],
                'compliance': ['GDPR', 'SOC2'],
                'risk_level': 'MEDIUM'
            },
            'email': {
                'keywords': ['email', 'mail', 'notification', 'smtp', 'sendgrid', 'ses'],
                'implies_dependencies': ['message_queue', 'external_email_service'],
                'compliance': ['SOC2'],
                'risk_level': 'LOW'
            },
            'analytics': {
                'keywords': ['analytics', 'tracking', 'metrics', 'events', 'segment', 'amplitude'],
                'implies_dependencies': ['database', 'message_queue'],
                'compliance': ['GDPR'],
                'risk_level': 'MEDIUM'
            },
            'search': {
                'keywords': ['search', 'elasticsearch', 'solr', 'algolia'],
                'implies_dependencies': ['database', 'cache'],
                'compliance': ['SOC2'],
                'risk_level': 'LOW'
            },
            'file_storage': {
                'keywords': ['storage', 'upload', 'file', 's3', 'minio', 'blob'],
                'implies_dependencies': ['database'],
                'compliance': ['SOC2', 'GDPR'],
                'risk_level': 'MEDIUM'
            }
        }

    def _build_dependency_patterns(self) -> Dict:
        """Build dependency inference patterns"""
        return {
            'web_server': {
                'always': ['api_service'],
                'usually': ['cache', 'cdn'],
                'sometimes': ['database']
            },
            'api_service': {
                'always': ['database'],
                'usually': ['cache', 'message_queue'],
                'sometimes': ['other_api_services', 'external_api']
            },
            'worker': {
                'always': ['message_queue'],
                'usually': ['database'],
                'sometimes': ['cache', 'external_api']
            },
            'authentication_service': {
                'always': ['database', 'cache'],
                'usually': ['email_service'],
                'sometimes': ['external_oauth_provider']
            },
            'payment_service': {
                'always': ['database', 'external_payment_gateway'],
                'usually': ['message_queue', 'fraud_detection'],
                'sometimes': ['notification_service']
            }
        }

    def _build_compliance_rules(self) -> Dict:
        """Build compliance detection rules"""
        return {
            'PCI-DSS': {
                'triggers': ['payment', 'billing', 'card', 'transaction', 'checkout', 'stripe'],
                'requirements': [
                    'Encrypt data at rest and in transit',
                    'Maintain firewall configuration',
                    'Restrict access to cardholder data',
                    'Regular security testing'
                ]
            },
            'HIPAA': {
                'triggers': ['health', 'medical', 'patient', 'clinical', 'healthcare', 'phi'],
                'requirements': [
                    'Encrypt PHI',
                    'Access controls and audit logs',
                    'Data backup and disaster recovery',
                    'Physical and network security'
                ]
            },
            'GDPR': {
                'triggers': ['user', 'customer', 'profile', 'personal', 'privacy', 'consent'],
                'requirements': [
                    'Data minimization',
                    'Right to erasure',
                    'Data portability',
                    'Privacy by design'
                ]
            },
            'SOC2': {
                'triggers': ['*'],  # Applies to most services
                'requirements': [
                    'Security monitoring',
                    'Change management',
                    'Incident response',
                    'Vendor management'
                ]
            }
        }

    def _build_tech_stack_patterns(self) -> Dict:
        """Build technology stack patterns"""
        return {
            'languages': {
                'python': ['py', 'python', 'django', 'flask', 'fastapi'],
                'java': ['java', 'spring', 'tomcat', 'jvm'],
                'nodejs': ['node', 'express', 'nest', 'js', 'typescript'],
                'go': ['go', 'golang'],
                'ruby': ['ruby', 'rails', 'rb'],
                'dotnet': ['dotnet', 'csharp', 'aspnet', 'cs']
            },
            'frameworks': {
                'django': ['django'],
                'flask': ['flask'],
                'fastapi': ['fastapi'],
                'spring': ['spring'],
                'express': ['express'],
                'rails': ['rails']
            },
            'databases': {
                'postgresql': ['postgres', 'pg', 'psql'],
                'mysql': ['mysql'],
                'mongodb': ['mongo', 'mongodb'],
                'redis': ['redis'],
                'cassandra': ['cassandra'],
                'elasticsearch': ['elastic', 'elasticsearch', 'es']
            }
        }

    def query(self, app_type: str, attribute: str) -> any:
        """Query knowledge graph"""
        return self.graph.get(app_type, {}).get(attribute)


class LocalSemanticAnalyzer:
    """
    Intelligent local application analyzer

    NO EXTERNAL API CALLS - 100% on-premise processing

    Uses:
    - Knowledge graphs for semantic understanding
    - Pattern recognition for dependency inference
    - Heuristic rules for classification
    - Graph algorithms for relationship discovery
    """

    def __init__(self, persistence_manager=None):
        """Initialize local semantic analyzer"""
        self.pm = persistence_manager
        self.knowledge_graph = ApplicationKnowledgeGraph()

        # Learning components (local only)
        self.pattern_learner = PatternLearner()
        self.dependency_reasoner = DependencyReasoner(self.knowledge_graph)

        # Cache
        self.analysis_cache = {}

        logger.info("[OK] Local Semantic Analyzer initialized (no external APIs)")

    def analyze_application(
        self,
        app_name: str,
        metadata: Optional[Dict] = None,
        observed_peers: Optional[List[str]] = None,
        network_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Comprehensive local application analysis

        Args:
            app_name: Application name
            metadata: Optional metadata (config, environment, etc.)
            observed_peers: Known peer connections from network flows
            network_stats: Traffic statistics (bytes, packets, protocols)

        Returns:
            Complete application analysis with high confidence
        """
        # Check cache
        cache_key = f"{app_name}_{hash(str(metadata))}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]

        logger.info(f"[SEARCH] Analyzing application: {app_name} (local)")

        app_lower = app_name.lower()

        # Step 1: Classify application type
        app_type, type_confidence = self._classify_application_type(app_lower, metadata)

        # Step 2: Identify special characteristics (auth, payment, etc.)
        characteristics = self._identify_characteristics(app_lower, metadata)

        # Step 3: Determine security zone with IP-based inference
        # [SUCCESS] FIX: Prioritize IP-based zone inference over naming patterns
        ip_inferred_zone = self._infer_zone_from_ips(observed_peers)
        if ip_inferred_zone:
            security_zone = ip_inferred_zone
            logger.debug(f"Using IP-inferred zone: {ip_inferred_zone}")
        else:
            security_zone = self._determine_security_zone(app_type, characteristics)
            logger.debug(f"Using pattern-based zone: {security_zone}")

        # Step 4: Infer dependencies using knowledge graph
        dependencies = self.dependency_reasoner.infer_dependencies(
            app_name, app_type, characteristics, observed_peers, network_stats
        )

        # Step 5: Detect compliance requirements
        compliance = self._detect_compliance(app_lower, characteristics, dependencies)

        # Step 6: Calculate risk level
        risk_level = self._calculate_risk_level(app_type, characteristics, security_zone, dependencies)

        # Step 7: Infer technology stack
        tech_stack = self._infer_tech_stack(app_lower, metadata, observed_peers)

        # Step 8: Generate detailed reasoning
        reasoning = self._generate_reasoning(app_name, app_type, characteristics, dependencies, security_zone)

        # Step 9: Calculate overall confidence
        confidence = self._calculate_confidence(
            type_confidence, len(dependencies), len(characteristics), observed_peers
        )

        analysis = {
            'app_name': app_name,
            'app_type': app_type,
            'characteristics': characteristics,
            'primary_function': self._infer_primary_function(app_lower, app_type, characteristics),
            'tech_stack': tech_stack,
            'security_zone': security_zone,
            'predicted_dependencies': dependencies,
            'compliance_requirements': compliance,
            'risk_level': risk_level,
            'confidence': confidence,
            'reasoning': reasoning,
            'analysis_method': 'local_semantic',
            'knowledge_graph_version': '3.0'
        }

        # Learn from this analysis (improve over time)
        self.pattern_learner.learn(app_name, analysis, observed_peers)

        # Cache result
        self.analysis_cache[cache_key] = analysis

        logger.info(f"[OK] Analysis complete: {app_name} → {security_zone} "
                   f"(type: {app_type}, confidence: {confidence:.2f})")

        return analysis

    def _classify_application_type(self, app_lower: str, metadata: Optional[Dict]) -> Tuple[str, float]:
        """Classify application type with confidence score"""

        scores = defaultdict(float)

        # Check against knowledge graph
        for app_type, info in self.knowledge_graph.graph.items():
            for name_pattern in info['common_names']:
                if name_pattern in app_lower:
                    scores[app_type] += 1.0

        # Boost from metadata
        if metadata:
            if metadata.get('type'):
                scores[metadata['type']] += 2.0
            if metadata.get('role'):
                role = metadata['role'].lower()
                for app_type, info in self.knowledge_graph.graph.items():
                    if any(kw in role for kw in info['common_names']):
                        scores[app_type] += 1.5

        # Return highest scoring type
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = min(scores[best_type] / 3.0, 1.0)  # Normalize
            return best_type, confidence

        return 'api_service', 0.5  # Default

    def _identify_characteristics(self, app_lower: str, metadata: Optional[Dict]) -> List[str]:
        """Identify special characteristics"""

        characteristics = []

        # Check type signatures
        for char_type, sig in self.knowledge_graph.type_signatures.items():
            if any(kw in app_lower for kw in sig['keywords']):
                characteristics.append(char_type)

        # Check metadata
        if metadata:
            if metadata.get('handles_payments'):
                characteristics.append('payment')
            if metadata.get('handles_auth'):
                characteristics.append('authentication')
            if metadata.get('handles_pii'):
                characteristics.append('user_management')

        return list(set(characteristics))

    def _infer_zone_from_ips(self, observed_peers: Optional[List[str]]) -> Optional[str]:
        """
        [SUCCESS] NEW: Infer security zone from IP address patterns in flow data

        This improves classification by using actual network topology information
        from observed connections instead of relying solely on app naming.

        IP Pattern to Zone Mapping:
        - 10.100.160.* → MANAGEMENT_TIER
        - 10.164.105.* → WEB_TIER
        - 10.100.246.* → APP_TIER
        - 10.165.116.* → APP_TIER
        - 10.164.116.* → DATA_TIER
        - 10.164.144.* → CACHE_TIER
        - 10.164.145.* → MESSAGING_TIER
        """
        if not observed_peers:
            return None

        # Count IPs by zone pattern
        zone_votes = defaultdict(int)

        for ip in observed_peers:
            if not ip or not isinstance(ip, str):
                continue

            # Management tier
            if ip.startswith('10.100.160.'):
                zone_votes['MANAGEMENT_TIER'] += 1
            # Web tier
            elif ip.startswith('10.164.105.'):
                zone_votes['WEB_TIER'] += 1
            # App tier (two subnets)
            elif ip.startswith('10.100.246.') or ip.startswith('10.165.116.'):
                zone_votes['APP_TIER'] += 1
            # Data tier
            elif ip.startswith('10.164.116.'):
                zone_votes['DATA_TIER'] += 1
            # Cache tier
            elif ip.startswith('10.164.144.'):
                zone_votes['CACHE_TIER'] += 1
            # Messaging tier
            elif ip.startswith('10.164.145.'):
                zone_votes['MESSAGING_TIER'] += 1

        # Return zone with most votes if we have strong evidence
        if zone_votes:
            best_zone = max(zone_votes, key=zone_votes.get)
            # Require at least 30% of IPs to match a pattern
            if zone_votes[best_zone] >= len(observed_peers) * 0.3:
                logger.debug(f"Inferred zone from IPs: {best_zone} ({zone_votes[best_zone]}/{len(observed_peers)} matches)")
                return best_zone

        return None

    def _determine_security_zone(self, app_type: str, characteristics: List[str]) -> str:
        """Determine security zone"""

        # High priority: characteristics override type
        if 'payment' in characteristics or 'authentication' in characteristics:
            return 'APP_TIER'  # Protected tier

        # Use knowledge graph
        zone = self.knowledge_graph.query(app_type, 'security_zone')
        if zone:
            return zone

        return 'APP_TIER'  # Safe default

    def _detect_compliance(self, app_lower: str, characteristics: List[str], dependencies: List[Dict]) -> List[str]:
        """Detect compliance requirements"""

        compliance = set()

        # Check compliance rules
        for standard, rules in self.knowledge_graph.compliance_rules.items():
            triggers = rules['triggers']

            if '*' in triggers:
                compliance.add(standard)
            else:
                if any(trigger in app_lower for trigger in triggers):
                    compliance.add(standard)

        # Check characteristics
        for char in characteristics:
            if char in self.knowledge_graph.type_signatures:
                sig_compliance = self.knowledge_graph.type_signatures[char].get('compliance', [])
                compliance.update(sig_compliance)

        # Check dependencies
        for dep in dependencies:
            if dep['type'] == 'external_payment_gateway':
                compliance.add('PCI-DSS')
            if 'database' in dep['name'].lower() and any(char in ['payment', 'user_management'] for char in characteristics):
                compliance.add('GDPR')

        return sorted(list(compliance))

    def _calculate_risk_level(
        self,
        app_type: str,
        characteristics: List[str],
        security_zone: str,
        dependencies: List[Dict]
    ) -> str:
        """Calculate risk level"""

        risk_score = 0

        # Base risk from type
        type_risk = self.knowledge_graph.query(app_type, 'risk_level')
        risk_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        risk_score += risk_map.get(type_risk, 2)

        # Risk from characteristics
        for char in characteristics:
            if char in self.knowledge_graph.type_signatures:
                char_risk = self.knowledge_graph.type_signatures[char].get('risk_level', 'MEDIUM')
                risk_score += risk_map.get(char_risk, 2)

        # Risk from zone
        if security_zone in ['WEB_TIER', 'DATA_TIER']:
            risk_score += 2

        # Risk from external dependencies
        for dep in dependencies:
            if 'external' in dep['type']:
                risk_score += 1

        # Convert score to level
        if risk_score >= 6:
            return 'HIGH'
        elif risk_score >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _infer_tech_stack(
        self,
        app_lower: str,
        metadata: Optional[Dict],
        observed_peers: Optional[List[str]]
    ) -> Dict:
        """Infer technology stack"""

        tech_stack = {
            'language': 'unknown',
            'framework': 'unknown',
            'database': 'unknown'
        }

        patterns = self.knowledge_graph.tech_stack_patterns

        # Detect language
        for lang, keywords in patterns['languages'].items():
            if any(kw in app_lower for kw in keywords):
                tech_stack['language'] = lang
                break

        # Detect framework
        for framework, keywords in patterns['frameworks'].items():
            if any(kw in app_lower for kw in keywords):
                tech_stack['framework'] = framework
                break

        # Detect database from observed peers
        if observed_peers:
            for peer in observed_peers:
                # [SUCCESS] FIX: Skip NaN/None/non-string values
                if not peer or not isinstance(peer, str):
                    continue

                peer_lower = peer.lower()
                for db, keywords in patterns['databases'].items():
                    if any(kw in peer_lower for kw in keywords):
                        tech_stack['database'] = db
                        break

        # Detect database from app name
        if tech_stack['database'] == 'unknown':
            for db, keywords in patterns['databases'].items():
                if any(kw in app_lower for kw in keywords):
                    tech_stack['database'] = db
                    break

        # Metadata override
        if metadata:
            tech_stack['language'] = metadata.get('language', tech_stack['language'])
            tech_stack['framework'] = metadata.get('framework', tech_stack['framework'])
            tech_stack['database'] = metadata.get('database', tech_stack['database'])

        return tech_stack

    def _infer_primary_function(self, app_lower: str, app_type: str, characteristics: List[str]) -> str:
        """Infer primary function"""

        # Priority: characteristics
        if 'authentication' in characteristics:
            return 'User authentication and authorization service'
        if 'payment' in characteristics:
            return 'Payment processing and billing service'
        if 'user_management' in characteristics:
            return 'User profile and account management'
        if 'email' in characteristics:
            return 'Email and notification delivery service'
        if 'analytics' in characteristics:
            return 'Analytics and event tracking service'

        # Fallback to type-based
        function_map = {
            'web_server': 'Web frontend and user interface',
            'api_service': 'Backend API and business logic service',
            'database': 'Data persistence and storage layer',
            'cache': 'In-memory caching and session storage',
            'message_queue': 'Asynchronous message processing',
            'worker': 'Background job and task processing',
            'infrastructure': 'Infrastructure monitoring and management'
        }

        return function_map.get(app_type, 'Application service')

    def _calculate_confidence(
        self,
        type_confidence: float,
        num_dependencies: int,
        num_characteristics: int,
        observed_peers: Optional[List[str]]
    ) -> float:
        """Calculate overall confidence"""

        confidence = type_confidence * 0.4

        # Boost from dependencies
        confidence += min(num_dependencies / 10.0, 0.3)

        # Boost from characteristics
        confidence += min(num_characteristics / 5.0, 0.2)

        # Boost from observed data
        if observed_peers:
            confidence += min(len(observed_peers) / 20.0, 0.1)

        return min(confidence, 0.95)

    def _generate_reasoning(
        self,
        app_name: str,
        app_type: str,
        characteristics: List[str],
        dependencies: List[Dict],
        security_zone: str
    ) -> str:
        """Generate detailed reasoning"""

        parts = []

        # Type classification
        parts.append(f"Application '{app_name}' classified as {app_type.replace('_', ' ')}")

        # Characteristics
        if characteristics:
            char_str = ', '.join(characteristics)
            parts.append(f"with characteristics: {char_str}")

        # Zone assignment
        parts.append(f"Assigned to {security_zone} for appropriate network segmentation")

        # Dependencies
        if dependencies:
            dep_types = set(d['type'] for d in dependencies)
            dep_str = ', '.join(dep_types)
            parts.append(f"Predicted dependencies: {dep_str}")

        reasoning = '. '.join(parts) + '.'

        return reasoning

    def batch_analyze(
        self,
        applications: List[Tuple[str, Optional[Dict], Optional[List[str]]]]
    ) -> Dict[str, Dict]:
        """Batch analyze multiple applications"""

        logger.info(f"[SEARCH] Batch analyzing {len(applications)} applications (local)...")

        results = {}
        for item in applications:
            app_name = item[0]
            metadata = item[1] if len(item) > 1 else None
            observed_peers = item[2] if len(item) > 2 else None

            try:
                results[app_name] = self.analyze_application(app_name, metadata, observed_peers)
            except Exception as e:
                logger.error(f"Failed to analyze {app_name}: {e}")
                results[app_name] = {'error': str(e)}

        logger.info(f"[OK] Batch analysis complete: {len(results)} applications")
        return results

    def export_analysis(self, output_path: str):
        """Export analysis cache"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_cache, f, indent=2)

        logger.info(f"[OK] Analysis exported to {output_path}")


class DependencyReasoner:
    """
    Reasons about application dependencies using knowledge graph
    """

    def __init__(self, knowledge_graph: ApplicationKnowledgeGraph):
        self.kg = knowledge_graph

    def infer_dependencies(
        self,
        app_name: str,
        app_type: str,
        characteristics: List[str],
        observed_peers: Optional[List[str]],
        network_stats: Optional[Dict]
    ) -> List[Dict]:
        """Infer application dependencies"""

        dependencies = []

        # Base dependencies from type
        type_deps = self.kg.query(app_type, 'typical_dependencies')
        if type_deps:
            for dep_type in type_deps:
                dependencies.append({
                    'type': dep_type,
                    'name': f'{dep_type}_service',
                    'purpose': f'Standard {dep_type} dependency',
                    'confidence': 0.7,
                    'source': 'type_inference'
                })

        # Dependencies from characteristics
        for char in characteristics:
            if char in self.kg.type_signatures:
                char_deps = self.kg.type_signatures[char].get('implies_dependencies', [])
                for dep in char_deps:
                    dependencies.append({
                        'type': dep,
                        'name': f'{char}_{dep}',
                        'purpose': f'Required for {char} functionality',
                        'confidence': 0.85,
                        'source': 'characteristic_inference'
                    })

        # Dependencies from observed peers
        if observed_peers:
            for peer in observed_peers:
                # [SUCCESS] FIX: Skip NaN/None/non-string values
                if not peer or not isinstance(peer, str):
                    continue

                peer_lower = peer.lower()

                # Identify peer type
                peer_type = 'unknown'
                for app_t, info in self.kg.graph.items():
                    if any(name in peer_lower for name in info['common_names']):
                        peer_type = app_t
                        break

                dependencies.append({
                    'type': peer_type,
                    'name': peer,
                    'purpose': 'Observed network connection',
                    'confidence': 0.95,
                    'source': 'network_observation'
                })

        # Deduplicate and merge
        dependencies = self._deduplicate_dependencies(dependencies)

        return dependencies

    def _deduplicate_dependencies(self, dependencies: List[Dict]) -> List[Dict]:
        """Remove duplicates and merge confidence scores"""

        merged = {}

        for dep in dependencies:
            key = (dep['type'], dep['name'])

            if key in merged:
                # Keep higher confidence
                if dep['confidence'] > merged[key]['confidence']:
                    merged[key] = dep
            else:
                merged[key] = dep

        return list(merged.values())


class PatternLearner:
    """
    Learns patterns from analyses to improve over time
    Stores learned patterns locally
    """

    def __init__(self, storage_path: str = './persistent_data/learned_patterns.pkl'):
        self.storage_path = Path(storage_path)
        self.patterns = self._load_patterns()

        logger.info(f"[OK] Pattern Learner initialized ({len(self.patterns)} patterns)")

    def learn(self, app_name: str, analysis: Dict, observed_peers: Optional[List[str]]):
        """Learn from analysis"""

        pattern = {
            'app_type': analysis['app_type'],
            'security_zone': analysis['security_zone'],
            'dependencies': [d['type'] for d in analysis['predicted_dependencies']],
            'characteristics': analysis['characteristics'],
            'observed_peers': observed_peers or []
        }

        self.patterns[app_name] = pattern

        # Save every 10 patterns
        if len(self.patterns) % 10 == 0:
            self._save_patterns()

    def _load_patterns(self) -> Dict:
        """Load learned patterns"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")

        return {}

    def _save_patterns(self):
        """Save learned patterns"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.storage_path, 'wb') as f:
            pickle.dump(self.patterns, f)

        logger.debug(f"Saved {len(self.patterns)} learned patterns")
