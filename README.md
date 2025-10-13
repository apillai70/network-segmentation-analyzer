# Network Segmentation Analyzer

A Python-based tool that creates network topology visualizations and analyzes network segmentation based on log files from monitoring applications such as Extrahop, Dynatrace, and Splunk.

## Features

- **Multi-Source Support**: Parse logs from Extrahop, Dynatrace, and Splunk monitoring applications
- **Network Topology Visualization**: Generate visual representations of network connections
- **Segmentation Analysis**: Automatically identify network segments and communities
- **Detailed Reporting**: Generate comprehensive reports with statistics and insights
- **Protocol Analysis**: Analyze connections by protocol type
- **Top Communicators**: Identify nodes with the most connections

## Installation

1. Clone the repository:
```bash
git clone https://github.com/apillai70/network-segmentation-analyzer.git
cd network-segmentation-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python analyzer.py <source> <logfile> [options]
```

**Arguments:**
- `source`: Monitoring application source (`extrahop`, `dynatrace`, or `splunk`)
- `logfile`: Path to the log file

**Options:**
- `-o, --output`: Output file for topology visualization (default: `network_topology.png`)
- `-r, --report`: Output file for text report (default: `network_report.txt`)

### Examples

Analyze Extrahop logs:
```bash
python analyzer.py extrahop examples/extrahop_sample.log
```

Analyze Dynatrace logs with custom output:
```bash
python analyzer.py dynatrace examples/dynatrace_sample.log -o my_topology.png -r my_report.txt
```

Analyze Splunk logs:
```bash
python analyzer.py splunk examples/splunk_sample.log
```

## Log File Formats

### Extrahop Format
JSON lines with the following fields:
```json
{"source_ip": "10.0.1.10", "dest_ip": "10.0.2.20", "protocol": "HTTP", "port": "80"}
```

### Dynatrace Format
JSON lines with the following fields:
```json
{"from_entity": "web-server-01", "to_entity": "app-server-01", "connection_type": "HTTP", "port": "8080"}
```

### Splunk Format
JSON lines with the following fields:
```json
{"src": "192.168.1.100", "dest": "192.168.2.200", "app": "web", "dest_port": "443"}
```

## Output

The analyzer produces two types of output:

1. **Topology Visualization**: A PNG image showing the network graph with nodes and directed edges
2. **Text Report**: A comprehensive report including:
   - Network statistics (nodes, edges, density)
   - Connection breakdown by protocol
   - Network segments identified
   - Top communicating nodes

## Sample Output

```
============================================================
NETWORK TOPOLOGY ANALYSIS REPORT
============================================================

STATISTICS:
  Total Nodes: 8
  Total Edges: 8
  Total Connections: 8
  Network Density: 0.1429

CONNECTIONS BY PROTOCOL:
  HTTP: 3
  MySQL: 2
  HTTPS: 2
  Redis: 1

NETWORK SEGMENTS:
  segment_1: 8 nodes
    Nodes: 10.0.1.10, 10.0.1.11, 10.0.1.12, 10.0.2.20, ...

TOP COMMUNICATORS:
  10.0.1.10: 3 outgoing connections
  10.0.2.20: 1 outgoing connections
  ...
============================================================
```

## Project Structure

```
network-segmentation-analyzer/
├── analyzer.py              # Main entry point
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── src/
│   ├── parsers/            # Log parsers for different sources
│   │   ├── base_parser.py
│   │   ├── extrahop_parser.py
│   │   ├── dynatrace_parser.py
│   │   └── splunk_parser.py
│   └── topology/           # Network topology builder
│       └── network_topology.py
└── examples/               # Sample log files
    ├── extrahop_sample.log
    ├── dynatrace_sample.log
    └── splunk_sample.log
```

## Dependencies

- `networkx>=3.0`: Network analysis and graph algorithms
- `matplotlib>=3.5.0`: Visualization and plotting

## License

MIT License