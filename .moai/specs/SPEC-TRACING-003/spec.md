# SPEC-TRACING-003: 분산 추적 시스템 (Distributed Tracing System)

## Specification Information

- **ID**: SPEC-TRACING-003
- **Title**: 분산 추적 시스템 구현 (Distributed Tracing System with OpenTelemetry)
- **Status**: Planned
- **Version**: 1.0.0
- **Created**: 2026-01-16
- **Priority**: High
- **Related SPECs**: SPEC-001 (Error Handler), SPEC-MONITOR-002 (Monitoring)

---

## Overview

이 SPEC은 fastapi-error-codes 패키지에 OpenTelemetry 기반 분산 추적(Distributed Tracing) 기능을 추가하는 것을 정의합니다. 분산 추적을 통해 마이크로서비스 아키텍처에서 에러의 전파 경로를 추적하고, 성능 병목을 식별하며, 서비스 간 호출 흐름을 시각화할 수 있습니다.

### Goals

- OpenTelemetry 통합을 통한 표준 기반 분산 추적 제공
- 에러 발생 시 자동 span 생성 및 trace context 전파
- FastAPI 요청 처리 전체에 대한 자동 추적
- 기존 에러 핸들러(SPEC-001)와의 seamless 통합
- 모니터링 시스템(SPEC-MONITOR-002)와의 호환성 유지
- Jaeger, Zipkin, OpenTelemetry Collector 등 다양한 백엔드 지원

### Success Criteria

- 모든 BaseAppException 발생이 자동으로 trace에 기록됨
- Trace context가 서비스 경계를 넘어 정확히 전파됨
- OpenTelemetry 표준을 완벽하게 준수
- 에러 핸들링 성능에 1ms 미만의 오버헤드만 추가
- 기존 SPEC-001, SPEC-MONITOR-002 기능과 호환성 유지
- 85%+ 테스트 커버리지 달성

---

## Requirements

### Ubiquitous Requirements

**WHILE the application is running**
- 시스템은 모든 HTTP 요청에 대해 trace를 생성해야 한다
- 시스템은 모든 BaseAppException 발생을 span에 기록해야 한다
- 시스템은 trace context를 W3C Trace Context 표준으로 관리해야 한다

**WHILE distributed tracing is enabled**
- 시스템은 비동기 방식으로 trace를 export해야 한다 (blocking 방지)
- 시스템은 sampling rate에 따라 trace를 수집해야 한다
- 시스템은 OpenTelemetry Resource를 자동으로 구성해야 한다

**WHILE error handling occurs**
- 시스템은 에러 발생 시 exception event를 span에 기록해야 한다
- 시스템은 error_code, error_domain을 span attribute로 추가해야 한다
- 시스템은 stacktrace를 span에 capture해야 한다 (선택적으로)

### Event-Driven Requirements

**WHEN setup_tracing is called**
- 시스템은 OpenTelemetry SDK를 초기화해야 한다
- 시스템은 FastAPIInstrumentation을 설정해야 한다
- 시스템은 TraceExporter를 구성해야 한다
- 시스템은 (선택적으로) BatchSpanProcessor를 설정해야 한다

**WHEN a BaseAppException is raised**
- 시스템은 현재 span을 가져와야 하거나 새로 생성해야 한다
- 시스템은 span에 exception event를 기록해야 한다
- 시스템은 error_code, error_domain, status_code를 attribute로 추가해야 한다
- 시스템은 span status를 Error로 설정해야 한다

**WHEN an HTTP request is received**
- 시스템은 traceparent header를 추출해야 한다 (존재하는 경우)
- 시스템은 새로운 root span을 생성해야 하거나 기존 trace를 연결해야 한다
- 시스템은 HTTP method, URL, status code를 span attribute로 추가해야 한다

**WHEN a downstream service is called**
- 시스템은 traceparent header를 inject해야 한다
- 시스템은 client span을 생성해야 한다
- 시스템은 HTTP 요청 세부정보를 span에 기록해야 한다

**WHEN tracing export occurs**
- 시스템은 선택한 exporter (Jaeger/Zipkin/OTLP)로 trace를 전송해야 한다
- 시스템은 전송 실패 시 graceful degradation을 제공해야 한다
- 시스템은 배치 처리를 통해 성능을 최적화해야 한다

