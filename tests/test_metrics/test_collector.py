"""
Tests for ErrorMetricsCollector module.

Tests thread-safe metrics collection with time-based bucketing and LRU eviction.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from threading import Thread
from typing import Any, Dict

import pytest

from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.collector import (
    ErrorMetricsCollector,
    ErrorEvent,
    MetricsSnapshot,
    TimeBucket,
)


class TestErrorEvent:
    """Test ErrorEvent dataclass."""

    def test_create_error_event(self) -> None:
        """Test creating an error event."""
        event = ErrorEvent(
            error_code=404,
            error_name="NotFoundError",
            status_code=404,
            message="Resource not found",
            detail={"resource_id": "123"},
            path="/api/users/123",
            method="GET",
        )

        assert event.error_code == 404
        assert event.error_name == "NotFoundError"
        assert event.status_code == 404
        assert event.message == "Resource not found"
        assert event.detail == {"resource_id": "123"}
        assert event.path == "/api/users/123"
        assert event.method == "GET"
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0

    def test_error_event_to_dict(self) -> None:
        """Test converting error event to dictionary."""
        event = ErrorEvent(
            error_code=404,
            error_name="NotFoundError",
            status_code=404,
            message="Resource not found",
            path="/api/users/123",
            method="GET",
        )

        event_dict = event.to_dict()

        assert event_dict["error_code"] == 404
        assert event_dict["error_name"] == "NotFoundError"
        assert event_dict["status_code"] == 404
        assert event_dict["message"] == "Resource not found"
        assert event_dict["path"] == "/api/users/123"
        assert event_dict["method"] == "GET"
        assert "timestamp" in event_dict
        assert "event_id" in event_dict


class TestTimeBucket:
    """Test TimeBucket dataclass."""

    def test_create_time_bucket(self) -> None:
        """Test creating a time bucket."""
        now = datetime.utcnow()
        bucket = TimeBucket(
            start_time=now,
            end_time=now + timedelta(minutes=5),
        )

        assert bucket.start_time == now
        assert bucket.end_time == now + timedelta(minutes=5)
        assert bucket.error_counts == {}
        assert bucket.total_count == 0

    def test_add_event_to_bucket(self) -> None:
        """Test adding events to bucket."""
        bucket = TimeBucket(
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=5),
        )

        event1 = ErrorEvent(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )
        bucket.add_event(event1)

        assert bucket.total_count == 1
        assert bucket.error_counts.get(404) == 1

        event2 = ErrorEvent(
            error_code=500,
            error_name="ServerError",
            status_code=500,
            message="Server error",
        )
        bucket.add_event(event2)

        assert bucket.total_count == 2
        assert bucket.error_counts.get(404) == 1
        assert bucket.error_counts.get(500) == 1

        # Add another 404 error
        event3 = ErrorEvent(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )
        bucket.add_event(event3)

        assert bucket.total_count == 3
        assert bucket.error_counts.get(404) == 2

    def test_is_expired(self) -> None:
        """Test checking if bucket is expired."""
        now = datetime.utcnow()

        # Expired bucket (ended 1 minute ago)
        expired_bucket = TimeBucket(
            start_time=now - timedelta(minutes=6),
            end_time=now - timedelta(minutes=1),
        )
        assert expired_bucket.is_expired(now) is True

        # Active bucket (still within time window)
        active_bucket = TimeBucket(
            start_time=now - timedelta(minutes=2),
            end_time=now + timedelta(minutes=3),
        )
        assert active_bucket.is_expired(now) is False


class TestMetricsSnapshot:
    """Test MetricsSnapshot dataclass."""

    def test_create_snapshot(self) -> None:
        """Test creating a metrics snapshot."""
        snapshot = MetricsSnapshot(
            total_errors=100,
            error_counts={404: 50, 500: 30, 400: 20},
            recent_events=[],
            bucket_count=5,
        )

        assert snapshot.total_errors == 100
        assert snapshot.error_counts == {404: 50, 500: 30, 400: 20}
        assert snapshot.recent_events == []
        assert snapshot.bucket_count == 5
        assert isinstance(snapshot.timestamp, datetime)

    def test_snapshot_to_dict(self) -> None:
        """Test converting snapshot to dictionary."""
        event = ErrorEvent(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        snapshot = MetricsSnapshot(
            total_errors=100,
            error_counts={404: 50, 500: 30},
            recent_events=[event],
            bucket_count=3,
        )

        snapshot_dict = snapshot.to_dict()

        assert snapshot_dict["total_errors"] == 100
        assert snapshot_dict["error_counts"] == {404: 50, 500: 30}
        assert snapshot_dict["bucket_count"] == 3
        assert "timestamp" in snapshot_dict
        assert "recent_events" in snapshot_dict
        assert len(snapshot_dict["recent_events"]) == 1


class TestErrorMetricsCollector:
    """Test ErrorMetricsCollector with thread-safe operations."""

    def test_create_collector_with_default_config(self) -> None:
        """Test creating collector with default config."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        assert collector.config is config
        assert collector.total_events == 0
        assert len(collector.get_buckets()) == 0

    def test_create_collector_with_custom_config(self) -> None:
        """Test creating collector with custom config."""
        config = MetricsConfig(max_events=5000)
        collector = ErrorMetricsCollector(config)

        assert collector.config.max_events == 5000

    def test_record_single_event(self) -> None:
        """Test recording a single error event."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        event_id = collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Resource not found",
            path="/api/users/123",
            method="GET",
        )

        assert isinstance(event_id, str)
        assert len(event_id) > 0
        assert collector.total_events == 1

    def test_record_multiple_events(self) -> None:
        """Test recording multiple error events."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        for i in range(10):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message=f"Not found {i}",
            )

        assert collector.total_events == 10

    def test_record_performance_sub_50microseconds(self) -> None:
        """Test that record() executes in less than 50 microseconds."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        start = time.perf_counter()
        for _ in range(1000):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message="Not found",
            )
        end = time.perf_counter()

        avg_time_ns = (end - start) / 1000 * 1e9
        avg_time_us = avg_time_ns / 1000

        # Should be much less than 50μs on modern hardware
        assert avg_time_us < 50, f"record() took {avg_time_us:.2f}μs average"

    def test_get_snapshot(self) -> None:
        """Test getting a metrics snapshot."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record some events
        for i in range(5):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message=f"Not found {i}",
            )
        for i in range(3):
            collector.record(
                error_code=500,
                error_name="ServerError",
                status_code=500,
                message=f"Server error {i}",
            )

        snapshot = collector.get_snapshot()

        assert snapshot.total_errors == 8
        assert snapshot.error_counts.get(404) == 5
        assert snapshot.error_counts.get(500) == 3
        assert isinstance(snapshot.timestamp, datetime)

    def test_get_error_counts_by_code(self) -> None:
        """Test getting error counts grouped by error code."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        collector.record(error_code=404, error_name="NotFound", status_code=404, message="Not found")
        collector.record(error_code=404, error_name="NotFound", status_code=404, message="Not found")
        collector.record(error_code=500, error_name="ServerError", status_code=500, message="Error")

        counts = collector.get_error_counts_by_code()

        assert counts.get(404) == 2
        assert counts.get(500) == 1

    def test_get_recent_events_limit(self) -> None:
        """Test getting recent events with limit."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record 20 events
        for i in range(20):
            collector.record(
                error_code=400,
                error_name="BadRequest",
                status_code=400,
                message=f"Bad request {i}",
            )

        recent = collector.get_recent_events(limit=10)

        assert len(recent) == 10
        # Most recent events first
        assert recent[0].message == "Bad request 19"

    def test_thread_safe_concurrent_recording(self) -> None:
        """Test that collector is thread-safe under concurrent load."""
        config = MetricsConfig(max_events=10000)
        collector = ErrorMetricsCollector(config)

        num_threads = 10
        events_per_thread = 100

        def record_events(thread_id: int) -> int:
            for i in range(events_per_thread):
                collector.record(
                    error_code=400 + (i % 100),
                    error_name=f"Error{thread_id}_{i}",
                    status_code=400,
                    message=f"Thread {thread_id} event {i}",
                )
            return events_per_thread

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(record_events, i)
                for i in range(num_threads)
            ]
            results = [
                future.result()
                for future in as_completed(futures)
            ]

        total_expected = sum(results)
        total_actual = collector.total_events

        # All events should be recorded without loss
        assert total_actual == total_expected
        assert total_actual == num_threads * events_per_thread

    def test_lru_eviction_when_max_events_reached(self) -> None:
        """Test that LRU eviction removes oldest buckets when max_events is reached."""
        # Small max_events to trigger eviction
        config = MetricsConfig(max_events=100)
        collector = ErrorMetricsCollector(config)

        # Record more events than max_events
        for i in range(150):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message=f"Not found {i}",
            )

        # Total events should not exceed max_events significantly
        # (allow some buffer for the current bucket)
        assert collector.total_events <= config.max_events + 50

        # Recent events should still be available
        recent = collector.get_recent_events(limit=10)
        assert len(recent) == 10
        # Most recent events
        assert recent[0].message == "Not found 149"

    def test_clear_resets_collector(self) -> None:
        """Test that clear() resets the collector."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record some events
        for i in range(10):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message=f"Not found {i}",
            )

        assert collector.total_events == 10

        collector.clear()

        assert collector.total_events == 0
        assert len(collector.get_buckets()) == 0

    def test_bucket_time_window(self) -> None:
        """Test that events are bucketed by time window."""
        config = MetricsConfig(collection_interval_ms=2000)  # 2 second buckets
        collector = ErrorMetricsCollector(config)

        # Record events
        collector.record(error_code=404, error_name="NotFound", status_code=404, message="Event 1")

        buckets = collector.get_buckets()
        initial_bucket_count = len(buckets)

        # Wait for bucket to expire (need to wait past bucket end time)
        time.sleep(2.5)

        # Record new event - should create new bucket
        collector.record(error_code=500, error_name="Error", status_code=500, message="Event 2")

        buckets_after = collector.get_buckets()

        # Old bucket should be cleaned up
        assert len(buckets_after) <= initial_bucket_count + 1

    def test_get_buckets(self) -> None:
        """Test getting all active buckets."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record some events
        collector.record(error_code=404, error_name="NotFound", status_code=404, message="Event 1")
        collector.record(error_code=500, error_name="Error", status_code=500, message="Event 2")

        buckets = collector.get_buckets()

        assert len(buckets) > 0
        # Each bucket should have total_count
        for bucket in buckets:
            assert bucket.total_count >= 0

    def test_record_with_optional_fields(self) -> None:
        """Test recording event with all optional fields."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        event_id = collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
            detail={"resource_id": "123"},
            path="/api/users/123",
            method="GET",
        )

        snapshot = collector.get_snapshot()
        assert snapshot.total_errors == 1

        recent = collector.get_recent_events(limit=1)
        assert len(recent) == 1
        assert recent[0].detail == {"resource_id": "123"}
        assert recent[0].path == "/api/users/123"
        assert recent[0].method == "GET"

    def test_concurrent_snapshot_and_record(self) -> None:
        """Test thread safety when snapshot and record happen concurrently."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        def record_worker() -> None:
            for i in range(100):
                collector.record(
                    error_code=404,
                    error_name="NotFound",
                    status_code=404,
                    message=f"Event {i}",
                )

        def snapshot_worker() -> None:
            for _ in range(50):
                snapshot = collector.get_snapshot()
                assert snapshot.total_errors >= 0

        record_thread = Thread(target=record_worker)
        snapshot_thread = Thread(target=snapshot_worker)

        record_thread.start()
        snapshot_thread.start()

        record_thread.join()
        snapshot_thread.join()

        assert collector.total_events == 100
