"""Grading logic for quiz responses.

Multiple choice: graded automatically (no Claude needed).
Free response / apply / fill-in-blank: graded by Claude via claude_service.
"""

from dataclasses import dataclass

from memoryforge.claude_service.prompts import build_grading_prompt
from memoryforge.claude_service.client import query_claude_json


@dataclass
class GradeResult:
    """Result of grading a student response."""

    quality: int  # 0-5 SM-2 scale
    correct: bool
    feedback: str


def grade_multiple_choice(
    student_answer: str,
    correct_answer: str,
) -> GradeResult:
    """Grade a multiple choice answer. No Claude needed."""
    is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
    if is_correct:
        return GradeResult(
            quality=5,
            correct=True,
            feedback="Correct!",
        )
    return GradeResult(
        quality=0,
        correct=False,
        feedback=f"Incorrect. The correct answer was {correct_answer}.",
    )


async def grade_free_response(
    question: str,
    student_answer: str,
    concept: str,
    strictness: int,
) -> GradeResult:
    """Grade a free response answer using Claude."""
    prompt = build_grading_prompt(
        question=question,
        student_answer=student_answer,
        concept=concept,
        strictness=strictness,
    )
    result = await query_claude_json(prompt)
    return GradeResult(
        quality=result.get("quality", 0),
        correct=result.get("correct", False),
        feedback=result.get("feedback", ""),
    )
