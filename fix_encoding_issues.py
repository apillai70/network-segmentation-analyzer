#!/usr/bin/env python3
"""
UTF-8 Encoding Fixer
====================
This script finds and reports all file operations that may have encoding issues.
It scans Python files for open() calls and pandas read operations without explicit encoding.

Usage:
    python fix_encoding_issues.py --scan      # Scan and report issues
    python fix_encoding_issues.py --fix       # Apply fixes automatically
    python fix_encoding_issues.py --test      # Test on sample files only
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import argparse

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass


class EncodingFixer:
    """Finds and fixes encoding issues in Python files"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues_found = []

        # Patterns to find
        self.patterns = {
            # open() without encoding
            'open_no_encoding': re.compile(
                r'''(with\s+open\(|open\()([^)]+?)(\)|,\s*mode\s*=\s*['\"][rwa]['\"])(?!\s*,\s*encoding)''',
                re.MULTILINE
            ),
            # read_csv without encoding
            'read_csv_no_encoding': re.compile(
                r'''(pd\.read_csv|read_csv)\(([^)]+?)(?!\s*,\s*encoding)''',
                re.MULTILINE
            ),
            # read_text without encoding
            'read_text_no_encoding': re.compile(
                r'''\.read_text\(\)''',
                re.MULTILINE
            ),
            # write_text without encoding
            'write_text_no_encoding': re.compile(
                r'''\.write_text\(([^)]+?)\)(?!\s*,\s*encoding)''',
                re.MULTILINE
            )
        }

    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for encoding issues"""
        issues = []

        try:
            # Read with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"⚠️  Cannot read {file_path}: {e}")
            return issues

        # Check for open() without encoding
        for match in re.finditer(r'open\([^)]+\)', content):
            matched_text = match.group(0)
            if 'encoding=' not in matched_text:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'type': 'open_no_encoding',
                    'content': lines[line_num - 1].strip(),
                    'fix': 'Add encoding=\'utf-8\' parameter'
                })

        # Check for pd.read_csv() without encoding
        for match in re.finditer(r'(pd\.read_csv|read_csv)\([^)]+\)', content):
            matched_text = match.group(0)
            if 'encoding=' not in matched_text:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'type': 'read_csv_no_encoding',
                    'content': lines[line_num - 1].strip(),
                    'fix': 'Add encoding=\'utf-8\' parameter'
                })

        # Check for .read_text() without encoding
        for match in re.finditer(r'\.read_text\(\)', content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'file': file_path,
                'line': line_num,
                'type': 'read_text_no_encoding',
                'content': lines[line_num - 1].strip(),
                'fix': 'Change to .read_text(encoding=\'utf-8\')'
            })

        # Check for .write_text() without encoding
        for match in re.finditer(r'\.write_text\([^)]+\)', content):
            matched_text = match.group(0)
            if 'encoding=' not in matched_text:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'type': 'write_text_no_encoding',
                    'content': lines[line_num - 1].strip(),
                    'fix': 'Add encoding=\'utf-8\' as second parameter'
                })

        return issues

    def scan_project(self, directories: List[str] = None) -> Dict:
        """Scan entire project for encoding issues"""
        if directories is None:
            directories = ['src', 'tests', 'scripts', '.']

        all_issues = []
        files_scanned = 0

        print("🔍 Scanning for UTF-8 encoding issues...\n")

        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue

            # Find all Python files
            if dir_path.is_file() and dir_path.suffix == '.py':
                python_files = [dir_path]
            else:
                python_files = list(dir_path.rglob('*.py'))

            for py_file in python_files:
                # Skip virtual environments and cache
                if any(skip in str(py_file) for skip in ['venv', '.venv', 'env', '__pycache__', 'site-packages']):
                    continue

                files_scanned += 1
                issues = self.scan_file(py_file)
                all_issues.extend(issues)

        # Group by file
        issues_by_file = {}
        for issue in all_issues:
            file_key = str(issue['file'])
            if file_key not in issues_by_file:
                issues_by_file[file_key] = []
            issues_by_file[file_key].append(issue)

        return {
            'total_files': files_scanned,
            'files_with_issues': len(issues_by_file),
            'total_issues': len(all_issues),
            'issues_by_file': issues_by_file
        }

    def print_report(self, results: Dict):
        """Print a detailed report of encoding issues"""
        print("="*80)
        print("UTF-8 ENCODING ISSUES REPORT")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"   Files scanned: {results['total_files']}")
        print(f"   Files with issues: {results['files_with_issues']}")
        print(f"   Total issues found: {results['total_issues']}")

        if results['total_issues'] == 0:
            print("\n✅ No encoding issues found! Your project is clean.")
            return

        print("\n" + "="*80)
        print("DETAILED ISSUES")
        print("="*80 + "\n")

        for file_path, issues in results['issues_by_file'].items():
            print(f"\n📁 {file_path}")
            print(f"   {len(issues)} issue(s) found\n")

            for issue in issues:
                print(f"   Line {issue['line']}:")
                print(f"      Code: {issue['content']}")
                print(f"      Fix:  {issue['fix']}")
                print()

    def generate_fix_commands(self, results: Dict) -> str:
        """Generate a bash/PowerShell script with fix commands"""
        if results['total_issues'] == 0:
            return "# No issues to fix"

        script_lines = [
            "# UTF-8 Encoding Fix Script",
            "# Generated by fix_encoding_issues.py",
            "# This script contains manual fix instructions",
            "",
            "# IMPORTANT: Review each change before applying!",
            ""
        ]

        for file_path, issues in results['issues_by_file'].items():
            script_lines.append(f"\n# File: {file_path}")
            script_lines.append(f"# Issues: {len(issues)}")

            for issue in issues:
                script_lines.append(f"# Line {issue['line']}: {issue['fix']}")
                script_lines.append(f"#   Current: {issue['content']}")

        return '\n'.join(script_lines)

    def apply_fixes(self, results: Dict, backup: bool = True) -> int:
        """Apply automatic fixes to files"""
        fixes_applied = 0

        print("\n🔧 Applying fixes...\n")

        for file_path, issues in results['issues_by_file'].items():
            file_path = Path(file_path)

            try:
                # Read original content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()

                # Create backup
                if backup:
                    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    print(f"   📋 Backup created: {backup_path}")

                # Apply fixes
                modified_content = original_content

                # Fix open() calls
                modified_content = re.sub(
                    r"open\(([^)]+?)\)",
                    lambda m: self._fix_open_call(m.group(0)),
                    modified_content
                )

                # Fix read_csv() calls
                modified_content = re.sub(
                    r"(pd\.read_csv|read_csv)\(([^)]+?)\)",
                    lambda m: self._fix_read_csv_call(m.group(0)),
                    modified_content
                )

                # Fix .read_text() calls
                modified_content = re.sub(
                    r"\.read_text\(\)",
                    ".read_text(encoding='utf-8')",
                    modified_content
                )

                # Fix .write_text() calls
                modified_content = re.sub(
                    r"\.write_text\(([^)]+?)\)",
                    lambda m: self._fix_write_text_call(m.group(0)),
                    modified_content
                )

                # Write fixed content
                if modified_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    print(f"   ✅ Fixed: {file_path}")
                    fixes_applied += len(issues)

            except Exception as e:
                print(f"   ❌ Error fixing {file_path}: {e}")

        return fixes_applied

    def _fix_open_call(self, match_text: str) -> str:
        """Fix a single open() call"""
        if 'encoding=' in match_text:
            return match_text

        # Add encoding parameter before closing parenthesis
        if match_text.endswith(')'):
            return match_text[:-1] + ", encoding='utf-8')"
        return match_text

    def _fix_read_csv_call(self, match_text: str) -> str:
        """Fix a single read_csv() call"""
        if 'encoding=' in match_text:
            return match_text

        # Add encoding parameter
        if match_text.endswith(')'):
            return match_text[:-1] + ", encoding='utf-8')"
        return match_text

    def _fix_write_text_call(self, match_text: str) -> str:
        """Fix a single write_text() call"""
        if 'encoding=' in match_text:
            return match_text

        # Add encoding as second parameter
        if match_text.endswith(')'):
            return match_text[:-1] + ", encoding='utf-8')"
        return match_text


def main():
    parser = argparse.ArgumentParser(
        description='Find and fix UTF-8 encoding issues in Python files'
    )
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scan for issues and generate report'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix issues (creates .bak backups)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files when fixing'
    )
    parser.add_argument(
        '--path',
        type=str,
        default='.',
        help='Project root path (default: current directory)'
    )
    parser.add_argument(
        '--dirs',
        nargs='+',
        default=['src', 'tests', 'scripts', 'bin'],
        help='Directories to scan (default: src tests scripts bin)'
    )

    args = parser.parse_args()

    if not args.scan and not args.fix:
        parser.print_help()
        sys.exit(1)

    fixer = EncodingFixer(args.path)
    results = fixer.scan_project(args.dirs)

    # Always print report
    fixer.print_report(results)

    if args.fix and results['total_issues'] > 0:
        print("\n" + "="*80)
        response = input("\n⚠️  Apply fixes automatically? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            fixes_applied = fixer.apply_fixes(results, backup=not args.no_backup)
            print(f"\n✅ Applied {fixes_applied} fixes")
            print("\n💡 Tip: Run tests to verify everything works correctly")
        else:
            print("\n❌ Fixes not applied. Use --scan to review issues.")

    # Save report to file
    report_file = Path(args.path) / 'encoding_issues_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("UTF-8 ENCODING ISSUES REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Files scanned: {results['total_files']}\n")
        f.write(f"Files with issues: {results['files_with_issues']}\n")
        f.write(f"Total issues: {results['total_issues']}\n\n")

        for file_path, issues in results['issues_by_file'].items():
            f.write(f"\n{file_path}\n")
            for issue in issues:
                f.write(f"  Line {issue['line']}: {issue['content']}\n")
                f.write(f"    Fix: {issue['fix']}\n")

    print(f"\n📄 Report saved to: {report_file}")


if __name__ == '__main__':
    main()
