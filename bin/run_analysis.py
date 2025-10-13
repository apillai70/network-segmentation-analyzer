#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Segmentation Analysis - CLI Entry Point
================================================
Command-line interface for running complete network segmentation analysis.

Usage:
    python bin/run_analysis.py --data-dir data/input --output-dir outputs
    python bin/run_analysis.py --app app_1 --verbose
    python bin/run_analysis.py --dry-run

Author: Network Security Team
Version: 2.0
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # Set console to UTF-8
    os.system('chcp 65001 > nul 2>&1')

# Add src to Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Import using importlib to avoid package conflicts
import importlib.util

def load_module(module_name, file_path):
    """Dynamically load a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load our modules
parser_module = load_module('network_parser', root_dir / 'src' / 'parser.py')
analysis_module = load_module('network_analysis', root_dir / 'src' / 'analysis.py')
diagrams_module = load_module('network_diagrams', root_dir / 'src' / 'diagrams.py')
docx_module = load_module('network_docx', root_dir / 'src' / 'docx_generator.py')
ml_predictor_module = load_module('ml_predictor', root_dir / 'src' / 'ml_predictor.py')
enterprise_analyzer_module = load_module('enterprise_analyzer', root_dir / 'enterprise_network_analyzer.py')

NetworkLogParser = parser_module.NetworkLogParser
TrafficAnalyzer = analysis_module.TrafficAnalyzer
MermaidDiagramGenerator = diagrams_module.MermaidDiagramGenerator
SolutionsArchitectureDocument = docx_module.SolutionsArchitectureDocument
MLNetworkPredictor = ml_predictor_module.MLNetworkPredictor
PersistenceManager = enterprise_analyzer_module.PersistenceManager
EnsembleNetworkModel = enterprise_analyzer_module.EnsembleNetworkModel


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def print_banner():
    """Print application banner"""
    banner = """
===============================================================

   Network Segmentation Analyzer
   Automated Security Analysis & Rule Generation

   Version: 2.0
   Author: Network Security Team

