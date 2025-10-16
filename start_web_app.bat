@echo off
REM Network Segmentation Analyzer - FastAPI Web Application Launcher
REM This script starts the modern web dashboard

echo ================================================================================
echo   Network Segmentation Analyzer - Web Dashboard
echo   FastAPI + Modern UI
echo ================================================================================
echo.

REM Check if FastAPI is installed
python -c "import fastapi" 2>NUL
if errorlevel 1 (
    echo FastAPI not found. Installing dependencies...
    pip install -r requirements_fastapi.txt
    echo.
)

REM Check if uvicorn is installed
python -c "import uvicorn" 2>NUL
if errorlevel 1 (
    echo Uvicorn not found. Installing dependencies...
    pip install -r requirements_fastapi.txt
    echo.
)

echo Starting FastAPI web server...
echo.
echo   Access the dashboard at: http://localhost:8000
echo   API documentation at:     http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo ================================================================================
echo.

REM Start the FastAPI application
python fastapi_app.py
