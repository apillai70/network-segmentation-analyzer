"""
Network Traffic Log Parser
==========================
Robust parser for network flow logs with support for multiple formats,
protocol normalization, IP validation, and flexible column mapping.

Author: Network Security Team
Version: 2.0
"""

import csv
import re
import ipaddress
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlowRecord:
    """Normalized network flow record"""

    def __init__(self, **kwargs):
        self.timestamp: Optional[datetime] = kwargs.get('timestamp')
        self.app_name: str = kwargs.get('app_name', 'unknown')
        self.src_hostname: str = kwargs.get('src_hostname', '')
        self.src_ip: str = kwargs.get('src_ip', '')
        self.dst_hostname: str = kwargs.get('dst_hostname', '')
        self.dst_ip: str = kwargs.get('dst_ip', '')
        self.protocol: str = kwargs.get('protocol', 'tcp')  # tcp, udp, icmp, other
        self.port: Optional[int] = kwargs.get('port')
        self.transport: str = kwargs.get('transport', 'tcp')
        self.bytes: int = kwargs.get('bytes', 0)
        self.packets: int = kwargs.get('packets', 0)
        self.duration: float = kwargs.get('duration', 0.0)

        # Additional metadata
        self.flow_id: Optional[str] = kwargs.get('flow_id')
        self.is_internal: bool = kwargs.get('is_internal', True)
        self.is_suspicious: bool = kwargs.get('is_suspicious', False)
        self.risk_score: int = kwargs.get('risk_score', 0)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'app_name': self.app_name,
            'src_hostname': self.src_hostname,
            'src_ip': self.src_ip,
            'dst_hostname': self.dst_hostname,
            'dst_ip': self.dst_ip,
            'protocol': self.protocol,
            'port': self.port,
            'transport': self.transport,
            'bytes': self.bytes,
            'packets': self.packets,
            'duration': self.duration,
            'is_internal': self.is_internal,
            'is_suspicious': self.is_suspicious,
            'risk_score': self.risk_score
        }

    def __repr__(self):
        return (f"FlowRecord({self.src_hostname or self.src_ip} -> "
                f"{self.dst_hostname or self.dst_ip} {self.protocol}:{self.port or '-'})")


