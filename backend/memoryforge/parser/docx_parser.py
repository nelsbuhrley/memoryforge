"""DOCX parser using python-docx."""

from pathlib import Path

from docx import Document

from memoryforge.parser import ParseResult


def parse_docx(file_path: Path) -> ParseResult:
    """Extract text and heading-based sections from a DOCX file."""
    doc = Document(str(file_path))
    sections = []
    full_text_parts = []
    current_heading = None
    current_body_lines: list[str] = []

    for para in doc.paragraphs:
        full_text_parts.append(para.text)

        if para.style and para.style.name.startswith("Heading"):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body_lines).strip(),
                })
            current_heading = para.text
            current_body_lines = []
        else:
            current_body_lines.append(para.text)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body_lines).strip(),
        })

    return ParseResult(
        text="\n".join(full_text_parts),
        sections=sections,
    )
