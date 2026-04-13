"""Plain text and markdown parser."""

import re
from pathlib import Path

from memoryforge.parser import ParseResult


def _read_text(file_path: Path) -> str:
    """Read file text with UTF-8, falling back to latin-1 for non-UTF-8 files."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def parse_text(file_path: Path) -> ParseResult:
    """Parse a plain text file."""
    return ParseResult(text=_read_text(file_path))


def parse_markdown(file_path: Path) -> ParseResult:
    """Parse a markdown file, extracting heading-based sections."""
    text = _read_text(file_path)
    sections = []
    current_heading = None
    current_body_lines: list[str] = []

    for line in text.split("\n"):
        match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if match:
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body_lines).strip(),
                })
            current_heading = match.group(2)
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body_lines).strip(),
        })

    return ParseResult(text=text, sections=sections)
