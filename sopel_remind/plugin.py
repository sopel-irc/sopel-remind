"""Reminder plugin for Sopel."""
import os
import threading
from datetime import datetime

import pytz
from sopel import plugin, tools  # type: ignore
from sopel.bot import Sopel, SopelWrapper  # type: ignore
from sopel.config import Config  # type: ignore
from sopel.trigger import Trigger  # type: ignore

from . import backend, config

LOCK = threading.RLock()
LOGGER = tools.get_logger('remind')


def setup(bot: Sopel):
    """Setup the plugin."""
    bot.settings.define_section('remind', config.RemindSection)
    backend.setup(bot)


def shutdown(bot: Sopel):
    """Shutdown the plugin."""
    backend.shutdown(bot)


def configure(settings: Config):
    """Configure the plugin."""
    settings.define_section('remind', config.RemindSection)
    settings.remind.configure_setting(
        'location',
        'In which folder would you like to store your reminders?',
        default=settings.core.homedir)
    os.makedirs(settings.remind.location, exist_ok=True)


@plugin.interval(2)
def reminder_job(bot: Sopel):
    """Check reminders every 2s."""
    if not bot.backend.connected:
        # Don't run if the bot is not connected.
        LOGGER.debug('No reminders to send while the bot is not connected.')
        return

    now = int(pytz.utc.localize(datetime.utcnow()).timestamp())
    kept = []

    with LOCK:
        # iterate over a copy of what is in memory
        reminders = list(bot.memory[backend.MEMORY_KEY])
        for reminder in reminders:
            # check time
            if reminder.timestamp > now:
                # keep for later
                kept.append(reminder)
                continue

            # send to destination if available or keep for later
            if reminder.destination in bot.channels:
                # send reminder to channel
                channel = bot.channels[reminder.destination]
                if tools.Identifier(reminder.nick) in channel.users:
                    bot.reply(
                        reminder.message,
                        reminder.destination,
                        reminder.nick)
                else:
                    # user is not here yet, keep for later
                    kept.append(reminder)
            elif reminder.destination in bot.users:
                # send reminder to user
                bot.say(reminder.message, reminder.destination, max_messages=2)
            else:
                # keep for later
                kept.append(reminder)

        # save if necessary
        if len(kept) != len(reminders):
            LOGGER.debug('Saving %d reminder(s).', len(kept))
            bot.memory[backend.MEMORY_KEY] = kept
            filename = backend.get_reminder_filename(bot.settings)
            backend.save_reminders(kept, filename)


@plugin.commands('in')
def remind_in(bot: SopelWrapper, trigger: Trigger):
    """Set a reminder for later."""
    args = trigger.group(2)

    if args is None:
        bot.reply("When and what would you like me to remind?")
        return

    try:
        delta, message = backend.parse_in_delta(args)
    except ValueError:
        bot.reply("Sorry I didn't understand that.")
        return

    reminder = backend.build_reminder(trigger, delta, message)

    with LOCK:
        backend.store(bot, reminder)

    when = datetime.fromtimestamp(
        reminder.timestamp, pytz.utc
    ).astimezone(backend.get_reminder_timezone(bot, reminder))
    bot.reply('I will remind you that at %s' % (when.strftime('%H:%M:%S')))