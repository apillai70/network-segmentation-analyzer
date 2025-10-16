# Word Document Generation - Quick Reference

## Overview

Three types of Word documents are generated, organized in separate folders:

```
outputs_final/word_reports/
├── architecture/              # Architecture documents (both types)
│   ├── Solution_Design-{AppID}.docx  (comprehensive)
│   └── {AppID}_architecture.docx     (simple)
├── netseg/                   # Network segmentation reports
│   └── {AppID}_report.docx
└── threat_surface/           # Threat surface analysis (NEW!)
    └── ThreatSurface-{AppID}.docx
```

## Document Types

### 1. Architecture Documents (Comprehensive)
**Location:** `outputs_final/word_reports/architecture/`
**Filename:** `Solution_Design-{AppID}.docx`
**Generator:** `src/comprehensive_solution_doc_generator.py`

**Contents:**
- Cover page with full branding
- Document control & revision history
- Executive summary
- Application overview (description, characteristics, tech stack)
- Architecture design with embedded diagrams
- Network segmentation details
- Data flows and dependencies
- Security considerations (10+ controls)
- Compliance and risk assessment
- Implementation recommendations
- Appendix with Mermaid code

**Best for:**
- Architecture reviews
- Security audits
- Compliance documentation
- Executive presentations
- Formal documentation

**Generation:**
```bash
python generate_solution_design_docs.py
```

### 2. Application Architecture Documents (Simple)
**Location:** `outputs_final/word_reports/architecture/`
**Filename:** `{AppID}_architecture.docx`
**Generator:** `src/app_docx_generator.py`

**Contents:**
- Title page
- Application data flow diagram (embedded PNG)
- Diagram legend
- Architecture overview
- Tier descriptions (web, app, data, cache, messaging, management)
- External dependencies
- Security considerations

**Best for:**
- Quick reference
- Network team documentation
- Firewall rule requests
- Day-to-day operations

**Generation:**
```bash
python generate_application_word_docs.py
```

### 3. Threat Surface Analysis & Network Segmentation (NEW!)
**Location:** `outputs_final/word_reports/threat_surface/`
**Filename:** `ThreatSurface-{AppID}.docx`
**Generator:** `src/threat_surface_netseg_generator.py`

**Contents:**
- Executive summary with threat scoring
- External attack surface analysis
- Internal attack surface (lateral movement paths)
- Attack vector analysis (5 major categories)
- Zero Trust micro-segmentation strategy
- Specific firewall rules and network ACLs
- Monitoring and threat detection requirements
- Implementation roadmap (phased approach)

**Attack Vectors Covered:**
1. External web application attacks
2. Lateral movement (east-west traffic)
3. Data exfiltration
4. Supply chain attacks
5. Privilege escalation

**Best for:**
- Security assessments and audits
- Threat modeling exercises
- Zero Trust architecture planning
- Network segmentation projects
- Security team planning
- Executive security briefings

**Generation:**
```bash
# Generate for all applications (auto-runs at end of batch processing)
python generate_threat_surface_docs.py

# Batch processing includes this automatically
python run_batch_processing.py --batch-size 10
```

## Quick Start

### Generate All Documents (Both Types)

```bash
# Generate comprehensive architecture documents
python generate_solution_design_docs.py

# Generate simple application architecture documents
python generate_application_word_docs.py

# Generate network segmentation reports (optional)
python generate_all_reports.py
```

### Generate for Specific Application

```python
# Architecture (comprehensive)
from src.comprehensive_solution_doc_generator import generate_comprehensive_solution_document
import json

with open('outputs_final/incremental_topology.json', 'r') as f:
    data = json.load(f)
    app_data = data['topology']['ACDA']

generate_comprehensive_solution_document(
    app_name='ACDA',
    app_data=app_data,
    png_path='outputs_final/diagrams/ACDA_application_diagram.png',
    mermaid_path='outputs_final/diagrams/ACDA_application_diagram.mmd',
    output_path='outputs_final/word_reports/architecture/Solution_Design-ACDA.docx'
)

# Application architecture (simple)
from src.app_docx_generator import generate_application_document

generate_application_document(
    app_name='ACDA',
    png_path='outputs_final/diagrams/ACDA_application_diagram.png',
    output_path='outputs_final/word_reports/architecture/ACDA_architecture.docx'
)
```

