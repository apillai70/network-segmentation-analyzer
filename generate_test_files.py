#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Synthetic Test Files
==============================
Create 166 synthetic App_Code_*.csv files for testing DNS validation

Raw CSV Format: IP, Name, Peer, Protocol, Bytes In, Bytes Out
"""

import random
import csv
from pathlib import Path

def generate_test_files():
    """Generate 166 synthetic test files"""

    output_dir = Path('data/input')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Application codes (166 apps)
    app_codes = [
        'XECHK', 'WAPRCG', 'SQLDB', 'WEBUI', 'APIGTW', 'AUTHSVC', 'FILESRV', 'MAILSRV',
        'DNSSRV', 'DHCPSRV', 'PROXYSRV', 'FWSRV', 'LDAPSRV', 'NFSSRV', 'SMTPSRV', 'IMAPSRV',
        'HTTPSRV', 'FTPSRV', 'TFTPSRV', 'SSHSRV', 'RDPSRV', 'VNCSRV', 'TELNET', 'SNMPSRV',
        'SYSLOG', 'NAGIOS', 'ZABBIX', 'SPLUNK', 'ELK', 'GRAFANA', 'PROM', 'INFLUX',
        'REDIS', 'MEMCACHE', 'RABBIT', 'KAFKA', 'ELASTIC', 'MONGO', 'POSTGRES', 'MYSQL',
        'ORACLE', 'MSSQL', 'MARIADB', 'CASSANDRA', 'HBASE', 'COUCHDB', 'DYNAMO', 'NEPTUNE',
        'JENKINS', 'GITLAB', 'GITHUB', 'BITBUCKET', 'JIRA', 'CONFLUENCE', 'SLACK', 'TEAMS',
        'DOCKER', 'K8S', 'OPENSHIFT', 'RANCHER', 'TERRAFORM', 'ANSIBLE', 'PUPPET', 'CHEF',
        'NGINX', 'APACHE', 'TOMCAT', 'JBOSS', 'WILDFLY', 'WEBLOGIC', 'WEBSPHERE', 'IIS',
        'NODEJS', 'PYTHON', 'JAVA', 'DOTNET', 'GOLANG', 'RUBY', 'PHP', 'PERL',
        'AWS', 'AZURE', 'GCP', 'ALIBABA', 'OCI', 'IBM', 'VMWARE', 'HYPER',
        'CITRIX', 'VDI', 'TERMINAL', 'DESKTOP', 'LAPTOP', 'MOBILE', 'IOT', 'EDGE',
        'FIREWALL', 'IDS', 'IPS', 'WAF', 'DLP', 'SIEM', 'SOAR', 'EDR',
        'BACKUP', 'STORAGE', 'SAN', 'NAS', 'OBJECT', 'BLOCK', 'FILE', 'TAPE',
        'MONITOR', 'LOGGING', 'METRICS', 'TRACING', 'APM', 'RUM', 'SYNTHETIC', 'UPTIME',
        'PAYMENTS', 'BILLING', 'INVOICE', 'ORDERS', 'SHIPPING', 'INVENTORY', 'CRM', 'ERP',
        'HR', 'PAYROLL', 'BENEFITS', 'TRAINING', 'ONBOARD', 'OFFBOARD', 'TIMECARD', 'EXPENSE',
        'LEGAL', 'COMPLIANCE', 'AUDIT', 'RISK', 'SECURITY', 'PRIVACY', 'POLICY', 'GOVERN',
        'DEVOPS', 'CICD', 'TESTING', 'STAGING', 'PROD', 'DR', 'BCP', 'HA',
        'LOAD', 'BALANCE', 'CACHE', 'CDN', 'DNS', 'DHCP', 'NTP', 'PKI',
        'VPN', 'PROXY', 'GATEWAY', 'ROUTER', 'SWITCH'
    ]

    # Ensure we have exactly 166
    while len(app_codes) < 166:
        app_codes.append(f'APP{len(app_codes)+1:03d}')
    app_codes = app_codes[:166]

    # Sample IPs and hostnames
    source_ips = [
        '10.100.246.18', '10.100.246.19', '10.100.246.20', '10.100.246.21',
        '10.164.92.166', '10.164.92.167', '10.164.92.168', '10.164.92.169',
        '10.10.10.50', '10.10.10.51', '10.10.10.52', '10.10.10.53',
        '192.168.1.100', '192.168.1.101', '192.168.1.102', '192.168.1.103',
        '172.16.0.10', '172.16.0.11', '172.16.0.12', '172.16.0.13'
    ]

    source_names = [
        'WAPRCG.rgbk.com', 'WPEVISQL02.corp.rgbk.com', 'APP-SERVER-01.rgbk.com',
        'WEB-SERVER-01.corp.local', 'DB-SERVER-01.rgbk.com', 'API-GATEWAY.rgbk.com',
        'VMware AD6FD1', 'vm-host-01.corp.local', 'vmhost-02.rgbk.com',
        'ESXi-Host-01.rgbk.com', 'ESXi-Host-02.corp.local', 'VM-Server-03.rgbk.com',
        'APP-VM-01.rgbk.com', 'DB-VM-01.corp.local', 'WEB-VM-01.rgbk.com',
        'server01.rgbk.com', 'server02.corp.local', 'server03.rgbk.com',
        'host01.rgbk.com', 'host02.corp.local'
    ]

    dest_ips = [
        '10.100.246.30', '10.100.246.31', '10.100.246.32', '10.100.246.33',
        '10.164.92.180', '10.164.92.181', '10.164.92.182', '10.164.92.183',
        '10.20.20.100', '10.20.20.101', '10.20.20.102', '10.20.20.103',
        '8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1',
        '172.16.1.50', '172.16.1.51', '172.16.1.52', '172.16.1.53'
    ]

    protocols = ['TCP', 'UDP', 'TCP:443', 'TCP:80', 'TCP:22', 'TCP:3306', 'TCP:5432', 'TCP:1433', 'UDP:53', 'TCP:8080']

    print(f"Generating {len(app_codes)} synthetic test files...")
    print(f"Output directory: {output_dir.absolute()}")
    print()

    for idx, app_code in enumerate(app_codes, 1):
        filename = f"App_Code_{app_code}.csv"
        filepath = output_dir / filename

        # Generate random number of flows (5-20 per app)
        num_flows = random.randint(5, 20)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header (raw format)
            writer.writerow(['IP', 'Name', 'Peer', 'Protocol', 'Bytes In', 'Bytes Out'])

            # Generate flows
            for _ in range(num_flows):
                src_ip = random.choice(source_ips)
                src_name = random.choice(source_names)
                dst_ip = random.choice(dest_ips)

                # Sometimes use source IPs from other apps as destinations (cross-referencing)
                if random.random() < 0.3:  # 30% chance
                    dst_ip = random.choice(source_ips)

                protocol = random.choice(protocols)
                bytes_in = random.randint(1000, 1000000)
                bytes_out = random.randint(1000, 1000000)

                writer.writerow([src_ip, src_name, dst_ip, protocol, bytes_in, bytes_out])

        if idx % 10 == 0:
            print(f"  Generated {idx}/{len(app_codes)} files...")

    print()
    print(f"[OK] Successfully generated {len(app_codes)} files")
    print(f"Location: {output_dir.absolute()}")
    print()
    print("Sample files:")
    files = sorted(output_dir.glob('App_Code_*.csv'))[:5]
    for f in files:
        print(f"  - {f.name}")

    print()
    print("Ready to test! Run:")
    print("  python process_all_flows.py")


if __name__ == '__main__':
    generate_test_files()
