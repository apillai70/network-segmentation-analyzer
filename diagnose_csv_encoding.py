#!/usr/bin/env python3
"""
Diagnose and fix CSV encoding issues

This script helps identify the correct encoding for CSV files that fail
to load with UTF-8, and provides options to convert them.
"""
import sys
import chardet
from pathlib import Path


def detect_encoding(file_path: Path) -> dict:
    """Detect the encoding of a file

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with encoding information
    """
    print(f"\nAnalyzing: {file_path}")
    print(f"File size: {file_path.stat().st_size:,} bytes")

    # Read raw bytes
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Detect encoding using chardet
    result = chardet.detect(raw_data)

    print(f"\nDetected encoding: {result['encoding']}")
    print(f"Confidence: {result['confidence'] * 100:.1f}%")

    return result


def try_read_with_encoding(file_path: Path, encoding: str) -> bool:
    """Try to read file with specific encoding

    Args:
        file_path: Path to the file
        encoding: Encoding to try

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
            print(f"\nSUCCESS: Read {len(lines)} lines with encoding: {encoding}")

            # Show first few lines
            print("\nFirst 3 lines:")
            for i, line in enumerate(lines[:3], 1):
                # Truncate long lines
                display_line = line.strip()[:100]
                if len(line.strip()) > 100:
                    display_line += "..."
                print(f"  {i}: {display_line}")

            return True
    except UnicodeDecodeError as e:
        print(f"FAILED: {encoding} - {e}")
        return False
    except Exception as e:
        print(f"ERROR: {encoding} - {e}")
        return False


def convert_encoding(file_path: Path, from_encoding: str, to_encoding: str = 'utf-8'):
    """Convert file from one encoding to another

    Args:
        file_path: Path to the file
        from_encoding: Source encoding
        to_encoding: Target encoding (default: utf-8)
    """
    output_path = file_path.with_suffix(f'.{to_encoding}.csv')

    print(f"\nConverting {file_path.name}")
    print(f"  From: {from_encoding}")
    print(f"  To: {to_encoding}")

    try:
        # Read with source encoding
        with open(file_path, 'r', encoding=from_encoding) as f:
            content = f.read()

        # Write with target encoding
        with open(output_path, 'w', encoding=to_encoding, newline='') as f:
            f.write(content)

        print(f"SUCCESS: Converted file saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"ERROR: Conversion failed - {e}")
        return None


def diagnose_csv_file(file_path_str: str):
    """Main diagnosis function

    Args:
        file_path_str: Path to CSV file to diagnose
    """
    file_path = Path(file_path_str)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return

    print("=" * 60)
    print("CSV Encoding Diagnosis Tool")
    print("=" * 60)

    # Step 1: Detect encoding
    detection_result = detect_encoding(file_path)
    detected_encoding = detection_result['encoding']

    # Step 2: Try common encodings
    print("\n" + "=" * 60)
    print("Testing common encodings:")
    print("=" * 60)

    encodings_to_try = [
        'utf-8',
        'latin-1',  # ISO-8859-1
        'cp1252',   # Windows-1252
        'iso-8859-1',
        detected_encoding  # The one chardet detected
    ]

    # Remove duplicates while preserving order
    encodings_to_try = list(dict.fromkeys([e for e in encodings_to_try if e]))

    successful_encoding = None

    for encoding in encodings_to_try:
        if try_read_with_encoding(file_path, encoding):
            if successful_encoding is None:
                successful_encoding = encoding

    # Step 3: Offer to convert
    if successful_encoding and successful_encoding != 'utf-8':
        print("\n" + "=" * 60)
        print("Recommendation:")
        print("=" * 60)
        print(f"The file is encoded as: {successful_encoding}")
        print("For best compatibility, convert to UTF-8")

        response = input(f"\nConvert to UTF-8? (y/n): ").strip().lower()
        if response == 'y':
            convert_encoding(file_path, successful_encoding, 'utf-8')

    elif successful_encoding == 'utf-8':
        print("\n" + "=" * 60)
        print("Result: File is already UTF-8 encoded")
        print("=" * 60)

    else:
        print("\n" + "=" * 60)
        print("WARNING: Could not read file with any common encoding")
        print("=" * 60)
        print("The file may be corrupted or use a rare encoding")


def show_usage():
    """Show usage instructions"""
    print("Usage:")
    print("  python diagnose_csv_encoding.py <path_to_csv_file>")
    print()
    print("Example:")
    print("  python diagnose_csv_encoding.py data/input/App_Code_RTRXX.csv")
    print()
    print("This tool will:")
    print("  1. Detect the file encoding")
    print("  2. Test reading with common encodings")
    print("  3. Offer to convert to UTF-8 if needed")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)

    file_path = sys.argv[1]
    diagnose_csv_file(file_path)
