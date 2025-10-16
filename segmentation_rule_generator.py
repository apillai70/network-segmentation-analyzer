import json
from collections import defaultdict

class SegmentationRuleGenerator:
    """
    Generates firewall rules, security group configs, and ACLs 
    for network micro-segmentation based on discovered topology.
    """
    
    def __init__(self, analysis_report_path):
        with open(analysis_report_path, 'r') as f:
            self.report = json.load(f)
        
        self.zones = {}
        self.build_zone_mappings()
    
    def build_zone_mappings(self):
        """Build IP-to-zone mappings"""
        for zone in self.report['network_segmentation']['zones']:
            self.zones[zone['zone']] = {
                'members': set(zone['members']),
                'description': zone['description']
            }
    
    def generate_iptables_rules(self, output_file='iptables_rules.sh'):
        """Generate Linux iptables rules"""
        rules = ["#!/bin/bash", "# Network Segmentation Rules", 
                "# Generated from topology analysis\n"]
        
        # Flush existing rules
        rules.append("iptables -F")
        rules.append("iptables -X")
        rules.append("iptables -P INPUT DROP")
        rules.append("iptables -P FORWARD DROP")
        rules.append("iptables -P OUTPUT ACCEPT\n")
        
        # Allow established connections
        rules.append("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
        rules.append("iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT\n")
        
        # DMZ -> WEB_TIER
        if 'DMZ' in self.zones and 'WEB_TIER' in self.zones:
            rules.append("# DMZ to WEB_TIER")
            for dmz_ip in self.zones['DMZ']['members']:
                for web_ip in self.zones['WEB_TIER']['members']:
                    rules.append(f"iptables -A FORWARD -s {dmz_ip} -d {web_ip} -p tcp --dport 80 -j ACCEPT")
                    rules.append(f"iptables -A FORWARD -s {dmz_ip} -d {web_ip} -p tcp --dport 443 -j ACCEPT")
            rules.append("")
        
        # WEB_TIER -> APP_TIER
        if 'WEB_TIER' in self.zones and 'APP_TIER' in self.zones:
            rules.append("# WEB_TIER to APP_TIER")
            for web_ip in self.zones['WEB_TIER']['members']:
                for app_ip in self.zones['APP_TIER']['members']:
                    rules.append(f"iptables -A FORWARD -s {web_ip} -d {app_ip} -p tcp -j ACCEPT")
            rules.append("")
        
        # APP_TIER -> DATA_TIER
        if 'APP_TIER' in self.zones and 'DATA_TIER' in self.zones:
            rules.append("# APP_TIER to DATA_TIER")
            for app_ip in self.zones['APP_TIER']['members']:
                for db_ip in self.zones['DATA_TIER']['members']:
                    rules.append(f"iptables -A FORWARD -s {app_ip} -d {db_ip} -p tcp --dport 3306 -j ACCEPT")
                    rules.append(f"iptables -A FORWARD -s {app_ip} -d {db_ip} -p tcp --dport 5432 -j ACCEPT")
                    rules.append(f"iptables -A FORWARD -s {app_ip} -d {db_ip} -p tcp --dport 27017 -j ACCEPT")
            rules.append("")
        
        # APP_TIER -> MESSAGING
        if 'APP_TIER' in self.zones and 'MESSAGING' in self.zones:
            rules.append("# APP_TIER to MESSAGING")
            for app_ip in self.zones['APP_TIER']['members']:
                for mq_ip in self.zones['MESSAGING']['members']:
                    rules.append(f"iptables -A FORWARD -s {app_ip} -d {mq_ip} -p tcp --dport 9092 -j ACCEPT")
                    rules.append(f"iptables -A FORWARD -s {app_ip} -d {mq_ip} -p tcp --dport 5672 -j ACCEPT")
            rules.append("")
        
        # Default deny
        rules.append("# Default deny")
        rules.append("iptables -A FORWARD -j LOG --log-prefix 'SEGMENTATION_DENY: '")
        rules.append("iptables -A FORWARD -j DROP")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(rules))
        
        print(f"[SUCCESS] iptables rules generated: {output_file}")
        return rules
    
    def generate_aws_security_groups(self, output_file='aws_security_groups.json'):
        """Generate AWS Security Group definitions"""
        security_groups = []
        
        for zone_name, zone_data in self.zones.items():
            sg = {
                'GroupName': f'sg-{zone_name.lower().replace("_", "-")}',
                'Description': zone_data['description'],
                'VpcId': 'vpc-XXXXXXXX',  # To be replaced
                'IngressRules': [],
                'EgressRules': []
            }
            
            # Define ingress rules based on zone type
            if zone_name == 'WEB_TIER':
                sg['IngressRules'].extend([
                    {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'CidrIp': '0.0.0.0/0'},
                    {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'CidrIp': '0.0.0.0/0'}
                ])
            
            elif zone_name == 'APP_TIER':
                # Only from WEB_TIER
                sg['IngressRules'].append({
                    'IpProtocol': 'tcp',
                    'FromPort': 8080,
                    'ToPort': 8080,
                    'SourceSecurityGroupName': 'sg-web-tier'
                })
            
            elif zone_name == 'DATA_TIER':
                # Only from APP_TIER
                sg['IngressRules'].extend([
                    {'IpProtocol': 'tcp', 'FromPort': 3306, 'ToPort': 3306, 'SourceSecurityGroupName': 'sg-app-tier'},
                    {'IpProtocol': 'tcp', 'FromPort': 5432, 'ToPort': 5432, 'SourceSecurityGroupName': 'sg-app-tier'}
                ])
            
            elif zone_name == 'MESSAGING':
                sg['IngressRules'].extend([
                    {'IpProtocol': 'tcp', 'FromPort': 9092, 'ToPort': 9092, 'SourceSecurityGroupName': 'sg-app-tier'},
                    {'IpProtocol': 'tcp', 'FromPort': 5672, 'ToPort': 5672, 'SourceSecurityGroupName': 'sg-app-tier'}
                ])
            
            # Default egress: allow all (can be restricted further)
            sg['EgressRules'].append({
                'IpProtocol': '-1',
                'CidrIp': '0.0.0.0/0'
            })
            
            security_groups.append(sg)
        
        with open(output_file, 'w') as f:
            json.dump({'SecurityGroups': security_groups}, f, indent=2)
        
        print(f"[SUCCESS] AWS Security Groups generated: {output_file}")
        return security_groups
    
    def generate_cisco_acls(self, output_file='cisco_acls.txt'):
        """Generate Cisco ACL configurations"""
        acls = ["! Network Segmentation ACLs", 
                "! Generated from topology analysis\n"]
        
        acl_num = 100
        
        for zone_name in self.zones.keys():
            acls.append(f"! ACL for {zone_name}")
            acls.append(f"ip access-list extended ACL_{zone_name}")
            
            # Permit established connections
            acls.append("  permit tcp any any established")
            
            # Zone-specific rules
            if zone_name == 'WEB_TIER':
                acls.append("  permit tcp any any eq 80")
                acls.append("  permit tcp any any eq 443")
            
            elif zone_name == 'DATA_TIER':
                acls.append("  permit tcp 10.0.0.0 0.255.255.255 any eq 3306")
                acls.append("  permit tcp 10.0.0.0 0.255.255.255 any eq 5432")
            
            # Default deny
            acls.append("  deny ip any any log")
            acls.append("  exit\n")
            
            acl_num += 1
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(acls))
        
        print(f"[SUCCESS] Cisco ACLs generated: {output_file}")
        return acls
    
    def generate_openshift_network_policy(self, output_file='openshift_network_policies.yaml'):
        """Generate OpenShift/Kubernetes NetworkPolicy definitions"""
        policies = []
        
        policies.append("---")
        policies.append("# Network Policies for Micro-segmentation")
        policies.append("# Apply to OpenShift/Kubernetes clusters\n")
        
        for zone_name, zone_data in self.zones.items():
            policy = f"""---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {zone_name.lower().replace('_', '-')}-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      zone: {zone_name.lower()}
  policyTypes:
  - Ingress
  - Egress
  ingress:"""
            
            # Define ingress rules based on zone
            if zone_name == 'WEB_TIER':
                policy += """
  - from:
    - podSelector:
        matchLabels:
          zone: dmz
    ports:
    - protocol: TCP
      port: 8080"""
            
            elif zone_name == 'APP_TIER':
                policy += """
  - from:
    - podSelector:
        matchLabels:
          zone: web_tier
    ports:
    - protocol: TCP
      port: 8080"""
            
            elif zone_name == 'DATA_TIER':
                policy += """
  - from:
    - podSelector:
        matchLabels:
          zone: app_tier
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 3306"""
            
            policy += """
  egress:
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
    - protocol: UDP
"""
            
            policies.append(policy)
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(policies))
        
        print(f"[SUCCESS] Kubernetes Network Policies generated: {output_file}")
        return policies
    
    def generate_application_labels(self, output_file='application_labels.csv'):
        """Generate application-to-zone label mappings for asset management"""
        import csv
        
        app_labels = []
        
        for node in self.report['node_inventory']:
            for app in node['applications']:
                zone = None
                for z in self.report['network_segmentation']['zones']:
                    if node['ip'] in z['members']:
                        zone = z['zone']
                        break
                
                app_labels.append({
                    'application': app,
                    'ip_address': node['ip'],
                    'hostname': node['hostname'],
                    'zone': zone or 'UNCLASSIFIED',
                    'infrastructure_type': node['infrastructure_type'] or 'application',
                    'security_labels': ','.join(node['security_labels'])
                })
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['application', 'ip_address', 'hostname', 
                                                   'zone', 'infrastructure_type', 'security_labels'])
            writer.writeheader()
            writer.writerows(app_labels)
        
        print(f"[SUCCESS] Application labels generated: {output_file}")
        return app_labels
    
    def generate_zero_trust_matrix(self, output_file='zero_trust_matrix.csv'):
        """Generate zero-trust access matrix"""
        import csv
        
        # Define allowed zone-to-zone communication
        allowed_flows = [
            ('DMZ', 'WEB_TIER', 'HTTP/HTTPS'),
            ('WEB_TIER', 'APP_TIER', 'Application'),
            ('APP_TIER', 'DATA_TIER', 'Database'),
            ('APP_TIER', 'MESSAGING', 'Message Queue'),
            ('APP_TIER', 'INFRASTRUCTURE', 'Infrastructure'),
            ('MANAGEMENT', '*', 'Management')
        ]
        
        matrix = []
        for src, dst, service in allowed_flows:
            matrix.append({
                'source_zone': src,
                'destination_zone': dst,
                'allowed_service': service,
                'authentication_required': 'YES',
                'encryption_required': 'YES',
                'logging': 'ENABLED'
            })
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['source_zone', 'destination_zone', 
                                                   'allowed_service', 'authentication_required',
                                                   'encryption_required', 'logging'])
            writer.writeheader()
            writer.writerows(matrix)
        
        print(f"[SUCCESS] Zero-trust matrix generated: {output_file}")
        return matrix
    
    def generate_all_outputs(self):
        """Generate all segmentation artifacts"""
        print("\n🔧 Generating Network Segmentation Artifacts...")
        print("="*60)
        
        self.generate_iptables_rules()
        self.generate_aws_security_groups()
        self.generate_cisco_acls()
        self.generate_openshift_network_policy()
        self.generate_application_labels()
        self.generate_zero_trust_matrix()
        
        print("\n[SUCCESS] All segmentation artifacts generated successfully!")


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    # After running the main analyzer and generating the report:
    generator = SegmentationRuleGenerator('network_segmentation_report.json')
    generator.generate_all_outputs()
    
    print("\n[STEP] Generated Files:")
    print("  ├─ iptables_rules.sh - Linux firewall rules")
    print("  ├─ aws_security_groups.json - AWS security group definitions")
    print("  ├─ cisco_acls.txt - Cisco ACL configurations")
    print("  ├─ openshift_network_policies.yaml - K8s/OpenShift policies")
    print("  ├─ application_labels.csv - Application zone mappings")
    print("  └─ zero_trust_matrix.csv - Zero-trust access matrix")