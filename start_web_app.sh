#!/bin/bash
# Network Segmentation Analyzer - FastAPI Web Application Launcher
# This script starts the modern web dashboard

echo "================================================================================"
echo "  Network Segmentation Analyzer - Web Dashboard"
echo "  FastAPI + Modern UI"
echo "================================================================================"
echo ""

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "FastAPI not found. Installing dependencies..."
    pip install -r requirements_fastapi.txt
    echo ""
fi

# Check if uvicorn is installed
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "Uvicorn not found. Installing dependencies..."
    pip install -r requirements_fastapi.txt
    echo ""
fi

echo "Starting FastAPI web server..."
echo ""
echo "  Access the dashboard at: http://localhost:8000"
echo "  API documentation at:     http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo "================================================================================"
echo ""

# Start the FastAPI application
python fastapi_app.py
