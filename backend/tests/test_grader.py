"""Tests for the grading module."""

from unittest.mock import AsyncMock, patch

import pytest

from memoryforge.session.grader import grade_multiple_choice, GradeResult


class TestMultipleChoiceGrading:
    def test_correct_answer(self):
        result = grade_multiple_choice(
            student_answer="B",
            correct_answer="B",
        )
        assert result.correct is True
        assert result.quality == 5

    def test_incorrect_answer(self):
        result = grade_multiple_choice(
            student_answer="A",
            correct_answer="C",
        )
        assert result.correct is False
        assert result.quality == 0

    def test_case_insensitive(self):
        result = grade_multiple_choice(
            student_answer="b",
            correct_answer="B",
        )
        assert result.correct is True

    def test_feedback_on_correct(self):
        result = grade_multiple_choice(
            student_answer="B",
            correct_answer="B",
        )
        assert result.feedback is not None
        assert len(result.feedback) > 0

    def test_feedback_on_incorrect(self):
        result = grade_multiple_choice(
            student_answer="A",
            correct_answer="B",
        )
        assert "B" in result.feedback
