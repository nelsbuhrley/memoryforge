"""Tests for the SM-2 spaced repetition algorithm."""

from memoryforge.sm2.engine import sm2, SM2State, quality_from_grade


class TestSM2Algorithm:
    def test_first_correct_review(self):
        state = SM2State()
        new_state = sm2(quality=4, state=state)
        assert new_state.repetitions == 1
        assert new_state.interval == 1
        assert new_state.easiness_factor >= 2.4

    def test_second_correct_review(self):
        state = SM2State(repetitions=1, interval=1, easiness_factor=2.5)
        new_state = sm2(quality=4, state=state)
        assert new_state.repetitions == 2
        assert new_state.interval == 6

    def test_third_correct_review(self):
        state = SM2State(repetitions=2, interval=6, easiness_factor=2.5)
        new_state = sm2(quality=5, state=state)
        assert new_state.repetitions == 3
        assert new_state.interval == 15  # round(6 * 2.5)

    def test_incorrect_resets_repetitions(self):
        state = SM2State(repetitions=5, interval=30, easiness_factor=2.5)
        new_state = sm2(quality=1, state=state)
        assert new_state.repetitions == 0
        assert new_state.interval == 1

    def test_easiness_factor_never_below_minimum(self):
        state = SM2State(easiness_factor=1.3)
        new_state = sm2(quality=0, state=state)
        assert new_state.easiness_factor == 1.3

    def test_perfect_score_increases_ef(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=5, state=state)
        assert new_state.easiness_factor == 2.6

    def test_quality_3_barely_correct(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=3, state=state)
        assert new_state.easiness_factor == 2.36

    def test_quality_0_blackout(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=0, state=state)
        assert new_state.repetitions == 0
        assert new_state.interval == 1
        # EF decreases but stays >= 1.3
        assert new_state.easiness_factor == 1.7

    def test_default_state(self):
        state = SM2State()
        assert state.repetitions == 0
        assert state.interval == 0
        assert state.easiness_factor == 2.5

    def test_long_term_interval_growth(self):
        """Simulate multiple perfect reviews to verify interval growth."""
        state = SM2State()
        intervals = []
        for _ in range(6):
            state = sm2(quality=5, state=state)
            intervals.append(state.interval)
        # Intervals should grow: 1, 6, 16, 42, 109, 283 (approximately)
        assert intervals[0] == 1
        assert intervals[1] == 6
        for i in range(2, len(intervals)):
            assert intervals[i] > intervals[i - 1]


class TestQualityMapping:
    def test_grade_5_maps_to_5(self):
        assert quality_from_grade(5) == 5

    def test_grade_0_maps_to_0(self):
        assert quality_from_grade(0) == 0

    def test_grade_out_of_range_clamps(self):
        assert quality_from_grade(7) == 5
        assert quality_from_grade(-1) == 0
