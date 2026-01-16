# SPEC-TRACING-003: Distributed Tracing System

**Status:** Draft
**Priority:** High
**Created:** 2025-01-16
**Author:** Yarang

## Executive Summary

Implement distributed tracing system for fastapi-error-codes using OpenTelemetry to track request flows across services, correlate errors with traces, and enable performance analysis.

## Background

Current monitoring system (SPEC-MONITOR-002) provides metrics and error tracking but lacks distributed tracing capabilities needed to:
- Track request flows across multiple services
- Correlate errors with trace context
- Identify performance bottlenecks in distributed systems
- Enable root cause analysis across service boundaries

## Requirements

### 1. Core Tracing Infrastructure

**WHEN** the system initializes
**THE SYSTEM SHALL** create TracingConfig with validation
- Service name validation (non-empty, alphanumeric with hyphens)
- Endpoint URL validation for exporters
- Sampling rate validation (0.0 to 1.0)
- Frozen dataclass for immutability

**WHEN** OpenTelemetry SDK initializes
**THE SYSTEM SHALL** configure tracing provider with:
- Resource attributes (service.name, service.version)
- BatchSpanProcessor for efficient export
- Configurable sampling strategy

**WHEN** HTTP requests are processed
**THE SYSTEM SHALL** create spans with:
- HTTP method, route, status code attributes
- W3C trace context propagation
- Parent-child span relationships

### 2. Exporter Integration

**WHEN** JaegerExporter is configured
**THE SYSTEM SHALL** export traces to Jaeger via thrift protocol
- Agent host and port configuration
- Async batch export with non-blocking I/O
- Retry logic for transient failures

**WHEN** OTLPExporter is configured
**THE SYSTEM SHALL** export traces via OpenTelemetry Protocol
- HTTP/protobuf or gRPC transport
- TLS support for secure transmission
- Headers authentication support

**WHEN** export fails
**THE SYSTEM SHALL** handle gracefully with:
- Exponential backoff retry
- Maximum retry limit (default: 3)
- Fallback to in-memory buffer

### 3. Exception Tracing & PII Masking

**WHEN** exceptions occur
**THE SYSTEM SHALL** record exception events with:
- Exception type and message
- Stack trace (sanitized)
- Error code from BaseAppException
- Timestamp and severity

**WHEN** span attributes contain PII
**THE SYSTEM SHALL** mask sensitive data:
- Email addresses: e***@example.com
- Phone numbers: ***-***-1234
- Credit cards: ****-****-****-1234
- SSN/Tax IDs: ***-**-****
- Custom patterns via regex configuration

**WHERE** PII masking is applied:
- Span attributes
- Exception details
- HTTP headers (Authorization, Cookie)

### 4. Trace Context Propagation

**WHEN** requests arrive with traceparent header
**THE SYSTEM SHALL** extract trace context:
- Parse W3C traceparent format (version-traceid-parentid-flags)
- Validate trace ID and span ID format
- Continue existing trace if valid

**WHEN** making downstream requests
**THE SYSTEM SHALL** inject trace context:
- Add traceparent header to outgoing requests
- Propagate baggage for additional metadata
- Maintain trace consistency across hops

**WHEN** trace context is missing
**THE SYSTEM SHALL** start new trace with:
- Random 16-byte trace ID
- Random 8-byte span ID
- Default sampling flags

### 5. SPEC-001/002 Integration

**WHEN** setup_tracing() is called
**THE SYSTEM SHALL** integrate with existing systems:
- Modify setup_exception_handler() to record exceptions in spans
- Add trace_id to error responses
- Correlate metrics with trace IDs

**WHEN** exceptions are handled
**THE SYSTEM SHALL** enrich error context:
- Add trace_id to ErrorResponse model
- Record span_id in error metrics
- Link error metrics to trace context

**WHEN** metrics are exported
**THE SYSTEM SHALL** include trace correlation:
- Add trace_id label to Prometheus metrics
- Include trace context in Sentry events
- Enable trace-metrics correlation in dashboards

## Architecture

### Module Structure

```
src/fastapi_error_codes/
  tracing/
    __init__.py           # Public API exports
    config.py             # TracingConfig, validation
    otel.py               # OpenTelemetryIntegration
    exporters.py          # JaegerExporter, OTLPExporter
    exceptions.py         # ExceptionTracer
    propagator.py         # TraceContextPropagator
    middleware.py         # FastAPI middleware for tracing
    pii.py                # PII masking utilities
```

