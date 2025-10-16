# Network Segmentation Analyzer - Command Reference Guide

**Quick Reference for All Scripts and Commands**

---

## 📋 TABLE OF CONTENTS

1. [Initial Setup & Analysis](#initial-setup--analysis)
2. [Diagram Generation (MMD, HTML, PNG)](#diagram-generation)
3. [Document Generation (Word)](#document-generation)
4. [Batch Processing](#batch-processing)
5. [Reports (Enterprise, DNS, Threat Surface)](#reports)
6. [Web Interface](#web-interface)
7. [Maintenance & Utilities](#maintenance--utilities)

---

## 🚀 INITIAL SETUP & ANALYSIS

### Complete Analysis Pipeline
```bash
# Option 1: Complete analysis with all steps
python start_system.py

# Option 2: Complete analysis (alternative)
python run_complete_analysis.py

# Option 3: Batch processing with incremental learning
python run_batch_processing.py --batch-size 10
```

**What they do:**
- Process CSV flow data
- Run ML predictions
- Generate topology
- Create diagrams (MMD + HTML + PNG)
- Generate reports

**Output locations:**
- `outputs_final/incremental_topology.json`
- `persistent_data/topology/*.json`
- `outputs_final/diagrams/*.html`
- `outputs_final/diagrams/*.mmd`
- `outputs_final/diagrams/*.png`

---

## 🎨 DIAGRAM GENERATION

### 1. Generate Mermaid (MMD) Files Only

#### Regenerate ALL MMD files
```bash
python regenerate_all_mmds.py
```

#### Regenerate SINGLE application MMD
```bash
python regenerate_acda_diagram.py
```
*(Edit the script to change the app name)*

**Output:**
- `outputs_final/diagrams/{APP}_diagram.mmd` (standard tier diagram)
- `outputs_final/diagrams/{APP}_application_diagram.mmd` (application architecture)

---

### 2. Generate HTML Files (Interactive Diagrams)

HTML files are generated automatically during:
```bash
python run_batch_processing.py
# or
python generate_application_reports.py
```

**Manual HTML generation:**
Edit `src/diagrams.py` or `src/application_diagram_generator.py` and run your script.

**Output:**
- `outputs_final/diagrams/{APP}_diagram.html` (zoomable, interactive)
- `outputs_final/diagrams/{APP}_application_diagram.html`

---

### 3. Generate PNG Images (4 Methods)

#### Method 1: Python-based (Recommended - No Node.js)
```bash
python generate_pngs_python.py
```
- Uses Playwright with Python
- No Node.js dependencies
- Generates from HTML files

#### Method 2: mmdc CLI (If Node.js installed)
```bash
python generate_pngs_mmdc.py
```
- Requires `npm install -g @mermaid-js/mermaid-cli`
- Generates from MMD files directly

#### Method 3: Playwright HTML rendering
```bash
python generate_pngs_playwright.py
```
- Similar to Method 1
- Alternative implementation

#### Method 4: Regenerate failed PNGs only
```bash
python regenerate_failed_pngs.py
```
- Only regenerates missing PNG files
- Checks `outputs_final/diagrams/` for missing PNGs

**Output:**
- `outputs_final/diagrams/{APP}_diagram.png`
- `outputs_final/diagrams/{APP}_application_diagram.png`

---

### 4. Generate Lucidchart-Compatible Files

**Not directly supported**, but you can:

1. **Export MMD files:**
   - MMD files are in `outputs_final/diagrams/*.mmd`
   - Import into Lucidchart using Mermaid import feature

2. **Use HTML/PNG:**
   - Import PNG screenshots into Lucidchart
   - Or copy Mermaid code from `.mmd` files

---

## 📄 DOCUMENT GENERATION (WORD)

### 1. Network Segmentation Solutions Architecture Documents (Comprehensive)

```bash
# Generate for ALL applications
python generate_solution_design_docs.py

# Output location:
# outputs_final/word_reports/architecture/Solution_Design-{APP}.docx
```

**Contents:**
- Cover page with branding
- Executive summary
- Application overview
- Architecture design with embedded diagrams
- Network segmentation details
- Security considerations (10+ controls)
- Compliance and risk assessment
- Implementation recommendations
- Appendix with Mermaid code

**Prepared by:** Enterprise Architecture Team

---

### 2. Application Architecture Documents (Simple)

```bash
# Generate for ALL applications
python generate_application_word_docs.py

# Output location:
# outputs_final/word_reports/architecture/{APP}_architecture.docx
```

**Contents:**
- Title page
- Application data flow diagram (embedded PNG)
- Diagram legend
- Architecture overview
- Tier descriptions
- External dependencies
- Security considerations

**Prepared by:** Prutech Network Security Team

---

### 3. Threat Surface Analysis Documents (NEW!)

```bash
# Generate for ALL applications
python generate_threat_surface_docs.py

# Generate for SINGLE application
python generate_threat_surface_single.py

# Output location:
# outputs_final/word_reports/threat_surface/ThreatSurface-{APP}.docx
```

**Contents:**
- Executive summary with threat scoring
- External attack surface analysis
- Internal attack surface (lateral movement)
- Attack vector analysis (5 categories)
- Zero Trust micro-segmentation strategy
- DNS configuration security analysis
- Risk-based segmentation decision framework
- Regulatory compliance mapping (PCI-DSS, HIPAA, SOX, GDPR)
- Firewall rules and network ACLs
- Monitoring and threat detection requirements
- Implementation roadmap (phased)

**Prepared by:** Prutech Network Security Team

---

### 4. Build Master Topology (Required for Threat Surface Docs)

```bash
python build_master_topology.py

# Output:
# persistent_data/master_topology.json
```

**Purpose:**
- Consolidates all application topologies into single file
- Required input for threat surface document generation

---

### 5. Enterprise Network Segmentation Strategy (NEW! - Data-Driven Options)

```bash
python generate_segmentation_strategy.py

# Output location:
# outputs_final/word_reports/Enterprise_Network_Segmentation_Strategy.docx
```

**Contents:**
- **Current state network analysis** (dynamically generated from your actual topology data)
- **4 Segmentation Options:**
  - Option 1: Minimal (3 zones) - $50K-150K
  - Option 2: Standard (6-7 zones) - $200K-500K - **RECOMMENDED for most orgs**
  - Option 3: Advanced (10+ zones) - $500K-1.5M
  - Option 4: Micro-segmentation (Zero Trust) - $1M-3M+
- **Detailed pros & cons** for each option (tagged with [COST], [SECURITY], [COMPLEXITY], etc.)
- **Cost-benefit analysis** with one-time and annual costs
- **Comparison matrix** (side-by-side comparison table)
- **Data-driven recommendations** based on your network size and characteristics
- **Implementation roadmap** with phased approach
- **Regulatory compliance** implications (PCI-DSS, HIPAA, SOX, GDPR)

**What makes this unique:**
- ✅ **Fully data-driven** - Analyzes YOUR network topology
- ✅ **Multiple options** - Not one-size-fits-all
- ✅ **Honest trade-offs** - Real pros AND cons for each approach
- ✅ **Cost transparency** - Detailed cost breakdowns
- ✅ **Actionable** - Clear recommendations based on your data

**Prepared by:** Prutech Network Security Team

**Use this document when:**
- Planning network segmentation strategy
- Presenting options to executive leadership
- Budgeting for security investments
- Comparing segmentation approaches
- Making build vs. buy decisions

---

## 📊 REPORTS

### 1. Enterprise-Wide Network Report

```bash
python generate_enterprise_report.py

# Output:
# outputs_final/reports/Enterprise_Network_Analysis_Report.html
```

**Contents:**
- Executive summary
- Network topology overview
- Security zone analysis
- Top applications by connections
- Risk assessment
- Recommendations

---

### 2. DNS Validation Report

```bash
python generate_dns_validation_report.py

# Output:
# outputs_final/reports/DNS_Validation_Report.html
```

**Contents:**
- DNS validation statistics
- Mismatch analysis (forward vs. reverse DNS)
- NXDOMAIN issues
- Multiple IP scenarios (VM + ESXi)
- Security implications
- Remediation recommendations

---

### 3. Generate ALL Reports (Comprehensive)

```bash
python generate_all_reports.py
```

**Generates:**
- Individual application reports
- HTML diagrams
- Network segmentation documents
- Enterprise report
- DNS validation report

---

## 🔄 BATCH PROCESSING

### Run Batch Processing with Options

```bash
# Default batch size (10 files at a time)
python run_batch_processing.py

# Custom batch size
python run_batch_processing.py --batch-size 20

# With DNS validation enabled
python run_batch_processing.py --enable-dns-validation

# Force regenerate all topology data
python run_batch_processing.py --force-regenerate
```

**Options:**
- `--batch-size N`: Process N files per batch (default: 10)
- `--enable-dns-validation`: Validate DNS for all IPs
- `--force-regenerate`: Regenerate topology even if it exists

**Output:**
- `persistent_data/topology/{APP}.json` (per-app topology)
- `outputs_final/incremental_topology.json` (cumulative)
- `outputs_final/diagrams/*.html`, `*.mmd`, `*.png`

---

## 🌐 WEB INTERFACE

### Start Web Application (FastAPI)

```bash
# Start web server
python fastapi_app.py

# Or
python run_web_app.py

# Access at:
# http://localhost:8000
```

**Features:**
- Interactive network topology viewer
- Application search and filtering
- Dependency visualization
- Export diagrams
- Real-time topology updates

---

### Verify Web App is Running

```bash
python verify_web_app.py
```

---

## 🛠️ MAINTENANCE & UTILITIES

### 1. Cleanup & Fresh Start

```bash
python cleanup_fresh_start.py
```

**WARNING:** Deletes all generated outputs and persistent data.

---

### 2. Regenerate Specific Diagrams

```bash
# Regenerate diagrams with hostname resolution
python regenerate_diagrams_with_hostnames.py

# Regenerate ALL diagrams (MMD + HTML)
python regenerate_all_diagrams.py
```

---

### 3. Verify System Installation

```bash
python verify_system.py
```

**Checks:**
- Python dependencies
- Directory structure
- Data files
- Configuration

---

### 4. Test DNS Validation

```bash
python test_dns_validation.py
```

---

### 5. Test Diagram Colors

```bash
python test_diagram_colors.py
```

---

### 6. Debug CSV Column Issues

```bash
python debug_csv_columns.py
```

---

## 📁 OUTPUT LOCATIONS

```
outputs_final/
├── diagrams/                       # All diagrams
│   ├── {APP}_diagram.html          # Standard tier diagram (interactive)
│   ├── {APP}_diagram.mmd           # Mermaid source
│   ├── {APP}_diagram.png           # PNG screenshot
│   ├── {APP}_application_diagram.html  # Application architecture (interactive)
│   ├── {APP}_application_diagram.mmd
│   └── {APP}_application_diagram.png
│
├── word_reports/
│   ├── architecture/               # Architecture documents
│   │   ├── Solution_Design-{APP}.docx      (comprehensive)
│   │   └── {APP}_architecture.docx         (simple)
│   ├── threat_surface/             # Threat surface analysis
│   │   └── ThreatSurface-{APP}.docx
│   ├── netseg/                     # Network segmentation reports
│   │   └── {APP}_report.docx
│   └── Enterprise_Network_Segmentation_Strategy.docx  # Enterprise strategy with options
│
├── reports/                        # Enterprise reports
│   ├── Enterprise_Network_Analysis_Report.html
│   └── DNS_Validation_Report.html
│
└── incremental_topology.json       # Cumulative topology data

persistent_data/
├── topology/                       # Per-application topology
│   ├── {APP}.json
│   └── ...
├── master_topology.json            # Consolidated topology
└── processed_files.json            # File tracking
```

---

## 🎯 COMMON WORKFLOWS

### Workflow 1: Complete Fresh Analysis
```bash
# 1. Run analysis pipeline
python start_system.py

# 2. Generate PNGs (if needed)
python generate_pngs_python.py

# 3. Build master topology
python build_master_topology.py

# 4. Generate all Word documents
python generate_solution_design_docs.py
python generate_application_word_docs.py
python generate_threat_surface_docs.py
python generate_segmentation_strategy.py

# 5. Generate enterprise reports
python generate_enterprise_report.py
python generate_dns_validation_report.py
```

---

### Workflow 2: Regenerate Diagrams Only
```bash
# 1. Regenerate MMD files
python regenerate_all_mmds.py

# 2. Regenerate PNGs
python generate_pngs_python.py
```

---

### Workflow 3: Generate Documents Only (Data Already Exists)
```bash
# 1. Ensure master topology exists
python build_master_topology.py

# 2. Generate Word documents
python generate_solution_design_docs.py
python generate_application_word_docs.py
python generate_threat_surface_docs.py
```

---

### Workflow 4: Add New CSV Data & Process Incrementally
```bash
# 1. Place new CSV files in raw_data/

# 2. Run batch processing (only processes new files)
python run_batch_processing.py --batch-size 10

# 3. Regenerate master topology
python build_master_topology.py

# 4. Update documents as needed
python generate_threat_surface_docs.py
```

---

## 🔧 CONFIGURATION

### Batch Processing Configuration
Edit `run_batch_processing.py`:
- `DEFAULT_BATCH_SIZE = 10`
- `ENABLE_DNS_VALIDATION = False`
- CSV file locations: `raw_data/*.csv`

### Diagram Styling
Edit:
- `src/diagrams.py` (standard diagrams)
- `src/application_diagram_generator.py` (application diagrams)

### Document Templates
Edit:
- `src/docx_generator.py` (network segmentation docs)
- `src/comprehensive_solution_doc_generator.py` (solution design docs)
- `src/threat_surface_netseg_generator.py` (threat surface docs)
- `src/app_docx_generator.py` (simple architecture docs)

---

## 📝 QUICK COMMAND CHEAT SHEET

| Task | Command |
|------|---------|
| **Complete analysis** | `python start_system.py` |
| **Batch processing** | `python run_batch_processing.py --batch-size 10` |
| **Generate all MMDs** | `python regenerate_all_mmds.py` |
| **Generate all PNGs** | `python generate_pngs_python.py` |
| **Generate comprehensive architecture docs** | `python generate_solution_design_docs.py` |
| **Generate simple architecture docs** | `python generate_application_word_docs.py` |
| **Generate threat surface docs** | `python generate_threat_surface_docs.py` |
| **Generate segmentation strategy (options & pros/cons)** | `python generate_segmentation_strategy.py` |
| **Build master topology** | `python build_master_topology.py` |
| **Enterprise report** | `python generate_enterprise_report.py` |
| **DNS validation report** | `python generate_dns_validation_report.py` |
| **Start web interface** | `python fastapi_app.py` |
| **Verify installation** | `python verify_system.py` |

---

## 🆘 TROUBLESHOOTING

### No diagrams generated
```bash
# Check if topology data exists
ls persistent_data/topology/

# If empty, run batch processing
python run_batch_processing.py
```

### PNGs not generating
```bash
# Try Python-based PNG generation (most reliable)
python generate_pngs_python.py

# If that fails, regenerate HTML first
python regenerate_all_diagrams.py
python generate_pngs_python.py
```

### Word documents missing data
```bash
# Ensure master topology exists
python build_master_topology.py

# Check if it was created
ls persistent_data/master_topology.json
```

### Codec errors (Unicode characters)
Fixed in `build_master_topology.py`. If you encounter in other scripts, let me know.

---

## 📞 SUPPORT

For issues or questions:
1. Check logs in project root
2. Run `python verify_system.py`
3. Review this guide

---

**Last Updated:** 2025-10-16
**System Version:** Network Segmentation Analyzer v3.0
