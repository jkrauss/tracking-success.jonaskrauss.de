import pytest
from datetime import time, date
from app.calculations import compute_sleep, compute_fasting


class TestSleepCalculation:
    """Test suite for sleep duration calculation."""

    def test_standard_overnight_sleep(self):
        """11pm to 7am = 8h raw - 1h fall-asleep = 7h"""
        assert compute_sleep(time(23, 0), time(7, 0)) == 7.0

    def test_short_sleep(self):
        """1am to 5am = 4h raw - 1h = 3h"""
        assert compute_sleep(time(1, 0), time(5, 0)) == 3.0

    def test_sleep_with_minutes(self):
        """23:30 to 6:45 = 7.25h - 1h = 6.25h"""
        result = compute_sleep(time(23, 30), time(6, 45))
        assert abs(result - 6.25) < 0.01

    def test_minimum_sleep_zero(self):
        """Very short sleep should not go below 0."""
        result = compute_sleep(time(23, 0), time(23, 30))
        assert result == 0.0

    def test_late_night_sleep(self):
        """3am to 11am = 8h - 1h = 7h"""
        assert compute_sleep(time(3, 0), time(11, 0)) == 7.0


class TestFastingCalculation:
    """Test suite for fasting duration calculation."""

    def test_standard_16_8(self):
        """Dinner 19:00, breakfast 11:00 = 16h fast"""
        assert compute_fasting(time(11, 0), time(19, 0)) == 16.0

    def test_15h_fast(self):
        """Dinner 19:00, breakfast 10:00 = 15h fast"""
        assert compute_fasting(time(10, 0), time(19, 0)) == 15.0

    def test_short_fast(self):
        """Dinner 20:00, breakfast 8:00 = 12h fast"""
        assert compute_fasting(time(8, 0), time(20, 0)) == 12.0

    def test_late_dinner(self):
        """Dinner 22:00, breakfast 10:00 = 12h fast"""
        assert compute_fasting(time(10, 0), time(22, 0)) == 12.0

    def test_early_dinner(self):
        """Dinner 17:00, breakfast 9:00 = 16h fast"""
        assert compute_fasting(time(9, 0), time(17, 0)) == 16.0


class TestSleepGoalSuccess:
    """Test that sleep >= 7h is considered success."""

    def test_exactly_7h_is_success(self):
        """7h sleep should be a success."""
        hours = compute_sleep(time(23, 0), time(7, 0))
        assert hours >= 7.0

    def test_6h_is_failure(self):
        """6h sleep should be a failure."""
        hours = compute_sleep(time(23, 0), time(6, 0))
        assert hours < 7.0

    def test_8h_is_success(self):
        """8h sleep should be a success."""
        hours = compute_sleep(time(22, 0), time(7, 0))
        assert hours >= 7.0


class TestFastingGoalSuccess:
    """Test that fasting >= 15h is considered success."""

    def test_exactly_15h_is_success(self):
        """15h fast should be a success."""
        hours = compute_fasting(time(10, 0), time(19, 0))
        assert hours >= 15.0

    def test_14h_is_failure(self):
        """14h fast should be a failure."""
        hours = compute_fasting(time(10, 0), time(20, 0))
        assert hours < 15.0

    def test_16h_is_success(self):
        """16h fast should be a success."""
        hours = compute_fasting(time(11, 0), time(19, 0))
        assert hours >= 15.0
