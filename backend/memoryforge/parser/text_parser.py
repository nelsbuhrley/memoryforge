"""Plain text and markdown parser."""

import re
from pathlib import Path

from memoryforge.parser import ParseResult


def parse_text(file_path: Path) -> ParseResult:
    """Parse a plain text file."""
    text = file_path.read_text(encoding="utf-8")
    return ParseResult(text=text)


def parse_markdown(file_path: Path) -> ParseResult:
    """Parse a markdown file, extracting heading-based sections."""
    text = file_path.read_text(encoding="utf-8")
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
