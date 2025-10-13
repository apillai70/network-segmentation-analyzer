# Network Segmentation Analyzer - AI Coding Agent Instructions

## System Architecture Overview

This is an **enterprise network segmentation analysis system** that processes network flow data to generate security recommendations. The system uses ML/AI models to analyze current network state and predict optimal future segmentation.

### Core Components & Data Flow

1. **Data Ingestion**: CSV files in `data/input/` (e.g., `app_1_flows.csv`, `app_2_flows.csv`)
2. **Analysis Pipeline**: `ensemble_persistence_system.py` → `unified_future_state_system.py` → outputs
3. **Persistence**: SQLite database (`network_analysis.db`) + pickled models in `models/`
4. **Outputs**: Interactive HTML visualizations, Word reports, firewall rules, JSON reports

### Key Entry Points

- **Quick Start**: `python scripts/quick_start.py` (main workflow)
- **Enterprise Analyzer**: `enterprise_network_analyzer.py` (full production system)
- **Verification**: `python verify_system.py` (system health check)

## Critical Architecture Patterns

### State Distinction (Visual Legend Pattern)
The system distinguishes between **current** vs **predicted** states using consistent visual encoding:
- **Solid, vibrant colors** = Current state (actual flows)
- **Dashed, lighter colors** = Future state (predicted flows)  
- **Dotted lines** = Markov predictions (opacity = confidence level)

See `src/utils/color_schemes.py` for the complete color mapping system.

### Multi-Model Ensemble Architecture
Located in `enterprise_network_analyzer.py`:
- **GNN** (Graph Neural Network): Node classification and link prediction
- **RNN/LSTM**: Temporal flow analysis
- **CNN**: Pattern recognition in flow matrices
- **Attention Mechanisms**: Service chain prediction
- **Markov Chains**: Communication pattern prediction with confidence scores

### Infrastructure Discovery Pattern
`ensemble_persistence_system.py` contains port-based service identification:
```python
self.PORT_SIGS = {
    'kafka': {9092, 9093, 2181, 9094},
    'rabbitmq': {5672, 15672, 5671, 4369},
    'kubernetes': {6443, 10250, 10251, 10252, 10255}
    # ... extensive port signature database
}
```

## Data Processing Conventions

### Flow Data Schema
Input CSV files must contain standardized columns (case-insensitive):
- `source_ip`/`src_ip`, `destination_ip`/`dst_ip`
- `source_port`/`src_port`, `destination_port`/`dst_port`
- `protocol`, `hostname`/`destination_hostname`

### Segmentation Labels
The system generates hierarchical segmentation:
- **Macro Segments**: `DMZ`, `WEB_TIER`, `APP_TIER`, `DATA_TIER`, `INFRASTRUCTURE`
- **Micro Segments**: Application-specific zones with security labels

## Output Generation Patterns

### Multi-Format Report Generation
Each analysis produces:
1. **Interactive HTML**: D3.js visualizations in `outputs/visualizations/`
2. **Word Documents**: Professional reports in `outputs/word_reports/` via `word_document_report_generator.py`
3. **Security Rules**: Firewall configs, K8s policies, Azure NSGs in `outputs/segmentation_rules/`
4. **JSON Reports**: Machine-readable results in `results/`

### Visualization Stack
- **D3.js**: Interactive network graphs (`static/js/d3-renderer.js`)
- **Mermaid**: Static diagrams (`static/js/mermaid-renderer.js`)
- **Templates**: Jinja2-style templates in `templates/`

## Development Workflows

### Testing Strategy
Tests are component-based:
- `tests/test_ensemble.py`: ML model validation
- `tests/test_integration.py`: End-to-end pipeline testing
- `tests/test_persistence.py`: Database operations
- `tests/test_markov.py`: Prediction accuracy

### Model Persistence Pattern
Models auto-save to `models/checkpoints/` with metadata in `models/metadata/model_registry.json`. The system supports incremental learning without restart.

### Database Schema
SQLite tables managed by `PersistenceManager`:
- `flows`: Network flow records
- `nodes`: Discovered network nodes with segmentation labels
- `predictions`: ML model outputs with confidence scores
- `analyses`: Historical analysis results

## Configuration Management

- **Model Config**: `config/model_config.py` (ML hyperparameters)
- **Database Config**: `config/database_config.py` (connection settings)
- **Color Schemes**: `src/utils/color_schemes.py` (consistent visualization colors)

## Critical Integration Points

### External Dependencies
- **NetworkX**: Graph analysis and topology operations
- **Pandas/NumPy**: Data processing pipeline
- **SQLite**: Embedded persistence (production can use PostgreSQL)
- **D3.js**: Frontend visualization engine

### Service Discovery
The system automatically identifies infrastructure components (load balancers, message queues, databases) based on port signatures and traffic patterns.

## Key Files for Code Generation

When implementing new features:
- **Analysis Logic**: Extend `src/analysis/` modules
- **Visualization**: Add to `static/js/` and `templates/`
- **Reports**: Follow patterns in `word_document_report_generator.py`
- **Rules**: Use `segmentation_rule_generator.py` for security policy generation

## Error Handling Patterns

The system uses structured error reporting with security issue classification:
- `HIGH`: Direct database access from DMZ
- `MEDIUM`: Unassigned network zones
- `LOW`: Suboptimal routing patterns

Each error includes remediation recommendations and migration path suggestions.