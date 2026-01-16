"""
Tests for PrometheusExporter module.

Tests Prometheus metrics export with prometheus-client integration.
"""

import re
from typing import List

import pytest

from fastapi_error_codes.metrics.collector import ErrorMetricsCollector
from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.prometheus import PrometheusExporter


class TestPrometheusExporter:
    """Test PrometheusExporter with prometheus-client integration."""

    def test_create_exporter(self) -> None:
        """Test creating a Prometheus exporter."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        assert exporter.collector is collector
        assert exporter.enabled is True

    def test_create_exporter_disabled(self) -> None:
        """Test creating a disabled Prometheus exporter."""
        config = MetricsConfig(prometheus_enabled=False)
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector, enabled=False)

        assert exporter.enabled is False

    def test_generate_metrics_empty(self) -> None:
        """Test generating metrics with no errors recorded."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        metrics = exporter.generate_metrics()

        assert isinstance(metrics, str)
        assert "fastapi_errors_total" in metrics
        assert "fastapi_errors_by_code" in metrics

    def test_generate_metrics_with_data(self) -> None:
        """Test generating metrics with error data."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record some errors
        for _ in range(5):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message="Not found",
            )
        for _ in range(3):
            collector.record(
                error_code=500,
                error_name="ServerError",
                status_code=500,
                message="Server error",
            )

        exporter = PrometheusExporter(collector)
        metrics = exporter.generate_metrics()

        # Check total counter
        assert 'fastapi_errors_total 8' in metrics

        # Check error code labels
        assert 'fastapi_errors_by_code{error_code="404"} 5' in metrics
        assert 'fastapi_errors_by_code{error_code="500"} 3' in metrics

    def test_metrics_format(self) -> None:
        """Test that metrics follow Prometheus format."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Record error
        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        metrics = exporter.generate_metrics()

        # Check for HELP and TYPE comments
        assert "# HELP fastapi_errors_total" in metrics
        assert "# TYPE fastapi_errors_total counter" in metrics
        assert "# HELP fastapi_errors_by_code" in metrics
        assert "# TYPE fastapi_errors_by_code gauge" in metrics

    def test_metric_labels(self) -> None:
        """Test that metrics include proper labels."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Record errors with different codes
        collector.record(
            error_code=400,
            error_name="BadRequest",
            status_code=400,
            message="Bad request",
        )
        collector.record(
            error_code=401,
            error_name="Unauthorized",
            status_code=401,
            message="Unauthorized",
        )

        metrics = exporter.generate_metrics()

        # Check label format
        assert 'error_code="400"' in metrics
        assert 'error_code="401"' in metrics

    def test_counter_increment(self) -> None:
        """Test that counter increments with new errors."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Initial state
        metrics_1 = exporter.generate_metrics()
        count_1 = self._extract_total_count(metrics_1)

        # Record error
        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        # After recording
        metrics_2 = exporter.generate_metrics()
        count_2 = self._extract_total_count(metrics_2)

        assert count_2 == count_1 + 1

    def test_multiple_error_codes(self) -> None:
        """Test metrics with multiple error codes."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Record errors with different codes
        error_codes = [400, 401, 403, 404, 500, 502, 503]
        for code in error_codes:
            collector.record(
                error_code=code,
                error_name=f"Error{code}",
                status_code=code,
                message=f"Error {code}",
            )

        metrics = exporter.generate_metrics()

        # Verify all error codes are present
        for code in error_codes:
            assert f'error_code="{code}"' in metrics

    def test_zero_values(self) -> None:
        """Test metrics with zero errors (initial state)."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        metrics = exporter.generate_metrics()

        # Total should be 0
        assert "fastapi_errors_total 0" in metrics

    def test_custom_namespace(self) -> None:
        """Test exporter with custom namespace."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector, namespace="custom_app")

        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        metrics = exporter.generate_metrics()

        # Check custom namespace is used
        assert "custom_app_errors_total" in metrics
        assert "custom_app_errors_by_code" in metrics

    def test_disabled_exporter_returns_empty(self) -> None:
        """Test that disabled exporter returns empty string."""
        config = MetricsConfig(prometheus_enabled=False)
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector, enabled=False)

        # Record error
        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        metrics = exporter.generate_metrics()

        # Should be empty
        assert metrics == ""

    def test_histogram_metric(self) -> None:
        """Test histogram metric for HTTP status codes."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Record errors with different status codes
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

        metrics = exporter.generate_metrics()

        # Check for status code histogram/bucket
        # The exporter should include status code distribution
        assert "fastapi_errors_by_status" in metrics or "status_code" in metrics

    def test_large_volume_metrics(self) -> None:
        """Test metrics generation with large error volume."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        exporter = PrometheusExporter(collector)

        # Record many errors
        for i in range(1000):
            collector.record(
                error_code=400 + (i % 100),
                error_name="Error",
                status_code=400,
                message=f"Error {i}",
            )

        metrics = exporter.generate_metrics()

        # Should contain all errors
        total = self._extract_total_count(metrics)
        assert total >= 1000

    def _extract_total_count(self, metrics: str) -> int:
        """Extract total count from metrics string."""
        match = re.search(r'fastapi_errors_total (\d+)', metrics)
        if match:
            return int(match.group(1))
        return 0
