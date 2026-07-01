"""Tests for the document parser service."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from app.services.parser_service import parse_document, parse_pdf
from tests.conftest import make_test_pdf


def test_parse_pdf_extracts_pages(tmp_path: Path) -> None:
    """parse_pdf returns one ParsedPage per page with 1-based numbers."""
    pdf_path = make_test_pdf(
        tmp_path / "sample.pdf",
        ["Introduction to RAG.", "Methods and experiments."],
    )

    parsed = parse_pdf(str(pdf_path))

    assert parsed.page_count == 2
    assert len(parsed.pages) == 2
    assert parsed.pages[0].page == 1
    assert parsed.pages[1].page == 2
    assert "Introduction" in parsed.pages[0].text
    assert "Methods" in parsed.pages[1].text


def test_parse_pdf_single_page(tmp_path: Path) -> None:
    """parse_pdf handles a single-page document."""
    pdf_path = make_test_pdf(tmp_path / "one.pdf", ["Only page."])

    parsed = parse_pdf(str(pdf_path))

    assert parsed.page_count == 1
    assert parsed.pages[0].page == 1
    assert "Only page" in parsed.pages[0].text


def test_parse_document_text_file(tmp_path: Path) -> None:
    text_path = tmp_path / "runbook.txt"
    text_path.write_text("Incident triage\n\nAssign an owner.", encoding="utf-8")

    parsed = parse_document(str(text_path), source="text")

    assert parsed.page_count == 1
    assert "Incident triage" in parsed.pages[0].text
    assert "Assign an owner" in parsed.pages[0].text


def test_parse_document_html_strips_scripts(tmp_path: Path) -> None:
    html_path = tmp_path / "policy.html"
    html_path.write_text(
        """
        <html>
          <head><style>.hidden { display: none; }</style></head>
          <body>
            <h1>Access Policy</h1>
            <p>Managers can review sources.</p>
            <script>alert("ignore me")</script>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    parsed = parse_document(str(html_path), source="html")

    assert parsed.page_count == 1
    assert "Access Policy" in parsed.pages[0].text
    assert "Managers can review sources" in parsed.pages[0].text
    assert "ignore me" not in parsed.pages[0].text


def test_parse_document_docx_extracts_paragraphs(tmp_path: Path) -> None:
    docx_path = tmp_path / "guide.docx"
    document_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Release checklist</w:t></w:r></w:p>
        <w:p><w:r><w:t>Verify citations before publishing.</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    parsed = parse_document(str(docx_path), source="docx")

    assert parsed.page_count == 1
    assert "Release checklist" in parsed.pages[0].text
    assert "Verify citations" in parsed.pages[0].text
