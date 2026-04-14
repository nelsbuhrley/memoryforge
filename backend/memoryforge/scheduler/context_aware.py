"""Context-aware session scheduler.

Builds session queues considering subject clustering, interleaving,
and difficulty progression. Uses SM-2 data to determine review due dates.
"""

from dataclasses import dataclass


@dataclass
class SessionQueueItem:
    """One item in a session queue (quiz or lesson)."""

    ku: dict  # Knowledge unit data
    activity_type: str  # "quiz" (review) or "lesson" (new)


def build_session_queue(
    due_kus: list[dict],
    new_topics: list[dict],
    interleave_ratio: float = 0.3,
) -> list[SessionQueueItem]:
    """Build a learning session queue.

    Args:
        due_kus: Knowledge units due for review (from SM-2)
        new_topics: New knowledge units to introduce
        interleave_ratio: How much to interleave subjects (0.0-1.0)

    Returns:
        Ordered list of SessionQueueItem with activity types
    """
    if not due_kus and not new_topics:
        return []

    # Sort due_kus by difficulty (easier first)
    sorted_due = sorted(due_kus, key=lambda ku: ku.get("difficulty", 3))

    # Interleave subjects if requested
    if interleave_ratio > 0 and sorted_due:
        sorted_due = _interleave_by_subject(sorted_due, interleave_ratio)

    # Build queue: reviews first, then new topics
    queue = [SessionQueueItem(ku=ku, activity_type="quiz") for ku in sorted_due]
    queue.extend(SessionQueueItem(ku=ku, activity_type="lesson") for ku in new_topics)

    return queue


def _interleave_by_subject(
    kus: list[dict],
    ratio: float,
) -> list[dict]:
    """Interleave KUs from different subjects.

    Args:
        kus: List of KUs (assumed sorted by difficulty)
        ratio: Interleave strength (0.0 = no mixing, 1.0 = maximum mixing)

    Returns:
        KUs reordered to interleave subjects
    """
    if ratio <= 0 or len(kus) <= 1:
        return kus

    # Group by subject_id
    by_subject: dict[int, list[dict]] = {}
    for ku in kus:
        subject_id = ku.get("subject_id", 0)
        if subject_id not in by_subject:
            by_subject[subject_id] = []
        by_subject[subject_id].append(ku)

    if len(by_subject) <= 1:
        return kus

    # Interleave: round-robin from subject groups
    import random

    result = []
    pending: dict[int, list[dict]] = {sid: list(group) for sid, group in by_subject.items()}

    while any(pending.values()):
        # Get list of subjects with remaining items
        available_subjects = [sid for sid in sorted(by_subject.keys()) if pending[sid]]

        if not available_subjects:
            break

        # Choose a subject: higher ratio = more likely to switch subjects
        if result and random.random() < ratio:
            # Try to pick a different subject
            last_subject = result[-1].get("subject_id", 0)
            other_subjects = [s for s in available_subjects if s != last_subject]
            if other_subjects:
                chosen_subject = random.choice(other_subjects)
            else:
                chosen_subject = available_subjects[0]
        else:
            # Continue with current subject or pick first available
            last_subject = result[-1].get("subject_id", 0) if result else None
            if last_subject in available_subjects:
                chosen_subject = last_subject
            else:
                chosen_subject = available_subjects[0]

        # Take next item from chosen subject
        if pending[chosen_subject]:
            result.append(pending[chosen_subject].pop(0))

    return result
