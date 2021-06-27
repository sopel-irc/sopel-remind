"""Backend to store and manage reminders."""
import csv
import os
import re
from datetime import datetime, timedelta
from typing import List, NamedTuple, Sequence, Tuple, Union

import pytz
from sopel import tools  # type: ignore
from sopel.bot import Sopel, SopelWrapper  # type: ignore
from sopel.config import Config  # type: ignore
from sopel.trigger import Trigger  # type: ignore

LOGGER = tools.get_logger('remind')

MEMORY_KEY = '__sopel_remind__reminders'

IN_TIME_PATTERN = '|'.join([
    r'(?P<days>(?:(\d+)d)(?:\s?(\d+)h)?(?:\s?(\d+)m)?(?:\s?(\d+)s)?)',
    r'(?P<hours>(?:(\d+)h)(?:\s?(\d+)m)?(?:\s?(\d+)s)?)',
    r'(?P<minutes>(?:(\d+)m)(?:\s?(\d+)s)?)',
    r'(?P<seconds>(?:(\d+)s))',
])

IN_ARGS_PATTERN = r'(?:' + IN_TIME_PATTERN + r')\s+(?P<text>\S+.*)'

IN_RE = re.compile(IN_ARGS_PATTERN)


class Reminder(NamedTuple):
    """User reminder."""
    timestamp: int
    """When the reminder must be sent."""
    destination: str
    """Where the reminder need to be sent."""
    nick: str
    """Who needs to be reminded of the message."""
    message: str
    """What message need to be reminded."""


def serialize(reminder: Reminder) -> Tuple[int, str, str, str]:
    """Serialize a ``reminder`` as a CSV compatible row, i.e. a tuple.

    :param reminder: a reminder to serialize
    :return: a 4-value tuple suitable for a CSV row

    A reminder is expected to contain:

    * a timestamp
    * a destination
    * a nick (who asked for the reminder)
    * a message
    """
    return (
        reminder.timestamp,
        reminder.destination,
        reminder.nick,
        reminder.message,
    )


def save_reminders(reminders: Sequence[Reminder], filename: str):
    """Save the ``reminders`` into a CSV file.

    :param reminders: list of reminders to save
    :param filename: CSV file to save the ``reminders`` to
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(
            csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        for reminder in reminders:
            writer.writerow(serialize(reminder))


def load_reminders(filename: str) -> List[Reminder]:
    """Load reminders from a CSV file.

    :param filename: CSV file to load reminders from
    :return: a list of reminders
    """
    # mode a+ allow to create the file if it doesn't exist yet
    with open(filename, 'a+', newline='', encoding='utf-8') as csvfile:
        csvfile.seek(0)  # read the file from the start
        reader = csv.reader(
            csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        reminders = [
            Reminder(int(timestamp), destination, nick, message)
            for timestamp, destination, nick, message, *args in reader
        ]

    return reminders


def parse_in_delta(line: str) -> Tuple[timedelta, str]:
    """Parse a reminder line using the ``in`` command format.

    :param line: reminder line from the ``in`` command
    :return: a 2-value tuple with ``(timedelta, message)``
    :raise ValueError: when ``line`` doesn't match the ``in`` command format
    """
    result = IN_RE.match(line)

    if not result:
        raise ValueError('Invalid in arguments: %r' % line)

    groups = result.groups()
    message = groups[-1]

    days, hours, minutes, seconds = 0, 0, 0, 0
    if groups[0]:
        days, hours, minutes, seconds = (int(i or 0) for i in groups[1:5])
    elif groups[5]:
        hours, minutes, seconds = (int(i or 0) for i in groups[6:9])
    elif groups[9]:
        minutes, seconds = (int(i or 0) for i in groups[10:12])
    else:
        seconds = int(groups[13] or 0)

    delta = timedelta(
        days=days,
        seconds=seconds,
        minutes=minutes,
        hours=hours)

    return delta, message


def build_reminder(
    trigger: Trigger,
    delta: timedelta,
    message: str,
) -> Reminder:
    """Make a reminder for the current ``trigger``, ``delta``, and ``message``.

    :param trigger: current trigger
    :param delta: timedelta object to generate the reminder
    :param message: message to remind later
    :return: the expected reminder
    """
    remind_at = pytz.utc.localize(datetime.utcnow()) + delta
    destination = str(trigger.sender)
    nick = str(trigger.nick)

    return Reminder(
        int(remind_at.timestamp()),
        destination,
        nick,
        message,
    )


def get_reminder_timezone(
    bot: Union[Sopel, SopelWrapper],
    reminder: Reminder
) -> pytz.BaseTzInfo:
    """Select the appropriate timezone for the ``reminder``.

    :param bot: bot instance
    :param reminder: reminder to get the timezone for
    :return: the appropriate timezone for ``reminder``
    """
    return pytz.timezone(tools.time.get_timezone(
        bot.db,
        nick=reminder.nick,
        channel=reminder.destination,
    ) or 'UTC')


def get_reminder_filename(settings: Config) -> str:
    """Retrieve the reminder filename from settings."""
    return os.path.join(
        settings.remind.location or settings.core.homedir,
        '%s.reminder.csv' % settings.basename,
    )


def setup(bot: Sopel):
    """Setup action for the plugin."""
    filename = get_reminder_filename(bot.settings)
    bot.memory[MEMORY_KEY] = load_reminders(filename)


def shutdown(bot: Sopel):
    """Shutdown action for the plugin."""
    filename = get_reminder_filename(bot.settings)
    save_reminders(bot.memory.get(MEMORY_KEY) or [], filename)
    try:
        del bot.memory[MEMORY_KEY]
    except KeyError:
        pass


def store(bot: Union[Sopel, SopelWrapper], reminder: Reminder):
    """Store a new reminder."""
    bot.memory[MEMORY_KEY].append(reminder)
    filename = get_reminder_filename(bot.settings)
    save_reminders(bot.memory[MEMORY_KEY], filename)
