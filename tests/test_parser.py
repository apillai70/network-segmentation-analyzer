"""
Unit Tests for Network Log Parser
==================================
Tests for src/parser.py - NetworkLogParser and FlowRecord
"""

import pytest
import tempfile
import csv
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import NetworkLogParser, FlowRecord


class TestFlowRecord:
    """Test FlowRecord class"""

    def test_flow_record_creation(self):
        """Test basic FlowRecord creation"""
        record = FlowRecord(
            app_name='test_app',
            src_ip='10.1.1.1',
            dst_ip='10.1.2.2',
            protocol='tcp:443',
            port=443
        )

        assert record.app_name == 'test_app'
        assert record.src_ip == '10.1.1.1'
        assert record.dst_ip == '10.1.2.2'
        assert record.port == 443

    def test_flow_record_to_dict(self):
        """Test FlowRecord to_dict conversion"""
        record = FlowRecord(
            app_name='test',
            src_ip='1.2.3.4',
            dst_ip='5.6.7.8',
            bytes=1000,
            packets=10
        )

        record_dict = record.to_dict()

        assert isinstance(record_dict, dict)
        assert record_dict['src_ip'] == '1.2.3.4'
        assert record_dict['bytes'] == 1000
        assert record_dict['packets'] == 10


class TestNetworkLogParser:
    """Test NetworkLogParser class"""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory with test CSV files"""
        tmpdir = tempfile.mkdtemp()
        tmppath = Path(tmpdir)

        # Create test CSV file with standard format
        csv_file1 = tmppath / 'test_app_1.csv'
        with open(csv_file1, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'src_hostname', 'src_ip', 'dst_hostname', 'dst_ip', 'protocol', 'bytes', 'packets'])
            writer.writerow(['2024-01-15 10:00:00', 'web-01', '10.1.1.10', 'app-01', '10.1.2.20', 'tcp:443', '1000', '10'])
            writer.writerow(['2024-01-15 10:00:01', 'app-01', '10.1.2.20', 'db-01', '10.1.3.30', 'tcp:3306', '5000', '50'])

        # Create test CSV file with alternate format
        csv_file2 = tmppath / 'test_app_2.csv'
        with open(csv_file2, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['source_ip', 'destination_ip', 'proto_port', 'bytes_transferred'])
            writer.writerow(['10.2.1.10', '10.2.2.20', 'tcp:8080', '2000'])
            writer.writerow(['10.2.2.20', '10.2.3.30', 'udp:53', '512'])

        yield tmppath

        # Cleanup
        import shutil
        shutil.rmtree(tmpdir)

    def test_parser_initialization(self, temp_data_dir):
        """Test parser initialization"""
        parser = NetworkLogParser(str(temp_data_dir))

        assert parser.data_dir == temp_data_dir
        assert len(parser.records) == 0
        assert len(parser.parse_errors) == 0

    def test_parse_all_logs(self, temp_data_dir):
        """Test parsing all log files"""
        parser = NetworkLogParser(str(temp_data_dir))
        records = parser.parse_all_logs()

        assert len(records) > 0
        assert all(isinstance(r, FlowRecord) for r in records)

    def test_protocol_parsing_with_port(self):
        """Test protocol parsing with port number"""
        parser = NetworkLogParser()

        transport, port = parser._parse_protocol('tcp:443')
        assert transport == 'tcp'
        assert port == 443

        transport, port = parser._parse_protocol('udp:53')
        assert transport == 'udp'
        assert port == 53

    def test_protocol_parsing_without_port(self):
        """Test protocol parsing without port"""
        parser = NetworkLogParser()

        transport, port = parser._parse_protocol('icmp')
        assert transport == 'icmp'
        assert port is None

    def test_protocol_parsing_service_name(self):
        """Test protocol parsing with service name"""
        parser = NetworkLogParser()

        transport, port = parser._parse_protocol('https')
        assert transport == 'tcp'
        assert port == 443

        transport, port = parser._parse_protocol('dns')
        assert transport == 'udp'
        assert port == 53

    def test_ip_validation(self):
        """Test IP address validation"""
        parser = NetworkLogParser()

        assert parser._is_valid_ip('10.1.1.1') is True
        assert parser._is_valid_ip('192.168.1.100') is True
        assert parser._is_valid_ip('256.1.1.1') is False
        assert parser._is_valid_ip('invalid') is False
        assert parser._is_valid_ip('') is False

    def test_internal_ip_detection(self):
        """Test internal IP range detection"""
        parser = NetworkLogParser()

        # Internal IPs
        assert parser._is_internal_ip('10.1.1.1') is True
        assert parser._is_internal_ip('192.168.1.1') is True
        assert parser._is_internal_ip('172.16.0.1') is True
        assert parser._is_internal_ip('127.0.0.1') is True

        # External IPs
        assert parser._is_internal_ip('8.8.8.8') is False
        assert parser._is_internal_ip('1.1.1.1') is False

    def test_timestamp_parsing(self):
        """Test timestamp parsing from various formats"""
        parser = NetworkLogParser()

        ts1 = parser._parse_timestamp('2024-01-15 10:00:00')
        assert isinstance(ts1, datetime)
        assert ts1.year == 2024

        ts2 = parser._parse_timestamp('2024-01-15T10:00:00')
        assert isinstance(ts2, datetime)

        ts3 = parser._parse_timestamp('invalid')
        assert ts3 is None

    def test_risk_calculation(self):
        """Test risk score calculation"""
        parser = NetworkLogParser()

        # External SSH access - high risk
        is_susp, risk = parser._calculate_risk(
            src_ip='1.2.3.4',
            dst_ip='10.1.1.1',
            port=22,
            is_internal=False,
            src_hostname='scanner',
            dst_hostname='server'
        )

        assert is_susp is True
        assert risk > 50

        # Internal database access - lower risk
        is_susp, risk = parser._calculate_risk(
            src_ip='10.1.1.1',
            dst_ip='10.1.2.2',
            port=3306,
            is_internal=True,
            src_hostname='app',
            dst_hostname='db'
        )

        assert risk < 50

    def test_export_normalized_csv(self, temp_data_dir):
        """Test exporting normalized CSV"""
        parser = NetworkLogParser(str(temp_data_dir))
        parser.parse_all_logs()

        output_file = temp_data_dir / 'normalized.csv'
        parser.export_normalized_csv(str(output_file))

        assert output_file.exists()

        # Verify CSV structure
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) > 0
            assert 'src_ip' in reader.fieldnames
            assert 'dst_ip' in reader.fieldnames
            assert 'protocol' in reader.fieldnames

    def test_get_summary_stats(self, temp_data_dir):
        """Test getting summary statistics"""
        parser = NetworkLogParser(str(temp_data_dir))
        parser.parse_all_logs()

        stats = parser.get_summary_stats()

        assert 'total_records' in stats
        assert 'total_errors' in stats
        assert 'internal_flows' in stats
        assert 'suspicious_flows' in stats
        assert stats['total_records'] > 0

    def test_extract_app_name(self):
        """Test extracting app name from filename"""
        parser = NetworkLogParser()

        assert parser._extract_app_name('app_1_flows.csv') == 'app_1'
        assert parser._extract_app_name('test_traffic.csv') == 'test'
        assert parser._extract_app_name('myapp.csv') == 'myapp'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
