# Network Segmentation Analyzer - Fast API Modern Web Dashboard  🚀

**Version 2.0** - FastAPI + Modern UI (No Node.js Required!)

---

## ✨ What's New?

Complete redesign with FastAPI backend and modern vanilla JavaScript frontend!

### Key Improvements

✅ **Faster Performance** - AsyncIO-powered FastAPI (3x faster than Flask)
✅ **Auto-Generated API Docs** - Interactive Swagger UI at /docs
✅ **Modern UI** - Clean, professional design without build tools
✅ **No Node.js** - Pure HTML/CSS/JS, works directly in browser
✅ **Type Safety** - Full Python type hints with Pydantic validation
✅ **Easy Testing** - Built-in test client and async support

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_fastapi.txt
```

This installs:
- `fastapi` - Modern web framework
- `uvicorn` - Lightning-fast ASGI server
- `python-multipart` - File upload support

### 2. Start the Server

```bash
# Windows
start_web_app.bat

# Linux/Mac
python fastapi_app.py
```

### 3. Access the Dashboard

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs ← Interactive Swagger UI!
- **Alternative Docs**: http://localhost:8000/redoc

---

## 📊 Dashboard Features

### Main Dashboard (`/`)
- Real-time statistics cards
- Security zone distribution chart (Chart.js)
- DNS validation health chart
- Recent applications table
- Auto-refresh every 30 seconds

### Applications (`/applications.html`)
- Complete application inventory (139 apps)
- Search and filter functionality
- Sort by zone, dependencies, DNS status
- Quick access to application details

### DNS Validation (`/dns.html`)
- DNS health overview
- Mismatches table with remediation steps
- Multiple IPs (VM + ESXi) detection
- NXDOMAIN tracking
- Visual status distribution

---

## 🔌 API Endpoints

All endpoints return JSON. Full API documentation at http://localhost:8000/docs

### Applications

```bash
# Get all applications
GET /api/applications
Response: {"applications": [...], "total": 139}

# Filter by security zone
GET /api/applications?zone=APP_TIER

# Get specific application
GET /api/applications/ACDA
Response: {"app_id": "ACDA", "data": {...}}
```

### Security Zones

```bash
# Get all zones with statistics
GET /api/security-zones
Response: {
  "zones": [
    {"name": "APP_TIER", "app_count": 103, "total_dependencies": 2400}
  ],
  "total_zones": 6,
  "total_apps": 139
}
```

### DNS Validation

```bash
# Get DNS summary
GET /api/dns-validation/summary
Response: {
  "statistics": {
    "total_valid": 2200,
    "total_mismatches": 100,
    "total_nxdomain": 50
  }
}

# Get DNS mismatches
GET /api/dns-validation/mismatches?limit=100
```

### Enterprise Analytics

```bash
# Get enterprise-wide summary
GET /api/enterprise/summary
Response: {
  "statistics": {
    "total_applications": 139,
    "total_dependencies": 3328,
    "cross_zone_connections": 450
  }
}

# Get dependency graph (for visualization)
GET /api/dependencies/graph
GET /api/dependencies/graph?app_id=ACDA

