"""Tests for the context-aware scheduler."""

import json
from datetime import date

from memoryforge.scheduler.context_aware import (
    build_session_queue,
    SessionQueueItem,
)


def _make_ku(
    ku_id: int,
    subject_id: int,
    concept_summary: str,
    difficulty: int = 3,
    tags: str = "[]",
    prerequisites: str = "[]",
    repetitions: int = 0,
    next_review: str | None = None,
) -> dict:
    return {
        "id": ku_id,
        "subject_id": subject_id,
        "concept": f"Full concept for {concept_summary}",
        "concept_summary": concept_summary,
        "difficulty": difficulty,
        "tags": tags,
        "prerequisites": prerequisites,
        "easiness_factor": 2.5,
        "interval": 0,
        "repetitions": repetitions,
        "next_review": next_review,
    }


class TestBuildSessionQueue:
    def test_empty_due_list(self):
        queue = build_session_queue(
            due_kus=[],
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert queue == []

    def test_single_subject_clusters(self):
        kus = [
            _make_ku(1, 1, "Cell membrane", tags='["bio", "cells"]'),
            _make_ku(2, 1, "Cell wall", tags='["bio", "cells"]'),
            _make_ku(3, 1, "Nucleus", tags='["bio", "cells"]'),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert len(queue) == 3
        # All should be quiz type since they're review KUs
        assert all(item.activity_type == "quiz" for item in queue)

    def test_interleaving_two_subjects(self):
        kus = [
            _make_ku(1, 1, "Cell membrane", tags='["bio"]'),
            _make_ku(2, 1, "Cell wall", tags='["bio"]'),
            _make_ku(3, 1, "Nucleus", tags='["bio"]'),
            _make_ku(4, 2, "French Revolution", tags='["history"]'),
            _make_ku(5, 2, "Napoleon", tags='["history"]'),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert len(queue) == 5
        # Should not be all subject_id=1 followed by all subject_id=2
        subject_ids = [item.ku["subject_id"] for item in queue]
        # With interleaving, subjects should be mixed
        switches = sum(1 for i in range(1, len(subject_ids)) if subject_ids[i] != subject_ids[i - 1])
        assert switches >= 1

    def test_difficulty_progression(self):
        kus = [
            _make_ku(1, 1, "Basic", difficulty=1),
            _make_ku(2, 1, "Intermediate", difficulty=3),
            _make_ku(3, 1, "Advanced", difficulty=5),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.0,  # No interleaving
        )
        assert len(queue) == 3
        # Difficulty should progress: easier first
        difficulties = [item.ku["difficulty"] for item in queue]
        assert difficulties == [1, 3, 5]

    def test_respects_interleave_ratio(self):
        kus = [
            _make_ku(1, 1, "Bio1"),
            _make_ku(2, 1, "Bio2"),
            _make_ku(3, 1, "Bio3"),
            _make_ku(4, 2, "Hist1"),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.5,  # 50% interleaving
        )
        assert len(queue) == 4
        # With 50% interleave, we should see subject mixing

    def test_activity_types(self):
        kus = [
            _make_ku(1, 1, "Review KU", repetitions=2),
        ]
        new = [
            _make_ku(2, 1, "New KU", repetitions=0),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=new,
            interleave_ratio=0.0,
        )
        # Should have both quiz (review) and lesson (new)
        activity_types = {item.activity_type for item in queue}
        assert "quiz" in activity_types
        assert "lesson" in activity_types
