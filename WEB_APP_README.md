# Network Segmentation Analyzer - Web Application

## Overview

Flask-based web interface for interactive network topology visualization and analysis.

### Key Features

- **Interactive Topology Visualization**: D3.js force-directed graph with zoom, pan, and drag
- **Real-time Dashboard**: Live statistics and zone distribution charts
- **PostgreSQL + JSON Fallback**: Automatic failover between database backends
- **Application Discovery**: Browse and search applications with detailed views
- **Security Zone Management**: Visual zone distribution and filtering
- **Incremental Learning Dashboard**: Monitor real-time learning progress
- **100% Local**: No external API calls, all processing on-premise

## Quick Start

### Prerequisites

```bash
# Core dependencies (already in requirements.txt)
pip install flask psycopg2-binary

# Optional: PostgreSQL (will fallback to JSON if not available)
```

### Installation

1. **Install Flask dependencies**:
```bash
pip install flask psycopg2-binary
```

2. **Configure PostgreSQL (Optional)**:
```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=network_segmentation
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
```

3. **Run the web application**:
```bash
python web_app.py
```

4. **Access the web interface**:
```
http://localhost:5000
```

## Architecture

### Backend Components

1. **Unified Persistence Manager** (`src/persistence/unified_persistence.py`)
   - PostgreSQL support with connection pooling
   - Automatic JSON fallback
   - Transaction support
   - Migration utilities

2. **Flask Web Server** (`web_app.py`)
   - Lightweight Flask server
   - No Docker dependency
   - Template rendering
   - Static file serving

3. **REST API** (`web_app/api_routes.py`)
   - `/api/applications` - List applications
   - `/api/topology` - Get topology data
   - `/api/topology/graph` - Graph data for visualization
   - `/api/zones` - Security zone distribution
   - `/api/statistics` - System statistics
   - `/api/search` - Search applications
   - `/api/incremental/status` - Learning status

### Frontend Components

1. **Dashboard** (`templates/index.html`)
   - Statistics cards
   - Zone distribution chart (Chart.js)
   - Recent applications list
   - Quick actions

2. **Topology Visualization** (`templates/topology.html` + `static/js/topology.js`)
   - D3.js force-directed graph
   - Interactive node details
   - Zone filtering
   - Search functionality
   - Export capabilities

3. **Navigation**
   - Responsive Bootstrap navbar
   - Consistent routing
   - Error handling

## Configuration

### PostgreSQL Configuration

```python
# Option 1: Environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=network_segmentation
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password

# Option 2: Command line arguments
python web_app.py --postgres-host localhost --postgres-db mydb
```

### JSON Fallback Configuration

If PostgreSQL is not available, the system automatically falls back to JSON file storage:

```python
# Data stored in: ./persistent_data/
persistent_data/
├── applications/
│   └── APP_ID/
│       ├── application.json
│       └── flows.csv
├── analysis/
├── topology/
└── models/
```

## API Endpoints

### Applications

**GET /api/applications**
```json
{
  "success": true,
  "count": 135,
  "applications": [
    {
      "app_id": "XECHK",
      "app_name": "XECHK",
      "flow_count": 1250,
      "created_at": "2025-10-12T10:00:00",
      "updated_at": "2025-10-12T10:30:00"
    }
  ]
}
```

**GET /api/applications/{app_id}**
```json
{
  "success": true,
  "application": {
    "app_id": "XECHK",
    "app_name": "XECHK",
    "flow_count": 1250,
    "metadata": {}
  }
}
```

### Topology

**GET /api/topology**
```json
{
  "success": true,
  "count": 135,
  "topology": [
    {
      "app_id": "XECHK",
      "security_zone": "APP_TIER",
      "dependencies": [...],
      "characteristics": ["api_service"]
    }
  ]
}
```

**GET /api/topology/graph**
```json
{
  "success": true,
  "graph": {
    "nodes": [
      {
        "id": "XECHK",
        "label": "XECHK",
        "zone": "APP_TIER",
        "characteristics": ["api_service"],
        "group": "APP_TIER"
      }
    ],
    "edges": [
      {
        "source": "XECHK",
        "target": "database_service",
        "type": "database",
        "confidence": 0.85
      }
    ]
  }
}
```

### Zones

**GET /api/zones**
```json
{
  "success": true,
  "zones": [
    {"zone": "WEB_TIER", "count": 25},
    {"zone": "APP_TIER", "count": 80},
    {"zone": "DATA_TIER", "count": 30}
  ]
}
```

### Statistics

**GET /api/statistics**
```json
{
  "success": true,
  "statistics": {
    "backend": "postgres",
    "applications": 135,
    "flow_records": 150000,
    "topology_records": 135,
    "analysis_results": 270
  }
}
```

### Search

**GET /api/search?q=payment**
```json
{
  "success": true,
  "query": "payment",
  "count": 5,
  "results": [...]
}
```

## Web Pages

### Dashboard (/)
- System statistics overview
- Zone distribution charts
- Recent applications
- Quick action buttons

### Topology (/topology)
- Interactive force-directed graph
- Node dragging and zooming
- Zone-based coloring
- Click for details

### Applications (/applications)
- Searchable application list
- Sort by various fields
- Quick access to details

### Application Detail (/application/{app_id})
- Full application information
- Flow statistics
- Topology details
- Dependencies list

### Security Zones (/zones)
- Zone overview
- Applications per zone
- Security requirements

### Incremental Learning (/incremental)
- Learning progress
- Files processed
- Model updates
- Real-time statistics

## Development

### Running in Debug Mode

```bash
python web_app.py --debug
```

### Custom Host and Port

```bash
python web_app.py --host 0.0.0.0 --port 8080
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get statistics
curl http://localhost:5000/api/statistics

# List applications
curl http://localhost:5000/api/applications

# Get topology
curl http://localhost:5000/api/topology/graph
```

## Deployment

### Production Deployment

For production use, deploy with a production WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install flask psycopg2-binary gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
```

### Environment Variables

```bash
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=network_segmentation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Storage
JSON_STORAGE_PATH=./persistent_data
```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U postgres -d network_segmentation

# Check logs
tail -f logs/web_app.log
```

### JSON Fallback

If PostgreSQL is unavailable, the system automatically uses JSON storage:

```
[WARNING] PostgreSQL connection failed: connection refused
[INFO] Using JSON file backend (fallback)
```

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
python web_app.py --port 8080
```

## Security Considerations

1. **Change Secret Key**: Set `SECRET_KEY` environment variable in production
2. **Database Credentials**: Never commit passwords to version control
3. **Network Access**: Bind to `127.0.0.1` if only local access needed
4. **HTTPS**: Use reverse proxy (nginx) with SSL/TLS in production
5. **CORS**: Configure if accessed from different domains

## Performance Optimization

1. **Connection Pooling**: Configured for PostgreSQL (1-10 connections)
2. **Caching**: Add Redis cache layer for frequently accessed data
3. **Compression**: Enable gzip compression in production
4. **Static Files**: Serve via nginx in production
5. **Database Indexes**: Automatically created for common queries

## License

Internal Enterprise Tool - All Rights Reserved

## Support

For issues or questions, contact the Enterprise Security Team.

---

**Version**: 3.0
**Last Updated**: 2025-10-12
**100% LOCAL PROCESSING - NO EXTERNAL API CALLS**
