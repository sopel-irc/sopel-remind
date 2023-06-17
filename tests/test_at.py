"""Test functions related to the ``.at`` command"""
from __future__ import annotations

from datetime import datetime

import pytest
import pytz

from sopel_remind.backend import parse_at_time

TODAY = pytz.utc.localize(datetime(2023, 6, 17, 10, 13, 10))


def _convert(raw: str, tzinfo: pytz.BaseTzInfo):
    """Helper function to convert string into an aware datetime"""
    return tzinfo.localize(datetime.strptime(raw, '%Y-%m-%d %H:%M:%S'))


def test_parse_at_time_time_only_no_second():
    """Assert pattern matches hh:mm"""
    assert parse_at_time('11:20 reminder', TODAY) == (
        _convert('2023-06-17 11:20:00', pytz.utc), 'reminder'
    )


def test_parse_at_time_time_only():
    """Assert pattern matches hh:mm:ss"""
    assert parse_at_time('11:20:30 reminder', TODAY) == (
        _convert('2023-06-17 11:20:30', pytz.utc), 'reminder'
    )


def test_parse_at_time_time_only_tomorrow():
    """Assert pattern matches hh:mm[:ss] when it should for tomorrow"""
    assert parse_at_time('05:20 reminder', TODAY) == (
        _convert('2023-06-18 05:20:00', pytz.utc), 'reminder'
    )
    assert parse_at_time('05:20:30 reminder', TODAY) == (
        _convert('2023-06-18 05:20:30', pytz.utc), 'reminder'
    )


def test_parse_at_time_date():
    """Assert pattern matches YYYY:MM:DD"""
    assert parse_at_time('2023-06-18 reminder', TODAY) == (
        _convert('2023-06-18 10:13:10', pytz.utc), 'reminder'
    )


def test_parse_at_time_date_time_no_seconds():
    """Assert pattern matches YYYY:MM:DD hh:mm"""
    assert parse_at_time('2023-06-18 17:15 reminder', TODAY) == (
        _convert('2023-06-18 17:15:00', pytz.utc), 'reminder'
    )


def test_parse_at_time_date_time():
    """Assert pattern matches YYYY:MM:DD hh:mm:ss"""
    assert parse_at_time('2023-06-18 17:15:39 reminder', TODAY) == (
        _convert('2023-06-18 17:15:39', pytz.utc), 'reminder'
    )


def test_parse_at_time_date_time_today():
    """Assert pattern matches hh:mm:ss YYYY:MM:DD"""
    assert parse_at_time('2023-06-17 17:15:39 reminder', TODAY) == (
        _convert('2023-06-17 17:15:39', pytz.utc), 'reminder'
    )


def test_parse_at_time_time_date_no_seconds():
    """Assert pattern matches hh:mm YYYY:MM:DD"""
    assert parse_at_time('17:15 2023-06-18 reminder', TODAY) == (
        _convert('2023-06-18 17:15:00', pytz.utc), 'reminder'
    )


def test_parse_at_time_time_date():
    """Assert pattern matches hh:mm:ss YYYY:MM:DD"""
    assert parse_at_time('17:15:39 2023-06-18 reminder', TODAY) == (
        _convert('2023-06-18 17:15:39', pytz.utc), 'reminder'
    )


def test_parse_at_time_time_date_today():
    """Assert pattern matches hh:mm:ss YYYY:MM:DD"""
    assert parse_at_time('17:15:39 2023-06-17 reminder', TODAY) == (
        _convert('2023-06-17 17:15:39', pytz.utc), 'reminder'
    )


def test_parse_at_time_invalid_datetime_is_today():
    """Assert date only or datetime that are today are invalid"""
    with pytest.raises(ValueError):
        parse_at_time('2023-06-17 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('2023-06-17 10:13:10 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('10:13:10 2023-06-17 reminder', TODAY)


def test_parse_at_time_invalid_datetime_is_past():
    """Assert date only or datetime that are in the past are invalid"""
    with pytest.raises(ValueError):
        parse_at_time('2023-06-16 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('2023-06-17 05:59:10 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('05:59:10 2023-06-17 reminder', TODAY)


def test_parse_at_time_invalid_format():
    """Assert pattern does not match on invalid time format"""
    with pytest.raises(ValueError):
        parse_at_time('5 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('05:0 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('120:00 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('01:130 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('24:00 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('2024-13-01 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('2024-02-30 reminder', TODAY)

    with pytest.raises(ValueError):
        parse_at_time('2024-12-32 reminder', TODAY)
