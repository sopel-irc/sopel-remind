"""Integration tests for the sopel-remind plugin."""
from __future__ import annotations

import io
import os
from datetime import datetime

import pytest
import pytz
from sopel.tests import rawlist

from sopel_remind.backend import (MEMORY_KEY, Reminder, get_reminder_filename,
                                  load_reminders)
from sopel_remind.plugin import configure, reminder_job

TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks, remind
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory.preloaded(tmpconfig, preloads=['remind'])


@pytest.fixture
def user(userfactory):
    return userfactory('TestUser')


@pytest.fixture
def irc(mockbot, user, ircfactory):
    server = ircfactory(mockbot)
    server.bot.backend.connected = True
    server.bot.connection_registered = True
    server.join(user, '#channel')
    server.bot.backend.clear_message_sent()
    return ircfactory(mockbot)


def test_configure(tmpconfig, monkeypatch):
    user_inputs = io.StringIO('%s\nn\n' % os.path.join('relative', 'path'))
    monkeypatch.setattr('sys.stdin', user_inputs)
    configure(tmpconfig)

    assert 'remind' in tmpconfig
    assert hasattr(tmpconfig.remind, 'location')

    assert tmpconfig.remind.location == os.path.join(
        tmpconfig.core.homedir, 'relative', 'path')


def test_configure_migration(tmpconfig, monkeypatch):
    expected = Reminder(1687797939, '#test', 'TestUser', 'Test Message.')
    builtin_filename = os.path.join(
        tmpconfig.core.homedir,
        tmpconfig.basename + '.reminders.db',
    )

    with open(builtin_filename, mode='w', encoding='utf-8') as fd:
        fd.writelines([
            '\t'.join((
                str(expected.timestamp),
                expected.destination,
                expected.nick,
                expected.message,
            )),
        ])

    user_inputs = io.StringIO('\n\n')
    monkeypatch.setattr('sys.stdin', user_inputs)
    configure(tmpconfig)

    assert not os.path.isfile(builtin_filename), (
        'Builtin file must be removed.'
    )

    assert os.path.isfile(builtin_filename + '.bk'), (
        'Builtin file must be renamed to a .bk file.'
    )

    filename = get_reminder_filename(tmpconfig)
    reminders = load_reminders(filename)

    assert len(reminders) == 1, 'Expected one reminder from migration.'
    assert reminders[0] == expected


def test_configure_migration_no_file(tmpconfig, monkeypatch):
    user_inputs = io.StringIO('\n\n')
    monkeypatch.setattr('sys.stdin', user_inputs)
    configure(tmpconfig)

    filename = get_reminder_filename(tmpconfig)
    reminders = load_reminders(filename)

    assert len(reminders) == 0, 'Expected no reminder from migration.'


def test_configure_migration_no_reminders(tmpconfig, monkeypatch):
    builtin_filename = os.path.join(
        tmpconfig.core.homedir,
        tmpconfig.basename + '.reminders.db',
    )

    with open(builtin_filename, mode='w', encoding='utf-8'):
        # the file is now created (and empty)
        pass

    user_inputs = io.StringIO('\n\n')
    monkeypatch.setattr('sys.stdin', user_inputs)
    configure(tmpconfig)

    assert not os.path.isfile(builtin_filename), (
        'Builtin file must be removed even when empty.'
    )

    assert os.path.isfile(builtin_filename + '.bk'), (
        'Builtin file must be renamed to a .bk file even when empty'
    )

    filename = get_reminder_filename(tmpconfig)
    reminders = load_reminders(filename)

    assert len(reminders) == 0, 'Expected no reminder from migration.'


def test_remind_in(irc, user):
    irc.say(user, '#channel', '.in 1s this is my reminder')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 1

    reminder = irc.bot.memory[MEMORY_KEY][0]
    when = datetime.fromtimestamp(reminder.timestamp, pytz.utc)

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: I will remind you that at %s"
        % when.strftime('%H:%M:%S'),
    )


