#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Type Classifier
=====================
Classifies servers based on hostname patterns and protocols

Classification Rules:
- DNS Servers: ForestDNS, DomainDnsZones + LDAP/CIFS/DNS/Kerberos protocols
- Active Directory: microsoftazuread-sso.com, microsoftazuread in name
- Traffic Managers: vortex, trafficmanager in name
- Splunk: splnk in name
- ServiceNow: SNOW in name
- AWS: amazonaws.com domain
- CyberArk: cyberark in name
- F5 Load Balancers: f5 in name
- DB Auditor: dbauditor in name
- CIFS Servers: smb in name + CIFS protocol
- SSRS: SSRS in name + TDS protocol
- MySQL/Oracle: port 1521, TNS protocol, -vip.unix.rgbk.com pattern
- Mail Servers: mail in name + SMTP port 25
- Rapid7: rapid7 in name (cybersecurity)
- CDN: akamai, fastly.net, edgesuite.net domains
- Azure Traffic Manager: trafficmanager.net domain
"""

from typing import Dict, List, Optional, Set
import re


class ServerClassifier:
    """Classifies servers by type based on hostname and protocol patterns"""

    # Server type definitions with patterns and protocols
    SERVER_TYPES = {
        'DNS': {
            'name_patterns': ['forestdns', 'domaindnszones'],
            'protocols': ['DNS'],
            'ports': [53],
            'tier': 'infrastructure'
        },
        'LDAP Server': {
            'name_patterns': ['ldap'],
            'protocols': ['LDAP', 'Kerberos'],
            'ports': [389, 636, 3268, 3269],
            'tier': 'infrastructure'
        },
        'Active Directory': {
            'name_patterns': ['microsoftazuread-sso.com', 'microsoftazuread'],
            'protocols': ['LDAP', 'Kerberos', 'DNS'],
            'ports': [],
            'tier': 'infrastructure'
        },
        'Traffic Manager': {
            'name_patterns': ['vortex', 'trafficmanager'],
            'protocols': [],
            'ports': [],
            'tier': 'infrastructure'
        },
        'Splunk': {
            'name_patterns': ['splnk'],
            'protocols': [],
            'ports': [],
            'tier': 'app'
        },
        'ServiceNow': {
            'name_patterns': ['SNOW', 'snow'],
            'protocols': [],
            'ports': [],
            'tier': 'app'
        },
        'AWS': {
            'name_patterns': ['amazonaws.com'],
            'protocols': [],
            'ports': [],
            'tier': 'cloud'
        },
        'CyberArk': {
            'name_patterns': ['cyberark'],
            'protocols': [],
            'ports': [],
            'tier': 'security'
        },
        'F5 Load Balancer': {
            'name_patterns': ['f5'],
            'protocols': [],
            'ports': [],
            'tier': 'infrastructure'
        },
        'DB Auditor': {
            'name_patterns': ['dbauditor'],
            'protocols': [],
            'ports': [],
            'tier': 'security'
        },
        'CIFS Server': {
            'name_patterns': ['smb'],
            'protocols': ['CIFS', 'SMB'],
            'ports': [445],
            'tier': 'app'
        },
        'SSRS': {
            'name_patterns': ['SSRS', 'ssrs'],
            'protocols': ['TDS'],
            'ports': [1433],
            'tier': 'app'
        },
        'MySQL/Oracle': {
            'name_patterns': ['-vip.unix.rgbk.com', 'oracle', 'mysql'],
            'protocols': ['TNS'],
            'ports': [1521, 3306],
            'tier': 'database'
        },
        'Mail Server': {
            'name_patterns': ['mail'],
            'protocols': ['SMTP'],
            'ports': [25],
            'tier': 'app'
        },
        'Rapid7': {
            'name_patterns': ['rapid7'],
            'protocols': [],
            'ports': [],
            'tier': 'security'
        },
        'CDN': {
            'name_patterns': ['akamai', 'fastly.net', 'edgesuite.net'],
            'protocols': [],
            'ports': [],
            'tier': 'infrastructure'
        },
        'Azure Traffic Manager': {
            'name_patterns': ['trafficmanager.net'],
            'protocols': [],
            'ports': [],
            'tier': 'cloud'
        },
        'Azure Key Vault': {
            'name_patterns': ['privatelink.vaultcore.azure.net', 'vaultcore.azure.net', 'vault.azure.net'],
            'protocols': ['HTTPS'],
            'ports': [443],
            'tier': 'security'
        }
    }

    # Application tier classification based on protocols and ports
    APP_TIER_RULES = {
        'web': {
            'protocols': ['HTTP', 'HTTPS', 'SSL', 'TLS'],
            'ports': [80, 443, 8080, 8443]
        },
        'app': {
            'protocols': ['RPC', 'SOAP', 'REST', 'gRPC'],
            'ports': [8000, 8001, 8002, 8003, 8004, 8005, 8888, 9000]
        },
        'database': {
            'protocols': ['TDS', 'TNS', 'PostgreSQL', 'MySQL', 'MongoDB'],
            'ports': [1433, 1521, 3306, 5432, 27017]
        }
    }

    def __init__(self):
        """Initialize the server classifier"""
        pass

    def classify_server_type(self, hostname: str, protocols: List[str] = None,
                            ports: List[int] = None) -> Optional[str]:
        """
        Classify server by type based on hostname and protocols

        Args:
            hostname: Server hostname or FQDN
            protocols: List of protocols (e.g., ['HTTP', 'HTTPS'])
            ports: List of ports (e.g., [80, 443])

        Returns:
            Server type string or None if no match
        """
        if not hostname:
            return None

        protocols = protocols or []
        ports = ports or []

        hostname_lower = hostname.lower()
        protocols_upper = [p.upper() for p in protocols]

        # Check each server type
        for server_type, rules in self.SERVER_TYPES.items():
            # Check name patterns
            name_match = any(pattern.lower() in hostname_lower
                           for pattern in rules['name_patterns'])

            # Check protocols
            protocol_match = any(proto in protocols_upper
                               for proto in rules['protocols']) if rules['protocols'] else True

            # Check ports
            port_match = any(port in ports
                           for port in rules['ports']) if rules['ports'] else True

            # If name matches and either protocols or ports match (or both are empty)
            if name_match and (protocol_match or port_match or
                             (not rules['protocols'] and not rules['ports'])):
                return server_type

        return None

    def classify_app_tier(self, hostname: str, protocols: List[str] = None,
                         ports: List[int] = None,
                         server_type: str = None) -> Optional[str]:
        """
        Classify application tier (web, app, database)

        Args:
            hostname: Server hostname
            protocols: List of protocols
            ports: List of ports
            server_type: Already classified server type (optional)

        Returns:
            Tier: 'web', 'app', 'database', or None
        """
        protocols = protocols or []
        ports = ports or []

        protocols_upper = [p.upper() for p in protocols]

        # If server type already has a tier, use it
        if server_type and server_type in self.SERVER_TYPES:
            tier = self.SERVER_TYPES[server_type].get('tier')
            if tier in ['web', 'app', 'database']:
                return tier

        # Score each tier based on protocols and ports
        tier_scores = {}

        for tier, rules in self.APP_TIER_RULES.items():
            score = 0

            # Check protocols
            for proto in protocols_upper:
                if proto in rules['protocols']:
                    score += 2

            # Check ports
            for port in ports:
                if port in rules['ports']:
                    score += 1

            if score > 0:
                tier_scores[tier] = score

        # Return tier with highest score
        if tier_scores:
            return max(tier_scores.items(), key=lambda x: x[1])[0]

        # Default heuristics based on hostname
        hostname_lower = hostname.lower()
        if any(keyword in hostname_lower for keyword in ['web', 'www', 'http']):
            return 'web'
        elif any(keyword in hostname_lower for keyword in ['db', 'sql', 'oracle', 'mysql', 'postgres']):
            return 'database'
        else:
            return 'app'

    def classify_server(self, hostname: str, protocols: List[str] = None,
                       ports: List[int] = None) -> Dict[str, Optional[str]]:
        """
        Fully classify a server (type and tier)

        Args:
            hostname: Server hostname
            protocols: List of protocols
            ports: List of ports

        Returns:
            Dict with 'type', 'tier', and 'category' keys
        """
        server_type = self.classify_server_type(hostname, protocols, ports)
        tier = self.classify_app_tier(hostname, protocols, ports, server_type)

        # Determine category for grouping
        if server_type:
            category = server_type
        elif tier:
            category = tier.capitalize()
        else:
            category = 'Unknown'

        return {
            'type': server_type,
            'tier': tier,
            'category': category,
            'hostname': hostname
        }

    def classify_application_servers(self, app_name: str,
                                    servers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify all servers for an application and group by tier

        Args:
            app_name: Application name
            servers: List of server dicts with 'hostname', 'protocols', 'ports'

        Returns:
            Dict with 'web', 'app', 'database' keys containing classified servers
        """
        classified = {
            'web': [],
            'app': [],
            'database': [],
            'infrastructure': [],
            'security': [],
            'cloud': [],
            'unknown': []
        }

        for server in servers:
            hostname = server.get('hostname', '')
            protocols = server.get('protocols', [])
            ports = server.get('ports', [])

            result = self.classify_server(hostname, protocols, ports)

            # Add to appropriate tier
            tier = result.get('tier') or 'unknown'

            classified_server = {
                **server,
                'server_type': result['type'],
                'tier': result['tier'],
                'category': result['category']
            }

            if tier in classified:
                classified[tier].append(classified_server)
            else:
                classified['unknown'].append(classified_server)

        return classified

    def get_server_display_name(self, server: Dict) -> str:
        """
        Get display name for server in diagram

        Args:
            server: Server dict with classification

        Returns:
            Display name (e.g., "AODSVY web", "F5 Load Balancer")
        """
        hostname = server.get('hostname', 'Unknown')
        server_type = server.get('server_type')
        tier = server.get('tier')

        # If server has a specific type, use it
        if server_type:
            return f"{server_type}"

        # Otherwise use tier
        if tier:
            return f"{tier.capitalize()} Server"

        # Fallback to hostname
        return hostname


