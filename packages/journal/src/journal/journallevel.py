#!/usr/bin/env python3
"""Journal event level values."""

from enum import StrEnum


class JournalLevel(StrEnum):
    """Operational event levels supported by the journal."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    URGENT = "urgent"