### State-Driven Requirements

**IF tracing is disabled**
- 시스템은 OpenTelemetry SDK를 초기화하지 않아야 한다
- 시스템은 어떠한 tracing overhead도 발생시키지 않아야 한다

**IF debug_mode is enabled**
- 시스템은 모든 trace를 수집해야 한다 (sampling rate=1.0)
- 시스템은 상세한 debugging 정보를 span에 포함해야 한다

**IF sampling_rate is less than 1.0**
- 시스템은 probability-based sampling을 적용해야 한다
- 시스템은 일관된 trace 추적을 위해 parent-based sampling을 사용해야 한다

**IF jaeger_exporter is enabled**
- 시스템은 Jaeger agent 또는 collector로 trace를 전송해야 한다
- 시스템은 Jaeger Thrift 또는 gRPC 프로토콜을 지원해야 한다

**IF otlp_exporter is enabled**
- 시스템은 OpenTelemetry Protocol (OTLP)로 trace를 전송해야 한다
- 시스템은 HTTP 또는 gRPC 전송을 지원해야 한다

### Unwanted Requirements

**THE SYSTEM SHALL NOT**
- 에러 핸들링 경로를 blocking해서는 안 된다
- Trace export 실패로 인해 요청 처리가 실패해서는 안 된다
- PII(개인정보)를 span에 포함해서는 안 된다 (자동 masking 필요)
- 1ms 이상의 요청 처리 지연을 유발해서는 안 된다
- 기존 SPEC-001, SPEC-MONITOR-002 기능을 깨뜨려서는 안 된다

### Optional Requirements

**WHERE POSSIBLE**
- 시스템은 Grafana Tempo와 호환되는 trace export를 제공할 수 있다
- 시스템은 trace를 로컬 파일로 export하는 기능을 제공할 수 있다
- 시스템은 custom span processor를 지원할 수 있다
- 시스템은 distributed context 전송을 위한 baggage propagation을 지원할 수 있다

---

## Architecture

### Component Overview

```
fastapi-error-codes (with distributed tracing)
├── SPEC-001 Components (Existing)
│   ├── BaseAppException
│   ├── ExceptionRegistry
│   ├── setup_exception_handler
│   └── ...
│
├── SPEC-MONITOR-002 Components (Existing)
│   ├── ErrorMetricsCollector
│   ├── PrometheusExporter
│   ├── SentryIntegration
│   └── ...
│
└── SPEC-TRACING-003 Components (New)
    ├── TracingConfig              # 추적 설정 관리
    ├── OpenTelemetryIntegration   # OpenTelemetry SDK 래퍼
    ├── ExceptionTracer            # 예외 자동 추적
    ├── setup_tracing              # FastAPI 통합 함수
    ├── JaegerExporter             # Jaeger export 지원
    ├── OTLPExporter               # OTLP export 지원
    └── TraceContextPropagator     # Trace context 전파
```

### Data Flow

```
HTTP Request (with traceparent header)
    ↓
FastAPIInstrumentation creates root span
    ↓
Request Processing (business logic)
    ↓
BaseAppException raised
    ↓
ExceptionTracer records exception event
    ↓
Span attributes: error_code, error_domain, status_code
    ↓
Span status: Error
    ↓
BatchSpanProcessor buffers spans
    ↓
Exporter sends to backend (Jaeger/Zipkin/OTLP)
```

### Trace Context Propagation

```
Service A (root span: trace_id=X, span_id=A)
    ↓ (inject traceparent header)
Service B (parent span: trace_id=X, parent_id=A, span_id=B)
    ↓ (inject traceparent header)
Service C (parent span: trace_id=X, parent_id=B, span_id=C)
    ↓
Error occurs → Exception event recorded in span C
```

### Span Attributes Schema

```python
# Base attributes (automatically added)
{
    "http.method": "GET",
    "http.url": "/api/users/123",
    "http.status_code": 401,
    "net.host.name": "api-service",
}

# Error attributes (added on exception)
{
    "error.code": 201,
    "error.domain": "AUTH",
    "error.type": "AuthRequiredException",
    "error.message": "Authentication required",
}

# Custom attributes (optional)
{
    "user.id": "123",
    "request.id": "abc-xyz",
}
```

