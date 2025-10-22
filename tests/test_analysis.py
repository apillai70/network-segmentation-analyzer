"""
Unit Tests for Traffic Analysis
================================
Tests for src/analysis.py - TrafficAnalyzer and SegmentationRule
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import FlowRecord

# Import analysis classes - try multiple approaches for compatibility
try:
    # Try importing from analysis.py file directly
    from src.analysis import TrafficAnalyzer, SegmentationRule, NetworkZone
except ImportError:
    try:
        # Fallback: if analysis is a package, try importing from it
        from src.analysis_modules import TrafficAnalyzer, SegmentationRule, NetworkZone
    except ImportError:
        # Last resort: direct import
        import analysis
        TrafficAnalyzer = analysis.TrafficAnalyzer
        SegmentationRule = analysis.SegmentationRule
        NetworkZone = analysis.NetworkZone


class TestSegmentationRule:
    """Test SegmentationRule class"""

    def test_rule_creation(self):
        """Test creating a segmentation rule"""
        rule = SegmentationRule(
            priority=100,
            source='WEB_TIER',
            destination='APP_TIER',
            protocol='tcp',
            port='8080',
            action='allow',
            justification='Web to app traffic',
            risk_score=20,
            enforcement_target='firewall',
            complexity='low'
        )

        assert rule.priority == 100
        assert rule.source == 'WEB_TIER'
        assert rule.action == 'allow'

    def test_rule_to_dict(self):
        """Test converting rule to dictionary"""
        rule = SegmentationRule(
            priority=200,
            source='any',
            destination='DATA_TIER',
            protocol='tcp',
            port='3306',
            action='deny',
            justification='Block external DB access',
            risk_score=95,
            enforcement_target='perimeter-firewall',
            complexity='low'
        )

        rule_dict = rule.to_dict()

        assert isinstance(rule_dict, dict)
        assert rule_dict['priority'] == 200
        assert rule_dict['action'] == 'deny'
        assert rule_dict['risk_score'] == 95


class TestNetworkZone:
    """Test NetworkZone class"""

    def test_zone_creation(self):
        """Test creating a network zone"""
        zone = NetworkZone(
            zone_name='WEB_TIER',
            zone_type='micro',
            members={'10.1.1.1', '10.1.1.2'},
            description='Web servers',
            security_level=2
        )

        assert zone.zone_name == 'WEB_TIER'
        assert len(zone.members) == 2
        assert zone.security_level == 2


class TestTrafficAnalyzer:
    """Test TrafficAnalyzer class"""

    @pytest.fixture
    def sample_records(self):
        """Create sample flow records"""
        records = [
            FlowRecord(
                app_name='test_app',
                src_ip='10.1.1.10',
                dst_ip='10.1.2.20',
                protocol='tcp:8080',
                port=8080,
                transport='tcp',
                bytes=1000,
                packets=10,
                is_internal=True
            ),
            FlowRecord(
                app_name='test_app',
                src_ip='10.1.2.20',
                dst_ip='10.1.3.30',
                protocol='tcp:3306',
                port=3306,
                transport='tcp',
                bytes=5000,
                packets=50,
                is_internal=True
            ),
            FlowRecord(
                app_name='test_app',
                src_ip='203.0.113.45',  # External IP
                dst_ip='10.1.1.10',
                protocol='tcp:443',
                port=443,
                transport='tcp',
                bytes=2000,
                packets=20,
                is_internal=False
            ),
            FlowRecord(
                app_name='test_app',
                src_ip='185.220.101.23',  # Suspicious external
                dst_ip='10.1.1.10',
                protocol='tcp:22',
                port=22,
                transport='tcp',
                bytes=100,
                packets=5,
                is_internal=False,
                is_suspicious=True,
                risk_score=85
            )
        ]
        return records

    def test_analyzer_initialization(self, sample_records):
        """Test analyzer initialization"""
        analyzer = TrafficAnalyzer(sample_records)

        assert len(analyzer.records) == 4
        assert len(analyzer.zones) == 0
        assert len(analyzer.rules) == 0

    def test_compute_summary_stats(self, sample_records):
        """Test computing summary statistics"""
        analyzer = TrafficAnalyzer(sample_records)
        summary = analyzer._compute_summary_stats()

        assert summary['total_flows'] == 4
        assert summary['total_bytes'] == 8100
        assert summary['internal_flows'] == 2
        assert summary['external_flows'] == 2
        assert summary['suspicious_count'] == 1

    def test_identify_top_talkers(self, sample_records):
        """Test identifying top talkers"""
        analyzer = TrafficAnalyzer(sample_records)
        top_talkers = analyzer._identify_top_talkers(top_n=5)

        assert 'top_sources_by_bytes' in top_talkers
        assert 'top_destinations_by_bytes' in top_talkers
        assert isinstance(top_talkers['top_sources_by_bytes'], dict)

    def test_analyze_ports(self, sample_records):
        """Test port analysis"""
        analyzer = TrafficAnalyzer(sample_records)
        port_analysis = analyzer._analyze_ports()

        assert 'total_unique_ports' in port_analysis
        assert 'port_details' in port_analysis

        port_details = port_analysis['port_details']
        assert 8080 in port_details or 3306 in port_details or 443 in port_details

    def test_classify_flows(self, sample_records):
        """Test flow classification"""
        analyzer = TrafficAnalyzer(sample_records)
        classification = analyzer._classify_flows()

        assert 'internal' in classification
        assert 'external_inbound' in classification
        assert 'east_west' in classification
        assert classification['internal'] == 2

    def test_generate_zones(self, sample_records):
        """Test network zone generation"""
        analyzer = TrafficAnalyzer(sample_records)
        zones = analyzer._generate_zones()

        assert isinstance(zones, dict)
        assert 'EXTERNAL' in zones or 'DMZ' in zones or 'INTERNAL' in zones

    def test_generate_segmentation_rules(self, sample_records):
        """Test segmentation rule generation"""
        analyzer = TrafficAnalyzer(sample_records)
        analyzer._generate_zones()  # Generate zones first
        rules = analyzer._generate_segmentation_rules()

        assert len(rules) > 0
        assert all(isinstance(r, SegmentationRule) for r in rules)

        # Check that rules are sorted by priority
        priorities = [r.priority for r in rules]
        assert priorities == sorted(priorities)

    def test_full_analysis(self, sample_records):
        """Test complete analysis workflow"""
        analyzer = TrafficAnalyzer(sample_records)
        results = analyzer.analyze()

        assert 'summary' in results
        assert 'top_talkers' in results
        assert 'port_analysis' in results
        assert 'zones' in results
        assert 'rules' in results

        # Verify some expected values
        assert results['summary']['total_flows'] == 4
        assert len(analyzer.rules) > 0

    def test_export_rules_csv(self, sample_records, tmp_path):
        """Test exporting rules to CSV"""
        analyzer = TrafficAnalyzer(sample_records)
        analyzer.analyze()

        output_file = tmp_path / 'test_rules.csv'
        analyzer.export_rules_csv(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert 'rule_id' in content
        assert 'priority' in content

    def test_export_iptables_rules(self, sample_records, tmp_path):
        """Test exporting IPTables rules"""
        analyzer = TrafficAnalyzer(sample_records)
        analyzer.analyze()

        output_file = tmp_path / 'test_iptables.sh'
        analyzer.export_iptables_rules(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert '#!/bin/bash' in content
        assert 'iptables' in content

    def test_export_aws_security_groups(self, sample_records, tmp_path):
        """Test exporting AWS Security Groups"""
        analyzer = TrafficAnalyzer(sample_records)
        analyzer.analyze()

        output_file = tmp_path / 'test_sg.json'
        analyzer.export_aws_security_groups(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert 'SecurityGroups' in content

    def test_export_analysis_report(self, sample_records, tmp_path):
        """Test exporting analysis report"""
        analyzer = TrafficAnalyzer(sample_records)
        analyzer.analyze()

        output_file = tmp_path / 'test_report.json'
        analyzer.export_analysis_report(str(output_file))

        assert output_file.exists()

        import json
        with open(output_file, 'r') as f:
            report = json.load(f)

        assert 'analysis_timestamp' in report
        assert 'summary' in report
        assert 'zones' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
