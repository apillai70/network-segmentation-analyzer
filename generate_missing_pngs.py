#!/usr/bin/env python3
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

print("="*80)
print("PNG GENERATION FROM MERMAID DIAGRAMS")
print("="*80)

diagram_dir = Path('outputs_final/diagrams')

# Find mmdc - check multiple locations
mmdc_cmd = None

print("\nSearching for mmdc (Mermaid CLI)...")

# Method 1: Check if mmdc is in PATH (works if nodeenv activated or globally installed)
mmdc_in_path = shutil.which('mmdc')
if mmdc_in_path:
    try:
        result = subprocess.run([mmdc_in_path, '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            mmdc_cmd = mmdc_in_path
            print(f"✓ Found mmdc in PATH: {mmdc_in_path}")
    except:
        pass

# Method 2: Check for nodeenv in project directory (common for customer deployments)
if not mmdc_cmd:
    project_root = Path(__file__).parent
    nodeenv_mmdc = project_root / 'nodeenv' / 'Scripts' / 'mmdc'
    if nodeenv_mmdc.exists():
        try:
            result = subprocess.run([str(nodeenv_mmdc), '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                mmdc_cmd = str(nodeenv_mmdc)
                print(f"✓ Found mmdc in nodeenv: {mmdc_cmd}")
        except:
            pass

# Method 3: Try standard Windows npm global location
if not mmdc_cmd:
    user_profile = os.environ.get('USERPROFILE', '')
    if user_profile:
        npm_mmdc = Path(user_profile) / 'AppData' / 'Roaming' / 'npm' / 'mmdc.cmd'
        if npm_mmdc.exists():
            try:
                result = subprocess.run([str(npm_mmdc), '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    mmdc_cmd = str(npm_mmdc)
                    print(f"✓ Found mmdc in npm global: {mmdc_cmd}")
            except:
                pass

# Method 4: Last resort - try 'mmdc' directly
if not mmdc_cmd:
    try:
        result = subprocess.run(['mmdc', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            mmdc_cmd = 'mmdc'
            print("✓ Found mmdc (direct command)")
    except:
        pass

if not mmdc_cmd:
    print("\n✗ ERROR: mmdc (mermaid-cli) not found")
    print("\nSolutions:")
    print("  1. Activate nodeenv: nodeenv\\Scripts\\activate (Windows)")
    print("  2. Install globally: npm install -g @mermaid-js/mermaid-cli")
    print("  3. Install in nodeenv: nodeenv\\Scripts\\npm install -g @mermaid-js/mermaid-cli")
    exit(1)

# Find all .mmd files that need PNG conversion
print(f"\nScanning {diagram_dir} for Mermaid diagrams...")
all_mmd_files = list(diagram_dir.glob('*_diagram.mmd'))
missing_pngs = []

for mmd_file in all_mmd_files:
    png_file = mmd_file.with_suffix('.png')
    if not png_file.exists():
        missing_pngs.append(mmd_file)

print(f"Found {len(all_mmd_files)} total Mermaid diagrams")
print(f"Missing {len(missing_pngs)} PNG files")

if not missing_pngs:
    print("\n✓ All PNG files already exist!")
    exit(0)

print(f"\nGenerating {len(missing_pngs)} PNG files...")
print("="*80)

success_count = 0
failed_count = 0

for mmd_file in missing_pngs:
    app_name = mmd_file.stem.replace('_diagram', '')
    png_path = mmd_file.with_suffix('.png')

    # Read and strip code fences
    with open(mmd_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract graph content (between code fences and before legend)
    lines = content.split('\n')
    graph_lines = []
    in_graph = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```mermaid'):
            in_graph = True
            continue
        elif stripped == '```':
            in_graph = False
            break
        elif in_graph:
            graph_lines.append(line)

    content = '\n'.join(graph_lines).strip()

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Generate PNG with high resolution (scale=4 for 300+ DPI equivalent)
    try:
        result = subprocess.run(
            [mmdc_cmd, '-i', tmp_path, '-o', str(png_path),
             '-w', '4800', '-H', '3600', '-s', '4', '-t', 'neutral', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f'✓ {app_name}: PNG generated')
            success_count += 1
        else:
            print(f'✗ {app_name}: mmdc returned error')
            if result.stderr:
                print(f'  Error: {result.stderr[:200]}')
            failed_count += 1
    except Exception as e:
        print(f'✗ {app_name}: {e}')
        failed_count += 1
    finally:
        try:
            Path(tmp_path).unlink()
        except:
            pass

print("\n" + "="*80)
print(f"PNG GENERATION COMPLETE")
print("="*80)
print(f"✓ Success: {success_count}/{len(missing_pngs)} PNG files generated")
if failed_count > 0:
    print(f"✗ Failed: {failed_count}/{len(missing_pngs)} PNG files")
print(f"\nOutput location: {diagram_dir}")
print("="*80)
