"""PDF parser using pymupdf (fitz)."""

from pathlib import Path

import fitz

from memoryforge.parser import ParseResult


def parse_pdf(file_path: Path) -> ParseResult:
    """Extract text and structure from a PDF file."""
    pages_text = []

    with fitz.open(str(file_path)) as doc:
        for page in doc:
            pages_text.append(page.get_text())

    full_text = "\n\n".join(pages_text)
    return ParseResult(
        text=full_text,
        page_count=len(pages_text),
    )
