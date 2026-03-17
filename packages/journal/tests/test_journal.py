#!/usr/bin/env python3
"""Tests for the journal package public behavior."""

import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from journal import Journal, JournalEvent, JournalLevel, JournalQuery, JournalWriteError


def test_append_event_writes_jsonl_record_with_generated_correlation_id(tmp_path: Path) -> None:
    """A valid event is written to the correct daily file."""
    journal = Journal(root_directory=tmp_path)
    event = JournalEvent(
        timestamp=datetime(2026, 3, 16, 13, 45, tzinfo=UTC),
        level=JournalLevel.INFO,
        event_type="scheduler.tick",
        source="hypothalamus",
        agent_id="main",
        tags=["autonomous", "health"],
        message="Nightly run completed",
        payload={"status": "ok"},
    )

    write_result = journal.append_event(event=event)

    assert write_result.event.correlation_id
    expected_path = tmp_path / "2026-03-16.jsonl"
    assert write_result.path == expected_path
    lines = expected_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert '"message":"Nightly run completed"' in lines[0]
    assert '"correlation_id":"' in lines[0]


def test_append_event_requires_agent_id(tmp_path: Path) -> None:
    """A journal event must identify its emitting agent."""
    journal = Journal(root_directory=tmp_path)

    with pytest.raises(ValueError, match="agent_id"):
        journal.append_event(
            event=JournalEvent(
                timestamp=datetime(2026, 3, 16, 13, 45, tzinfo=UTC),
                level=JournalLevel.INFO,
                event_type="scheduler.tick",
                source="hypothalamus",
                agent_id="",
                tags=["autonomous"],
                message="Missing agent id",
                payload={"status": "bad"},
            )
        )


def test_query_recent_filters_by_metadata_and_text(tmp_path: Path) -> None:
    """Recent queries filter by time, metadata, and text content."""
    journal = Journal(root_directory=tmp_path)
    matching_event = JournalEvent(
        timestamp=datetime(2026, 3, 16, 10, 0, tzinfo=UTC),
        level=JournalLevel.ERROR,
        event_type="provider.error",
        source="gateway",
        agent_id="main",
        correlation_id="corr-1",
        tags=["provider", "openai"],
        message="OpenAI provider request failed",
        payload={"provider": "openai", "detail": "timeout"},
    )
    non_matching_event = JournalEvent(
        timestamp=datetime(2026, 3, 16, 11, 0, tzinfo=UTC),
        level=JournalLevel.INFO,
        event_type="provider.success",
        source="gateway",
        agent_id="researcher",
        correlation_id="corr-2",
        tags=["provider", "anthropic"],
        message="Anthropic provider request succeeded",
        payload={"provider": "anthropic", "detail": "ok"},
    )

    journal.append_event(event=matching_event)
    journal.append_event(event=non_matching_event)

    events = journal.query_recent(
        query=JournalQuery(
            since="3 hours ago",
            until="30 minutes ago",
            now=datetime(2026, 3, 16, 12, 0, tzinfo=UTC),
            levels=[JournalLevel.ERROR],
            tags=["provider"],
            agent_ids=["main"],
            event_types=["provider.error"],
            text="timeout",
        )
    )

    assert [event.correlation_id for event in events] == ["corr-1"]


def test_query_recent_understands_last_weekday_and_today_at(tmp_path: Path) -> None:
    """Human-friendly time expressions resolve deterministically."""
    journal = Journal(root_directory=tmp_path)
    journal.append_event(
        event=JournalEvent(
            timestamp=datetime(2026, 3, 11, 18, 0, tzinfo=UTC),
            level=JournalLevel.INFO,
            event_type="memory.update",
            source="hypothalamus",
            agent_id="main",
            correlation_id="corr-3",
            tags=["memory"],
            message="Memory updated last Wednesday",
            payload={"hours": 24},
        )
    )
    journal.append_event(
        event=JournalEvent(
            timestamp=datetime(2026, 3, 16, 14, 15, tzinfo=UTC),
            level=JournalLevel.INFO,
            event_type="memory.update",
            source="hypothalamus",
            agent_id="main",
            correlation_id="corr-4",
            tags=["memory"],
            message="Memory updated today",
            payload={"hours": 24},
        )
    )

    weekday_events = journal.query_recent(
        query=JournalQuery(
            since="last wednesday",
            until="today at 12:00",
            now=datetime(2026, 3, 16, 15, 0, tzinfo=UTC),
        )
    )
    today_events = journal.query_recent(
        query=JournalQuery(
            since="today at 14:00",
            now=datetime(2026, 3, 16, 15, 0, tzinfo=UTC),
        )
    )

    assert [event.correlation_id for event in weekday_events] == ["corr-3"]
    assert [event.correlation_id for event in today_events] == ["corr-4"]


