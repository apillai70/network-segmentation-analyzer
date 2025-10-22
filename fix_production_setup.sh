#!/bin/bash
# Fix Production Setup.py Encoding Issue
# This script ensures setup.py has UTF-8 encoding for README.md

echo "=== Production Setup.py Encoding Fix ==="
echo ""

SETUP_FILE="setup.py"

# Check if setup.py exists
if [ ! -f "$SETUP_FILE" ]; then
    echo "ERROR: setup.py not found in current directory"
    echo "Please run this script from the project root"
    exit 1
fi

# Read current setup.py
echo "Reading current setup.py..."
content=$(cat "$SETUP_FILE")

# Check if it already has the fix
if echo "$content" | grep -q 'open("README.md", encoding="utf-8")'; then
    echo "✓ setup.py already has UTF-8 encoding fix"
    echo ""
    echo "Trying pip install -e . to verify..."
    pip install -e .
    exit $?
fi

# Create backup
BACKUP_FILE="setup.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "Creating backup: $BACKUP_FILE"
cp "$SETUP_FILE" "$BACKUP_FILE"

# Apply fix using sed
echo "Applying UTF-8 encoding fix..."
sed -i.tmp 's/with open("README\.md") as f:/with open("README.md", encoding="utf-8") as f:/g' "$SETUP_FILE"
sed -i.tmp "s/with open('README\.md') as f:/with open('README.md', encoding='utf-8') as f:/g" "$SETUP_FILE"
rm -f "${SETUP_FILE}.tmp"

echo "✓ Applied fix to setup.py"
echo ""

# Show the change
echo "Changes made:"
echo "  OLD: with open(\"README.md\") as f:"
echo "  NEW: with open(\"README.md\", encoding=\"utf-8\") as f:"
echo ""

# Try installing
echo "Testing pip install -e ..."
echo ""

pip install -e .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ SUCCESS! Package installed successfully"
    echo ""
    echo "Backup saved as: $BACKUP_FILE"
else
    echo ""
    echo "ERROR: Installation failed"
    echo "Restoring backup..."
    cp "$BACKUP_FILE" "$SETUP_FILE"
    echo "Backup restored. Original setup.py preserved."
    exit 1
fi
