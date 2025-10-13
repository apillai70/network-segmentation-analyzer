#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installation Script for Network Segmentation Analyzer v3.0
===========================================================
Automated installation with dependency checking and configuration

Usage:
    python install.py
    python install.py --full  # Install with deep learning
    python install.py --gpu   # Install with GPU support
"""

import sys
import subprocess
import platform
import os
from pathlib import Path


def print_banner():
    """Print installation banner"""
    print("=" * 80)
    print("NETWORK SEGMENTATION ANALYZER v3.0 - INSTALLATION")
    print("=" * 80)
    print()


def check_python_version():
    """Check if Python version is compatible"""
    print("✓ Checking Python version...")

    required_version = (3, 8)
    current_version = sys.version_info[:2]

    if current_version < required_version:
        print(f"❌ Python {required_version[0]}.{required_version[1]}+ required")
        print(f"   Current version: {current_version[0]}.{current_version[1]}")
        sys.exit(1)

    print(f"  Python {current_version[0]}.{current_version[1]} detected ✓")


def install_dependencies(full_install=False, gpu_support=False):
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")

    # Modify requirements based on options
    if full_install or gpu_support:
        print("  Installing FULL version (with deep learning)...")

        # Read requirements
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()

        # Uncomment torch line
        modified_lines = []
        for line in lines:
            if line.strip().startswith('# torch=='):
                # Uncomment torch
                if gpu_support:
                    modified_lines.append('torch==2.1.2+cu118\n')
                else:
                    modified_lines.append('torch==2.1.2+cpu\n')
            else:
                modified_lines.append(line)

        # Write temporary requirements
        with open('requirements_temp.txt', 'w') as f:
            f.writelines(modified_lines)

        # Install
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements_temp.txt'
        ])

        # Clean up
        os.remove('requirements_temp.txt')

    else:
        print("  Installing BASIC version (without deep learning)...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])

    print("  ✓ Dependencies installed")


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")

    directories = [
        'data/input',
        'data/processed',
        'outputs',
        'outputs_final',
        'logs',
        'models',
        'persistent_data',
        'visualizations',
        'reports'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("  ✓ Directories created")


def create_config_files():
    """Create default configuration files"""
    print("\n⚙️  Creating configuration files...")

    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("""# Network Segmentation Analyzer Configuration
# ==============================================

# Database settings
DATABASE_PATH=./outputs_final/network_analysis.db

# Model settings
MODELS_DIR=./models
USE_DEEP_LEARNING=true
USE_GPU=false
DEVICE=cpu

# Analysis settings
DEFAULT_DATA_DIR=./data/input
DEFAULT_OUTPUT_DIR=./outputs_final

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Features
ENABLE_GAT=true
ENABLE_VAE=true
ENABLE_TRANSFORMER=true
ENABLE_RL_OPTIMIZATION=true
ENABLE_GRAPH_ALGORITHMS=true
""")

    print("  ✓ Configuration files created")


def run_verification():
    """Run installation verification"""
    print("\n🔍 Verifying installation...")

    try:
        # Test basic imports
        import pandas
        import numpy
        import networkx
        import sklearn

        print("  ✓ Basic dependencies OK")

        # Test deep learning (optional)
        try:
            import torch
            print(f"  ✓ PyTorch {torch.__version__} available")
            print(f"    CUDA available: {torch.cuda.is_available()}")
        except ImportError:
            print("  ⚠️  PyTorch not available (deep learning disabled)")

        # Test project imports
        sys.path.insert(0, str(Path.cwd() / 'src'))

        from core.persistence_manager import PersistenceManager
        print("  ✓ Core modules OK")

        from agentic.local_semantic_analyzer import LocalSemanticAnalyzer
        print("  ✓ Agentic AI modules OK")

        try:
            from deep_learning.gat_model import GATApplicationAnalyzer
            print("  ✓ Deep learning modules OK")
        except ImportError as e:
            print(f"  ⚠️  Deep learning modules unavailable: {e}")

        print("\n  ✅ Verification passed!")

    except Exception as e:
        print(f"\n  ❌ Verification failed: {e}")
        print("  Please check the error and try again")
        return False

    return True


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 80)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Place your network flow CSV files in: ./data/input/")
    print("  2. Run analysis:")
    print("     python run_complete_analysis.py")
    print("\n  Or for full features:")
    print("     python run_complete_analysis.py --enable-all")
    print("\nFor help:")
    print("  python run_complete_analysis.py --help")
    print("\nDocumentation:")
    print("  README.md - Overview and quick start")
    print("  docs/USER_GUIDE.md - Detailed usage guide")
    print("  docs/ARCHITECTURE.md - System architecture")
    print("=" * 80)


def main():
    """Main installation function"""
    import argparse

    parser = argparse.ArgumentParser(description='Install Network Segmentation Analyzer')
    parser.add_argument('--full', action='store_true', help='Install with deep learning features')
    parser.add_argument('--gpu', action='store_true', help='Install with GPU support (CUDA)')
    args = parser.parse_args()

    print_banner()

    try:
        # Check Python version
        check_python_version()

        # Install dependencies
        install_dependencies(full_install=args.full or args.gpu, gpu_support=args.gpu)

        # Create directories
        create_directories()

        # Create config files
        create_config_files()

        # Verify installation
        if not run_verification():
            sys.exit(1)

        # Print next steps
        print_next_steps()

    except KeyboardInterrupt:
        print("\n⚠️  Installation interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
