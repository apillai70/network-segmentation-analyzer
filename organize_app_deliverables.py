#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Organize Application Deliverables
==================================
Creates one folder per application and copies all related files:
- Word reports (architecture, solution design, netseg, threat surface)
- Diagrams (PNG, SVG, MMD, HTML)
- Enhanced diagrams
- Enriched flows
- HTML reports

Usage:
    python organize_app_deliverables.py
    python organize_app_deliverables.py --output-dir results
"""

import sys
import shutil
from pathlib import Path
import argparse
import re

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def discover_app_codes():
    """Discover all app codes from CSV files"""
    processed_dir = Path('data/input/processed')

    if not processed_dir.exists():
        print(f"ERROR: Directory not found: {processed_dir}")
        return []

    pattern = re.compile(r'^App_Code_([A-Za-z0-9_-]+)\.csv$', re.IGNORECASE)
    app_codes = []

    for file_path in processed_dir.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)
            if match:
                app_codes.append(match.group(1))

    return sorted(app_codes)


def copy_file_safe(src, dst):
    """Copy file safely, creating parent directories if needed"""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"    [WARNING] Failed to copy {src.name}: {e}")
        return False


def organize_app_files(app_code, output_base_dir):
    """
    Organize all files for a specific application

    Args:
        app_code: Application code (e.g., 'ACDA')
        output_base_dir: Base output directory (e.g., 'results')

    Returns:
        Dictionary with counts of copied files by category
    """
    # Create app directory
    app_dir = output_base_dir / app_code
    app_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'word_docs': 0,
        'diagrams': 0,
        'enhanced_diagrams': 0,
        'enriched_flows': 0,
        'html_reports': 0
    }

    # 1. Word Documents
    word_sources = [
        (Path('outputs_final/word_reports/architecture'), f'{app_code}_architecture.docx'),
        (Path('outputs_final/word_reports/architecture'), f'Solution_Design-{app_code}.docx'),
        (Path('outputs_final/word_reports/netseg'), f'NetSeg-{app_code}.docx'),
        (Path('outputs_final/word_reports/threat_surface'), f'ThreatSurface-{app_code}.docx'),
    ]

    word_dir = app_dir / 'word_reports'
    for src_dir, filename in word_sources:
        src_file = src_dir / filename
        if src_file.exists():
            dst_file = word_dir / filename
            if copy_file_safe(src_file, dst_file):
                stats['word_docs'] += 1

    # 2. Standard Diagrams (PNG, SVG, MMD, HTML)
    diagram_dir = Path('outputs_final/diagrams')
    if diagram_dir.exists():
        diagram_patterns = [
            f'{app_code}_diagram.png',
            f'{app_code}_diagram.svg',
            f'{app_code}_diagram.mmd',
            f'{app_code}_diagram.html',
            f'{app_code}_application_diagram.png',
            f'{app_code}_application_diagram.svg',
            f'{app_code}_application_diagram.mmd',
            f'{app_code}_application_diagram.html',
        ]

        diagrams_dest = app_dir / 'diagrams'
        for pattern in diagram_patterns:
            src_file = diagram_dir / pattern
            if src_file.exists():
                dst_file = diagrams_dest / src_file.name
                if copy_file_safe(src_file, dst_file):
                    stats['diagrams'] += 1

    # 3. Enhanced Diagrams
    enhanced_dir = Path('outputs_final/enhanced_diagrams')
    if enhanced_dir.exists():
        enhanced_patterns = [
            f'{app_code}_enhanced_application_diagram.html',
            f'{app_code}_enhanced_application_diagram.mmd',
            f'{app_code}_enhanced_application_diagram.png',
            f'{app_code}_enhanced_application_diagram.svg',
        ]

        enhanced_dest = app_dir / 'enhanced_diagrams'
        for pattern in enhanced_patterns:
            src_file = enhanced_dir / pattern
            if src_file.exists():
                dst_file = enhanced_dest / src_file.name
                if copy_file_safe(src_file, dst_file):
                    stats['enhanced_diagrams'] += 1

    # 4. Enriched Flows
    flows_dir = Path('outputs_final/enriched_flows')
    if flows_dir.exists():
        flow_patterns = [
            f'{app_code}_enriched_flows.csv',
            f'{app_code}_enriched_flows.json',
        ]

        flows_dest = app_dir / 'enriched_flows'
        for pattern in flow_patterns:
            src_file = flows_dir / pattern
            if src_file.exists():
                dst_file = flows_dest / src_file.name
                if copy_file_safe(src_file, dst_file):
                    stats['enriched_flows'] += 1

    # 5. HTML Reports - Enhanced
    html_enhanced_dir = Path('outputs/html/enhanced')
    if html_enhanced_dir.exists():
        html_enhanced_patterns = [
            f'{app_code}_enhanced_application_diagram.html',
        ]

        html_dest = app_dir / 'html_reports' / 'enhanced'
        for pattern in html_enhanced_patterns:
            src_file = html_enhanced_dir / pattern
            if src_file.exists():
                dst_file = html_dest / src_file.name
                if copy_file_safe(src_file, dst_file):
                    stats['html_reports'] += 1

    # 6. HTML Reports - Threat
    html_threat_dir = Path('outputs/html/threat')
    if html_threat_dir.exists():
        html_threat_patterns = [
            f'{app_code}_threat_surface.html',
        ]

        html_dest = app_dir / 'html_reports' / 'threat'
        for pattern in html_threat_patterns:
            src_file = html_threat_dir / pattern
            if src_file.exists():
                dst_file = html_dest / src_file.name
                if copy_file_safe(src_file, dst_file):
                    stats['html_reports'] += 1

    return stats


def create_app_readme(app_dir, app_code, stats):
    """Create a README file for the app directory"""
    readme_path = app_dir / 'README.md'

    total_files = sum(stats.values())

    content = f"""# {app_code} - Application Deliverables