## File Organization

### Current Structure
```
outputs_final/
├── diagrams/                       # Source diagrams
│   ├── ACDA_application_diagram.png
│   ├── ACDA_application_diagram.mmd
│   └── ...
└── word_reports/                   # Word documents
    ├── architecture/               # Architecture docs (both types)
    │   ├── Solution_Design-ACDA.docx     (comprehensive)
    │   ├── Solution_Design-AODSVY.docx   (comprehensive)
    │   ├── ACDA_architecture.docx        (simple)
    │   ├── AODSVY_architecture.docx      (simple)
    │   └── ...
    └── netseg/                     # Network segmentation reports
        ├── ACDA_report.docx
        ├── AODSVY_report.docx
        └── ...
```

## When to Use Which Document Type

| Scenario | Use Document Type |
|----------|------------------|
| Security audit | Threat Surface Analysis |
| Threat modeling | Threat Surface Analysis |
| Zero Trust planning | Threat Surface Analysis |
| Network segmentation project | Threat Surface Analysis |
| Architecture review board | Architecture (comprehensive) |
| Compliance documentation | Architecture (comprehensive) |
| Executive presentation | Architecture (comprehensive) or Threat Surface |
| Firewall rule request | NetSeg (simple) or Threat Surface |
| Network team reference | NetSeg (simple) |
| Quick lookup | NetSeg (simple) |
| Day-to-day operations | NetSeg (simple) |
| Penetration test planning | Threat Surface Analysis |
| Security team planning | Threat Surface Analysis |

## Prerequisites

1. **Run analysis pipeline:**
   ```bash
   python start_system.py
   # or
   python run_complete_analysis.py
   ```

2. **Ensure diagrams exist:**
   - PNG and Mermaid files in `outputs_final/diagrams/`

3. **Install dependencies:**
   ```bash
   pip install python-docx
   ```

## Customization

### Architecture Documents
Edit: `src/comprehensive_solution_doc_generator.py`

- Add/remove sections: Create new `_add_*()` methods
- Change styling: Modify `_setup_styles()`
- Update branding: Edit `_add_cover_page()`

### NetSeg Documents
Edit: `src/app_docx_generator.py`

- Simpler structure, fewer sections
- Focus on network segmentation
- Quick to customize

## Batch Generation Performance

| Document Type | Time per App | 100 Apps |
|--------------|--------------|----------|
| Architecture | ~8-12 seconds | ~15-20 min |
| NetSeg | ~3-5 seconds | ~5-8 min |

## Troubleshooting

### No diagrams found
```bash
# Generate diagrams first
python generate_application_reports.py
```

### Missing application data
```bash
# Run analysis
python start_system.py
```

### Path issues
Check that you're running from the project root directory.

## Tips

1. **Generate both types** for complete documentation coverage
2. **Use architecture docs** for formal reviews and audits
3. **Use netseg docs** for operational work
4. **Customize templates** before batch generation
5. **Review one document** before generating all

## Document Authorship

- **Architecture Documents**: Prepared by Enterprise Architecture Team
- **NetSeg Documents**: Prepared by Network Security Team

## Related Files

- `SOLUTION_DESIGN_DOCS_GUIDE.md` - Detailed guide for architecture documents
- `generate_solution_design_docs.py` - Batch generator for architecture docs
- `generate_application_word_docs.py` - Batch generator for netseg docs
- `src/comprehensive_solution_doc_generator.py` - Architecture document generator
- `src/app_docx_generator.py` - NetSeg document generator

## Support

Check logs:
- `solution_docs_generation.log` - Architecture docs log
- `logs/word_docs_*.log` - NetSeg docs log
