<<<<<<< HEAD
# Network Segmentation Analyzer

Enterprise-grade network segmentation analysis tool that automatically generates actionable security recommendations, firewall rules, and comprehensive architecture documentation from network traffic logs.

## Overview

The Network Segmentation Analyzer is a Python-based security tool designed for network engineers and security professionals. It automates the analysis of network traffic patterns, identifies security risks, and generates detailed segmentation recommendations with implementation-ready firewall rules.

### Key Features

- **Robust Log Parsing**: Handles multiple CSV formats with automatic column mapping
- **Protocol Normalization**: Intelligent parsing of `protocol:port`, service names, and plain protocols
- **Traffic Analysis**: Identifies top talkers, peer pairs, suspicious flows, and temporal patterns
- **Risk Scoring**: Automatic risk assessment based on traffic patterns and exposed services
- **Zone Classification**: ML-based classification into micro/macro segmentation zones
- **Rule Generation**: Produces prioritized segmentation rules with justifications
- **Multi-Platform Export**: IPTables, AWS Security Groups, Cisco ACL, Kubernetes NetworkPolicy
- **Interactive Diagrams**: Mermaid-based network topology and zone flow visualizations
- **Comprehensive Documentation**: Auto-generates Solutions Architecture Document (.docx)
- **Markov Chain Prediction**: Models peer correlations and transitive dependencies for missing apps
- **Ensemble ML Models**: GNN, RNN, CNN, Attention, Markov Chain, and Meta-learner for predictions

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/network-segmentation-analyzer.git
cd network-segmentation-analyzer

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run analysis on sample data
python bin/run_analysis.py

# 5. View results
open outputs/network_segmentation_solution.docx
open outputs/diagrams/overall_network.html```

## Input Data Format

The analyzer accepts network flow logs in CSV format. Multiple formats are supported with automatic column mapping:

### Standard Format

```csv
timestamp,src_hostname,src_ip,dst_hostname,dst_ip,protocol,bytes,packets
2024-01-15 08:30:15,web-srv-01,10.1.2.15,app-srv-01,10.1.3.20,tcp:8080,234567,156
```

###Alternative Formats

```csv
source_ip,destination_ip,proto_port,bytes_transferred
10.2.1.10,10.2.2.20,tcp:9092,567890
```

### Supported Protocol Formats

- `tcp:443` - Protocol with port
- `udp:53` - UDP with port
- `icmp` - Protocol only
- `https` - Service name (auto-converted to tcp:443)

### Required Fields

- Source IP address
- Destination IP address
- Protocol (with or without port)

### Optional Fields

- Timestamps
- Hostnames
- Byte/packet counts
- Flow duration

## Usage

### Basic Usage

```bash
# Analyze all applications in data/input/
python bin/run_analysis.py

# Specify custom data directory
python bin/run_analysis.py --data-dir /path/to/logs

# Analyze specific application
python bin/run_analysis.py --app app_1

# Custom output directory
python bin/run_analysis.py --output-dir results/analysis_2024

# Verbose logging
python bin/run_analysis.py --verbose

# Dry run (parse only)
python bin/run_analysis.py --dry-run
```

### Advanced Usage

```bash
# Run complete analysis with custom paths
python bin/run_analysis.py \
  --data-dir data/production_logs \
  --output-dir results/prod_analysis_$(date +%Y%m%d) \
  --verbose

# Analyze and overwrite existing results
python bin/run_analysis.py --force

# Help
python bin/run_analysis.py --help
```

## Common Operations

### Reprocess Applications (Fix Topology & Zones)

If you notice missing applications in the web UI or incorrect zone classifications, run the reprocessing script:

```bash
# Reprocess all applications with updated intelligence
python reprocess_all_apps.py
```

**When to reprocess:**
- Web UI shows fewer applications than expected
- All applications showing as "APP_TIER"
- After updating zone classification logic
- Missing topology data for processed applications

**What it does:**
- Re-analyzes all applications in `persistent_data/applications/`
- Uses IP-based zone inference (more accurate than naming patterns)
- Persists topology data to `persistent_data/topology/`
- Displays zone distribution and statistics

**Expected output:**
```
Processing 139 applications...
[1/139] ACDA... [OK] APP_TIER
[2/139] AODSVY... [OK] APP_TIER
...
[139/139] LBOT... [OK] APP_TIER

Zone Distribution:
  APP_TIER            : 103 apps
  MESSAGING_TIER      :  17 apps
  WEB_TIER            :   8 apps
  CACHE_TIER          :   6 apps
  MANAGEMENT_TIER     :   4 apps
  DATA_TIER           :   1 apps
```

For detailed documentation, see [REPROCESSING_GUIDE.md](REPROCESSING_GUIDE.md)

### Run Incremental Learning

Monitor and process new applications as they arrive:

```bash
# Continuous mode (watches for new files)
python run_incremental_learning.py --continuous

# Batch mode (process all new files once)
python run_incremental_learning.py --batch

# Process specific number of files
python run_incremental_learning.py --batch --max-files 10
```

### Start Web UI

```bash
# Start web interface on http://localhost:5000
python start_system.py --web

