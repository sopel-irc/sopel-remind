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

The ``.at`` command is timezone aware, and tries to use the timezone set for
the user. If not found, it will use the timezone set for the channel. If none
is set, it will assume UTC+0.

When using ``.at`` with a past hour, the command will assume tomorrow instead
of today: setting a reminder for 9 a.m. when it's 10 a.m. will create a
reminder for 9 a.m. tomorrow.

Install
=======

The recommended way to install this plugin **will** be to use ``pip``
**once it is officially released on pypi**::

    $ pip install sopel-remind

Note that this plugin requires Python 3.7+ and Sopel 7.1+.
