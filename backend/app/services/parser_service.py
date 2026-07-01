"""Document parsing service.

PDF parsing uses PyMuPDF to preserve page numbers. Text-like formats are parsed
with the standard library as a lightweight Stage 4 ingestion baseline; richer
layout-aware parsing remains a later provider upgrade.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import fitz  # PyMuPDF

SUPPORTED_DOCUMENT_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".html": "html",
    ".htm": "html",
    ".docx": "docx",
}

SUPPORTED_DOCUMENT_EXTENSIONS_LABEL = "PDF, Markdown, TXT, HTML, DOCX"


@dataclass
class ParsedPage:
    """A single parsed page: its 1-based page number and extracted text."""

    page: int
    text: str


@dataclass
class ParsedDocument:
    """Result of parsing a document: page count and per-page text."""

    page_count: int
    pages: list[ParsedPage]


def get_supported_document_source(filename: str) -> str | None:
    """Return the normalized source type for a supported filename."""
    return SUPPORTED_DOCUMENT_EXTENSIONS.get(Path(filename).suffix.lower())


def parse_document(file_path: str, *, source: str) -> ParsedDocument:
    """Parse a supported source document into text pages."""
    if source == "pdf":
        return parse_pdf(file_path)
    if source in {"markdown", "text"}:
        return parse_text_file(file_path)
    if source == "html":
        return parse_html(file_path)
    if source == "docx":
        return parse_docx(file_path)
    raise ValueError(f"Unsupported document source: {source}")


def parse_pdf(file_path: str) -> ParsedDocument:
    """Parse a PDF file into per-page text.

    Args:
        file_path: Path to the PDF on disk.

    Returns:
        A :class:`ParsedDocument` with one :class:`ParsedPage` per page
        (1-based page numbers).
    """
    doc = fitz.open(file_path)
    pages: list[ParsedPage] = []
    for index, page in enumerate(doc):
        # 1-based page number to match how readers display pages.
        pages.append(ParsedPage(page=index + 1, text=page.get_text("text")))
    page_count = doc.page_count
    doc.close()
    return ParsedDocument(page_count=page_count, pages=pages)


def parse_text_file(file_path: str) -> ParsedDocument:
    """Parse a plain text or Markdown file as a single logical page."""
    text = Path(file_path).read_text(encoding="utf-8-sig", errors="replace")
    return _single_page_document(text)


def parse_html(file_path: str) -> ParsedDocument:
    """Parse an HTML file into readable text."""
    raw_html = Path(file_path).read_text(encoding="utf-8-sig", errors="replace")
    parser = _TextHTMLParser()
    parser.feed(raw_html)
    parser.close()
    return _single_page_document(parser.text())


def parse_docx(file_path: str) -> ParsedDocument:
    """Parse a DOCX file by extracting paragraph text from word/document.xml."""
    try:
        with ZipFile(file_path) as archive:
            document_xml = archive.read("word/document.xml")
    except KeyError as exc:
        raise ValueError("DOCX is missing word/document.xml") from exc
    except BadZipFile as exc:
        raise ValueError("Invalid DOCX file") from exc

    root = ET.fromstring(document_xml)
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespaces):
        text = "".join(
            node.text or ""
            for node in paragraph.findall(".//w:t", namespaces)
        ).strip()
        if text:
            paragraphs.append(text)
    return _single_page_document("\n\n".join(paragraphs))


def _single_page_document(text: str) -> ParsedDocument:
    return ParsedDocument(page_count=1, pages=[ParsedPage(page=1, text=text.strip())])


class _TextHTMLParser(HTMLParser):
    """Small HTML-to-text parser for Stage 4 baseline ingestion."""

    _BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if text:
            self._parts.append(text)

    def text(self) -> str:
        lines = [line.strip() for line in "".join(self._parts).splitlines()]
        return "\n\n".join(line for line in lines if line)
