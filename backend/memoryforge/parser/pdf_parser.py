"""PDF parser using pymupdf (fitz)."""

from pathlib import Path

import fitz

from memoryforge.parser import ParseResult


def parse_pdf(file_path: Path) -> ParseResult:
    """Extract text and structure from a PDF file."""
    doc = fitz.open(str(file_path))
    pages_text = []
    sections = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages_text.append(text)

    doc.close()

    full_text = "\n\n".join(pages_text)
    return ParseResult(
        text=full_text,
        page_count=len(pages_text),
        sections=sections,
    )
