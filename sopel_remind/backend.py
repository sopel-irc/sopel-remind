"""Backend to store and manage reminders."""
import collections
import csv
import os
import re
from datetime import datetime, timedelta

import pytz
from sopel import tools

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


Reminder = collections.namedtuple(
    'Reminder', ['timestamp', 'destination', 'nick', 'message'])


def serialize(reminder):
    """Serialize a ``reminder`` as a CSV compatible row, i.e. a tuple.

    :param reminder: a reminder to serialize
    :type reminder: :class:``
    :return: a 4-value tuple suitable for a CSV row
    :rtype: tuple

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


def save_reminders(reminders, filename):
    """Save the ``reminders`` into a CSV file.

    :param list reminders: list of reminders to save
    :param str filename: CSV file to save the ``reminders`` to
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(
            csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        for reminder in reminders:
            writer.writerow(serialize(reminder))


def load_reminders(filename):
    """Load reminders from a CSV file.

    :param str filename: CSV file to load reminders from
    :return: a list of reminders
    :rtype: tuple
    """
    reminders = []
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


def parse_in_delta(line):
    """Parse a reminder line using the ``in`` command format.

    :param str line: reminder line from the ``in`` command
    :return: a 2-value tuple with ``(timedelta, message)``
    :rtype: tuple
    :raise ValueError: when ``line`` doesn't match the ``in`` command format
    """
    result = IN_RE.match(line)

    if not result:
        raise ValueError('Invalid in arguments: %r' % line)

    groups = result.groups()
    message = groups[-1]

    days, hours, minutes, seconds = 0, 0, 0, 0
    if groups[0]:
        days, hours, minutes, seconds = groups[1:5]
    elif groups[5]:
        hours, minutes, seconds = groups[6:9]
    elif groups[9]:
        minutes, seconds = groups[10:12]
    else:
        seconds = groups[13]

    delta = timedelta(
        days=int(days or 0),
        seconds=int(seconds or 0),
        minutes=int(minutes or 0),
        hours=int(hours or 0))

    return delta, message


def build_reminder(trigger, delta, message):
    """Make a reminder for the current ``trigger``, ``delta``, and ``message``.

    :param trigger: current trigger
    :type trigger: :class:`sopel.trigger.Trigger`
    :param delta: timedelta object to generate the reminder
    :type delta: :class:`datetime.timedelta`
    :param str message: message to remind later
    :return: the expected reminder
    :rtype: :class:`~sopel_remind.backend.Reminder`
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


def get_reminder_timezone(bot, reminder):
    """Select the appropriate timezone for the ``reminder``.

    :param bot: bot instance
    :param reminder: reminder to get the timezone for
    :type reminder: :class:`~sopel_remind.backend.Reminder`
    :return: the appropriate timezone for ``reminder``
    :rtype: :class:`datetime.tzinfo`
    """
    return pytz.timezone(tools.time.get_timezone(
        bot.db,
        nick=reminder.nick,
        channel=reminder.destination,
    ) or 'UTC')


def get_reminder_filename(settings):
    """Retrieve the reminder filename from settings."""
    return os.path.join(
        settings.remind.location or settings.core.homedir,
        '%s.reminder.csv' % settings.basename,
    )


def setup(bot):
    """Setup action for the plugin."""
    filename = get_reminder_filename(bot.settings)
    bot.memory[MEMORY_KEY] = load_reminders(filename)


def shutdown(bot):
    """Shutdown action for the plugin."""
    filename = get_reminder_filename(bot.settings)
    save_reminders(bot.memory.get(MEMORY_KEY) or [], filename)
    try:
        del bot.memory[MEMORY_KEY]
    except KeyError:
        pass


def store(bot, reminder):
    """Store a new reminder."""
    bot.memory[MEMORY_KEY].append(reminder)
    filename = get_reminder_filename(bot.settings)
    save_reminders(bot.memory[MEMORY_KEY], filename)
