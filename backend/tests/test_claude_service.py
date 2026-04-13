"""Tests for the Claude service layer.

These tests mock the Claude agent-sdk to test prompt construction
and response handling without making real API calls.
"""

from unittest.mock import AsyncMock, patch
import json

from memoryforge.claude_service.client import query_claude_json
from memoryforge.claude_service.prompts import (
    build_ku_extraction_prompt,
    build_quiz_prompt,
    build_grading_prompt,
    build_lesson_prompt,
    build_reteach_prompt,
    build_generative_probe_prompt,
    build_learning_plan_prompt,
)
from memoryforge.claude_service.three_layer import (
    build_summary_context,
    build_expanded_context,
)


class TestPromptConstruction:
    def test_ku_extraction_prompt_includes_text(self):
        prompt = build_ku_extraction_prompt(
            text_chunk="Mitochondria are the powerhouse of the cell.",
            subject_name="BIO 301",
            section_heading="Chapter 5: Cell Organelles",
        )
        assert "Mitochondria" in prompt
        assert "BIO 301" in prompt
        assert "Chapter 5" in prompt
        assert "JSON" in prompt  # Should request structured output

    def test_quiz_prompt_includes_concept(self):
        prompt = build_quiz_prompt(
            concept="Mitochondria produce ATP via oxidative phosphorylation",
            concept_summary="Mitochondria: ATP production",
            question_format="free_response",
            difficulty=3,
            previous_questions=["What organelle produces ATP?"],
        )
        assert "oxidative phosphorylation" in prompt
        assert "free_response" in prompt

    def test_quiz_prompt_varies_with_format(self):
        fr = build_quiz_prompt(
            concept="X", concept_summary="X",
            question_format="free_response", difficulty=3,
        )
        mc = build_quiz_prompt(
            concept="X", concept_summary="X",
            question_format="multiple_choice", difficulty=3,
        )
        assert fr != mc

    def test_grading_prompt_includes_answer(self):
        prompt = build_grading_prompt(
            question="What do mitochondria produce?",
            student_answer="They make ATP",
            concept="Mitochondria produce ATP via oxidative phosphorylation",
            strictness=2,
        )
        assert "They make ATP" in prompt
        assert "strictness" in prompt.lower() or "moderate" in prompt.lower()

    def test_lesson_prompt(self):
        prompt = build_lesson_prompt(
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP production",
            student_context="Student previously learned about cell membranes.",
        )
        assert "Mitochondria" in prompt
        assert "cell membranes" in prompt

    def test_reteach_prompt_socratic(self):
        prompt = build_reteach_prompt(
            concept="Mitochondria produce ATP",
            student_answer="I don't know",
            question="What do mitochondria produce?",
            attempt_number=1,
        )
        assert "guiding question" in prompt.lower() or "socratic" in prompt.lower()

    def test_reteach_prompt_direct_after_attempts(self):
        prompt = build_reteach_prompt(
            concept="Mitochondria produce ATP",
            student_answer="Still not sure",
            question="What do mitochondria produce?",
            attempt_number=3,
        )
        assert "explain" in prompt.lower() or "direct" in prompt.lower()

    def test_generative_probe_prompt(self):
        prompt = build_generative_probe_prompt(
            topic="Photosynthesis",
            subject_name="BIO 301",
            student_knowledge_summary="Has studied cell biology and respiration.",
        )
        assert "Photosynthesis" in prompt
        assert "think" in prompt.lower() or "predict" in prompt.lower()

    def test_learning_plan_prompt(self):
        prompt = build_learning_plan_prompt(
            subject_name="BIO 301",
            material_outline='["Cell Biology", "Genetics", "Evolution"]',
            current_progress='{"Cell Biology": 0.8, "Genetics": 0.2}',
            deadlines='{"midterm": "2026-05-01"}',
        )
        assert "BIO 301" in prompt
        assert "midterm" in prompt


class TestThreeLayerPattern:
    def test_build_summary_context(self):
        kus = [
            {"id": 1, "concept_summary": "Mitochondria: ATP", "difficulty": 3, "easiness_factor": 2.5, "repetitions": 3},
            {"id": 2, "concept_summary": "Cell membrane: selective permeability", "difficulty": 2, "easiness_factor": 2.1, "repetitions": 1},
        ]
        summary = build_summary_context(kus)
        assert "Mitochondria" in summary
        assert "Cell membrane" in summary
        # Should be compact — no full concept text
        assert len(summary) < 500

    def test_build_expanded_context(self):
        kus = [
            {"id": 1, "concept": "Mitochondria produce ATP via oxidative phosphorylation", "concept_summary": "Mitochondria: ATP", "tags": '["biology"]', "difficulty": 3},
        ]
        reviews = [
            {"quality": 4, "reviewed_at": "2026-04-10"},
            {"quality": 2, "reviewed_at": "2026-04-12"},
        ]
        expanded = build_expanded_context(kus, {1: reviews})
        assert "oxidative phosphorylation" in expanded
        assert "quality" in expanded.lower() or "review" in expanded.lower()


class TestQueryClaudeJson:
    async def test_parses_plain_json(self):
        with patch("memoryforge.claude_service.client.query_claude", new=AsyncMock(return_value='{"key": "value"}')):
            result = await query_claude_json("prompt")
        assert result == {"key": "value"}

    async def test_strips_fenced_code_block(self):
        response = "```json\n{\"key\": \"value\"}\n```"
        with patch("memoryforge.claude_service.client.query_claude", new=AsyncMock(return_value=response)):
            result = await query_claude_json("prompt")
        assert result == {"key": "value"}

    async def test_strips_code_block_with_prose(self):
        response = "Here is the result:\n```json\n{\"key\": \"value\"}\n```\nHope that helps."
        with patch("memoryforge.claude_service.client.query_claude", new=AsyncMock(return_value=response)):
            result = await query_claude_json("prompt")
        assert result == {"key": "value"}

    async def test_strips_unnamed_code_block(self):
        response = "```\n{\"key\": \"value\"}\n```"
        with patch("memoryforge.claude_service.client.query_claude", new=AsyncMock(return_value=response)):
            result = await query_claude_json("prompt")
        assert result == {"key": "value"}
