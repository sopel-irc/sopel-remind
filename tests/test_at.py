from datetime import time

import pytest

from sopel_remind.backend import parse_at_time


def test_parse_at_time_hours():
    assert parse_at_time('1:00 reminder') == (time(1), 'reminder')
    assert parse_at_time('01:00 reminder') == (time(1), 'reminder')


def test_parse_at_time_hours_minutes():
    assert parse_at_time('1:20 reminder') == (time(1, 20), 'reminder')
    assert parse_at_time('01:20 reminder') == (time(1, 20), 'reminder')


def test_parse_at_time_hours_minutes_seconds():
    assert parse_at_time('1:20:30 reminder') == (time(1, 20, 30), 'reminder')
    assert parse_at_time('01:20:30 reminder') == (time(1, 20, 30), 'reminder')


def test_parse_at_time_invalid():
    with pytest.raises(ValueError):
        parse_at_time('5 reminder')

    with pytest.raises(ValueError):
        parse_at_time('05:0 reminder')

    with pytest.raises(ValueError):
        parse_at_time('120:00 reminder')

    with pytest.raises(ValueError):
        parse_at_time('01:130 reminder')


def test_parse_at_time_out_of_bound():
    with pytest.raises(ValueError):
        parse_at_time('24:00 reminder')

    with pytest.raises(ValueError):
        parse_at_time('01:60 reminder')

    with pytest.raises(ValueError):
        parse_at_time('01:00:60 reminder')