---

## Technical Stack

### Required Dependencies

| Package                   | Version        | Purpose                             |
|---------------------------|----------------|-------------------------------------|
| opentelemetry-api         | >=1.20.0       | OpenTelemetry API                   |
| opentelemetry-sdk         | >=1.20.0       | OpenTelemetry SDK                   |
| opentelemetry-instrumentation | >=0.40b0   | Auto-instrumentation for FastAPI    |
| opentelemetry-semantic-conventions | >=0.40b0 | Standard attribute names |
| opentelemetry-exporter-jaeger | >=1.20.0    | Jaeger exporter                     |
| opentelemetry-exporter-otlp | >=1.20.0     | OTLP exporter                       |

### Optional Dependencies

| Package                   | Version        | Purpose                             |
|---------------------------|----------------|-------------------------------------|
| opentelemetry-exporter-zipkin | >=1.20.0    | Zipkin exporter                     |
| opentelemetry-instrumentation-httpx | >=0.40b0 | HTTP client instrumentation |

### Python Built-in Modules

- `contextvars` - Context propagation for async
- `uuid` - Trace ID generation
- `typing` - Type hints
- `dataclasses` - Configuration data classes

---

## Configuration

### TracingConfig

```python
@dataclass(frozen=True)
class TracingConfig:
    """분산 추적 설정"""

    # 기본 설정
    enabled: bool = True                      # 전체 활성화

    # Service identification
    service_name: str = "fastapi-service"    # 서비스 이름
    service_version: str = "1.0.0"           # 서비스 버전
    deployment_environment: str = "production" # 환경 (production/development)

    # Sampling 설정
    sampling_rate: float = 0.1               # Trace sampling rate (0.0-1.0)
    parent_based: bool = True                # Parent-based sampling

    # Exporter 설정
    exporter_type: str = "otlp"              # jaeger, otlp, zipkin, console
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    otlp_endpoint: str = "http://localhost:4317"
    otlp_headers: Dict[str, str] = field(default_factory=dict)

    # Batch processing
    batch_export_max_batch_size: int = 512
    batch_export_schedule_delay_millis: int = 5000
    batch_export_max_queue_size: int = 2048

    # Debugging
    debug_mode: bool = False                 # 상세 추적 활성화
    console_export: bool = False             # 콘솔에 trace 출력

    # PII 보호
    mask_pii_in_spans: bool = True          # 자동 PII masking

    # Class methods
    @classmethod
    def disabled(cls) -> "TracingConfig":
        """추적 비활성화 설정"""

    @classmethod
    def development(cls) -> "TracingConfig":
        """개발 환경 프리셋 (sampling_rate=1.0, console_export=True)"""

    @classmethod
    def production(cls, otlp_endpoint: str) -> "TracingConfig":
        """프로덕션 환경 프리셋"""

    @classmethod
    def from_environment(cls) -> "TracingConfig":
        """환경변수에서 로드"""
```

---

## Integration with SPEC-001 and SPEC-MONITOR-002

### setup_exception_handler Enhancement

기존 `setup_exception_handler` 함수에 선택적 추적 기능 추가:

```python
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None,
    metrics_config: Optional[MetricsConfig] = None,
    tracing_config: Optional[TracingConfig] = None,  # NEW
) -> None:
    """
    FastAPI exception handler 설정

    Args:
        app: FastAPI 앱
        config: 에러 핸들러 설정 (SPEC-001)
        metrics_config: 모니터링 설정 (SPEC-MONITOR-002, 선택)
        tracing_config: 분산 추적 설정 (SPEC-TRACING-003, 선택)
    """
    # 기존 핸들러 등록
    app.add_exception_handler(BaseAppException, base_exception_handler)

    # 메트릭 수집기 초기화 (선택)
    if metrics_config and metrics_config.enabled:
        setup_metrics(app, metrics_config)

    # 분산 추적 초기화 (선택)
    if tracing_config and tracing_config.enabled:
        setup_tracing(app, tracing_config)
```

