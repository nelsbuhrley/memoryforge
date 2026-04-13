"""3-layer token-efficiency pattern for Claude interactions.

Inspired by claude-mem's search pattern:
1. Summary layer — compact KU descriptions for broad context
2. Expanded layer — full details for selected KUs
3. Generation layer — Claude produces content with focused context

This keeps token usage manageable across large course loads.
"""

import json


def build_summary_context(kus: list[dict]) -> str:
    """Layer 1: Build a compact summary of KUs for broad context.

    Used when Claude needs awareness of many KUs but doesn't need
    full details on each one. ~20-30 tokens per KU.
    """
    lines = []
    for ku in kus:
        ef = ku.get("easiness_factor", 2.5)
        reps = ku.get("repetitions", 0)
        diff = ku.get("difficulty", 3)
        mastery = "new" if reps == 0 else f"reps:{reps},ef:{ef:.1f}"
        lines.append(f"[KU#{ku['id']}] {ku['concept_summary']} (d:{diff},{mastery})")
    return "\n".join(lines)


def build_expanded_context(
    kus: list[dict],
    review_histories: dict[int, list[dict]],
) -> str:
    """Layer 2: Expand selected KUs with full concept and review history.

    Used after layer 1 identifies which KUs need attention.
    """
    parts = []
    for ku in kus:
        ku_id = ku["id"]
        reviews = review_histories.get(ku_id, [])
        review_summary = ""
        if reviews:
            recent = reviews[-3:]  # Last 3 reviews
            review_lines = [
                f"  - quality:{r['quality']} on {r['reviewed_at']}"
                for r in recent
            ]
            review_summary = "\nRecent reviews:\n" + "\n".join(review_lines)

        tags = ku.get("tags", "[]")
        if isinstance(tags, str):
            tags = json.loads(tags)

        parts.append(
            f"[KU#{ku_id}] {ku['concept']}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Difficulty: {ku.get('difficulty', 3)}/5"
            f"{review_summary}"
        )
    return "\n\n".join(parts)
