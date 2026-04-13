"""Material parsing for uploaded documents."""

from dataclasses import dataclass, field


@dataclass
class ParseResult:
    """Result of parsing a document."""

    text: str
    page_count: int | None = None
    sections: list[dict] = field(default_factory=list)
