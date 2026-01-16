"""
Error metrics and monitoring integration for fastapi-error-codes.

This module provides:
- MetricsConfig: Configuration management with presets
- ErrorMetricsCollector: Thread-safe metrics collection
- PrometheusExporter: Prometheus metrics export
- SentryIntegration: Sentry error tracking
- DashboardAPI: JSON API endpoints for metrics
- setup_metrics: FastAPI integration function
"""

from fastapi_error_codes.metrics.config import (
    MetricsConfig,
    MetricsPreset,
    get_config_from_env,
)
from fastapi_error_codes.metrics.collector import (
    ErrorMetricsCollector,
    ErrorEvent,
    MetricsSnapshot,
    TimeBucket,
)
from fastapi_error_codes.metrics.prometheus import PrometheusExporter
from fastapi_error_codes.metrics.sentry import SentryIntegration, mask_pii
from fastapi_error_codes.metrics.dashboard import DashboardAPI
from fastapi_error_codes.metrics.setup import setup_metrics

__all__ = [
    # Config
    "MetricsConfig",
    "MetricsPreset",
    "get_config_from_env",
    # Collector
    "ErrorMetricsCollector",
    "ErrorEvent",
    "MetricsSnapshot",
    "TimeBucket",
    # Exporters
    "PrometheusExporter",
    "SentryIntegration",
    "mask_pii",
    # Dashboard
    "DashboardAPI",
    # Setup
    "setup_metrics",
]
