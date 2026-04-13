"""Pure SM-2 algorithm implementation.

No external dependencies. No Claude. No network. Fully deterministic.
Based on the SuperMemo SM-2 algorithm by Piotr Wozniak.
"""

from dataclasses import dataclass


MIN_EASINESS_FACTOR = 1.3
DEFAULT_EASINESS_FACTOR = 2.5


@dataclass
class SM2State:
    """Current SM-2 scheduling state for a knowledge unit."""

    repetitions: int = 0
    interval: int = 0
    easiness_factor: float = DEFAULT_EASINESS_FACTOR


def sm2(quality: int, state: SM2State) -> SM2State:
    """Run one SM-2 review cycle.

    Args:
        quality: 0-5 rating of recall quality.
            5=perfect, 4=hesitation, 3=difficult, 2=incorrect but recognized,
            1=incorrect vaguely remembered, 0=blackout.
        state: Current SM-2 state.

    Returns:
        New SM2State with updated values.
    """
    repetitions = state.repetitions
    interval = state.interval
    ef = state.easiness_factor

    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    # EF is always updated regardless of success/failure (per SM-2 spec)
    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ef = max(MIN_EASINESS_FACTOR, ef)

    return SM2State(
        repetitions=repetitions,
        interval=interval,
        easiness_factor=round(ef, 2),
    )


def quality_from_grade(grade: int) -> int:
    """Clamp a grade value to the valid 0-5 SM-2 quality range."""
    return max(0, min(5, grade))
