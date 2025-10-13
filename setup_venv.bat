@echo off
REM ============================================================================
REM Virtual Environment Setup for Network Segmentation Analyzer
REM ============================================================================
REM Windows Batch Script

echo.
echo ========================================
echo Network Segmentation Analyzer v3.0
echo Virtual Environment Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [STEP 1] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

echo.
echo [STEP 2] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

echo.
echo [STEP 3] Upgrading pip...
python -m pip install --upgrade pip
echo [OK] Pip upgraded

echo.
echo [STEP 4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To activate the virtual environment in future sessions:
echo   venv\Scripts\activate.bat
echo.
echo To deactivate:
echo   deactivate
echo.
echo Quick start:
echo   python start_system.py --web --generate-data 140 --incremental
echo.
pause
