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
    ):
        """
        Initialize MarkItDown.

        Args:
            llm_client: Optional LLM client for AI-assisted conversions (e.g., image descriptions).
            llm_model: The LLM model name to use when llm_client is provided.
            style_map: Optional style map string for DOCX conversion.
        """
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._style_map = style_map
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
            pass

    def register_converter(self, converter_class: type, **kwargs) -> None:
        """Register a custom document converter.

        Args:
            converter_class: A class that subclasses DocumentConverter.
            **kwargs: Additional keyword arguments passed to the converter.
        """
        self._converters.append((converter_class, kwargs))

    def convert(
        self,
        source: Union[str, Path],
        **kwargs,
    ) -> DocumentConverterResult:
        """Convert a file or URL to Markdown.

        Args:
            source: A file path or URL to convert.
            **kwargs: Additional keyword arguments forwarded to converters.

        Returns:
            A DocumentConverterResult containing the Markdown text.

        Raises:
            FileNotFoundError: If the source file does not exist.
            ValueError: If the source cannot be converted.
        """
        source = str(source)

        # Detect if source is a URL
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            return self._convert_url(source, **kwargs)

        # Treat as local file path
        local_path = os.path.abspath(source)
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        return self._convert_local(local_path, **kwargs)

    def _convert_url(self, url: str, **kwargs) -> DocumentConverterResult:
        """Download and convert a URL to Markdown."""
        import tempfile
        import urllib.request

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            tmp_path = tmp.name

        try:
            urllib.request.urlretrieve(url, tmp_path)
            result = self._convert_local(tmp_path, url=url, **kwargs)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return result

    def _convert_local(
        self, local_path: str, **kwargs
    ) -> DocumentConverterResult:
        """Convert a local file to Markdown using registered converters."""
        mime_type, _ = mimetypes.guess_type(local_path)

        for converter_class, converter_kwargs in self._converters:
            merged_kwargs = {**converter_kwargs, **kwargs}
            converter = converter_class(**merged_kwargs)
            result = converter.convert(local_path, mime_type=mime_type, **merged_kwargs)
            if result is not None:
                return result

        # Fallback: return raw text if readable
        try:
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return DocumentConverterResult(
                title=Path(local_path).stem,
                text_content=text,
            )
        except Exception as exc:
            raise ValueError(
                f"Could not convert file: {local_path}"
            ) from exc
