#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

diagram_dir = Path('outputs_final/diagrams')
missing_apps = ['DNINT', 'IVRMC', 'IW', 'IWDE', 'IX', 'IXCI', 'IXOF', 'LB', 'LBCC', 'LBOT']

mmdc_cmd = r'C:\Users\AjayPillai\AppData\Roaming\npm\mmdc.cmd'

for app in missing_apps:
    mmd_path = diagram_dir / f'{app}_application_diagram.mmd'
    png_path = diagram_dir / f'{app}_application_diagram.png'

    if not mmd_path.exists():
        print(f'Warning: {app}: .mmd file not found')
        continue

    # Read and strip code fences
    with open(mmd_path, 'r', encoding='utf-8') as f:
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

    # Generate PNG
    try:
        result = subprocess.run(
            [mmdc_cmd, '-i', tmp_path, '-o', str(png_path)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f'Success: {app}: PNG generated')
        else:
            print(f'Failed: {app}: mmdc returned error')
            if result.stderr:
                print(f'  Error: {result.stderr[:200]}')
    except Exception as e:
        print(f'Failed: {app}: {e}')
    finally:
        try:
            Path(tmp_path).unlink()
        except:
            pass

print(f'\nDone! Check outputs_final/diagrams/ for PNG files')
