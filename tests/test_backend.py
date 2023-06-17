from __future__ import annotations

import datetime
import os
from unittest import mock

import pytest
import pytz

from sopel_remind import backend, config

TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable =
    coretasks
    remind
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


@pytest.fixture
def mockreminder():
    timestamp = int(datetime.datetime(2021, 5, 22, 12, 0, 0).timestamp())
    return backend.Reminder(timestamp, '#channel', 'Test', 'message')


def test_serialize():
    args = (523553400, '#channel', 'Exirel', 'yay!')
    reminder = backend.Reminder(*args)
    assert backend.serialize(reminder) == args


def test_save_load_reminders(tmp_path):
    testfile = tmp_path / 'storage.csv'
    reminders = [
        backend.Reminder(523553400, '#channel', 'Exirel', 'yay!'),
        backend.Reminder(523553405, '#channel', 'Exirel', 'yay + 5s'),
    ]

    backend.save_reminders(reminders, str(testfile))
    result = backend.load_reminders(str(testfile))

    assert result == reminders


def test_get_reminder_filename(tmpconfig):
    tmpconfig.define_section('remind', config.RemindSection)
    result = backend.get_reminder_filename(tmpconfig)

    assert result == os.path.join(tmpconfig.core.homedir, 'test.reminder.csv')


def test_get_reminder_filename_custom_location(tmpconfig):
    tmpconfig.define_section('remind', config.RemindSection)
    tmpconfig.remind.location = os.path.join('custom', 'relative')
    result = backend.get_reminder_filename(tmpconfig)

    assert result == os.path.join(
        tmpconfig.core.homedir,
        'custom',
        'relative',
        'test.reminder.csv')


def test_get_reminder_filename_custom_location_absolute(tmpconfig):
    tmpconfig.define_section('remind', config.RemindSection)
    tmpconfig.remind.location = os.path.abspath(
        os.path.join('absolute', 'path'))
    result = backend.get_reminder_filename(tmpconfig)

    assert result == os.path.join(
        tmpconfig.remind.location,
        'test.reminder.csv')


def test_setup(mockbot):
    mockbot.settings.define_section('remind', config.RemindSection)
    assert backend.MEMORY_KEY not in mockbot.memory

    backend.setup(mockbot)

    assert backend.MEMORY_KEY in mockbot.memory
    assert mockbot.memory[backend.MEMORY_KEY] == []


def test_setup_existing_reminders(mockbot):
    mockbot.settings.define_section('remind', config.RemindSection)
    filename = backend.get_reminder_filename(mockbot.settings)

    reminders = [
        backend.Reminder(523553400, '#channel', 'Exirel', 'yay!'),
        backend.Reminder(523553405, '#channel', 'Exirel', 'yay + 5s'),
    ]

    backend.save_reminders(reminders, filename)

    assert backend.MEMORY_KEY not in mockbot.memory

    backend.setup(mockbot)

    assert backend.MEMORY_KEY in mockbot.memory
    assert mockbot.memory[backend.MEMORY_KEY] == reminders


def test_shutdown(mockbot):
    mockbot.settings.define_section('remind', config.RemindSection)
    filename = backend.get_reminder_filename(mockbot.settings)
    backend.shutdown(mockbot)

    assert backend.MEMORY_KEY not in mockbot.memory
    assert backend.load_reminders(filename) == []


def test_shutdown_with_reminders(mockbot):
    mockbot.settings.define_section('remind', config.RemindSection)
    filename = backend.get_reminder_filename(mockbot.settings)

    reminders = [
        backend.Reminder(523553400, '#channel', 'Exirel', 'yay!'),
        backend.Reminder(523553405, '#channel', 'Exirel', 'yay + 5s'),
    ]
    mockbot.memory[backend.MEMORY_KEY] = reminders

    backend.shutdown(mockbot)

    assert backend.MEMORY_KEY not in mockbot.memory
    assert backend.load_reminders(filename) == reminders


