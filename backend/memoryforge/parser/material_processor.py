"""Orchestrates document parsing and KU extraction.

Two phases:
1. Light parse — extract text and structure (fast, no Claude)
2. Deep parse — send to Claude for KU extraction (slow, uses tokens)
"""

import json
from pathlib import Path

from memoryforge.config import Config
from memoryforge.db.repository import Repository
from memoryforge.parser.pdf_parser import parse_pdf
from memoryforge.parser.docx_parser import parse_docx
from memoryforge.parser.text_parser import parse_text, parse_markdown
from memoryforge.claude_service.prompts import build_ku_extraction_prompt
from memoryforge.claude_service.client import query_claude_json, SONNET


class MaterialProcessor:
    """Orchestrates material parsing and KU extraction."""

    def __init__(self, repo: Repository, config: Config) -> None:
        self.repo = repo
        self.config = config

    def _detect_parser(self, filename: str) -> str | None:
        """Detect which parser to use based on file extension."""
        ext = Path(filename).suffix.lower()
        return {
            ".pdf": "pdf",
            ".docx": "docx",
            ".txt": "text",
            ".md": "markdown",
        }.get(ext)

    def light_parse(self, material_id: int) -> bool:
        """Phase 1: Extract text and structure without Claude.

        Returns True if successful.
        """
        mat = self.repo.get_material(material_id)
        if not mat:
            return False

        parser_type = self._detect_parser(mat["filename"])
        if not parser_type:
            self.repo.update_material_status(material_id, "error")
            return False

        file_path = Path(mat["file_path"])
        if not file_path.exists():
            self.repo.update_material_status(material_id, "error")
            return False

        if parser_type == "pdf":
            result = parse_pdf(file_path)
        elif parser_type == "docx":
            result = parse_docx(file_path)
        elif parser_type == "markdown":
            result = parse_markdown(file_path)
        else:
            result = parse_text(file_path)

        outline = json.dumps([s["heading"] for s in result.sections] if result.sections else [])

        self.repo.update_material_status(
            material_id,
            status="parsed_light",
            structure_outline=outline,
        )

        if result.page_count and not mat.get("page_count"):
            self.repo.conn.execute(
                "UPDATE materials SET page_count = ? WHERE id = ?",
                (result.page_count, material_id),
            )
            self.repo.conn.commit()

        return True

    async def deep_parse(self, material_id: int) -> int:
        """Phase 2: Send to Claude for KU extraction.

        Returns the number of KUs created.
        """
        mat = self.repo.get_material(material_id)
        if not mat:
            return 0

        self.repo.update_material_status(material_id, "processing")

        file_path = Path(mat["file_path"])
        parser_type = self._detect_parser(mat["filename"])

        if parser_type == "pdf":
            result = parse_pdf(file_path)
        elif parser_type == "docx":
            result = parse_docx(file_path)
        elif parser_type == "markdown":
            result = parse_markdown(file_path)
        else:
            result = parse_text(file_path)

        subject = self.repo.get_subject(mat["subject_id"])
        subject_name = subject["name"] if subject else "Unknown"

        # Use sections if available, otherwise chunk the full text
        chunks = []
        if result.sections:
            for section in result.sections:
                chunks.append((section.get("heading", ""), section.get("body", "")))
        else:
            # Split into ~1000 char chunks
            text = result.text
            chunk_size = 1000
            for i in range(0, len(text), chunk_size):
                chunks.append((None, text[i:i + chunk_size]))

        MAX_KUS_PER_MATERIAL = 20
        KUS_PER_CHUNK = 4
        total_kus = 0
        for heading, text_chunk in chunks:
            if not text_chunk.strip():
                continue
            if total_kus >= MAX_KUS_PER_MATERIAL:
                break

            prompt = build_ku_extraction_prompt(
                text_chunk=text_chunk,
                subject_name=subject_name,
                section_heading=heading,
                max_kus=KUS_PER_CHUNK,
            )

            try:
                kus_data = await query_claude_json(prompt, model=SONNET)
                if not isinstance(kus_data, list):
                    kus_data = [kus_data]
            except Exception:
                continue

            for ku_data in kus_data:
                if total_kus >= MAX_KUS_PER_MATERIAL:
                    break
                self.repo.create_ku(
                    subject_id=mat["subject_id"],
                    material_id=material_id,
                    concept=ku_data.get("concept", ""),
                    concept_summary=ku_data.get("concept_summary", ""),
                    source_location=heading or f"chunk at position {total_kus}",
                    difficulty=ku_data.get("difficulty", 3),
                    tags=json.dumps(ku_data.get("tags", [])),
                    prerequisites=json.dumps(ku_data.get("prerequisites", [])),
                )
                total_kus += 1

        self.repo.update_material_status(material_id, "complete")
        return total_kus
