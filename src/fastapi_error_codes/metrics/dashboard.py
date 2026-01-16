"""
Dashboard API for JSON metrics endpoints.

This module provides FastAPI router with /api/metrics/* endpoints
for metrics consumption and querying.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from fastapi_error_codes.metrics.collector import ErrorMetricsCollector, MetricsSnapshot


class MetricsSummaryResponse(BaseModel):
    """Summary of current metrics state."""

    total_errors: int
    error_counts: Dict[int, int]
    bucket_count: int
    timestamp: str


class ErrorEventResponse(BaseModel):
    """Single error event response."""

    error_code: int
    error_name: str
    status_code: int
    message: str
    detail: Any
    path: Optional[str]
    method: Optional[str]
    timestamp: str
    event_id: str


class RecentEventsResponse(BaseModel):
    """Recent error events response."""

    events: List[ErrorEventResponse]
    count: int
    timestamp: str


class TimeSeriesResponse(BaseModel):
    """Time series data response."""

    start_time: str
    end_time: str
    data_points: List[Dict[str, Any]]
    total_errors: int


class DashboardAPI:
    """
    Dashboard API for metrics consumption.

    Provides FastAPI router with JSON endpoints for querying metrics.

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_error_codes.metrics import DashboardAPI, ErrorMetricsCollector, MetricsConfig

        app = FastAPI()
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        dashboard = DashboardAPI(collector)

        app.include_router(dashboard.router, prefix="/api/metrics")
        ```
    """

    def __init__(self, collector: ErrorMetricsCollector) -> None:
        """
        Initialize dashboard API.

        Args:
            collector: Error metrics collector
        """
        self.collector = collector
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.router.get("/summary", response_model=MetricsSummaryResponse)
        async def get_summary() -> MetricsSummaryResponse:
            """Get metrics summary."""
            snapshot = self.collector.get_snapshot()
            return MetricsSummaryResponse(
                total_errors=snapshot.total_errors,
                error_counts=snapshot.error_counts,
                bucket_count=snapshot.bucket_count,
                timestamp=snapshot.timestamp.isoformat() + "Z",
            )

        @self.router.get("/recent", response_model=RecentEventsResponse)
        async def get_recent_events(
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
        ) -> RecentEventsResponse:
            """Get recent error events."""
            events = self.collector.get_recent_events(limit=limit)
            return RecentEventsResponse(
                events=[
                    ErrorEventResponse(
                        error_code=event.error_code,
                        error_name=event.error_name,
                        status_code=event.status_code,
                        message=event.message,
                        detail=event.detail,
                        path=event.path,
                        method=event.method,
                        timestamp=event.timestamp.isoformat() + "Z",
                        event_id=event.event_id,
                    )
                    for event in events
                ],
                count=len(events),
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        @self.router.get("/by-code/{error_code}", response_model=Dict[str, Any])
        async def get_by_code(error_code: int) -> Dict[str, Any]:
            """Get metrics for specific error code."""
            counts = self.collector.get_error_counts_by_code()
            count = counts.get(error_code, 0)
            return {
                "error_code": error_code,
                "count": count,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        @self.router.get("/top-errors", response_model=List[Dict[str, Any]])
        async def get_top_errors(
            limit: int = Query(10, ge=1, le=100, description="Number of top errors to return"),
        ) -> List[Dict[str, Any]]:
            """Get top error codes by count."""
            counts = self.collector.get_error_counts_by_code()
            sorted_errors = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [
                {
                    "error_code": code,
                    "count": count,
                    "rank": i + 1,
                }
                for i, (code, count) in enumerate(sorted_errors)
            ]
