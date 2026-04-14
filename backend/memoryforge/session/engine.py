"""Session engine that orchestrates quiz sessions.

A session manages one quiz interaction: question generation, answer grading,
reteaching, and completion. It coordinates with the question registry, grader,
and Claude service.
"""

from enum import Enum
from dataclasses import dataclass, field

from memoryforge.session.grader import GradeResult


class SessionState(Enum):
    """Session lifecycle states."""
    ACTIVE = "active"
    GRADED = "graded"
    COMPLETED = "completed"


@dataclass
class SessionEngine:
    """Manages a single quiz session."""

    ku: dict
    quiz_format: str
    state: SessionState = field(default=SessionState.ACTIVE)
    attempt_count: int = field(default=0)
    grade_result: GradeResult | None = field(default=None)
    reteach_prompt: str | None = field(default=None)

    async def grade_answer(self, student_answer: str) -> GradeResult:
        """Grade the student's answer. Transitions state to GRADED."""
        self.attempt_count += 1
        self.grade_result = await self._grade_response(student_answer)
        self.state = SessionState.GRADED
        return self.grade_result

    async def reteach_answer(self) -> str | None:
        """Generate a reteach prompt for incorrect answers."""
        if not self.grade_result or self.grade_result.correct:
            return None
        self.reteach_prompt = await self._build_reteach_prompt()
        return self.reteach_prompt

    def complete_session(self) -> None:
        """Mark session as completed."""
        self.state = SessionState.COMPLETED

    async def _grade_response(self, student_answer: str) -> GradeResult:
        """Internal grading — delegates to grader module."""
        raise NotImplementedError("Wire up to grader.grade_free_response()")

    async def _build_reteach_prompt(self) -> str:
        """Internal reteach — delegates to Claude service."""
        raise NotImplementedError("Wire up to claude_service reteach prompt")
