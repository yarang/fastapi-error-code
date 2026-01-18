# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project documentation and development setup
- MoAI-ADK integration with Alfred orchestrator

## [0.1.0] - 2025-01-17

### Added
- Core exception handling framework
  - `BaseAppException` base class for custom application exceptions
  - Custom error codes support (0-9999 range)
  - HTTP status code mapping
  - Timestamp generation (ISO 8601 format)
  - Detail information support

- Error domain management
  - Predefined error domains: AUTH (200-299), RESOURCE (300-399), VALIDATION (400-499), SERVER (500-599), CUSTOM (900-999)
  - `ErrorDomain` class for code range validation
  - Custom domain registration support

- Exception registration system
  - `ExceptionRegistry` for centralized error code management
  - `@register_exception` decorator for automatic registration
  - Thread-safe registry operations
  - Duplicate error code detection

- Internationalization (i18n)
  - `MessageProvider` class for multi-language support
  - Fallback chain: requested locale → fallback locales → default locale → key
  - Accept-Language header parsing
  - Locale file loading (JSON format)

- FastAPI integration
  - `setup_exception_handler()` function for handler registration
  - `ErrorHandlerConfig` with development/production presets
  - Environment variable configuration support
  - Automatic error response generation

- Pydantic response models
  - `ErrorResponse` for standard API errors
  - `ValidationErrorResponse` for validation errors
  - `ErrorDetail` and `ErrorDetailItem` for structured error information
  - Pydantic v1/v2 compatibility

- Monitoring & Metrics (SPEC-MONITOR-002)
  - `ErrorMetricsCollector` with thread-safe collection (< 50μs performance)
  - `PrometheusExporter` for `/metrics` endpoint
  - `SentryIntegration` for automatic error tracking
  - `DashboardAPI` with JSON endpoints (`/api/metrics/*`)
  - Time-based bucketing with automatic cleanup
  - PII masking for sensitive data

- Distributed Tracing (SPEC-TRACING-003)
  - OpenTelemetry SDK integration
  - `TracingConfig` with validation
  - Multiple exporters: Jaeger and OTLP
  - `ExceptionTracer` for automatic exception recording in spans
  - `PIIMasker` for sensitive data masking (email, phone, credit card, SSN)
  - `TraceContextPropagator` for W3C Trace Context support
  - Trace ID correlation with error responses

- Configuration management
  - `ErrorHandlerConfig` with frozen dataclass
  - `MetricsConfig` with validation and presets
  - `TracingConfig` with validation
  - Environment variable support for all configs

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- PII masking implemented for logs, metrics, and traces
- Sensitive data patterns: email, phone, credit card, SSN, API keys

---

## Version History

| Version | Date       | Status      | Description                    |
|---------|------------|-------------|--------------------------------|
| 0.1.0   | 2025-01-17 | Released    | Initial production release     |

---

## Project Links

- **GitHub**: https://github.com/yarang/fastapi-error-codes
- **Documentation**: https://github.com/yarang/fastapi-error-codes/blob/main/README.md
- **Issues**: https://github.com/yarang/fastapi-error-codes/issues
