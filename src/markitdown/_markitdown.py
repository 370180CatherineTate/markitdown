"""Core MarkItDown conversion engine.

This module provides the main MarkItDown class responsible for converting
various file formats and URLs to Markdown.
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse


class DocumentConverterResult:
    """Holds the result of a document conversion."""

    def __init__(self, title: Optional[str] = None, text_content: str = ""):
        self.title = title
        self.text_content = text_content

    def __str__(self) -> str:
        return self.text_content


class DocumentConverter:
    """Base class for all document converters."""

    def convert(
        self,
        local_path: str,
        **kwargs,
    ) -> Optional[DocumentConverterResult]:
        """Convert a document to Markdown.

        Args:
            local_path: Path to the local file to convert.
            **kwargs: Additional keyword arguments for conversion.

        Returns:
            A DocumentConverterResult or None if conversion is not supported.
        """
        raise NotImplementedError("Subclasses must implement convert()")


class MarkItDown:
    """Main class for converting documents to Markdown.

    Supports conversion of various file formats including HTML, PDF,
    Word documents, Excel spreadsheets, images, and more.

    Example:
        >>> md = MarkItDown()
        >>> result = md.convert("document.pdf")
        >>> print(result.text_content)
    """

    def __init__(
        self,
        llm_client=None,
        llm_model: Optional[str] = None,
        style_map: Optional[str] = None,
        # Personal preference: strip trailing whitespace from converted output by default
        strip_trailing_whitespace: bool = True,
        # Personally I find it useful to normalize multiple blank lines into one;
        # keeps converted output cleaner without losing any real content.
        collapse_blank_lines: bool = True,
    ):
        """
        Initialize MarkItDown.

        Args:
            llm_client: Optional LLM client for AI-assisted conversions (e.g., image descriptions).
            llm_model: The LLM model name to use when llm_client is provided.
            style_map: Optional style map string for DOCX conversion.
            strip_trailing_whitespace: If True, strip trailing whitespace from each line
                of the converted Markdown output. Defaults to True.
            collapse_blank_lines: If True, collapse runs of more than one blank line into
                a single blank line in the converted Markdown output. Defaults to True.
        """
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._style_map = style_map
        self._strip_trailing_whitespace = strip_trailing_whitespace
        self._collapse_blank_lines = collapse_blank_lines
        self._converters: list[tuple[type, dict]] = []

        # Register built-in converters
        self._register_default_converters()

    def _register_default_converters(self) -> None:
        """Register all built-in document converters."""
        # Converters are registered in priority order (first match wins)
        # Lazy imports to keep startup time low and avoid hard dependencies
        try:
            from markitdown.converters import PlainTextConverter
            self.register_converter(PlainTextConverter)
        except ImportError:
          