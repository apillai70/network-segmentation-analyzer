#!/bin/bash
# ============================================================================
# Virtual Environment Setup for Network Segmentation Analyzer
# ============================================================================
# Linux/macOS Shell Script

echo ""
echo "========================================"
echo "Network Segmentation Analyzer v3.0"
echo "Virtual Environment Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

echo "[STEP 1] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to create virtual environment"
    exit 1
fi
echo "[OK] Virtual environment created"

echo ""
echo "[STEP 2] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi
echo "[OK] Virtual environment activated"

echo ""
echo "[STEP 3] Upgrading pip..."
pip install --upgrade pip
echo "[OK] Pip upgraded"

echo ""
echo "[STEP 4] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To activate the virtual environment in future sessions:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
echo "Quick start:"
echo "  python start_system.py --web --generate-data 140 --incremental"
echo ""