===============================================================
    """
    print(banner)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_analysis(args):
    """Run complete network segmentation analysis"""
    print_banner()

    # Create output directories
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'diagrams').mkdir(exist_ok=True)

    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting network segmentation analysis")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Output directory: {args.output_dir}")

    try:
        # Step 1: Parse network logs
        print_section("STEP 1: Parsing Network Traffic Logs")
        print(f"📂 Reading logs from: {args.data_dir}")

        parser = NetworkLogParser(args.data_dir)
        parser.parse_all_logs()

        stats = parser.get_summary_stats()
        print(f"\n✅ Parsing Complete!")
        print(f"   Total records parsed: {stats['total_records']:,}")
        print(f"   Applications found: {stats['apps_parsed']}")
        print(f"   Unique source IPs: {stats['unique_src_ips']}")
        print(f"   Unique destination IPs: {stats['unique_dst_ips']}")
        print(f"   Suspicious flows: {stats['suspicious_flows']}")
        print(f"   Total bytes: {stats['total_bytes'] / (1024**3):.2f} GB")

        if args.dry_run:
            print("\n⚠️  DRY RUN MODE - Stopping after parsing")
            return 0

        # Export normalized data
        normalized_path = output_dir / 'normalized_flows.csv'
        parser.export_normalized_csv(str(normalized_path))
        print(f"   Normalized data exported: {normalized_path}")

        # Step 2: Traffic Analysis
        print_section("STEP 2: Traffic Analysis & Rule Generation")

        analyzer = TrafficAnalyzer(parser.records)
        analysis_results = analyzer.analyze()

        print(f"\n✅ Analysis Complete!")
        print(f"   Network zones identified: {len(analyzer.zones)}")
        print(f"   Segmentation rules generated: {len(analyzer.rules)}")
        print(f"   Top talkers identified: {len(analysis_results.get('top_talkers', {}).get('top_sources_by_bytes', {}))}")

        # Export analysis artifacts
        print(f"\n📤 Exporting analysis artifacts...")
        analyzer.export_rules_csv(str(output_dir / 'segmentation_rules.csv'))
        analyzer.export_iptables_rules(str(output_dir / 'iptables_rules.sh'))
        analyzer.export_aws_security_groups(str(output_dir / 'aws_security_groups.json'))
        analyzer.export_analysis_report(str(output_dir / 'analysis_report.json'))
        print(f"   ✓ Rules exported (CSV, IPTables, AWS SG)")

        # Step 2.5: ML Prediction for Apps Without Data
        print_section("STEP 2.5: ML Prediction for Apps Without Data")

        # Check if app catalog exists
        app_catalog_path = root_dir / 'config' / 'app_catalog.json'
        ml_predictions = None

        if app_catalog_path.exists():
            import json
            with open(app_catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)

            all_apps = catalog_data['applications']
            apps_with_data = set(catalog_data.get('apps_with_data', []))

            # Only run ML prediction if we have apps without data
            apps_without_data = set(all_apps) - apps_with_data

            if apps_without_data:
                print(f"📊 Total applications in catalog: {len(all_apps)}")
                print(f"   Apps with traffic data: {len(apps_with_data)}")
                print(f"   Apps requiring prediction: {len(apps_without_data)}")

                try:
                    # Initialize ML components
                    print(f"\n🤖 Initializing ML ensemble models...")
                    db_path = output_dir / 'network_analysis.db'
                    persistence = PersistenceManager(str(db_path))
                    ensemble = EnsembleNetworkModel(persistence)

                    # Initialize ML predictor
                    ml_predictor = MLNetworkPredictor(persistence, ensemble)

                    # Train on observed apps
                    print(f"🎓 Training ensemble models on {len(apps_with_data)} observed apps...")
                    training_results = ml_predictor.train_on_observed_apps(parser.records)

                    print(f"   ✓ Training complete!")
                    print(f"   • Observed apps: {training_results.get('observed_apps_count', 0)}")
                    print(f"   • Total flows: {training_results.get('total_flows', 0):,}")
                    print(f"   • Network zones: {training_results.get('zones_identified', 0)}")

                    # Predict missing apps
                    print(f"\n🔮 Predicting network patterns for {len(apps_without_data)} apps...")
                    ml_predictions = ml_predictor.predict_missing_apps(all_apps)

                    print(f"\n✅ ML Prediction Complete!")
                    print(f"   • Apps predicted: {len(ml_predictions)}")

                    # Show sample predictions
                    if ml_predictions:
                        print(f"\n   Sample predictions:")
                        sample_count = 0
                        for app_name, pred in list(ml_predictions.items())[:5]:
                            confidence = pred.get('confidence', 0) * 100
                            zone = pred.get('predicted_zone', 'UNKNOWN')
                            similar_count = len(pred.get('similar_apps', []))
                            print(f"   • {app_name}: {zone} (confidence: {confidence:.0f}%, {similar_count} similar apps)")
                            sample_count += 1

                    # Export ML predictions
                    ml_predictions_path = output_dir / 'ml_predictions.json'
                    with open(ml_predictions_path, 'w', encoding='utf-8') as f:
                        json.dump(ml_predictions, f, indent=2, ensure_ascii=False)
                    print(f"\n   ✓ ML predictions exported: {ml_predictions_path}")

                    # Add predictions to analysis results
                    analysis_results['ml_predictions'] = {
                        'total_predicted_apps': len(ml_predictions),
                        'predictions': ml_predictions,
                        'training_stats': training_results
                    }

                except Exception as e:
                    print(f"\n⚠️  Warning: ML prediction failed: {e}")
                    logger.warning(f"ML prediction error: {e}", exc_info=True)
                    print(f"   Continuing without ML predictions...")
            else:
                print(f"ℹ️  All {len(all_apps)} applications have traffic data - no prediction needed")
        else:
            print(f"ℹ️  App catalog not found at {app_catalog_path}")
            print(f"   Skipping ML prediction step")

        # Step 3: Generate Diagrams
        print_section("STEP 3: Generating Network Diagrams")

        diagram_gen = MermaidDiagramGenerator(parser.records, analyzer.zones)

        # Overall network diagram
        overall_mmd = output_dir / 'diagrams' / 'overall_network.mmd'
        diagram_gen.generate_overall_network_diagram(str(overall_mmd))
        print(f"   ✓ Overall network diagram: {overall_mmd}")

        # Zone flow diagram
        zone_flow_mmd = output_dir / 'diagrams' / 'zone_flows.mmd'
        diagram_gen.generate_zone_flow_diagram(str(zone_flow_mmd))
        print(f"   ✓ Zone flow diagram: {zone_flow_mmd}")

        # Per-app diagrams
        if args.app:
            # Generate specific app diagram
            app_mmd = output_dir / 'diagrams' / f'{args.app}_diagram.mmd'
            diagram_gen.generate_app_diagram(args.app, str(app_mmd))
            print(f"   ✓ Application diagram for {args.app}: {app_mmd}")
        else:
            # Generate all app diagrams
            diagrams = diagram_gen.generate_all_app_diagrams(str(output_dir / 'diagrams'))
            print(f"   ✓ Generated {len(diagrams)} application diagrams")

        print(f"\n💡 Tip: Open the .html files in a browser to view interactive diagrams")

        # Step 4: Generate Solutions Architecture Document
        print_section("STEP 4: Creating Solutions Architecture Document")

        doc_gen = SolutionsArchitectureDocument(
            analysis_results,
            analyzer.zones,
            analyzer.rules,
            ml_predictions=ml_predictions
        )

        doc_path = output_dir / 'network_segmentation_solution.docx'
        doc_gen.generate_document(str(doc_path))

        print(f"\n✅ Solutions Document Generated!")
        print(f"   Document: {doc_path}")
        print(f"   Pages: ~25-30")
        print(f"   Sections: Executive Summary, Analysis, Design, Rules, Implementation")

        # Final Summary
        print_section("ANALYSIS COMPLETE")
        print(f"✅ All outputs generated successfully!")
        print(f"\n📊 Summary:")
        print(f"   • Parsed {stats['total_records']:,} network flows")
        print(f"   • Identified {len(analyzer.zones)} network zones")
        print(f"   • Generated {len(analyzer.rules)} segmentation rules")
        if ml_predictions:
            print(f"   • Predicted network patterns for {len(ml_predictions)} apps using ML")
        print(f"   • Created {len(list((output_dir / 'diagrams').glob('*.html')))} interactive diagrams")
        print(f"   • Produced comprehensive Solutions Architecture Document")

        print(f"\n📁 Output Directory: {output_dir}")
        print(f"\n   Key Files:")
        print(f"   ├── network_segmentation_solution.docx  (Solutions Document)")
        print(f"   ├── segmentation_rules.csv               (All rules in CSV)")
        print(f"   ├── iptables_rules.sh                    (Linux firewall rules)")
        print(f"   ├── aws_security_groups.json             (AWS security groups)")
        print(f"   ├── analysis_report.json                 (Full analysis data)")
        if ml_predictions:
            print(f"   ├── ml_predictions.json                  (ML predictions for apps without data)")
        print(f"   └── diagrams/")
        print(f"       ├── overall_network.html             (Interactive network map)")
        print(f"       ├── zone_flows.html                  (Zone traffic flows)")
        print(f"       └── app_*.html                       (Per-app diagrams)")

        print(f"\n🎯 Next Steps:")
        print(f"   1. Review the Solutions Architecture Document")
        print(f"   2. Validate the segmentation rules with your team")
        print(f"   3. Test rules in staging environment")
        print(f"   4. Plan phased production rollout")

        print(f"\n{'='*60}\n")

        logger.info("Analysis completed successfully")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Please ensure the data directory exists and contains CSV files.")
        logger.error(f"File not found: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: An unexpected error occurred")
        print(f"   {e}")
        logger.exception("Unexpected error during analysis")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Network Segmentation Analysis Tool - Automated security analysis and rule generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete analysis on all applications
  python bin/run_analysis.py

  # Specify custom data and output directories
  python bin/run_analysis.py --data-dir /path/to/logs --output-dir results

  # Analyze specific application
  python bin/run_analysis.py --app app_1

  # Dry run (parse only, no analysis)
  python bin/run_analysis.py --dry-run

  # Verbose logging for debugging
  python bin/run_analysis.py --verbose

For more information, see README.md
        """
    )

    parser.add_argument(
        '--data-dir',
        default='data/input',
        help='Directory containing network traffic CSV files (default: data/input)'
    )

    parser.add_argument(
        '--output-dir',
        default='outputs',
        help='Directory for output files (default: outputs)'
    )

    parser.add_argument(
        '--app',
        help='Analyze specific application only (e.g., app_1, app_2)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse logs only, skip analysis and report generation'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing output files without confirmation'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Network Segmentation Analyzer 2.0'
    )

    args = parser.parse_args()

    # Check if output directory exists and not empty
    output_path = Path(args.output_dir)
    if output_path.exists() and any(output_path.iterdir()) and not args.force:
        print(f"⚠️  Warning: Output directory '{args.output_dir}' is not empty.")
        response = input("Continue and overwrite existing files? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted.")
            return 1

    # Run analysis
    return run_analysis(args)


if __name__ == '__main__':
    sys.exit(main())
