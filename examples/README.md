# Sample Log Files

This directory contains sample log files for testing the Network Segmentation Analyzer with different monitoring application formats.

## Files

### extrahop_sample.log
Sample log file in Extrahop format. Contains 8 network connections between various IP addresses showing HTTP, HTTPS, MySQL, PostgreSQL, and Redis traffic.

**Usage:**
```bash
python analyzer.py extrahop examples/extrahop_sample.log
```

### dynatrace_sample.log
Sample log file in Dynatrace format. Contains 7 connections between named entities (web servers, app servers, database, cache) showing HTTP, SQL, and Redis traffic.

**Usage:**
```bash
python analyzer.py dynatrace examples/dynatrace_sample.log
```

### splunk_sample.log
Sample log file in Splunk format. Contains 7 connections between IP addresses showing web, database, cache, and queue traffic.

**Usage:**
```bash
python analyzer.py splunk examples/splunk_sample.log
```

## Expected Output

Each sample will generate:
1. A network topology visualization (PNG image)
2. A detailed text report with statistics and analysis
