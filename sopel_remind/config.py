"""Configuration section for plugin."""
from __future__ import annotations

from sopel.config.types import FilenameAttribute, StaticSection  # type: ignore


class RemindSection(StaticSection):
    """``[remind]`` config section."""
    location = FilenameAttribute(
        name='location',
        relative=True,
        directory=True)
    """Folder to put the reminders file into. Default to the config's homedir.

    This location is relative to the homedir and will be used to store the
    remind database file.

    The file itself will looks like ``<basename>.reminder.csv``.
    """