### Class Design

#### TracingConfig
```python
@dataclass(frozen=True)
class TracingConfig:
    service_name: str
    endpoint: str
    sample_rate: float = 1.0
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    otlp_endpoint: str = "http://localhost:4317"
    enable_pii_masking: bool = True
    pii_patterns: Dict[str, str] = field(default_factory=dict)
```

#### OpenTelemetryIntegration
```python
class OpenTelemetryIntegration:
    def __init__(self, config: TracingConfig)
    def initialize(self) -> None
    def shutdown(self) -> None
    def get_tracer(self, name: str) -> Tracer
    def configure_exporter(self, exporter_type: str) -> SpanExporter
```

#### ExceptionTracer
```python
class ExceptionTracer:
    def record_exception(self, span: Span, exc: Exception) -> None
    def sanitize_stacktrace(self, traceback: str) -> str
    def extract_error_code(self, exc: Exception) -> Optional[int]
```

#### TraceContextPropagator
```python
class TraceContextPropagator:
    def extract(self, headers: Dict[str, str]) -> Context
    def inject(self, context: Context, headers: Dict[str, str]) -> None
    def parse_traceparent(self, header: str) -> Optional[TraceContext]
```

## Dependencies

```
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation>=0.40b0
opentelemetry-semantic-conventions>=0.40b0
opentelemetry-exporter-jaeger>=1.20.0
opentelemetry-exporter-otlp>=1.20.0
opentelemetry-instrumentation-fastapi>=0.40b0
opentelemetry-instrumentation-httpx>=0.40b0
```

## Quality Gates

- Test coverage: 85%+
- All TRUST 5 pillars compliance
- Performance: < 1ms overhead for span creation
- PII masking verified with test cases
- Thread safety for concurrent operations
- No memory leaks in span buffers

## Implementation Phases

### Phase 1: Core Infrastructure (1-2 days)
- TracingConfig with validation
- OpenTelemetryIntegration SDK wrapper
- Basic span creation tests

### Phase 2: Exporter Integration (1-2 days)
- JaegerExporter implementation
- OTLPExporter implementation
- Async export with retry logic

### Phase 3: Exception Tracing (1 day)
- ExceptionTracer with event recording
- PII masking utilities
- Stack trace sanitization

### Phase 4: Context Propagation (1 day)
- TraceContextPropagator
- W3C traceparent parsing
- Header injection/extraction

### Phase 5: Integration (1-2 days)
- setup_tracing() function
- Integration with setup_exception_handler()
- Trace ID correlation in metrics

## Acceptance Criteria

### Phase 1
- [ ] TracingConfig validates all inputs
- [ ] OpenTelemetryIntegration initializes without errors
- [ ] Spans are created for HTTP requests
- [ ] Unit tests pass with 85%+ coverage

### Phase 2
- [ ] JaegerExporter exports traces successfully
- [ ] OTLPExporter exports traces successfully
- [ ] Export failures are handled gracefully
- [ ] Async export doesn't block requests

### Phase 3
- [ ] Exceptions are recorded as span events
- [ ] PII is masked according to patterns
- [ ] Stack traces are sanitized
- [ ] Error codes are extracted from BaseAppException

### Phase 4
- [ ] Trace context is extracted from traceparent
- [ ] Trace context is injected to downstream requests
- [ ] New traces start when context missing
- [ ] W3C format compliance verified

### Phase 5
- [ ] setup_tracing() integrates with FastAPI
- [ ] Trace ID appears in error responses
- [ ] Metrics include trace_id labels
- [ ] Sentry events include trace context

## Success Metrics

- Zero errors in OpenTelemetry initialization
- < 1% trace export failure rate
- < 1ms overhead for span creation
- 100% PII masking coverage
- End-to-end trace correlation working

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenTelemetry version conflicts | High | Pin compatible versions in pyproject.toml |
| Performance degradation | Medium | Async export, sampling, configurable buffers |
| PII masking misses data | High | Comprehensive test cases, pattern validation |
| Trace context propagation breaks | Medium | W3C compliance tests, integration tests |

## Documentation Requirements

- API reference for all public functions
- Usage examples with Jaeger and OTLP
- PII masking configuration guide
- Integration guide with SPEC-001/002
- Troubleshooting guide for common issues

## Related Specifications

- SPEC-001: Base Error Handler (exception handling)
- SPEC-MONITOR-002: Monitoring (metrics, Sentry, dashboard)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-16 | Initial draft |
