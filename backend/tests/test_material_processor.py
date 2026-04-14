"""Tests for the material processor (orchestrates parsing + KU extraction)."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from memoryforge.parser.material_processor import MaterialProcessor


class TestMaterialProcessor:
    def test_detect_file_type_pdf(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("test.pdf") == "pdf"

    def test_detect_file_type_docx(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.docx") == "docx"

    def test_detect_file_type_txt(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.txt") == "text"

    def test_detect_file_type_md(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.md") == "markdown"

    def test_detect_file_type_unknown(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("image.png") is None

    def test_light_parse_text_file(self, repo, test_config, tmp_path):
        repo.create_subject(name="BIO 301")
        f = tmp_path / "notes.txt"
        f.write_text("Chapter 1\n\nCells are the basic unit of life.")
        mat_id = repo.create_material(
            subject_id=1, filename="notes.txt",
            file_path=str(f), file_type="txt",
            material_type="lecture_notes",
        )
        proc = MaterialProcessor(repo=repo, config=test_config)
        result = proc.light_parse(material_id=mat_id)
        assert result is True
        mat = repo.get_material(mat_id)
        assert mat["parse_status"] == "parsed_light"

    @pytest.mark.asyncio
    async def test_deep_parse_creates_kus(self, repo, test_config, tmp_path):
        repo.create_subject(name="BIO 301")
        f = tmp_path / "notes.txt"
        f.write_text("Mitochondria produce ATP.\n\nDNA stores genetic info.")
        mat_id = repo.create_material(
            subject_id=1, filename="notes.txt",
            file_path=str(f), file_type="txt",
            material_type="lecture_notes",
        )
        proc = MaterialProcessor(repo=repo, config=test_config)
        proc.light_parse(material_id=mat_id)

        mock_response = [
            {
                "concept": "Mitochondria produce ATP through oxidative phosphorylation",
                "concept_summary": "Mitochondria: ATP production",
                "difficulty": 3,
                "tags": ["biology", "cells"],
                "prerequisites": [],
            },
            {
                "concept": "DNA stores genetic information as nucleotide sequences",
                "concept_summary": "DNA: genetic storage",
                "difficulty": 2,
                "tags": ["biology", "genetics"],
                "prerequisites": [],
            },
        ]

        with patch(
            "memoryforge.parser.material_processor.query_claude_json",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            count = await proc.deep_parse(material_id=mat_id)

        assert count == 2
        kus = repo.get_kus_by_subject(1)
        assert len(kus) == 2
        mat = repo.get_material(mat_id)
        assert mat["parse_status"] == "complete"
