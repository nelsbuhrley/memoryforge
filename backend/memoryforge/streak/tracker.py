"""Streak tracker — Duolingo-inspired daily study streak.

Wraps the repository's streak methods with higher-level logic
for checking risk and computing stats.
"""

from datetime import date
from typing import Any

from memoryforge.db.repository import Repository


class StreakTracker:
    """Tracks daily study streaks."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def record_day(self, study_date: date, sessions: int, minutes: int) -> None:
        """Record that studying happened on this date."""
        self.repo.record_study_day(
            study_date=study_date,
            sessions_count=sessions,
            total_minutes=minutes,
        )

    def get_info(self) -> dict[str, Any]:
        """Get current streak information."""
        return self.repo.get_streak_info()

    def is_at_risk(self, today: date) -> bool:
        """Check if the streak is at risk (studied yesterday but not today)."""
        info = self.get_info()
        if info["current_streak"] == 0:
            return False

        # Check if there's a record for today
        row = self.repo.conn.execute(
            "SELECT id FROM streaks WHERE date = ?",
            (today.isoformat(),),
        ).fetchone()

        return row is None
