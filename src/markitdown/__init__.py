"""MarkItDown - A utility for converting various file formats to Markdown.

This package provides tools to convert documents, spreadsheets, presentations,
and other file formats into clean, readable Markdown text.

Note: Forked from microsoft/markitdown for personal use and experimentation.
"""

from markitdown._markitdown import MarkItDown, DocumentConverter, ConversionResult

__version__ = "0.1.0"
__author__ = "MarkItDown Contributors"
__license__ = "MIT"

# Expose StreamInfo if available, useful for programmatic usage
try:
    from markitdown._markitdown import StreamInfo
    __all__ = [
        "MarkItDown",
        "DocumentConverter",
        "ConversionResult",
        "StreamInfo",
    ]
except ImportError:
    __all__ = [
        "MarkItDown",
        "DocumentConverter",
        "ConversionResult",
    ]