def test_append_event_is_thread_safe(tmp_path: Path) -> None:
    """Concurrent writes produce intact records without losing data."""
    journal = Journal(root_directory=tmp_path)

    def write_event(index: int) -> None:
        journal.append_event(
            event=JournalEvent(
                timestamp=datetime(2026, 3, 16, 9, 0, tzinfo=UTC),
                level=JournalLevel.DEBUG,
                event_type="worker.step",
                source="tools",
                agent_id="coder",
                correlation_id=f"corr-{index}",
                tags=["worker"],
                message=f"Worker step {index}",
                payload={"index": index},
            )
        )

    threads = [threading.Thread(target=write_event, args=(index,)) for index in range(20)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    written_lines = (tmp_path / "2026-03-16.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(written_lines) == 20
    assert all(line.endswith("}") for line in written_lines)


@pytest.mark.asyncio
async def test_async_wrapper_matches_sync_behavior(tmp_path: Path) -> None:
    """Async wrappers provide the same behavior as sync calls."""
    journal = Journal(root_directory=tmp_path)
    event = JournalEvent(
        timestamp=datetime(2026, 3, 16, 17, 0, tzinfo=UTC),
        level=JournalLevel.URGENT,
        event_type="reflex.escalation",
        source="hypothalamus",
        agent_id="main",
        correlation_id="corr-async",
        tags=["urgent"],
        message="Escalate the user alert",
        payload={"target": "main"},
    )

    await journal.append_event_async(event=event)
    events = await journal.query_recent_async(
        query=JournalQuery(
            since="1 hour ago",
            now=datetime(2026, 3, 16, 17, 30, tzinfo=UTC),
            levels=[JournalLevel.URGENT],
        )
    )

    assert [saved_event.correlation_id for saved_event in events] == ["corr-async"]


def test_rotation_uses_event_date(tmp_path: Path) -> None:
    """Events are written to their own daily file based on timestamp."""
    journal = Journal(root_directory=tmp_path)
    journal.append_event(
        event=JournalEvent(
            timestamp=datetime(2026, 3, 15, 23, 59, tzinfo=UTC),
            level=JournalLevel.INFO,
            event_type="scheduler.tick",
            source="hypothalamus",
            agent_id="main",
            correlation_id="corr-old",
            tags=["autonomous"],
            message="Previous day",
            payload={},
        )
    )
    journal.append_event(
        event=JournalEvent(
            timestamp=datetime(2026, 3, 16, 0, 1, tzinfo=UTC),
            level=JournalLevel.INFO,
            event_type="scheduler.tick",
            source="hypothalamus",
            agent_id="main",
            correlation_id="corr-new",
            tags=["autonomous"],
            message="Next day",
            payload={},
        )
    )

    assert (tmp_path / "2026-03-15.jsonl").exists()
    assert (tmp_path / "2026-03-16.jsonl").exists()


def test_append_event_raises_explicit_error_on_write_failure(tmp_path: Path) -> None:
    """Write failures raise a journal-specific exception."""
    non_directory_path = tmp_path / "journal-root"
    non_directory_path.write_text("not-a-directory", encoding="utf-8")
    journal = Journal(root_directory=non_directory_path)

    with pytest.raises(JournalWriteError):
        journal.append_event(
            event=JournalEvent(
                timestamp=datetime(2026, 3, 16, 13, 45, tzinfo=UTC),
                level=JournalLevel.INFO,
                event_type="scheduler.tick",
                source="hypothalamus",
                agent_id="main",
                correlation_id="corr-write-error",
                tags=["autonomous"],
                message="Cannot write into a file path",
                payload={"status": "bad"},
            )
        )