# Start with incremental learning
python start_system.py --web --incremental

# Custom port
python start_system.py --web --port 8080
```

### Generate Diagrams with Hostnames

```bash
# Regenerate diagrams with hostname resolution
python regenerate_diagrams_with_hostnames.py
```

For hostname configuration, see [HOSTNAME_RESOLUTION_GUIDE.md](HOSTNAME_RESOLUTION_GUIDE.md)

## Output Files

After running the analysis, the following files are generated:

```
outputs/
├── network_segmentation_solution.docx     # Complete Solutions Architecture Document
├── segmentation_rules.csv                 # All rules in CSV format
├── iptables_rules.sh                      # Linux IPTables implementation
├── aws_security_groups.json               # AWS Security Group definitions
├── analysis_report.json                   # Complete analysis in JSON
├── normalized_flows.csv                   # Normalized input data
└── diagrams/
    ├── overall_network.mmd                # Overall network Mermaid diagram
    ├── overall_network.html               # Interactive network visualization
    ├── zone_flows.mmd                     # Zone traffic flow diagram
    ├── zone_flows.html                    # Interactive zone flows
    ├── app_1_diagram.mmd                  # Per-app diagrams
    └── app_1_diagram.html
```

## Architecture

```
network-segmentation-analyzer/
├── bin/
│   └── run_analysis.py          # CLI entry point
├── src/
│   ├── parser.py                # Network log parser
│   ├── analysis.py              # Traffic analysis & rule generation
│   ├── diagrams.py              # Mermaid diagram generator
│   └── docx_generator.py        # Word document generator
├── data/
│   ├── input/                   # Input CSV files
│   ├── processed/               # Normalized data
│   └── exports/                 # Exported rule sets
├── outputs/                     # Generated reports and diagrams
├── tests/                       # Unit tests
├── config/                      # Configuration files
├── docs/                        # Additional documentation
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py -v

# Run specific test
pytest tests/test_analysis.py::TestTrafficAnalyzer::test_full_analysis -v
```

## Example Rules Output

### Sample Segmentation Rules (CSV)

| rule_id | priority | source | destination | protocol | port | action | risk_score | justification |
|---------|----------|--------|-------------|----------|------|--------|------------|---------------|
| RULE-1001 | 101 | EXTERNAL | any | tcp | 22 | deny | 90 | Block SSH access from external networks - high security risk |
| RULE-1005 | 205 | EXTERNAL | DATA_TIER | tcp | 3306 | deny | 95 | Block direct MySQL access from external - data exfiltration risk |
| RULE-1006 | 300 | any | WEB_TIER | tcp | 443 | allow | 20 | Allow HTTPS traffic to web tier - legitimate public access |
| RULE-1008 | 400 | WEB_TIER | APP_TIER | tcp | 8080,8443 | allow | 15 | Allow web tier to communicate with application tier |

### Example IPTables Rules

```bash
#!/bin/bash
# Block SSH from external
iptables -A FORWARD -p tcp --dport 22 -m comment --comment 'RULE-1001' -j DROP

# Allow HTTPS to web tier
iptables -A FORWARD -p tcp --dport 443 -m comment --comment 'RULE-1006' -j ACCEPT