class NetworkLogParser:
    """
    Robust network log parser with automatic format detection and normalization
    """

    # Column name mappings (various formats -> normalized)
    COLUMN_MAPPINGS = {
        'src_hostname': ['src_hostname', 'source_hostname', 'src_host', 'source_host', 'source hostname'],
        'src_ip': ['src_ip', 'source_ip', 'src_addr', 'source_address', 'source_addr', 'source ip'],
        'dst_hostname': ['dst_hostname', 'destination_hostname', 'dst_host', 'dest_host', 'destination_host', 'dest hostname'],
        'dst_ip': ['dst_ip', 'destination_ip', 'dst_addr', 'dest_ip', 'destination_address', 'destination_addr', 'dest ip'],
        'protocol': ['protocol', 'proto', 'proto_port', 'protocol_port'],
        'bytes': ['bytes', 'bytes_transferred', 'bytes_in', 'byte_count', 'octets', 'bytes in', 'bytes out'],
        'packets': ['packets', 'packet_count', 'pkts', 'pkt_count'],
        'timestamp': ['timestamp', 'time', 'datetime', 'ts', 'event_time'],
        'duration': ['duration', 'elapsed_time', 'session_duration'],
        'port': ['port', 'dst_port', 'dest_port', 'destination_port']
    }

    # Known internal IP ranges (RFC1918 + additional)
    INTERNAL_IP_RANGES = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
        ipaddress.IPv4Network('127.0.0.0/8'),
    ]

    # Suspicious ports (management, database, etc. exposed)
    SUSPICIOUS_PORTS = {
        22: 'SSH',
        23: 'Telnet',
        3389: 'RDP',
        3306: 'MySQL',
        5432: 'PostgreSQL',
        27017: 'MongoDB',
        6379: 'Redis',
        9200: 'Elasticsearch'
    }

    def __init__(self, data_dir: str = 'data/input'):
        self.data_dir = Path(data_dir)
        self.records: List[FlowRecord] = []
        self.parse_errors: List[Dict] = []
        self.stats = defaultdict(int)

        logger.info(f"NetworkLogParser initialized with data_dir: {self.data_dir}")

    def parse_all_logs(self) -> List[FlowRecord]:
        """Parse all CSV files in data directory"""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        csv_files = list(self.data_dir.glob('*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files to parse")

        for csv_file in csv_files:
            self.parse_log_file(csv_file)

        logger.info(f"Parsing complete. Total records: {len(self.records)}, Errors: {len(self.parse_errors)}")
        return self.records

    def parse_log_file(self, file_path: Path) -> List[FlowRecord]:
        """Parse a single CSV log file"""
        logger.info(f"Parsing file: {file_path.name}")

        # Extract app name from filename (e.g., app_1_flows.csv -> app_1)
        app_name = self._extract_app_name(file_path.name)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect delimiter
                delimiter = self._detect_delimiter(f)
                f.seek(0)

                reader = csv.DictReader(f, delimiter=delimiter)

                # Detect column mapping
                column_mapping = self._detect_column_mapping(reader.fieldnames)

                row_count = 0
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 for header)
                    try:
                        record = self._parse_row(row, column_mapping, app_name)
                        if record:
                            self.records.append(record)
                            row_count += 1
                    except Exception as e:
                        self.parse_errors.append({
                            'file': file_path.name,
                            'row': row_num,
                            'error': str(e),
                            'data': row
                        })
                        logger.warning(f"Error parsing row {row_num} in {file_path.name}: {e}")

                self.stats[f'parsed_{app_name}'] = row_count
                logger.info(f"  [OK] Parsed {row_count} records from {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to parse {file_path.name}: {e}")
            raise

        return self.records

    def _extract_app_name(self, filename: str) -> str:
        """Extract application name from filename"""
        # Remove file extension and common suffixes
        name = filename.replace('.csv', '').replace('_flows', '').replace('_traffic', '')
        return name

    def _detect_delimiter(self, file_handle) -> str:
        """Detect CSV delimiter"""
        first_line = file_handle.readline()
        if ',' in first_line:
            return ','
        elif '\t' in first_line:
            return '\t'
        elif ';' in first_line:
            return ';'
        else:
            return ','  # default

    def _detect_column_mapping(self, fieldnames: List[str]) -> Dict[str, str]:
        """Detect which columns map to our normalized fields"""
        mapping = {}

        for normalized_field, possible_names in self.COLUMN_MAPPINGS.items():
            for field in fieldnames:
                if field.lower() in [name.lower() for name in possible_names]:
                    mapping[normalized_field] = field
                    break

        logger.debug(f"Detected column mapping: {mapping}")
        return mapping

    def _parse_row(self, row: Dict, column_mapping: Dict, app_name: str) -> Optional[FlowRecord]:
        """Parse a single row into a FlowRecord"""
        try:
            # Extract and normalize fields
            src_hostname = row.get(column_mapping.get('src_hostname', ''), '').strip()
            src_ip = row.get(column_mapping.get('src_ip', ''), '').strip()
            dst_hostname = row.get(column_mapping.get('dst_hostname', ''), '').strip()
            dst_ip = row.get(column_mapping.get('dst_ip', ''), '').strip()

            # Validate IPs
            if not src_ip or not self._is_valid_ip(src_ip):
                logger.debug(f"Invalid source IP: {src_ip}")
                return None

            if not dst_ip or not self._is_valid_ip(dst_ip):
                logger.debug(f"Invalid destination IP: {dst_ip}")
                return None

            # Parse protocol and port
            protocol_field = row.get(column_mapping.get('protocol', ''), '').strip()
            transport, port = self._parse_protocol(protocol_field)

            # Parse timestamp
            timestamp_field = row.get(column_mapping.get('timestamp', ''), '').strip()
            timestamp = self._parse_timestamp(timestamp_field) if timestamp_field else None

            # Parse numeric fields
            bytes_val = self._parse_int(row.get(column_mapping.get('bytes', ''), '0'))
            packets_val = self._parse_int(row.get(column_mapping.get('packets', ''), '0'))
            duration_val = self._parse_float(row.get(column_mapping.get('duration', ''), '0'))

            # Determine if internal traffic
            is_internal = self._is_internal_ip(src_ip) and self._is_internal_ip(dst_ip)

            # Calculate risk score
            is_suspicious, risk_score = self._calculate_risk(
                src_ip, dst_ip, port, is_internal, src_hostname, dst_hostname
            )

            # Create flow record
            record = FlowRecord(
                timestamp=timestamp,
                app_name=app_name,
                src_hostname=src_hostname,
                src_ip=src_ip,
                dst_hostname=dst_hostname,
                dst_ip=dst_ip,
                protocol=protocol_field,
                port=port,
                transport=transport,
                bytes=bytes_val,
                packets=packets_val,
                duration=duration_val,
                is_internal=is_internal,
                is_suspicious=is_suspicious,
                risk_score=risk_score
            )

            return record

        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            raise

    def _parse_protocol(self, protocol_str: str) -> Tuple[str, Optional[int]]:
        """
        Parse protocol field which can be:
        - 'tcp:443' -> ('tcp', 443)
        - 'udp:53' -> ('udp', 53)
        - 'icmp' -> ('icmp', None)
        - 'dns' -> ('tcp', 53)  # Common service mapping
        """
        protocol_str = protocol_str.lower().strip()

        # Check for protocol:port format
        if ':' in protocol_str:
            parts = protocol_str.split(':')
            transport = parts[0]
            try:
                port = int(parts[1])
                return transport, port
            except (ValueError, IndexError):
                return transport, None

        # Handle special cases
        service_mappings = {
            'http': ('tcp', 80),
            'https': ('tcp', 443),
            'dns': ('udp', 53),
            'ssh': ('tcp', 22),
            'ftp': ('tcp', 21),
            'smtp': ('tcp', 25),
            'icmp': ('icmp', None),
            'igmp': ('igmp', None)
        }

        if protocol_str in service_mappings:
            return service_mappings[protocol_str]

        # Default: assume it's a transport protocol
        return protocol_str, None

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        if not ts_str:
            return None

        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

        logger.debug(f"Could not parse timestamp: {ts_str}")
        return None

    def _parse_int(self, value: str) -> int:
        """Safely parse integer"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _parse_float(self, value: str) -> float:
        """Safely parse float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _is_valid_ip(self, ip_str: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.IPv4Address(ip_str)
            return True
        except (ipaddress.AddressValueError, ValueError):
            return False

    def _is_internal_ip(self, ip_str: str) -> bool:
        """Check if IP is in internal ranges"""
        try:
            ip = ipaddress.IPv4Address(ip_str)
            for network in self.INTERNAL_IP_RANGES:
                if ip in network:
                    return True
            return False
        except (ipaddress.AddressValueError, ValueError):
            return False

    def _calculate_risk(
        self,
        src_ip: str,
        dst_ip: str,
        port: Optional[int],
        is_internal: bool,
        src_hostname: str,
        dst_hostname: str
    ) -> Tuple[bool, int]:
        """
        Calculate risk score for a flow
        Returns: (is_suspicious, risk_score)
        """
        risk_score = 0
        is_suspicious = False

        # External connections to internal services
        if not self._is_internal_ip(src_ip) and self._is_internal_ip(dst_ip):
            risk_score += 30
            is_suspicious = True

        # Suspicious ports exposed externally
        if port and port in self.SUSPICIOUS_PORTS:
            if not is_internal:
                risk_score += 40
                is_suspicious = True
                logger.warning(
                    f"Suspicious: {self.SUSPICIOUS_PORTS[port]} port {port} "
                    f"exposed from {src_ip} to {dst_ip}"
                )
            else:
                risk_score += 10  # Still notable even internally

        # Known malicious patterns in hostname
        malicious_keywords = ['malicious', 'suspicious', 'scanner', 'bot', 'exploit']
        for keyword in malicious_keywords:
            if keyword in src_hostname.lower() or keyword in dst_hostname.lower():
                risk_score += 50
                is_suspicious = True

        # SSH from external sources
        if port == 22 and not self._is_internal_ip(src_ip):
            risk_score += 35
            is_suspicious = True

        # Database ports from many sources (potential exfiltration)
        if port in [3306, 5432, 27017, 6379] and not is_internal:
            risk_score += 45
            is_suspicious = True

        return is_suspicious, min(risk_score, 100)  # Cap at 100

    def get_summary_stats(self) -> Dict:
        """Get parsing summary statistics"""
        return {
            'total_records': len(self.records),
            'total_errors': len(self.parse_errors),
            'internal_flows': sum(1 for r in self.records if r.is_internal),
            'external_flows': sum(1 for r in self.records if not r.is_internal),
            'suspicious_flows': sum(1 for r in self.records if r.is_suspicious),
            'apps_parsed': len(set(r.app_name for r in self.records)),
            'unique_src_ips': len(set(r.src_ip for r in self.records)),
            'unique_dst_ips': len(set(r.dst_ip for r in self.records)),
            'total_bytes': sum(r.bytes for r in self.records),
            'total_packets': sum(r.packets for r in self.records)
        }

    def export_normalized_csv(self, output_path: str):
        """Export normalized records to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            'timestamp', 'app_name', 'src_hostname', 'src_ip', 'dst_hostname', 'dst_ip',
            'protocol', 'port', 'transport', 'bytes', 'packets', 'duration',
            'is_internal', 'is_suspicious', 'risk_score'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for record in self.records:
                writer.writerow(record.to_dict())

        logger.info(f"[OK] Exported {len(self.records)} normalized records to {output_path}")


# Convenience function
def parse_network_logs(data_dir: str = 'data/input') -> NetworkLogParser:
    """
    Convenience function to parse all network logs

    Args:
        data_dir: Directory containing CSV log files

    Returns:
        NetworkLogParser instance with parsed records
    """
    parser = NetworkLogParser(data_dir)
    parser.parse_all_logs()
    return parser


if __name__ == '__main__':
    # Example usage
    print("="*60)
    print("Network Log Parser - Test Run")
    print("="*60)

    parser = parse_network_logs('data/input')

    print(f"\n[DATA] Parsing Summary:")
    stats = parser.get_summary_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\n[WARNING]️  Suspicious Flows:")
    suspicious = [r for r in parser.records if r.is_suspicious][:5]
    for record in suspicious:
        print(f"  - {record} (risk: {record.risk_score})")

    # Export normalized data
    parser.export_normalized_csv('data/processed/normalized_flows.csv')

    print("\n[SUCCESS] Parsing complete!")