## Contents

This folder contains all deliverables for application **{app_code}**.

### Files Included ({total_files} total)

- **Word Documents** ({stats['word_docs']} files)
  - Architecture Document: `{app_code}_architecture.docx`
  - Solution Design: `Solution_Design-{app_code}.docx`
  - Network Segmentation: `NetSeg-{app_code}.docx`
  - Threat Surface: `ThreatSurface-{app_code}.docx`

- **Diagrams** ({stats['diagrams']} files)
  - PNG, SVG, MMD, HTML formats
  - Application and standard diagrams

- **Enhanced Diagrams** ({stats['enhanced_diagrams']} files)
  - Enhanced application diagrams with Zero Trust analysis
  - Multiple formats available

- **Enriched Flows** ({stats['enriched_flows']} files)
  - CSV and JSON formats
  - Complete flow data with enrichment

- **HTML Reports** ({stats['html_reports']} files)
  - Interactive HTML visualizations
  - Enhanced and threat surface views

## Folder Structure

```
{app_code}/
├── word_reports/          # Word documents
├── diagrams/              # Standard diagrams
├── enhanced_diagrams/     # Enhanced diagrams
├── enriched_flows/        # Flow data
├── html_reports/          # HTML visualizations
│   ├── enhanced/
│   └── threat/
└── README.md             # This file
```

## Generated

- Date: {Path.cwd()}
- Application Code: {app_code}
- Total Files: {total_files}
"""

    try:
        readme_path.write_text(content, encoding='utf-8')
    except Exception as e:
        print(f"    [WARNING] Failed to create README: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Organize application deliverables into per-app folders'
    )
    parser.add_argument(
        '--output-dir',
        default='results',
        help='Output directory for organized files (default: results)'
    )
    parser.add_argument(
        '--apps',
        nargs='+',
        help='Specific app codes to process (default: all discovered apps)'
    )

    args = parser.parse_args()

    print("="*80)
    print("APPLICATION DELIVERABLES ORGANIZER")
    print("="*80)
    print()

    # Determine which apps to process
    if args.apps:
        app_codes = args.apps
        print(f"Processing {len(app_codes)} specified applications...")
    else:
        print("[1/4] Discovering application codes...")
        app_codes = discover_app_codes()
        print(f"      Found {len(app_codes)} applications")

    if not app_codes:
        print("ERROR: No applications found")
        sys.exit(1)

    print()

    # Create output directory
    output_base_dir = Path(args.output_dir)
    output_base_dir.mkdir(parents=True, exist_ok=True)
    print(f"[2/4] Output directory: {output_base_dir.absolute()}")
    print()

    # Process each application
    print(f"[3/4] Organizing files for {len(app_codes)} applications...")
    print()

    total_stats = {
        'word_docs': 0,
        'diagrams': 0,
        'enhanced_diagrams': 0,
        'enriched_flows': 0,
        'html_reports': 0
    }

    success_count = 0
    empty_count = 0

    for idx, app_code in enumerate(app_codes, 1):
        print(f"  [{idx}/{len(app_codes)}] {app_code}...", end=' ', flush=True)

        # Organize files
        stats = organize_app_files(app_code, output_base_dir)

        # Update totals
        for key in total_stats:
            total_stats[key] += stats[key]

        total_files = sum(stats.values())

        if total_files > 0:
            # Create README
            create_app_readme(output_base_dir / app_code, app_code, stats)
            print(f"✓ ({total_files} files)")
            success_count += 1
        else:
            print("⊘ (no files found)")
            empty_count += 1

    print()
    print("[4/4] Summary")
    print()

    # Print summary
    print("="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print()
    print(f"Applications Processed:    {len(app_codes)}")
    print(f"  With Files:              {success_count}")
    print(f"  Without Files:           {empty_count}")
    print()
    print("Total Files Copied:")
    print(f"  Word Documents:          {total_stats['word_docs']}")
    print(f"  Standard Diagrams:       {total_stats['diagrams']}")
    print(f"  Enhanced Diagrams:       {total_stats['enhanced_diagrams']}")
    print(f"  Enriched Flows:          {total_stats['enriched_flows']}")
    print(f"  HTML Reports:            {total_stats['html_reports']}")
    print(f"  TOTAL:                   {sum(total_stats.values())}")
    print()
    print(f"Output Location: {output_base_dir.absolute()}")
    print()
    print("Each application folder contains:")
    print("  - All related documents and diagrams")
    print("  - README.md with folder contents")
    print()
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
