# Web Application Installation Guide

## Quick Install (5 minutes)

### Step 1: Install Dependencies

```bash
# Basic installation (JSON backend only)
pip install flask

# Full installation (with PostgreSQL support)
pip install flask psycopg2-binary

# Production installation (includes gunicorn)
pip install flask psycopg2-binary gunicorn
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python -c "import flask; print('Flask:', flask.__version__)"
```

### Step 3: Run Web Application

```bash
# Simple start
python web_app.py

# Or use quick start script
python run_web_app.py

# Custom configuration
python run_web_app.py --port 8080 --debug
```

### Step 4: Access Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## PostgreSQL Setup (Optional)

If you want to use PostgreSQL instead of JSON files:

### Option 1: Local PostgreSQL

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql

# Install PostgreSQL (Windows)
# Download from: https://www.postgresql.org/download/windows/

# Create database
createdb network_segmentation

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=network_segmentation
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
```

### Option 2: Docker PostgreSQL

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name postgres-netanalyzer \
  -e POSTGRES_DB=network_segmentation \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15

# Connect to it
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=network_segmentation
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
```

### Run with PostgreSQL

```bash
python run_web_app.py \
  --postgres-host localhost \
  --postgres-db network_segmentation \
  --postgres-user postgres \
  --postgres-password postgres
```

## Directory Structure

After installation, you should have:

```
network-segmentation-analyzer/
├── web_app.py                          # Main Flask application
├── run_web_app.py                      # Quick start script
├── web_app/
│   ├── __init__.py
│   ├── api_routes.py                   # REST API endpoints
│   ├── templates/
│   │   ├── index.html                  # Dashboard
│   │   ├── topology.html               # Topology visualization
│   │   ├── base.html                   # Base template
│   │   └── error.html                  # Error page
│   └── static/
│       ├── js/
│       │   └── topology.js             # D3.js visualization
│       └── css/
│           └── style.css               # Custom styles
├── src/
│   └── persistence/
│       ├── __init__.py
│       └── unified_persistence.py      # Unified storage backend
└── persistent_data/                     # JSON storage (fallback)
    ├── applications/
    ├── flows/
    ├── analysis/
    └── topology/
```

## Testing the Installation

### Test 1: Health Check

```bash
curl http://localhost:5000/api/health
```

Expected output:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T10:00:00",
  "backend": "json"
}
```

### Test 2: Statistics

```bash
curl http://localhost:5000/api/statistics
```

### Test 3: Web Interface

Open browser and check:
- Dashboard: http://localhost:5000/
- Topology: http://localhost:5000/topology
- Applications: http://localhost:5000/applications

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
pip install flask
```

### Problem: "ModuleNotFoundError: No module named 'psycopg2'"

**Solution:**
```bash
pip install psycopg2-binary
```

Or disable PostgreSQL:
```bash
# Will automatically fallback to JSON
python web_app.py
```

### Problem: "Port 5000 already in use"

**Solution:**
```bash
# Use different port
python web_app.py --port 8080

# Or kill the process using port 5000
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Problem: "PostgreSQL connection refused"

**Solution:**

1. Check if PostgreSQL is running:
```bash
pg_isready -h localhost -p 5432
```

2. Check connection details:
```bash
psql -h localhost -U postgres -d network_segmentation
```

3. Or use JSON fallback (automatic):
```bash
python web_app.py  # Will automatically use JSON
```

### Problem: "Template not found"

**Solution:**

Check that template files exist:
```bash
ls -la web_app/templates/
```

If missing, make sure you have all files from the repository.

### Problem: "Static files not loading"

**Solution:**

1. Check static directory exists:
```bash
ls -la web_app/static/
```

2. Check Flask configuration:
```python
# In web_app.py, verify:
app = Flask(__name__,
    template_folder='web_app/templates',
    static_folder='web_app/static'
)
```

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app

# With more options
gunicorn \
  -w 4 \
  -b 0.0.0.0:5000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  web_app:app
```

### Using Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/netanalyzer
server {
    listen 80;
    server_name netanalyzer.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/network-segmentation-analyzer/web_app/static;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/netanalyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Systemd Service

Create `/etc/systemd/system/netanalyzer.service`:

```ini
[Unit]
Description=Network Segmentation Analyzer Web App
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/network-segmentation-analyzer
Environment="PATH=/path/to/venv/bin"
Environment="POSTGRES_HOST=localhost"
Environment="POSTGRES_DB=network_segmentation"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 web_app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable netanalyzer
sudo systemctl start netanalyzer
sudo systemctl status netanalyzer
```

## Security Hardening

### 1. Change Secret Key

```bash
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

Or in `web_app.py`:
```python
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
```

### 2. Restrict Access

Bind to localhost only:
```bash
python web_app.py --host 127.0.0.1
```

### 3. Use HTTPS

Always use HTTPS in production with nginx/Apache as reverse proxy.

### 4. Database Security

- Use strong passwords
- Restrict database access by IP
- Use SSL/TLS for database connections
- Never commit credentials to git

### 5. Environment Variables

Use `.env` file (add to .gitignore):
```bash
SECRET_KEY=your-secret-key
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=secure-password
```

## Performance Tuning

### 1. Enable Caching

Add Redis caching:
```bash
pip install redis flask-caching
```

### 2. Database Connection Pool

Already configured in `unified_persistence.py`:
- Min connections: 1
- Max connections: 10

### 3. Gunicorn Workers

Formula: (2 × CPU cores) + 1
```bash
# For 4 CPU cores
gunicorn -w 9 -b 0.0.0.0:5000 web_app:app
```

### 4. Enable Compression

In nginx:
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## Monitoring

### Application Logs

```bash
# View Flask logs
tail -f logs/web_app.log

# View Gunicorn logs
tail -f logs/access.log
tail -f logs/error.log
```

### Health Monitoring

```bash
# Check health endpoint
curl http://localhost:5000/api/health

# Monitor with watch
watch -n 5 'curl -s http://localhost:5000/api/statistics | jq .'
```

## Backup

### Backup JSON Data

```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz persistent_data/

# Restore backup
tar -xzf backup-20251012.tar.gz
```

### Backup PostgreSQL

```bash
# Backup database
pg_dump -h localhost -U postgres network_segmentation > backup.sql

# Restore database
psql -h localhost -U postgres network_segmentation < backup.sql
```

## Upgrading

### Pull Latest Changes

```bash
git pull origin main
```

### Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Migrate Data

```bash
# If using PostgreSQL, run migrations
python -c "from src.persistence.unified_persistence import create_persistence_manager; pm = create_persistence_manager(); pm.migrate_to_postgres()"
```

### Restart Service

```bash
sudo systemctl restart netanalyzer
```

## Support

For issues or questions:
1. Check logs: `tail -f logs/web_app.log`
2. Check troubleshooting section above
3. Verify installation: `python run_web_app.py --help`
4. Contact Enterprise Security Team

---

**Version**: 3.0
**Last Updated**: 2025-10-12
