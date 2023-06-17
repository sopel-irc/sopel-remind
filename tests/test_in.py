from __future__ import annotations

import re

import pytest

from sopel_remind.backend import IN_RE, IN_TIME_PATTERN, parse_in_delta


def test_parse_in_delta_seconds():
    dt, message = parse_in_delta('5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 5


def test_parse_in_delta_minutes():
    dt, message = parse_in_delta('2m 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 125

    dt, message = parse_in_delta('2m reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 120


def test_parse_in_delta_hours():
    dt, message = parse_in_delta('1h 2m 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 3725

    dt, message = parse_in_delta('1h 2m reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 3720

    dt, message = parse_in_delta('1h 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 3605

    dt, message = parse_in_delta('1h reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 3600


def test_parse_in_delta_days():
    dt, message = parse_in_delta('1d 1h 2m 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 3600 + 120 + 5

    dt, message = parse_in_delta('1d 1h 2m reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 3600 + 120

    dt, message = parse_in_delta('1d 1h 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 3600 + 5

    dt, message = parse_in_delta('1d 1h reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 3600

    dt, message = parse_in_delta('1d 2m 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 120 + 5

    dt, message = parse_in_delta('1d 2m reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 120

    dt, message = parse_in_delta('1d 5s reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400 + 5

    dt, message = parse_in_delta('1d reminder')
    assert message == 'reminder'
    assert dt.total_seconds() == 86400


def test_parse_in_delta_invalid():
    with pytest.raises(ValueError):
        parse_in_delta('1s1d reminder')


def test_in_args_pattern():
    assert IN_RE.match('13h37m tell me more')
    assert IN_RE.match('13h37m        something something            ')
    assert not IN_RE.match('13h37m')
    assert not IN_RE.match('13h37m ')
    assert not IN_RE.match('13h37m      ')


def test_in_args_pattern_days_match():
    reminder = 'here is a reminder'
    result = IN_RE.match('5d 13h 25m 12s %s' % reminder)

    assert result is not None

    groups = result.groups()
    assert len(groups) == 15
    assert groups[-1] == reminder, 'Last group must be the reminder'

    assert not any(groups[5:14])
    assert groups[0:5] == ('5d 13h 25m 12s', '5', '13', '25', '12')


def test_in_args_pattern_hours_match():
    reminder = 'here is a reminder'
    result = IN_RE.match('13h 25m 12s %s' % reminder)

    assert result is not None

    groups = result.groups()
    assert len(groups) == 15
    assert groups[-1] == reminder, 'Last group must be the reminder'

    assert not any(groups[0:5])
    assert not any(groups[9:14])
    assert groups[5:9] == ('13h 25m 12s', '13', '25', '12')


def test_in_args_pattern_minutes_match():
    reminder = 'here is a reminder'
    result = IN_RE.match('25m 12s %s' % reminder)

    assert result is not None

    groups = result.groups()
    assert len(groups) == 15
    assert groups[-1] == reminder, 'Last group must be the reminder'

    assert not any(groups[0:9])
    assert not any(groups[12:14])
    assert groups[9:12] == ('25m 12s', '25', '12')


def test_in_args_pattern_seconds_match():
    reminder = 'here is a reminder'
    result = IN_RE.match('12s %s' % reminder)

    assert result is not None

    groups = result.groups()
    assert len(groups) == 15
    assert groups[-1] == reminder, 'Last group must be the reminder'

    assert not any(groups[0:12])
    assert groups[12:14] == ('12s', '12')


def test_in_time_pattern_match():
    regex = re.compile(IN_TIME_PATTERN)

    # full
    assert regex.match('10d21h5m37s')

    # keep the days
    # no seconds
    assert regex.match('10d21h5m')
    # no minutes
    assert regex.match('10d21h37s')
    # no hours
    assert regex.match('10d5m37s')
    # no seconds and no minutes
    assert regex.match('10d21h')
    # no seconds and no hours
    assert regex.match('10d5m')
    # no minutes and no hours
    assert regex.match('10d37s')
    # no seconds, no minutes, and no hours
    assert regex.match('10d')

    # keep the hours
    # no days
    assert regex.match('21h5m37s')
    # no seconds and no days
    assert regex.match('21h5m')
    # no minutes and no days
    assert regex.match('21h37s')
    # no seconds, no minutes, and no days
    assert regex.match('21h')

    # keep the minutes
    # no hours and no days
    assert regex.match('5m37s')
    # no seconds, no hours, and no days
    assert regex.match('5m')

    # keep the seconds
    # no minutes, no hours, and no days
    assert regex.match('37s')


def test_in_time_pattern_match_group():
    regex = re.compile(IN_TIME_PATTERN)

    match = regex.match('10d21h5m37s')
    assert match.group(0) == '10d21h5m37s'
    assert match.group(1) == '10d21h5m37s'
    assert match.group(2) == '10'
    assert match.group(3) == '21'
    assert match.group(4) == '5'
    assert match.group(5) == '37'
    assert match.group('days') is not None
    assert match.group('hours') is None
    assert match.group('minutes') is None
    assert match.group('seconds') is None

    match = regex.match('21h5m37s')
    assert match.group(0) == '21h5m37s'
    assert match.group(6) == '21h5m37s'
    assert match.group(7) == '21'
    assert match.group(8) == '5'
    assert match.group(9) == '37'
    assert match.group('days') is None
    assert match.group('hours') is not None
    assert match.group('minutes') is None
    assert match.group('seconds') is None

    match = regex.match('5m37s')
    assert match.group(0) == '5m37s'
    assert match.group(10) == '5m37s'
    assert match.group(11) == '5'
    assert match.group(12) == '37'
    assert match.group('days') is None
    assert match.group('hours') is None
    assert match.group('minutes') is not None
    assert match.group('seconds') is None

    match = regex.match('37s')
    assert match.group(0) == '37s'
    assert match.group(13) == '37s'
    assert match.group(14) == '37'
    assert match.group('days') is None
    assert match.group('hours') is None
    assert match.group('minutes') is None
    assert match.group('seconds') is not None
