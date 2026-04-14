"""Tests for the session engine."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from memoryforge.session.engine import SessionEngine, SessionState
from memoryforge.session.grader import GradeResult


class TestSessionEngine:
    @pytest.fixture
    def mock_claude_service(self):
        """Mock Claude service for testing."""
        mock = AsyncMock()
        mock.query_claude = AsyncMock(return_value="Sample question text")
        return mock

    @pytest.fixture
    def mock_grader(self):
        """Mock grader for testing."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def sample_ku(self):
        """Sample knowledge unit for testing."""
        return {
            "id": 1,
            "subject_id": 1,
            "concept": "Full concept text",
            "concept_summary": "Photosynthesis",
            "difficulty": 3,
            "tags": '["bio", "energy"]',
            "prerequisites": "[]",
        }

    def test_session_init(self, sample_ku):
        """Test SessionEngine initialization."""
        engine = SessionEngine(ku=sample_ku, quiz_format="free_response")
        assert engine.state == SessionState.ACTIVE
        assert engine.ku == sample_ku
        assert engine.quiz_format == "free_response"

    @pytest.mark.asyncio
    async def test_session_state_transitions(self, sample_ku):
        """Test session state: ACTIVE -> grade_answer -> GRADED -> complete_session -> COMPLETED."""
        engine = SessionEngine(ku=sample_ku, quiz_format="multiple_choice")
        assert engine.state == SessionState.ACTIVE

        grade = GradeResult(quality=5, correct=True, feedback="Correct!")
        with patch.object(engine, '_grade_response', return_value=grade):
            await engine.grade_answer("B")
        assert engine.state == SessionState.GRADED

        engine.complete_session()
        assert engine.state == SessionState.COMPLETED

    @pytest.mark.asyncio
    async def test_grade_answer_stores_result(self, sample_ku, mock_grader):
        """Test that grade_answer stores the grading result."""
        engine = SessionEngine(ku=sample_ku, quiz_format="free_response")
        grade = GradeResult(quality=4, correct=True, feedback="Good!")

        # Mock the internal grading method
        with patch.object(engine, '_grade_response', return_value=grade):
            result = await engine.grade_answer("User's answer")
            assert engine.grade_result == grade
            assert engine.state == SessionState.GRADED

    @pytest.mark.asyncio
    async def test_reteach_returns_prompt(self, sample_ku):
        """Test that reteach_answer returns a reteach prompt."""
        engine = SessionEngine(ku=sample_ku, quiz_format="free_response")
        engine.grade_result = GradeResult(quality=2, correct=False, feedback="Try again")

        # Mock reteach logic
        with patch.object(engine, '_build_reteach_prompt', return_value="Reteach prompt text"):
            prompt = await engine.reteach_answer()
            assert prompt is not None
            assert isinstance(prompt, str)

    @pytest.mark.asyncio
    async def test_session_tracks_attempts(self, sample_ku):
        """Test that grade_answer increments attempt_count."""
        engine = SessionEngine(ku=sample_ku, quiz_format="multiple_choice")
        assert engine.attempt_count == 0

        grade = GradeResult(quality=5, correct=True, feedback="Correct!")
        with patch.object(engine, '_grade_response', return_value=grade):
            await engine.grade_answer("B")
        assert engine.attempt_count == 1

        with patch.object(engine, '_grade_response', return_value=grade):
            await engine.grade_answer("B")
        assert engine.attempt_count == 2

    def test_complete_session(self, sample_ku):
        """Test session completion."""
        engine = SessionEngine(ku=sample_ku, quiz_format="free_response")
        engine.state = SessionState.GRADED
        engine.grade_result = GradeResult(quality=5, correct=True, feedback="Excellent!")

        engine.complete_session()
        assert engine.state == SessionState.COMPLETED

    @pytest.mark.asyncio
    async def test_reteach_skipped_on_correct_answer(self, sample_ku):
        """reteach_answer returns None if answer was correct."""
        engine = SessionEngine(ku=sample_ku, quiz_format="free_response")
        engine.grade_result = GradeResult(quality=5, correct=True, feedback="Great!")
        result = await engine.reteach_answer()
        assert result is None
