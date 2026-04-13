"""Tests for the question type registry."""

from memoryforge.session.question_registry import (
    QuestionRegistry,
    get_question_format,
)


class TestQuestionRegistry:
    def test_default_formats_registered(self):
        registry = QuestionRegistry()
        formats = registry.list_formats()
        assert "free_response" in formats
        assert "multiple_choice" in formats
        assert "fill_in_blank" in formats
        assert "apply_the_concept" in formats

    def test_get_format_for_difficulty(self):
        registry = QuestionRegistry()
        # High difficulty concepts should prefer free_response or apply_the_concept
        fmt = registry.select_format(difficulty=5, quiz_format_pref="mixed")
        assert fmt in ("free_response", "apply_the_concept")

    def test_respects_user_preference(self):
        registry = QuestionRegistry()
        fmt = registry.select_format(difficulty=3, quiz_format_pref="multiple_choice")
        assert fmt == "multiple_choice"

    def test_mixed_varies_format(self):
        """Mixed mode should produce different formats across calls."""
        registry = QuestionRegistry()
        formats_seen = set()
        for d in range(1, 6):
            fmt = registry.select_format(difficulty=d, quiz_format_pref="mixed")
            formats_seen.add(fmt)
        # Should see at least 2 different formats across 5 difficulty levels
        assert len(formats_seen) >= 2

    def test_register_custom_format(self):
        registry = QuestionRegistry()
        registry.register("diagram", difficulty_range=(3, 5))
        assert "diagram" in registry.list_formats()

    def test_free_response_preference(self):
        registry = QuestionRegistry()
        fmt = registry.select_format(difficulty=3, quiz_format_pref="free_response")
        assert fmt == "free_response"