def test_remind_in_no_argument(irc, user):
    irc.say(user, '#channel', '.in')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 0

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: "
        "When and what would you like me to remind?"
    )


def test_remind_in_invalid_argument(irc, user):
    irc.say(user, '#channel', '.in 5s2m something')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 0

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: Sorry I didn't understand that."
    )


def test_remind_at(irc, user):
    irc.say(user, '#channel', '.at 10:00 this is my reminder')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 1

    reminder = irc.bot.memory[MEMORY_KEY][0]
    when = datetime.fromtimestamp(reminder.timestamp, pytz.utc)

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: I will remind you that at %s"
        % when.strftime('%H:%M:%S'),
    )


def test_remind_at_no_argument(irc, user):
    irc.say(user, '#channel', '.at')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 0

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: "
        "When and what would you like me to remind?"
    )


def test_remind_at_invalid_argument(irc, user):
    irc.say(user, '#channel', '.at 26:61 something')

    assert len(irc.bot.backend.message_sent) == 1
    assert len(irc.bot.memory[MEMORY_KEY]) == 0

    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: Sorry I didn't understand that."
    )


def test_shutdown(irc):
    timestamp = int(datetime.utcnow().timestamp())
    reminder = Reminder(timestamp, '#channel', 'TestUser', 'Test message.')
    irc.bot.memory[MEMORY_KEY].append(reminder)
    irc.bot.on_close()

    assert irc.bot.backend.message_sent == []

    filename = get_reminder_filename(irc.bot.settings)
    reminders = load_reminders(filename)

    assert len(reminders) == 1
    assert reminder in reminders


def test_job_no_reminders(irc):
    # no reminders
    reminder_job(irc.bot)
    assert irc.bot.backend.message_sent == []


def test_job_future_reminders(irc):
    timestamp = int(pytz.utc.localize(datetime.utcnow()).timestamp()) + 3600
    reminder = Reminder(timestamp, '#channel', 'TestUser', 'Test message.')
    irc.bot.memory[MEMORY_KEY].append(reminder)

    # no reminders... yet!
    reminder_job(irc.bot)
    assert irc.bot.backend.message_sent == []


def test_job_past_reminders(irc):
    timestamp = int(pytz.utc.localize(datetime.utcnow()).timestamp())
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(timestamp - 1, '#channel', 'TestUser', 'Test message.'))
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(
            timestamp - 1, 'TestUser', 'TestUser', 'Test private message.'))
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(
            timestamp + 3600, '#channel', 'TestUser', 'Future message.'))
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(
            timestamp - 1, '#channel', 'Unknownuser', 'Unknown user message.'))
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(
            timestamp - 1,
            '#unknownchan',
            'TestUser',
            'Unknown channel message.',
        ))

    # now there should be a reminder!
    reminder_job(irc.bot)
    assert irc.bot.backend.message_sent == rawlist(
        "PRIVMSG #channel :TestUser: Test message.",
        "PRIVMSG TestUser :Test private message."
    )

    assert len(irc.bot.memory[MEMORY_KEY]) == 3


def test_job_not_connected(irc):
    timestamp = int(pytz.utc.localize(datetime.utcnow()).timestamp())
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(timestamp - 1, '#channel', 'TestUser', 'Test message.'))

    irc.bot.backend.connected = False

    # not connected: there should not be any messages
    reminder_job(irc.bot)
    assert irc.bot.backend.message_sent == []

    assert len(irc.bot.memory[MEMORY_KEY]) == 1


def test_job_connected_but_not_registered(irc):
    timestamp = int(pytz.utc.localize(datetime.utcnow()).timestamp())
    irc.bot.memory[MEMORY_KEY].append(
        Reminder(timestamp - 1, '#channel', 'TestUser', 'Test message.'))

    irc.bot.connection_registered = False

    # not connected: there should not be any messages
    reminder_job(irc.bot)
    assert irc.bot.backend.message_sent == []

    assert len(irc.bot.memory[MEMORY_KEY]) == 1
