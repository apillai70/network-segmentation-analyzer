"""
Unit Tests for Diagram Generation
==================================
Tests for src/diagrams.py - MermaidDiagramGenerator
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import FlowRecord
from src.diagrams import MermaidDiagramGenerator
from src.analysis import NetworkZone


class TestMermaidDiagramGenerator:
    """Test MermaidDiagramGenerator class"""

    @pytest.fixture
    def sample_records(self):
        """Create sample flow records"""
        return [
            FlowRecord(
                app_name='test_app',
                src_ip='10.1.1.10',
                src_hostname='web-01',
                dst_ip='10.1.2.20',
                dst_hostname='app-01',
                protocol='tcp:8080',
                port=8080,
                bytes=1000,
                is_internal=True
            ),
            FlowRecord(
                app_name='test_app',
                src_ip='10.1.2.20',
                src_hostname='app-01',
                dst_ip='10.1.3.30',
                dst_hostname='db-01',
                protocol='tcp:3306',
                port=3306,
                bytes=5000,
                is_internal=True
            )
        ]

    @pytest.fixture
    def sample_zones(self):
        """Create sample zones"""
        return {
            'WEB_TIER': NetworkZone(
                zone_name='WEB_TIER',
                zone_type='micro',
                members={'10.1.1.10'},
                description='Web servers',
                security_level=2
            ),
            'APP_TIER': NetworkZone(
                zone_name='APP_TIER',
                zone_type='micro',
                members={'10.1.2.20'},
                description='App servers',
                security_level=3
            ),
            'DATA_TIER': NetworkZone(
                zone_name='DATA_TIER',
                zone_type='micro',
                members={'10.1.3.30'},
                description='Databases',
                security_level=4
            )
        }

    def test_generator_initialization(self, sample_records, sample_zones):
        """Test diagram generator initialization"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        assert len(generator.records) == 2
        assert len(generator.zones) == 3

    def test_generate_overall_network_diagram(self, sample_records, sample_zones, tmp_path):
        """Test generating overall network diagram"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        output_file = tmp_path / 'network.mmd'
        content = generator.generate_overall_network_diagram(str(output_file))

        assert output_file.exists()
        assert 'graph' in content
        assert 'WEB_TIER' in content or 'APP_TIER' in content

    def test_generate_app_diagram(self, sample_records, sample_zones, tmp_path):
        """Test generating per-app diagram"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        output_file = tmp_path / 'app_diagram.mmd'
        content = generator.generate_app_diagram('test_app', str(output_file))

        assert output_file.exists()
        assert 'graph' in content
        assert len(content) > 0

    def test_generate_zone_flow_diagram(self, sample_records, sample_zones, tmp_path):
        """Test generating zone flow diagram"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        output_file = tmp_path / 'zone_flow.mmd'
        content = generator.generate_zone_flow_diagram(str(output_file))

        assert output_file.exists()
        assert 'graph' in content

    def test_safe_name_conversion(self, sample_records, sample_zones):
        """Test safe name conversion"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        assert generator._safe_name('test.name') == 'test_name'
        assert generator._safe_name('test-name') == 'test_name'
        assert generator._safe_name('test:name') == 'test_name'

    def test_html_diagram_generation(self, sample_records, sample_zones, tmp_path):
        """Test HTML diagram generation"""
        generator = MermaidDiagramGenerator(sample_records, sample_zones)

        mmd_file = tmp_path / 'test.mmd'
        generator.generate_overall_network_diagram(str(mmd_file))

        html_file = tmp_path / 'test.html'
        assert html_file.exists()  # HTML should be created alongside .mmd

        content = html_file.read_text()
        assert '<!DOCTYPE html>' in content
        assert 'mermaid' in content.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
