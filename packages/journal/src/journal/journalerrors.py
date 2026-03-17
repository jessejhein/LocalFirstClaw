#!/usr/bin/env python3
"""Journal-specific exceptions."""


class JournalError(Exception):
    """Base exception for journal package failures."""


class JournalWriteError(JournalError):
    """Raised when an event cannot be written to the journal."""


class JournalQueryError(JournalError):
    """Raised when a journal query cannot be completed."""
