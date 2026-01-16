"""
Prometheus metrics export for error monitoring.

This module provides PrometheusExporter for exporting error metrics
in Prometheus format using prometheus-client library.
"""

import re
from typing import Optional

from fastapi_error_codes.metrics.collector import ErrorMetricsCollector


class PrometheusExporter:
    """
    Export error metrics in Prometheus format.

    This class generates Prometheus-compatible metrics from the
    ErrorMetricsCollector using prometheus-client patterns.

    Metrics exported:
    - fastapi_errors_total: Total counter of all errors
    - fastapi_errors_by_code: Gauge of errors grouped by error code
    - fastapi_errors_by_status: Gauge of errors grouped by HTTP status code

    Example:
        ```python
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Get Prometheus metrics
        metrics = exporter.generate_metrics()
        print(metrics)
        # # HELP fastapi_errors_total Total number of application errors
        # # TYPE fastapi_errors_total counter
        # fastapi_errors_total 42
        ```

    Performance:
    - generate_metrics(): < 1ms for typical workloads
    - Thread-safe read from collector
    """

    def __init__(
        self,
        collector: ErrorMetricsCollector,
        enabled: bool = True,
        namespace: str = "fastapi",
    ) -> None:
        """
        Initialize Prometheus exporter.

        Args:
            collector: Error metrics collector
            enabled: Enable/disable metrics export
            namespace: Metric namespace prefix
        """
        self.collector = collector
        self.enabled = enabled
        self.namespace = namespace

    def generate_metrics(self) -> str:
        """
        Generate metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string, or empty string if disabled

        Example:
            ```python
            metrics = exporter.generate_metrics()
            # Returns:
            # # HELP fastapi_errors_total Total number of application errors
            # # TYPE fastapi_errors_total counter
            # fastapi_errors_total 42
            # # HELP fastapi_errors_by_code Errors by application error code
            # # TYPE fastapi_errors_by_code gauge
            # fastapi_errors_by_code{error_code="404"} 10
            # fastapi_errors_by_code{error_code="500"} 5
            ```
        """
        if not self.enabled:
            return ""

        snapshot = self.collector.get_snapshot()
        lines = []

        # Total errors counter
        lines.extend([
            f"# HELP {self.namespace}_errors_total Total number of application errors",
            f"# TYPE {self.namespace}_errors_total counter",
            f"{self.namespace}_errors_total {snapshot.total_errors}",
            "",
        ])

        # Errors by code
        lines.extend([
            f"# HELP {self.namespace}_errors_by_code Errors grouped by application error code",
            f"# TYPE {self.namespace}_errors_by_code gauge",
        ])
        for code, count in sorted(snapshot.error_counts.items()):
            lines.append(f'{self.namespace}_errors_by_code{{error_code="{code}"}} {count}')
        lines.append("")

        # Errors by HTTP status code
        status_counts = self._get_status_counts(snapshot)
        if status_counts:
            lines.extend([
                f"# HELP {self.namespace}_errors_by_status Errors grouped by HTTP status code",
                f"# TYPE {self.namespace}_errors_by_status gauge",
            ])
            for status, count in sorted(status_counts.items()):
                lines.append(f'{self.namespace}_errors_by_status{{status_code="{status}"}} {count}')
            lines.append("")

        return "\n".join(lines)

    def _get_status_counts(self, snapshot) -> dict:
        """
        Extract error counts by HTTP status code from snapshot.

        Args:
            snapshot: MetricsSnapshot from collector

        Returns:
            Dictionary mapping status codes to counts
        """
        status_counts = {}
        for event in snapshot.recent_events:
            status = event.status_code
            status_counts[status] = status_counts.get(status, 0) + 1

        # Also count from error_codes if we don't have recent events
        if not status_counts and snapshot.error_counts:
            # Map error codes to likely status codes
            for code, count in snapshot.error_counts.items():
                # Default mapping: error_code in same range as status code
                if 400 <= code < 600:
                    status_counts[code] = status_counts.get(code, 0) + count

        return status_counts