def test_build_reminder(mockbot, triggerfactory):
    trigger = triggerfactory(
        mockbot, ':Test!test@example.com PRIVMSG #channel :.in 5s message')

    now = pytz.utc.localize(datetime.datetime.utcnow())
    delta = datetime.timedelta(seconds=5)
    message = 'test message'

    reminder = backend.build_reminder(trigger, delta, message)

    assert isinstance(reminder, backend.Reminder)
    assert reminder.message == message
    assert reminder.destination == '#channel'
    assert reminder.nick == 'Test'
    assert int((now + delta).timestamp()) <= reminder.timestamp

    after_now = pytz.utc.localize(datetime.datetime.utcnow())
    assert int((after_now + delta).timestamp()) >= reminder.timestamp


def test_build_at_reminder(mockbot, triggerfactory):
    trigger = triggerfactory(
        mockbot, ':Test!test@example.com PRIVMSG #channel :.at 01:30 message')

    timezone = pytz.timezone('Europe/Paris')
    remind_at = timezone.localize(datetime.datetime(2021, 9, 28, 1, 30, 0))
    message = 'test message'

    reminder = backend.build_at_reminder(trigger, remind_at, message)
    expected_at = timezone.localize(
        datetime.datetime(2021, 9, 28, 1, 30, 0))

    assert int(expected_at.timestamp()) == reminder.timestamp


def test_get_reminder_timezone(mockbot, mockreminder):
    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = 'Europe/Paris'
        result = backend.get_reminder_timezone(mockbot, mockreminder)

    mock_get_timezone.assert_called_once_with(
        mockbot.db, nick='Test', channel='#channel')
    assert result.zone == 'Europe/Paris'


def test_get_reminder_timezone_no_info(mockbot, mockreminder):
    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = None
        result = backend.get_reminder_timezone(mockbot, mockreminder)

    mock_get_timezone.assert_called_once_with(
        mockbot.db, nick='Test', channel='#channel')
    assert result.zone == 'UTC'


def test_get_user_timezone(mockbot, triggerfactory):
    trigger = triggerfactory(
        mockbot, ':Test!test@example.com PRIVMSG #channel :.in 5s message')

    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = 'Europe/Paris'
        result = backend.get_user_timezone(
            mockbot, trigger.nick, trigger.sender)

    mock_get_timezone.assert_called_once_with(
        mockbot.db, nick='Test', channel='#channel')
    assert result.zone == 'Europe/Paris'


def test_get_user_timezone_pm(mockbot, triggerfactory):
    trigger = triggerfactory(
        mockbot, ':Test!test@example.com PRIVMSG :.in 5s message')

    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = 'Europe/Paris'
        result = backend.get_user_timezone(
            mockbot, trigger.nick, trigger.sender)

    mock_get_timezone.assert_called_once_with(
        mockbot.db, nick='Test', channel=None)
    assert result.zone == 'Europe/Paris'


def test_get_user_timezone_edge_case(mockbot, triggerfactory):
    trigger = triggerfactory(
        mockbot, 'TOPIC #test :.in 5s for real???')

    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = 'Europe/Paris'
        result = backend.get_user_timezone(
            mockbot, trigger.nick, trigger.sender)

    mock_get_timezone.assert_called_once_with(
        mockbot.db, nick=None, channel='#test')
    assert result.zone == 'Europe/Paris'


def test_get_user_timezone_none(mockbot, triggerfactory):
    with mock.patch('sopel.tools.time.get_timezone') as mock_get_timezone:
        mock_get_timezone.return_value = 'Europe/Paris'
        result = backend.get_user_timezone(
            mockbot, None, None)

    mock_get_timezone.assert_not_called()
    assert result.zone == 'UTC'


def test_store(mockbot, mockreminder):
    mockbot.settings.define_section('remind', config.RemindSection)
    filename = backend.get_reminder_filename(mockbot.settings)

    mockbot.memory[backend.MEMORY_KEY] = []
    backend.store(mockbot, mockreminder)

    assert mockreminder in mockbot.memory[backend.MEMORY_KEY]
    assert len(mockbot.memory[backend.MEMORY_KEY]) == 1
    assert backend.load_reminders(filename) == [mockreminder]
