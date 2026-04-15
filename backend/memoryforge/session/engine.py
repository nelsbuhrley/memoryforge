"""Session engine that orchestrates quiz sessions.

A session manages one quiz interaction: question generation, answer grading,
reteaching, and completion. It coordinates with the question registry, grader,
and Claude service.
"""

from enum import Enum
from dataclasses import dataclass, field

from memoryforge.session.grader import GradeResult, grade_free_response
from memoryforge.claude_service.client import query_claude
from memoryforge.claude_service.prompts import build_reteach_prompt


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
    question: str = field(default="")
    strictness: int = field(default=2)
    state: SessionState = field(default=SessionState.ACTIVE)
    attempt_count: int = field(default=0)
    grade_result: GradeResult | None = field(default=None)
    reteach_prompt: str | None = field(default=None)
    _last_answer: str = field(default="", repr=False)

    async def grade_answer(self, student_answer: str) -> GradeResult:
        """Grade the student's answer. Transitions state to GRADED."""
        self._last_answer = student_answer
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
        """Grade via Claude."""
        return await grade_free_response(
            question=self.question,
            student_answer=student_answer,
            concept=self.ku.get("concept", ""),
            strictness=self.strictness,
        )

    async def _build_reteach_prompt(self) -> str:
        """Generate reteach via Claude."""
        prompt = build_reteach_prompt(
            concept=self.ku.get("concept", ""),
            student_answer=self._last_answer,
            question=self.question,
            attempt_number=self.attempt_count,
        )
        return await query_claude(prompt)
