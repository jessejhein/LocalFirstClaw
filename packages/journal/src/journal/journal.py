#!/usr/bin/env python3
"""File-backed JSONL journal with deterministic querying."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from journal.journalerrors import JournalQueryError, JournalWriteError
from journal.journalevent import JournalEvent
from journal.journalquery import JournalQuery
from journal.journaltimeparser import resolve_time_value
from journal.journalwriteresult import JournalWriteResult

LOGGER = logging.getLogger(Path(__file__).stem)


class Journal:
    """Thread-safe append and query API for daily JSONL journal files."""

    def __init__(self, root_directory: Path | str):
        """
        Create a journal rooted at a directory containing daily JSONL files.

        Args:
            root_directory: Directory where daily journal files are stored.
        """
        self.root_directory = Path(root_directory)
        self._lock = threading.RLock()

    def append_event(self, event: JournalEvent) -> JournalWriteResult:
        """
        Append an event to the correct daily journal file.

        Args:
            event: Structured event to append.

        Returns:
            A result containing the normalized event and target file path.

        Raises:
            JournalWriteError: If the event cannot be persisted.
        """
        logger = LOGGER.getChild("append_event")
        normalized_event = self._normalize_event(event=event)
        target_path = self._journal_path_for_timestamp(timestamp=normalized_event.timestamp)

        try:
            with self._lock:
                self._ensure_root_directory()
                serialized_event = self._serialize_event(event=normalized_event)
                with target_path.open(mode="a", encoding="utf-8") as output_handle:
                    output_handle.write(serialized_event)
                    output_handle.write("\n")
        except OSError as error:
            logger.error("Failed to append journal event to %s: %s", target_path, error)
            raise JournalWriteError(f"unable to write event to {target_path}") from error

        return JournalWriteResult(path=target_path, event=normalized_event)

    async def append_event_async(self, event: JournalEvent) -> JournalWriteResult:
        """Expose append_event through an async-compatible method."""
        return self.append_event(event=event)

    def query_recent(self, query: JournalQuery) -> list[JournalEvent]:
        """
        Query recent events from the daily journal files.

        Args:
            query: Structured filters for the journal read.

        Returns:
            Matching events ordered by timestamp.

        Raises:
            JournalQueryError: If the query cannot be resolved.
        """
        logger = LOGGER.getChild("query_recent")
        now = query.now or datetime.now(UTC)
        try:
            since = resolve_time_value(query.since, now=now)
            until = resolve_time_value(query.until, now=now)
        except JournalQueryError:
            raise
        except ValueError as error:
            raise JournalQueryError(str(error)) from error

        if since is not None and until is not None and since > until:
            raise JournalQueryError("since must not be later than until")

        with self._lock:
            if self.root_directory.exists() and not self.root_directory.is_dir():
                raise JournalQueryError("journal root must be a directory")

            if not self.root_directory.exists():
                return []

            events: list[JournalEvent] = []
            for file_path in self._candidate_files(since=since, until=until):
                events.extend(self._read_matching_events(file_path=file_path, query=query, since=since, until=until))

        logger.debug("Found %d matching journal events", len(events))
        return sorted(events, key=lambda event: event.timestamp)

    async def query_recent_async(self, query: JournalQuery) -> list[JournalEvent]:
        """Expose query_recent through an async-compatible method."""
        return self.query_recent(query=query)

    def _normalize_event(self, *, event: JournalEvent) -> JournalEvent:
        """Ensure required runtime-generated values are present."""
        if event.correlation_id is not None:
            return event

        return JournalEvent(**(event.model_dump() | {"correlation_id": str(uuid.uuid4())}))

    def _journal_path_for_timestamp(self, *, timestamp: datetime) -> Path:
        """Map an event timestamp to its daily JSONL file."""
        return self.root_directory / f"{timestamp.astimezone(UTC).date().isoformat()}.jsonl"

    def _ensure_root_directory(self) -> None:
        """Create the journal directory if needed and validate its type."""
        if self.root_directory.exists():
            if not self.root_directory.is_dir():
                raise JournalWriteError("journal root must be a directory")
            return

        self.root_directory.mkdir(parents=True, exist_ok=True)

    def _serialize_event(self, *, event: JournalEvent) -> str:
        """Serialize an event to compact stable JSON."""
        return json.dumps(
            event.model_dump(mode="json", exclude_none=True),
            sort_keys=True,
            separators=(",", ":"),
        )

    def _candidate_files(self, *, since: datetime | None, until: datetime | None) -> list[Path]:
        """Return the daily files that may contain matching events."""
        if since is None and until is None:
            return sorted(self.root_directory.glob("*.jsonl"))

        start_date = (since or until).date()
        end_date = (until or since).date()

        if since is not None and until is None:
            end_date = max(start_date, datetime.now(UTC).date())

        if since is None and until is not None:
            start_date = end_date

        file_paths: list[Path] = []
        current_date = start_date
        while current_date <= end_date:
            file_path = self.root_directory / f"{current_date.isoformat()}.jsonl"
            if file_path.exists():
                file_paths.append(file_path)
            current_date += timedelta(days=1)

        return file_paths

    def _read_matching_events(
        self,
        *,
        file_path: Path,
        query: JournalQuery,
        since: datetime | None,
        until: datetime | None,
    ) -> list[JournalEvent]:
        """Read one daily file and filter matching events."""
        matching_events: list[JournalEvent] = []

        try:
            raw_lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise JournalQueryError(f"unable to read journal file {file_path}") from error

        for raw_line in raw_lines:
            if not raw_line.strip():
                continue

            try:
                event = JournalEvent.model_validate_json(raw_line)
            except ValueError as error:
                raise JournalQueryError(f"invalid journal line in {file_path}") from error

            if self._event_matches(event=event, query=query, since=since, until=until):
                matching_events.append(event)

        return matching_events

    def _event_matches(
        self,
        *,
        event: JournalEvent,
        query: JournalQuery,
        since: datetime | None,
        until: datetime | None,
    ) -> bool:
        """Apply all structured filters to one event."""
        if since is not None and event.timestamp < since:
            return False

        if until is not None and event.timestamp > until:
            return False

        if query.levels and event.level not in query.levels:
            return False

        if query.tags and not set(query.tags).issubset(set(event.tags)):
            return False

        if query.agent_ids and event.agent_id not in query.agent_ids:
            return False

        if query.event_types and event.event_type not in query.event_types:
            return False

        if query.text and query.text.lower() not in self._searchable_text(event=event):
            return False

        return True

    def _searchable_text(self, *, event: JournalEvent) -> str:
        """Build a normalized text blob for simple substring matching."""
        payload_text = json.dumps(event.payload, sort_keys=True).lower()
        return f"{event.message.lower()} {payload_text}"
