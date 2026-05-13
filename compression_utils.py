"""
compression_utils.py — gzip/zip based compression
"""

import io
import gzip
import zipfile


def compress_file(data: bytes, filename: str = 'file') -> bytes:
    """
    Compress file data using gzip.
    Returns compressed bytes.
    """
    buf = io.BytesIO()
    with gzip.GzipFile(filename=filename, mode='wb', fileobj=buf, compresslevel=9) as gz:
        gz.write(data)
    return buf.getvalue()


def compress_zip(data: bytes, filename: str = 'file') -> bytes:
    """
    Compress file data using zip.
    Returns zip archive as bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(filename, data)
    return buf.getvalue()


def decompress_gzip(data: bytes) -> bytes:
    """Decompress gzip data."""
    with gzip.open(io.BytesIO(data), 'rb') as gz:
        return gz.read()


def decompress_zip(data: bytes, filename: str = None) -> bytes:
    """Decompress zip data, returning first file or named file."""
    with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
        names = zf.namelist()
        if not names:
            raise ValueError("Empty zip archive")
        target = filename if filename and filename in names else names[0]
        return zf.read(target)


def get_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Calculate compression ratio as percentage saved.
    e.g., 100 -> 40 bytes = 60.0% savings
    """
    if original_size == 0:
        return 0.0
    saved = original_size - compressed_size
    return max(0.0, (saved / original_size) * 100)


def get_compression_stats(original_size: int, compressed_size: int) -> dict:
    ratio = get_compression_ratio(original_size, compressed_size)
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'bytes_saved': max(0, original_size - compressed_size),
        'ratio_percent': round(ratio, 2),
        'is_effective': compressed_size < original_size
    }