# Convenience function for quick classification
def classify_server(hostname: str, protocols: List[str] = None,
                   ports: List[int] = None) -> Dict[str, Optional[str]]:
    """
    Quick server classification

    Args:
        hostname: Server hostname
        protocols: List of protocols
        ports: List of ports

    Returns:
        Classification dict with 'type', 'tier', 'category'
    """
    classifier = ServerClassifier()
    return classifier.classify_server(hostname, protocols, ports)


if __name__ == '__main__':
    # Test server classification
    classifier = ServerClassifier()

    test_servers = [
        {'hostname': 'roc-f5-prod-snat.netops.rgbk.com', 'protocols': [], 'ports': []},
        {'hostname': 'rociarc02smb.rgbk.com', 'protocols': ['CIFS'], 'ports': [445]},
        {'hostname': 'WPDBASQLSSRS07.corp.rgbk.com', 'protocols': ['TDS'], 'ports': [1433]},
        {'hostname': 'utexaraclnt04-vip.unix.rgbk.com', 'protocols': ['TNS'], 'ports': [1521]},
        {'hostname': 'mail01.rgbk.com', 'protocols': ['SMTP'], 'ports': [25]},
        {'hostname': 'splnk-prod-01.rgbk.com', 'protocols': [], 'ports': []},
        {'hostname': 'cdn.akamai.net', 'protocols': [], 'ports': []},
        {'hostname': 'microsoftazuread-sso.com', 'protocols': ['LDAP'], 'ports': []},
        {'hostname': 'keyvault.privatelink.vaultcore.azure.net', 'protocols': ['HTTPS'], 'ports': [443]},
        {'hostname': 'ldap-server-01.corp.rgbk.com', 'protocols': ['LDAP', 'Kerberos'], 'ports': [389]},
        {'hostname': 'LDAP-SERVER-02.CORP.RGBK.COM', 'protocols': ['ldap'], 'ports': [636]},
    ]

    print("Server Classification Test")
    print("=" * 80)

    for server in test_servers:
        result = classifier.classify_server(
            server['hostname'],
            server['protocols'],
            server['ports']
        )

        print(f"\nHostname: {server['hostname']}")
        print(f"  Type: {result['type'] or 'Unknown'}")
        print(f"  Tier: {result['tier'] or 'Unknown'}")
        print(f"  Category: {result['category']}")
