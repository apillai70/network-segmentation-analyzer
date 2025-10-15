#!/bin/bash
################################################################################
# Batch Processing with Nodeenv - Shell Script Wrapper
################################################################################
# This script:
# 1. Sources .bashrc to set up nodeenv/PATH
# 2. Checks if mmdc (mermaid-cli) is available
# 3. Installs mmdc if not found
# 4. Runs batch processing
#
# Usage:
#   ./run_batch_with_nodeenv.sh --batch-size 10
#   ./run_batch_with_nodeenv.sh --batch-size 10 --clear-first
################################################################################

set -e  # Exit on error

echo "================================================================================"
echo "BATCH PROCESSING WITH NODEENV"
echo "================================================================================"
echo ""

# Step 1: Source .bashrc to set up environment
echo "1. Setting up environment..."
if [ -f ~/.bashrc ]; then
    echo "   Sourcing ~/.bashrc..."
    source ~/.bashrc
    echo "   ✓ Environment loaded"
else
    echo "   ⚠ ~/.bashrc not found - continuing anyway"
fi

# Also try to activate nodeenv if it exists in project
# Check for both "nodeenv" and "nodevenv" (common typo)
NODEENV_DIR=""
if [ -d "nodeenv" ]; then
    NODEENV_DIR="nodeenv"
elif [ -d "nodevenv" ]; then
    NODEENV_DIR="nodevenv"
    echo "   ⚠ WARNING: Found 'nodevenv' directory (should be 'nodeenv')"
fi

if [ -n "$NODEENV_DIR" ]; then
    if [ -f "$NODEENV_DIR/bin/activate" ]; then
        echo "   Activating $NODEENV_DIR..."
        source "$NODEENV_DIR/bin/activate"
        echo "   ✓ Nodeenv activated"
    elif [ -f "$NODEENV_DIR/Scripts/activate" ]; then
        # Windows Git Bash path
        echo "   Activating $NODEENV_DIR (Windows)..."
        source "$NODEENV_DIR/Scripts/activate"
        echo "   ✓ Nodeenv activated"
    fi
fi

echo ""

# Step 2: Check if mmdc is available
echo "2. Checking for mmdc (mermaid-cli)..."
if command -v mmdc &> /dev/null; then
    MMDC_VERSION=$(mmdc --version 2>&1 | head -1)
    echo "   ✓ Found: mmdc $MMDC_VERSION"
    echo "   ✓ Location: $(which mmdc)"
    MMDC_OK=true
else
    echo "   ✗ mmdc not found in PATH"
    MMDC_OK=false
fi

echo ""

# Step 3: Install mmdc if not found
if [ "$MMDC_OK" = false ]; then
    echo "3. Installing mermaid-cli..."

    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo "   ✗ ERROR: npm not found"
        echo ""
        echo "   Please install Node.js and npm first:"
        echo "   - https://nodejs.org/"
        echo ""
        exit 1
    fi

    echo "   Installing @mermaid-js/mermaid-cli globally..."
    npm install -g @mermaid-js/mermaid-cli

    # Verify installation
    if command -v mmdc &> /dev/null; then
        MMDC_VERSION=$(mmdc --version 2>&1 | head -1)
        echo "   ✓ Installed: mmdc $MMDC_VERSION"
    else
        echo "   ✗ ERROR: Installation failed"
        echo ""
        echo "   Please install manually:"
        echo "      npm install -g @mermaid-js/mermaid-cli"
        echo ""
        exit 1
    fi
    echo ""
fi

# Step 4: Run batch processing
echo "4. Starting batch processing..."
echo "   Command: python run_batch_processing.py $@"
echo ""
echo "================================================================================"
echo ""

python run_batch_processing.py "$@"

EXIT_CODE=$?

echo ""
echo "================================================================================"
echo "BATCH PROCESSING COMPLETE"
echo "================================================================================"
echo "Exit code: $EXIT_CODE"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Success!"
    echo ""
    echo "Outputs:"
    echo "  - Diagrams: outputs_final/diagrams/"
    echo "  - Word docs: outputs_final/word_reports/"
    echo "  - Logs: logs/"
else
    echo "✗ Processing failed"
    echo ""
    echo "Check logs:"
    echo "  tail -100 logs/batch_processing_*.log"
fi

echo "================================================================================"

exit $EXIT_CODE
