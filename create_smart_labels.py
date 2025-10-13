#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Label Generator - Analyze Files to Determine Zones
=========================================================
This script analyzes flow files and makes intelligent predictions about zones
based on multiple signals:

1. NAMING PATTERNS (app name archetypes)
2. NETWORK BEHAVIOR (ports, protocols)
3. TRAFFIC CHARACTERISTICS (bytes, packets, patterns)

Author: Enterprise Security Team
"""

import sys
import os
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartLabelGenerator:
    """Analyzes flow files to predict zones based on multiple signals"""

    def __init__(self):
        # Naming pattern rules
        self.name_patterns = {
            'WEB_TIER': ['web', 'ui', 'frontend', 'portal', 'www', 'http'],
            'APP_TIER': ['api', 'service', 'app', 'backend', 'gateway', 'proxy'],
            'DATA_TIER': ['db', 'database', 'sql', 'dm_', 'datamart', 'warehouse', 'oracle', 'postgres'],
            'MESSAGING_TIER': ['mq', 'queue', 'kafka', 'rabbit', 'messaging', 'jms'],
            'CACHE_TIER': ['cache', 'redis', 'memcache', 'memcached'],
            'MANAGEMENT_TIER': ['admin', 'mgmt', 'manage', 'monitor', 'dashboard'],
            'INFRASTRUCTURE_TIER': ['dns', 'ldap', 'ad', 'auth', 'identity', 'idm']
        }

        # Port-based rules
        self.port_patterns = {
            'WEB_TIER': [80, 443, 8080, 8443],
            'APP_TIER': [8000, 8001, 8080, 9090, 5000],
            'DATA_TIER': [3306, 5432, 1521, 1433, 27017, 9042],  # MySQL, Postgres, Oracle, SQL Server, MongoDB, Cassandra
            'MESSAGING_TIER': [5672, 9092, 61616],  # RabbitMQ, Kafka, ActiveMQ
            'CACHE_TIER': [6379, 11211],  # Redis, Memcached
        }

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single flow file and predict zone"""

        app_name = file_path.stem.replace('App_Code_', '')
        df = pd.read_csv(file_path)

        # Score each zone based on multiple signals
        zone_scores = {}

        # Signal 1: Naming patterns (weight: 0.4)
        name_scores = self._analyze_name(app_name)
        for zone, score in name_scores.items():
            zone_scores[zone] = zone_scores.get(zone, 0) + (score * 0.4)

        # Signal 2: Port patterns (weight: 0.3)
        port_scores = self._analyze_ports(df)
        for zone, score in port_scores.items():
            zone_scores[zone] = zone_scores.get(zone, 0) + (score * 0.3)

        # Signal 3: Traffic patterns (weight: 0.3)
        traffic_scores = self._analyze_traffic(df, app_name)
        for zone, score in traffic_scores.items():
            zone_scores[zone] = zone_scores.get(zone, 0) + (score * 0.3)

        # Pick zone with highest score
        if zone_scores:
            best_zone = max(zone_scores, key=zone_scores.get)
            confidence = zone_scores[best_zone]
        else:
            best_zone = 'APP_TIER'
            confidence = 0.3  # Low confidence default

        return {
            'app_name': app_name,
            'predicted_zone': best_zone,
            'confidence': round(confidence, 2),
            'name_match': name_scores.get(best_zone, 0) > 0,
            'port_match': port_scores.get(best_zone, 0) > 0,
            'signals_used': f"Name:{name_scores.get(best_zone, 0):.2f}, Port:{port_scores.get(best_zone, 0):.2f}, Traffic:{traffic_scores.get(best_zone, 0):.2f}"
        }

    def _analyze_name(self, app_name: str) -> dict:
        """Analyze app name for zone hints"""
        scores = {}
        name_lower = app_name.lower()

        for zone, patterns in self.name_patterns.items():
            for pattern in patterns:
                if pattern in name_lower:
                    # Exact match gets higher score
                    if app_name.lower().startswith(pattern):
                        scores[zone] = scores.get(zone, 0) + 1.0
                    else:
                        scores[zone] = scores.get(zone, 0) + 0.7

        return scores

    def _analyze_ports(self, df: pd.DataFrame) -> dict:
        """Analyze destination ports for zone hints"""
        scores = {}

        if 'Dest Port' not in df.columns:
            return scores

        # Get most common ports
        port_counts = df['Dest Port'].value_counts()

        for zone, ports in self.port_patterns.items():
            for port in ports:
                if port in port_counts.index:
                    # Higher score if this port is very common
                    port_freq = port_counts[port] / len(df)
                    scores[zone] = scores.get(zone, 0) + port_freq

        return scores

    def _analyze_traffic(self, df: pd.DataFrame, app_name: str) -> dict:
        """Analyze traffic patterns for zone hints"""
        scores = {}

        # Pattern 1: Many inbound connections (web tier)
        if 'Source IP' in df.columns:
            unique_sources = df['Source IP'].nunique()
            if unique_sources > 10:  # Many different sources
                scores['WEB_TIER'] = scores.get('WEB_TIER', 0) + 0.5

        # Pattern 2: Few destinations (database tier - apps connect to DB)
        if 'Dest IP' in df.columns:
            unique_dests = df['Dest IP'].nunique()
            if unique_dests <= 3:  # Few destinations
                scores['DATA_TIER'] = scores.get('DATA_TIER', 0) + 0.3

        # Pattern 3: High bytes/packets (database/data transfer)
        if 'Bytes' in df.columns:
            avg_bytes = df['Bytes'].mean()
            if avg_bytes > 5000:  # Large transfers
                scores['DATA_TIER'] = scores.get('DATA_TIER', 0) + 0.3

        # Pattern 4: Many protocols (infrastructure)
        if 'Protocol' in df.columns:
            unique_protocols = df['Protocol'].nunique()
            if unique_protocols > 2:
                scores['INFRASTRUCTURE_TIER'] = scores.get('INFRASTRUCTURE_TIER', 0) + 0.2

        return scores

    def generate_labels(self, input_dir='data/input/processed'):
        """Generate smart labels for all files"""

        files = list(Path(input_dir).glob('App_Code_*.csv'))

        print(f"\n{'='*80}")
        print(f"SMART LABEL GENERATION")
        print(f"{'='*80}")
        print(f"Analyzing {len(files)} files...")
        print()

        results = []
        zone_counts = Counter()

        for file_path in sorted(files):
            result = self.analyze_file(file_path)
            results.append(result)
            zone_counts[result['predicted_zone']] += 1

            # Show high-confidence predictions
            if result['confidence'] >= 0.7:
                print(f"✓ {result['app_name']:20s} -> {result['predicted_zone']:20s} ({result['confidence']:.0%}) [{result['signals_used']}]")

        # Create DataFrame
        df = pd.DataFrame(results)

        # Add full confidence for ground truth (user can adjust)
        df['zone'] = df['predicted_zone']
        df['ground_truth_confidence'] = 1.0

        # Sort by confidence (review low confidence first)
        df_sorted = df.sort_values('confidence')

        # Save to CSV
        output_file = 'smart_labels.csv'
        df_sorted[['app_name', 'zone', 'ground_truth_confidence']].to_csv(output_file, index=False)

        # Save detailed analysis
        analysis_file = 'label_analysis.csv'
        df_sorted.to_csv(analysis_file, index=False)

        print(f"\n{'='*80}")
        print(f"LABEL GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"\nZone Distribution:")
        for zone, count in zone_counts.most_common():
            pct = (count / len(results)) * 100
            print(f"  {zone:25s}: {count:3d} ({pct:5.1f}%)")

        print(f"\nConfidence Distribution:")
        print(f"  High (≥0.7):   {len(df[df['confidence'] >= 0.7]):3d} apps")
        print(f"  Medium (0.4-0.7): {len(df[(df['confidence'] >= 0.4) & (df['confidence'] < 0.7)]):3d} apps")
        print(f"  Low (<0.4):    {len(df[df['confidence'] < 0.4]):3d} apps")

        print(f"\nOutput Files:")
        print(f"  {output_file:25s} - Labels for training (REVIEW & EDIT!)")
        print(f"  {analysis_file:25s} - Detailed analysis")

        print(f"\n⚠️  IMPORTANT:")
        print(f"  1. Review {output_file}")
        print(f"  2. Correct any wrong zones (especially low confidence ones)")
        print(f"  3. Run: python train_with_labels.py --labels-file {output_file}")
        print(f"{'='*80}\n")

        return df


def main():
    generator = SmartLabelGenerator()
    df_results = generator.generate_labels()

    # Show some examples
    print(f"\nExample Predictions (High Confidence):")
    print(f"{'='*80}")
    high_conf = df_results[df_results['confidence'] >= 0.7].head(10)

    for _, row in high_conf.iterrows():
        print(f"{row['app_name']:20s} -> {row['predicted_zone']:20s} ({row['confidence']:.0%})")
        print(f"  Signals: {row['signals_used']}")
        print(f"  Name match: {'✓' if row['name_match'] else '✗'}, Port match: {'✓' if row['port_match'] else '✗'}")
        print()


if __name__ == '__main__':
    main()
