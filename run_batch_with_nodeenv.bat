@echo off
REM Batch Processing with Nodeenv - Windows Wrapper
REM ================================================
REM This script activates nodeenv before running batch processing
REM ensuring mmdc (mermaid-cli) is in PATH

echo ================================================================================
echo BATCH PROCESSING WITH NODEENV
echo ================================================================================
echo.

REM Check if nodeenv exists
if not exist "nodeenv\Scripts\activate.bat" (
    echo ERROR: nodeenv not found at nodeenv\Scripts\activate.bat
    echo.
    echo Please ensure nodeenv is set up in this directory.
    pause
    exit /b 1
)

REM Activate nodeenv
echo Activating nodeenv...
call nodeenv\Scripts\activate.bat

REM Check if mmdc is now accessible
echo Checking for mmdc...
mmdc --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: mmdc not found even after activating nodeenv
    echo.
    echo You may need to install mermaid-cli in nodeenv:
    echo    npm install -g @mermaid-js/mermaid-cli
    echo.
    pause
    exit /b 1
)

echo   Found mmdc - OK
echo.

REM Run batch processing with all arguments passed through
echo Starting batch processing...
echo.
python run_batch_processing.py %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================================================================
echo Batch processing complete (exit code: %EXIT_CODE%)
echo ================================================================================

exit /b %EXIT_CODE%