### Exception Tracing

```python
def base_exception_handler(request: Request, exc: BaseAppException):
    # 기존 에러 응답 생성 (SPEC-001)
    error_response = create_error_response(exc, request)

    # 메트릭 수집 (SPEC-MONITOR-002, non-blocking)
    if _metrics_collector:
        try:
            _metrics_collector.record_async(exc, request)
        except Exception:
            pass

    # 분산 추적 기록 (SPEC-TRACING-003, non-blocking)
    if _exception_tracer:
        try:
            _exception_tracer.record_exception(exc, request)
        except Exception:
            pass

    return JSONResponse(content=error_response.model_dump(), ...)
```

### Trace ID to Metrics Link

Trace ID와 metrics 연동:

```python
# Prometheus metrics with trace_id label
fastapi_errors_total{
    error_code="201",
    error_domain="AUTH",
    trace_id="4bf92f3577b34da6a3ce929d0e0e4736"
}

# Sentry event with trace context
{
    "contexts": {
        "trace": {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7"
        }
    }
}
```

---

## Implementation Plan Summary

### Main Components

1. **TracingConfig** (src/fastapi_error_codes/tracing/config.py)
   - 설정 데이터 클래스
   - 환경변수 로드
   - 프리셋 (development/production)

2. **OpenTelemetryIntegration** (src/fastapi_error_codes/tracing/otel.py)
   - OpenTelemetry SDK 초기화
   - Resource 구성
   - TracerProvider 설정

3. **ExceptionTracer** (src/fastapi_error_codes/tracing/tracer.py)
   - 예외 자동 추적
   - Span attribute 설정
   - PII masking

4. **JaegerExporter** (src/fastapi_error_codes/tracing/jaeger.py)
   - Jaeger agent/collector exporter
   - Thrift/gRPC 프로토콜 지원

5. **OTLPExporter** (src/fastapi_error_codes/tracing/otlp.py)
   - OTLP over HTTP/gRPC
   - OpenTelemetry Collector 호환

6. **setup_tracing** (src/fastapi_error_codes/tracing/setup.py)
   - FastAPI 통합 함수
   - 전체 컴포넌트 초기화

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| 성능 영향 | High | 비동기 export, sampling, benchmarking |
| 메모리 사용 | Medium | 배치 처리, buffer size 제한 |
| Export 실패 | Low | Graceful degradation, 재시도 정책 |
| PII 유출 | High | 자동 masking, 필드별 제외 설정 |
| 기존 기능 호환성 | Medium | 통합 테스트, 점진적 롤아웃 |

---

## Dependencies

### Internal Dependencies

- SPEC-001: BaseAppException, setup_exception_handler
- SPEC-MONITOR-002: ErrorMetricsCollector (선택적 연동)
- ExceptionRegistry: error_code 정보 조회

### External Dependencies

```
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation>=0.40b0
opentelemetry-semantic-conventions>=0.40b0
opentelemetry-exporter-jaeger>=1.20.0
opentelemetry-exporter-otlp>=1.20.0
```

### Version Verification (2026-01-16)

- `opentelemetry-api 1.20.0` (2024-10 stable) ✓
- `opentelemetry-sdk 1.20.0` (2024-10 stable) ✓
- `opentelemetry-instrumentation 0.40b0` (2024-08 stable) ✓

---

## Documentation References

- [SPEC-001](.moai/specs/SPEC-001/spec.md) - 기본 에러 핸들러 구현
- [SPEC-MONITOR-002](.moai/specs/SPEC-MONITOR-002/spec.md) - 모니터링 시스템 구현
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)

---

## Change History

| Version | Date       | Changes                                  |
|---------|------------|------------------------------------------|
| 1.0.0   | 2026-01-16 | Initial SPEC-TRACING-003 documentation   |

---

## Traceability Tags

**TAG_BLOCK**: SPEC-TRACING-003

**Related Components**:
- tracing/config.py - TracingConfig
- tracing/otel.py - OpenTelemetryIntegration
- tracing/tracer.py - ExceptionTracer
- tracing/jaeger.py - JaegerExporter
- tracing/otlp.py - OTLPExporter
- tracing/setup.py - setup_tracing
