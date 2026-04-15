"""Pluggable question type registry.

The session engine asks "give me a question format for this KU"
and the registry handles selection based on difficulty, user
preference, and available formats.

New formats can be registered without changing the session engine.
"""

from dataclasses import dataclass


@dataclass
class QuestionFormat:
    """A registered question format."""

    name: str
    difficulty_range: tuple[int, int]  # (min, max) difficulty where this format applies


class QuestionRegistry:
    """Registry of available question formats."""

    def __init__(self) -> None:
        self._formats: dict[str, QuestionFormat] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("free_response", difficulty_range=(1, 5))
        self.register("multiple_choice", difficulty_range=(1, 4))
        self.register("fill_in_blank", difficulty_range=(1, 3))
        self.register("apply_the_concept", difficulty_range=(3, 5))

    def register(self, name: str, difficulty_range: tuple[int, int] = (1, 5)) -> None:
        """Register a new question format."""
        self._formats[name] = QuestionFormat(name=name, difficulty_range=difficulty_range)

    def list_formats(self) -> list[str]:
        """Return all registered format names."""
        return list(self._formats.keys())

    def select_format(self, difficulty: int, quiz_format_pref: str) -> str:
        """Select a question format based on difficulty and user preference.

        If quiz_format_pref is a specific format, use that.
        If "mixed", select based on difficulty and variety.
        """
        if quiz_format_pref != "mixed" and quiz_format_pref in self._formats:
            return quiz_format_pref

        # Mixed mode: select based on difficulty
        eligible = [
            name for name, fmt in self._formats.items()
            if fmt.difficulty_range[0] <= difficulty <= fmt.difficulty_range[1]
        ]

        if not eligible:
            return "free_response"

        # Prefer harder formats for harder concepts
        if difficulty >= 4:
            for preferred in ("apply_the_concept", "free_response"):
                if preferred in eligible:
                    return preferred
        elif difficulty <= 2:
            for preferred in ("fill_in_blank", "multiple_choice"):
                if preferred in eligible:
                    return preferred

        return eligible[0]

    def generate(self, ku: dict, quiz_format_pref: str) -> str:
        """Generate a question string for a knowledge unit."""
        difficulty = ku.get("difficulty", 3)
        fmt = self.select_format(difficulty, quiz_format_pref)
        concept = ku.get("concept", "this concept")
        summary = ku.get("concept_summary", concept)

        if fmt == "fill_in_blank":
            return f"Fill in the blank: ____________ refers to {summary}."
        elif fmt == "multiple_choice":
            return f"Which of the following best describes '{summary}'?\n(Answer in your own words or choose the best description.)"
        elif fmt == "apply_the_concept":
            return f"Apply the concept: Give a real-world example that demonstrates '{summary}'."
        else:  # free_response
            return f"Explain '{summary}' in your own words."


def get_question_format(
    difficulty: int,
    quiz_format_pref: str,
    registry: QuestionRegistry | None = None,
) -> str:
    """Convenience function to get a question format."""
    if registry is None:
        registry = QuestionRegistry()
    return registry.select_format(difficulty, quiz_format_pref)
