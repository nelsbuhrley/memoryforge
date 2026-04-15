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
        subject = ku.get("subject_name", "")
        subject_ctx = f" in the context of {subject}" if subject else ""

        if fmt == "fill_in_blank":
            # Causal/conditional reasoning — requires understanding, not just recall
            return (
                f"Complete the reasoning: If '{concept}' were removed or absent{subject_ctx}, "
                f"the key consequence would be ____________, because {summary}."
            )
        elif fmt == "multiple_choice":
            # Distinguishing — forces comparison against near-miss alternatives
            return (
                f"What distinguishes '{concept}' from superficially similar ideas{subject_ctx}? "
                f"Identify the key property that sets it apart, given that: {summary}. "
                f"\n(Explain your reasoning — do not just restate the definition.)"
            )
        elif fmt == "apply_the_concept":
            # Application with failure analysis — requires reasoning about conditions
            return (
                f"Describe a situation{subject_ctx} where '{concept}' would be applied. "
                f"Then identify one condition under which it would break down or give the wrong result. "
                f"(Context: {summary})"
            )
        else:  # free_response — hardest, most analytical
            return (
                f"Analyze '{concept}'{subject_ctx}: What are the key conditions that make it work correctly, "
                f"and what happens when those conditions are violated? "
                f"Go beyond restating the definition — explain the underlying mechanism. "
                f"(Definition for reference: {summary})"
            )


def get_question_format(
    difficulty: int,
    quiz_format_pref: str,
    registry: QuestionRegistry | None = None,
) -> str:
    """Convenience function to get a question format."""
    if registry is None:
        registry = QuestionRegistry()
    return registry.select_format(difficulty, quiz_format_pref)
