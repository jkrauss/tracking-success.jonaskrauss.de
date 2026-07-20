import pytest
from datetime import time, date, timedelta
from app.calculations import compute_sleep, compute_fasting


def test_compute_sleep_basic():
    """Test basic sleep calculation: 11pm to 7am = 8h - 1h = 7h"""
    bedtime = time(23, 0)
    waketime = time(7, 0)
    result = compute_sleep(bedtime, waketime)
    assert result == 7.0


def test_compute_sleep_short():
    """Test short sleep: 1am to 6am = 5h - 1h = 4h"""
    bedtime = time(1, 0)
    waketime = time(6, 0)
    result = compute_sleep(bedtime, waketime)
    assert result == 4.0


def test_compute_sleep_with_minutes():
    """Test sleep with minutes: 23:30 to 7:15 = 7.75h - 1h = 6.75h"""
    bedtime = time(23, 30)
    waketime = time(7, 15)
    result = compute_sleep(bedtime, waketime)
    assert abs(result - 6.75) < 0.01


def test_compute_sleep_minimum_zero():
    """Test that sleep cannot be negative"""
    bedtime = time(23, 0)
    waketime = time(0, 30)  # Only 1.5h - 1h = 0.5h
    result = compute_sleep(bedtime, waketime)
    assert result == 0.5


def test_compute_fasting_basic():
    """Test basic fasting: dinner at 19:00, breakfast at 10:00 = 15h"""
    breakfast = time(10, 0)
    dinner = time(19, 0)
    result = compute_fasting(breakfast, dinner)
    assert result == 15.0


def test_compute_fasting_long():
    """Test long fasting: dinner at 18:00, breakfast at 12:00 = 18h"""
    breakfast = time(12, 0)
    dinner = time(18, 0)
    result = compute_fasting(breakfast, dinner)
    assert result == 18.0


def test_compute_fasting_short():
    """Test short fasting: dinner at 21:00, breakfast at 8:00 = 11h"""
    breakfast = time(8, 0)
    dinner = time(21, 0)
    result = compute_fasting(breakfast, dinner)
    assert result == 11.0


def test_compute_fasting_overnight():
    """Test fasting crossing midnight: dinner at 23:00, breakfast at 10:00 = 11h"""
    breakfast = time(10, 0)
    dinner = time(23, 0)
    result = compute_fasting(breakfast, dinner)
    assert result == 11.0
