"""Tests for fasting calculation — dinner yesterday to breakfast today."""
from datetime import time
from app.calculations import compute_fasting


class TestFastingOvernight:
    """Fasting = time from yesterday's dinner to today's breakfast."""

    def test_standard_16_8(self):
        """Dinner 19:00 yesterday, breakfast 11:00 today = 16h fast."""
        assert compute_fasting(time(11, 0), time(19, 0)) == 16.0

    def test_15h_fast(self):
        """Dinner 19:00 yesterday, breakfast 10:00 today = 15h."""
        assert compute_fasting(time(10, 0), time(19, 0)) == 15.0

    def test_short_fast(self):
        """Dinner 22:00 yesterday, breakfast 8:00 today = 10h."""
        assert compute_fasting(time(8, 0), time(22, 0)) == 10.0

    def test_late_dinner_early_breakfast(self):
        """Dinner 23:00 yesterday, breakfast 7:00 today = 8h."""
        assert compute_fasting(time(7, 0), time(23, 0)) == 8.0

    def test_early_dinner_late_breakfast(self):
        """Dinner 18:00 yesterday, breakfast 12:00 today = 18h."""
        assert compute_fasting(time(12, 0), time(18, 0)) == 18.0

    def test_minimum_fast(self):
        """Dinner 23:30 yesterday, breakfast 0:30 today = 1h."""
        assert compute_fasting(time(0, 30), time(23, 30)) == 1.0

    def test_goal_15h_success(self):
        """15h fast should be success (>= 15h goal)."""
        hours = compute_fasting(time(10, 0), time(19, 0))
        assert hours >= 15.0

    def test_goal_15h_failure(self):
        """14h fast should be failure (< 15h goal)."""
        hours = compute_fasting(time(9, 0), time(19, 0))
        assert hours < 15.0
