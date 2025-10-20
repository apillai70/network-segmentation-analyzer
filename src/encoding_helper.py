"""
Encoding Helper for CSV Files

Provides robust encoding detection and handling for CSV files
that may use different encodings (UTF-8, Latin-1, Windows-1252, etc.)
"""
import logging
from pathlib import Path
from typing import Optional

# Try to import chardet, but make it optional
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

logger = logging.getLogger(__name__)


def detect_file_encoding(file_path: str, sample_size: int = 10000) -> str:
    """Detect the encoding of a file

    Args:
        file_path: Path to the file
        sample_size: Number of bytes to sample (default: 10000)

    Returns:
        Detected encoding name (e.g., 'utf-8', 'latin-1', 'cp1252')
    """
    if not HAS_CHARDET:
        logger.debug("chardet not available, defaulting to utf-8")
        return 'utf-8'

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)

        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)

        logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")

        # If confidence is very low, default to utf-8
        if confidence < 0.5:
            logger.warning(f"Low confidence ({confidence:.2f}) for detected encoding {encoding}, defaulting to utf-8")
            return 'utf-8'

        return encoding

    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}, defaulting to utf-8")
        return 'utf-8'


def open_csv_with_fallback(file_path: str, mode: str = 'r', **kwargs):
    """Open a CSV file with automatic encoding fallback

    Tries multiple encodings in order of likelihood:
    1. UTF-8
    2. Auto-detected encoding
    3. Latin-1 (ISO-8859-1)
    4. Windows-1252 (cp1252)

    Args:
        file_path: Path to the CSV file
        mode: File open mode (default: 'r')
        **kwargs: Additional arguments to pass to open()

    Returns:
        File handle

    Raises:
        Exception: If file cannot be opened with any encoding
    """
    encodings_to_try = [
        'utf-8',
        detect_file_encoding(file_path),
        'latin-1',
        'cp1252',
        'iso-8859-1'
    ]

    # Remove duplicates while preserving order
    encodings_to_try = list(dict.fromkeys(encodings_to_try))

    last_error = None

    for encoding in encodings_to_try:
        try:
            # Try to open and read a bit to verify encoding works
            f = open(file_path, mode, encoding=encoding, **kwargs)

            # Verify we can read the file
            if 'r' in mode:
                # Read first 1000 characters to verify encoding
                pos = f.tell()
                f.read(1000)
                f.seek(pos)  # Reset to beginning

            logger.info(f"Successfully opened {Path(file_path).name} with encoding: {encoding}")
            return f

        except UnicodeDecodeError as e:
            last_error = e
            logger.debug(f"Failed to open with {encoding}: {e}")
            try:
                f.close()
            except:
                pass
            continue

        except Exception as e:
            last_error = e
            logger.debug(f"Error with {encoding}: {e}")
            try:
                f.close()
            except:
                pass
            continue

    # If all encodings failed, raise the last error
    error_msg = f"Could not open {file_path} with any encoding. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


def convert_to_utf8(input_path: str, output_path: Optional[str] = None, source_encoding: Optional[str] = None) -> str:
    """Convert a file to UTF-8 encoding

    Args:
        input_path: Path to input file
        output_path: Path to output file (default: adds .utf8.csv suffix)
        source_encoding: Source encoding (default: auto-detect)

    Returns:
        Path to converted file
    """
    input_file = Path(input_path)

    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}.utf8.csv")

    if source_encoding is None:
        source_encoding = detect_file_encoding(input_path)

    logger.info(f"Converting {input_file.name} from {source_encoding} to UTF-8")

    try:
        # Read with source encoding
        with open(input_path, 'r', encoding=source_encoding) as f:
            content = f.read()

        # Write as UTF-8
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)

        logger.info(f"Converted file saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


# Example usage:
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Detecting encoding for: {file_path}")
        encoding = detect_file_encoding(file_path)
        print(f"Detected: {encoding}")

        print(f"\nTrying to open with fallback...")
        with open_csv_with_fallback(file_path) as f:
            lines = f.readlines()
            print(f"Successfully read {len(lines)} lines")
            print(f"First line: {lines[0][:100]}")
    else:
        print("Usage: python encoding_helper.py <csv_file>")