# Get zone distribution for charts
GET /api/analytics/zone-distribution
GET /api/analytics/dns-health
```

---

## 🏗️ Architecture

### Backend: FastAPI (Python)

**File**: `fastapi_app.py` (490 lines)

**Features**:
- Async/await for high performance
- Automatic OpenAPI schema generation
- Type-safe with Pydantic models
- CORS enabled for cross-origin requests
- Error handling with proper HTTP status codes

**Integrations**:
- `dns_validation_reporter.py` - Collects DNS validation data
- `enterprise_report_generator.py` - Enterprise-wide analytics
- Reads topology data from `persistent_data/topology/*.json`

### Frontend: Modern Vanilla JS

**Location**: `web_static/`

**Files**:
- `index.html` - Main dashboard (200 lines)
- `applications.html` - Applications list (180 lines)
- `dns.html` - DNS validation (220 lines)
- `css/main.css` - Modern CSS with design system (600 lines)
- `js/main.js` - Dashboard logic (250 lines)

**Technology**:
- Pure HTML5/CSS3/JavaScript ES6+
- Chart.js 4.4 for charts (from CDN)
- Font Awesome 6.4 for icons (from CDN)
- NO build process - works directly in browser!

---

## 🎨 Design System

The modern UI uses a clean design system defined in CSS variables:

**Colors**:
- Primary: `#2563eb` (blue)
- Success: `#10b981` (green)
- Warning: `#f59e0b` (orange)
- Danger: `#ef4444` (red)

**Zone Colors**:
- WEB_TIER: Purple `#8b5cf6`
- APP_TIER: Blue `#3b82f6`
- DATA_TIER: Green `#10b981`
- CACHE_TIER: Orange `#f59e0b`
- MESSAGING_TIER: Pink `#ec4899`
- MANAGEMENT_TIER: Indigo `#6366f1`

**Typography**:
- System fonts (no external font loading!)
- 16px base font size
- Responsive scaling

---

## 📁 File Structure

```
network-segmentation-analyzer/
├── fastapi_app.py              ← FastAPI backend (NEW!)
├── start_web_app.bat           ← Windows launcher
├── requirements_fastapi.txt    ← FastAPI dependencies
├── FASTAPI_GUIDE.md            ← This file
│
├── web_static/                 ← Frontend (NEW!)
│   ├── index.html              ← Dashboard
│   ├── applications.html       ← Apps list
│   ├── dns.html                ← DNS validation
│   ├── css/
│   │   └── main.css            ← Modern styles
│   └── js/
│       └── main.js             ← Dashboard JS
│
├── src/                        ← Python modules
│   ├── dns_validation_reporter.py
│   ├── enterprise_report_generator.py
│   ├── threat_surface_netseg_generator.py
│   └── topology_network_analysis_generator.py
│
└── persistent_data/
    └── topology/               ← Topology JSON files
        └── *.json              (139 applications)
```

---

## 🔧 Configuration

### Change Port

Edit `fastapi_app.py` (last line):
```python
uvicorn.run(
    "fastapi_app:app",
    host="0.0.0.0",
    port=8001,  # Change port here
    reload=True
)
```

### Change Topology Directory

Edit `fastapi_app.py` (line ~55):
```python
TOPOLOGY_DIR = Path("your/custom/path/topology")
```

### Disable Auto-Reload

For production:
```python
uvicorn.run(
    "fastapi_app:app",
    host="0.0.0.0",
    port=8000,
    reload=False  # Disable auto-reload
)
```

---

## 🚢 Deployment

### Production Deployment

```bash
# Install dependencies
pip install -r requirements_fastapi.txt

# Run with 4 worker processes
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Nginx Reverse Proxy

`nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/web_static/;
    }
}
```

### With systemd (Linux)

`/etc/systemd/system/netseganal.service`:
```ini
[Unit]
Description=Network Segmentation Analyzer
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/network-segmentation-analyzer
ExecStart=/usr/bin/python3 fastapi_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable netseganal
sudo systemctl start netseganal
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### No Topology Data

```bash
# Run batch processing first
python run_batch_processing.py
```

### Charts Not Loading

1. Check browser console (F12)
2. Verify Chart.js CDN is accessible
3. Check API endpoints return data:
   ```bash
   curl http://localhost:8000/api/analytics/zone-distribution
   ```

### API Errors

Check server logs for detailed error messages:
```bash
python fastapi_app.py
# Watch console output for errors
```

---

## 📚 Comparing Flask vs FastAPI

| Feature | Flask (Old) | FastAPI (New) |
|---------|------------|---------------|
| **Speed** | Good (WSGI) | Excellent (ASGI, async) |
| **Performance** | ~1000 req/sec | ~3000+ req/sec |
| **API Docs** | Manual (Swagger separate) | Auto-generated (built-in) |
| **Type Safety** | Optional | Required (Pydantic) |
| **Async Support** | Limited | Native |
| **Request Validation** | Manual | Automatic |
| **Modern Python** | 2.7 - 3.x | 3.7+ only |
| **Learning Curve** | Easy | Easy |
| **Production Ready** | Yes | Yes |

**Winner**: FastAPI for modern, high-performance APIs! 🏆

---

## ✅ What's Completed

- ✅ FastAPI backend with 15+ API endpoints
- ✅ Modern dashboard with real-time stats
- ✅ Applications inventory page
- ✅ DNS validation dashboard
- ✅ Chart visualizations (Chart.js)
- ✅ Responsive design
- ✅ Auto-refresh functionality
- ✅ Search and filter
- ✅ Enterprise analytics integration
- ✅ Automatic API documentation

---

## 📝 Future Enhancements

- 🔲 Security zones dedicated page
- 🔲 Advanced analytics page
- 🔲 Dependency graph visualization (D3.js/Cytoscape.js)
- 🔲 Export to CSV/Excel/PDF
- 🔲 User authentication (OAuth2)
- 🔲 WebSocket for real-time updates
- 🔲 Dark mode toggle
- 🔲 Mobile app (Progressive Web App)

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Chart.js Docs**: https://www.chartjs.org/docs
- **Font Awesome**: https://fontawesome.com
- **Modern CSS**: https://web.dev/learn/css

---

## 💡 Tips & Tricks

### Test APIs with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Get applications
curl http://localhost:8000/api/applications | jq

# Filter by zone
curl "http://localhost:8000/api/applications?zone=APP_TIER" | jq
```

### Test APIs with Python

```python
import requests

# Get applications
response = requests.get('http://localhost:8000/api/applications')
data = response.json()
print(f"Total apps: {data['total']}")

# Get DNS summary
dns_response = requests.get('http://localhost:8000/api/dns-validation/summary')
dns_data = dns_response.json()
print(f"DNS mismatches: {dns_data['total_mismatches']}")
```

### Interactive API Docs

Visit http://localhost:8000/docs and try out APIs directly in the browser!

- Click "Try it out"
- Enter parameters
- Click "Execute"
- See response instantly

---

## 🙏 Credits

**Built with**:
- [FastAPI](https://fastapi.tiangolo.com) by Sebastián Ramírez
- [Uvicorn](https://www.uvicorn.org) by Tom Christie
- [Chart.js](https://www.chartjs.org) by Chart.js Contributors
- [Font Awesome](https://fontawesome.com) by Fonticons

**Network Segmentation Analyzer**
Enterprise Security Team
Version 2.0 - FastAPI Edition

---

**Enjoy your modern, lightning-fast web dashboard! ⚡**

Need help? Check the interactive API docs at http://localhost:8000/docs
