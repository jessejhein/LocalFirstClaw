#!/usr/bin/env python3
"""Write result metadata for journal append operations."""

from dataclasses import dataclass
from pathlib import Path

from journal.journalevent import JournalEvent


@dataclass(frozen=True)
class JournalWriteResult:
    """Details returned after a journal event is appended."""

    path: Path
    event: JournalEvent
