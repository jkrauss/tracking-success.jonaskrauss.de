"""Tests for compute_duration — same-day duration calculation."""
from datetime import time
from app.calculations import compute_duration


class TestComputeDuration:
    def test_10_minutes(self):
        """10 minutes = 0.167 hours."""
        assert abs(compute_duration(time(9, 0), time(9, 10)) - 10/60) < 0.01

    def test_1_hour(self):
        """1 hour."""
        assert compute_duration(time(9, 0), time(10, 0)) == 1.0

    def test_8_hours(self):
        """8 hours work day."""
        assert compute_duration(time(9, 0), time(17, 0)) == 8.0

    def test_with_minutes(self):
        """9:15 to 17:30 = 8.25h."""
        assert abs(compute_duration(time(9, 15), time(17, 30)) - 8.25) < 0.01

    def test_crosses_midnight(self):
        """23:00 to 1:00 = 2h (wraps around)."""
        assert compute_duration(time(23, 0), time(1, 0)) == 2.0

    def test_same_time(self):
        """Same start and end = 0."""
        assert compute_duration(time(9, 0), time(9, 0)) == 0.0


class TestMeditationGoal:
    def test_10_min_is_success(self):
        """10 minutes >= 10min goal."""
        hours = compute_duration(time(9, 0), time(9, 10))
        assert hours >= 10 / 60

    def test_5_min_is_failure(self):
        """5 minutes < 10min goal."""
        hours = compute_duration(time(9, 0), time(9, 5))
        assert hours < 10 / 60

    def test_20_min_is_success(self):
        """20 minutes >= 10min goal."""
        hours = compute_duration(time(9, 0), time(9, 20))
        assert hours >= 10 / 60
