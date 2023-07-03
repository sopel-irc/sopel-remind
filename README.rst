============
sopel-remind
============

Sopel plugin ``.in`` command::

    [17:30] Exirel: .in 2h go to the grocery store
    [17:30] Sopel: Exirel: I will remind you that at 19:30:00
    (... 2h later ...)
    [19:30] Sopel: Exirel: go to the grocery store

And ``.at`` command::

    [17:30] Exirel: .at 19:30 go to the grocery store
    [17:30] Sopel: Exirel: I will remind you that at 19:30:00
    (... 2h later ...)
    [19:30] Sopel: Exirel: go to the grocery store

The ``.in`` command accepts time units ranging from days to seconds::

    .in 1d2h In one day and 2 hours
    .in 2h59m3s In 2 hours, 59 minutes, and 3 seconds

The ``.at`` command is timezone aware, and tries to use the timezone set for
the user. If not found, it will use the timezone set for the channel. If none
is set, it will assume UTC+0.

When using ``.at`` with a past hour, the command will assume tomorrow instead
of today: setting a reminder for 9 a.m. when it's 10 a.m. will create a
reminder for 9 a.m. tomorrow.

You can also use a date instead of a time, or you can use both, placed before
or after the time::

    .at 2023-06-27 Python 3.7 EOL
    .at 12:00 2023-06-27 Python 3.7 EOL
    .at 2023-06-27 12:00 Python 3.7 EOL

Passing only a date will set a reminder on that date with *the current time*
(not adjusted for summer/daylight-savings).

Install
=======

The recommended way to install this plugin is to use ``pip``::

    $ pip install sopel-remind

Note that this plugin requires Python 3.7+ and Sopel 7.1+. It won't work on
Python versions that are not supported by the version of Sopel you are using.

Migration from built-in
=======================

If you used Sopel 7.1 (or any previous version) and its built-in "remind"
plugin, you may want to migrate your reminders to the new plugin. To do that,
you can run the ``sopel-plugins configure remind`` command and allow the script
to perform the migration. This will import the reminders from the original file
before renaming it (by adding the ``.bk`` suffix).