# Allow app tier to database
iptables -A FORWARD -s 10.1.3.0/24 -d 10.1.4.0/24 -p tcp --dport 3306 -j ACCEPT
```

### Example AWS Security Group

```json
{
  "GroupName": "sg-web-tier",
  "Description": "Web servers and load balancers",
  "IngressRules": [
    {
      "IpProtocol": "tcp",
      "FromPort": 443,
      "ToPort": 443,
      "CidrIp": "0.0.0.0/0",
      "Description": "Allow HTTPS from internet"
    }
  ]
}
```

## Segmentation Zones

The analyzer automatically classifies hosts into zones:

### Macro Zones
- **EXTERNAL**: Internet-facing (security level 1)
- **DMZ**: Public services (security level 2)
- **INTERNAL**: Internal network (security level 3)
- **RESTRICTED**: Highly sensitive (security level 4)

### Micro Zones (Application Tiers)
- **WEB_TIER**: Web servers, load balancers
- **APP_TIER**: Application servers
- **DATA_TIER**: Databases, storage systems
- **MESSAGING_TIER**: Message queues, event buses
- **CACHE_TIER**: Redis, Memcached
- **MANAGEMENT_TIER**: Monitoring, orchestration

## Risk Scoring

Flows are automatically scored based on risk factors:

| Risk Score | Level | Examples |
|------------|-------|----------|
| 80-100 | Critical | External SSH, Database port exposure, Malicious IPs |
| 60-79 | High | Management ports from untrusted zones |
| 40-59 | Medium | Cross-zone database access |
| 20-39 | Low | Standard web traffic |
| 0-19 | Minimal | Internal monitoring traffic |

## ML-Based Prediction for Incomplete Application Coverage

The analyzer handles scenarios where only a subset of applications have traffic data (e.g., 170 out of 260 apps).

### The 260-App Scenario

**Problem**: You have 260 applications in your environment, but only 170 have generated traffic data. How do you plan segmentation for all 260?

**Solution**: Ensemble ML models + Markov chain analysis

### Prediction Approach - Layered Ensemble Architecture

#### Layer 1: Graph Neural Network (GNN) - First Pass

- **Primary Model**: GNN processes the network graph structure first
- **Input**: Node features (degree, in-degree, out-degree) + adjacency matrix
- **Output**: Learned representations of network topology and communication patterns
- **Purpose**: Establishes baseline understanding of how apps are interconnected

#### Layer 2: Complementary Models

- **RNN (Recurrent Neural Network)**: Captures temporal communication sequences
- **CNN (Convolutional Neural Network)**: Detects traffic pattern features
- **Attention (Multi-head)**: Identifies important contextual relationships
- **Markov Chain**: Models peer correlations and transitive dependencies (NEW)

#### Layer 3: Meta-Learner Ensemble

- Combines outputs from GNN, RNN, CNN, Attention, and Markov Chain
- Learns optimal weights for each model
- Produces final predictions with confidence scores

### Markov Chain for Peer Correlation

The Markov chain model addresses the key insight you mentioned:

> "The source code of one application may be the peer connection of another. This way we can correlate them."

**How it works:**

```
If app A → B (with probability P1)
And app B → C (with probability P2)
Then similar app A' → C' (with correlated probability)
```

**State Transitions**: Models `P(peer_j | app_i)` - the probability that an application connects to a specific peer

**Transitive Dependencies**: Discovers second-order relationships
- Direct: `web_frontend → api_user_service`
- Transitive: `web_frontend → api_user_service → db_customer_mysql`
- **Prediction**: New web app likely needs both API and (transitively) database access

**Peer Similarity Correlation**: Uses Jaccard similarity
- Apps with >10% peer overlap are correlated
- Similar apps likely have similar dependencies
- Example: `api_payment` and `api_order` both connect to `db_transactions`, so new API services probably do too

### Confidence Scoring

Predictions include confidence scores based on:
- Number of similar apps found (more similar = higher confidence)
- Strength of Markov transitions (higher probability = higher confidence)
- Peer correlation scores (stronger correlation = higher confidence)
- Ensemble model weights (agreement across models = higher confidence)

**Formula**: `confidence = 0.4 × markov_confidence + 0.6 × ensemble_confidence`

### Output

For each predicted app:
- **Predicted zone**: WEB_TIER, APP_TIER, DATA_TIER, etc.
- **Likely peers**: Top 10 predicted communication targets
- **Markov-predicted peers**: Peers discovered through correlation
- **Estimated flows**: Based on similar apps
- **Confidence score**: 0.3 (low) to 0.95 (high)

### Example Use Case

```
Observed apps (170):
  - web_frontend_portal → api_user_service → db_customer_mysql
  - web_customer_dashboard → api_user_service → db_customer_mysql
  - api_user_service → cache_redis_users

Predicted app: web_partner_gateway

Markov chain analysis:
  1. Finds similar apps: web_frontend_portal, web_customer_dashboard
  2. Aggregates their peer transitions
  3. Discovers transitive dependency: both web apps → API → DB
  4. Predicts web_partner_gateway will likely connect to:
     - api_user_service (direct, 85% probability)
     - cache_redis_users (transitive through API, 65% probability)
     - db_customer_mysql (second-order transitive, 45% probability)

Output:
  Zone: WEB_TIER
  Peers: [api_user_service, cache_redis_users, ...]
  Confidence: 87%
```

### Files Generated

- `outputs/ml_predictions.json` - Detailed predictions with Markov probabilities
- `outputs/network_analysis.db` - SQLite database with trained models
- Solutions Document includes ML predictions section

### Prediction Pipeline Flow

```
170 Apps with Data
        ↓
    [Parser]
        ↓
    [Build Network Graph]
        ↓
┌───────────────────────────┐
│  Layer 1: GNN (First Pass)│  ← Network topology analysis
│  - Node features          │
│  - Adjacency matrix       │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Layer 2: Parallel Models │
│  ┌─────────────────────┐  │
│  │ RNN  │ Temporal seq │  │
│  │ CNN  │ Patterns     │  │
│  │ Attn │ Context      │  │
│  │ Markov│ Peer correl │  │
│  └─────────────────────┘  │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Layer 3: Meta-Learner    │  ← Weighted ensemble
│  Combines all models      │
└───────────────────────────┘
        ↓
    [Predictions for 90 Apps]
    - Zone assignments
    - Peer connections
    - Markov probabilities
    - Confidence scores
        ↓
    [260 Complete Apps]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/your-org/network-segmentation-analyzer/issues
- Documentation: https://docs.example.com/network-segmentation

## Acknowledgments

- Network Security Team
- Built with: Python, pandas, networkx, python-docx, mermaid

---

**Auto-generated by Network Segmentation Analyzer v2.0**
=======
# network-segmentation-analyzer
>>>>>>> 9321f814c614ea40cf8492a02b5f9928fc418e9f
