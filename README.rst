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

The recommended way to install this plugin **will** be to use ``pip``
**once it is officially released on pypi**::

    $ pip install sopel-remind

Note that this plugin requires Python 3.7+ and Sopel 7.1+.
