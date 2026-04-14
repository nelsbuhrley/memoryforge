"""Tests for the streak tracker."""

from datetime import date

from memoryforge.streak.tracker import StreakTracker


class TestStreakTracker:
    def test_get_streak_no_history(self, repo):
        tracker = StreakTracker(repo=repo)
        info = tracker.get_info()
        assert info["current_streak"] == 0
        assert info["longest_streak"] == 0

    def test_single_day_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 1

    def test_multi_day_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 11), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 3
        assert info["longest_streak"] == 3

    def test_broken_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 10), sessions=1, minutes=30)
        # Skip April 11
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 2
        assert info["longest_streak"] == 2

    def test_is_at_risk(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        # If today is April 13 and no session yet, streak is at risk
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is True

    def test_not_at_risk_if_studied_today(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is False

    def test_not_at_risk_if_no_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is False
