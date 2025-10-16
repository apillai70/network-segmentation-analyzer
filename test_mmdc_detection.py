#!/usr/bin/env python3
"""
Test mmdc Detection
===================
Diagnostic script to check if mmdc can be found
"""

import subprocess
import shutil
import os
from pathlib import Path

print("=" * 80)
print("MMDC DETECTION DIAGNOSTIC")
print("=" * 80)

# Test 1: Check if mmdc is in PATH
print("\n1. Checking PATH...")
mmdc_in_path = shutil.which('mmdc')
if mmdc_in_path:
    print(f"   [OK] Found in PATH: {mmdc_in_path}")
    try:
        result = subprocess.run([mmdc_in_path, '--version'], capture_output=True, timeout=5, text=True)
        if result.returncode == 0:
            print(f"   [OK] Version: {result.stdout.strip()}")
        else:
            print(f"   [ERROR] Failed to get version")
    except Exception as e:
        print(f"   [ERROR] Error running: {e}")
else:
    print("   [ERROR] Not in PATH")

# Test 2: Check for nodeenv in project directory
print("\n2. Checking nodeenv...")
project_root = Path(__file__).parent
nodeenv_mmdc = project_root / 'nodeenv' / 'Scripts' / 'mmdc'
print(f"   Looking for: {nodeenv_mmdc}")

if nodeenv_mmdc.exists():
    print(f"   [OK] File exists")
    try:
        result = subprocess.run([str(nodeenv_mmdc), '--version'], capture_output=True, timeout=5, text=True)
        if result.returncode == 0:
            print(f"   [OK] Version: {result.stdout.strip()}")
        else:
            print(f"   [ERROR] Failed to run: {result.stderr}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
else:
    print(f"   [ERROR] File not found")

# Test 3: Check Windows npm global
print("\n3. Checking Windows npm global...")
user_profile = os.environ.get('USERPROFILE', '')
if user_profile:
    npm_mmdc = Path(user_profile) / 'AppData' / 'Roaming' / 'npm' / 'mmdc.cmd'
    print(f"   Looking for: {npm_mmdc}")
    if npm_mmdc.exists():
        print(f"   [OK] File exists")
        try:
            result = subprocess.run([str(npm_mmdc), '--version'], capture_output=True, timeout=5, text=True)
            if result.returncode == 0:
                print(f"   [OK] Version: {result.stdout.strip()}")
            else:
                print(f"   [ERROR] Failed to run")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")
    else:
        print(f"   [ERROR] File not found")
else:
    print("   [ERROR] USERPROFILE not set")

# Test 4: Try direct command
print("\n4. Checking direct 'mmdc' command...")
try:
    result = subprocess.run(['mmdc', '--version'], capture_output=True, timeout=5, text=True)
    if result.returncode == 0:
        print(f"   [OK] Works: {result.stdout.strip()}")
    else:
        print(f"   [ERROR] Failed")
except FileNotFoundError:
    print("   [ERROR] Command not found")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 5: Check environment
print("\n5. Environment check...")
print(f"   Python: {subprocess.run(['python', '--version'], capture_output=True, text=True).stdout.strip()}")
print(f"   CWD: {os.getcwd()}")
print(f"   PATH entries containing 'node':")
path_dirs = os.environ.get('PATH', '').split(os.pathsep)
node_paths = [p for p in path_dirs if 'node' in p.lower()]
for p in node_paths:
    print(f"      - {p}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if mmdc_in_path:
    print("[OK] mmdc is accessible - should work!")
elif nodeenv_mmdc.exists():
    print("[WARNING] mmdc exists but not in PATH")
    print("\nSolution: Activate nodeenv first:")
    print(f"   {project_root}\\nodeenv\\Scripts\\activate")
    print("   python run_batch_processing.py --batch-size 10")
else:
    print("[ERROR] mmdc not found anywhere")
    print("\nSolution: Install mermaid-cli:")
    print("   npm install -g @mermaid-js/mermaid-cli")

print("=" * 80)
