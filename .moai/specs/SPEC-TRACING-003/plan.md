# SPEC-TRACING-003: 구현 계획

## Implementation Plan

### Overview

이 문서는 SPEC-TRACING-003의 구현 계획, 기술 접근 방식, 마일스톤, 위험 관리 전략을 정의합니다.

---

## Implementation Approach

### Phase 1: Core Tracing Infrastructure (Primary Goal)

**목표**: OpenTelemetry SDK 통합의 핵심 기능 구현

**Components**:
- `TracingConfig` - 설정 관리 데이터 클래스
- `OpenTelemetryIntegration` - OpenTelemetry SDK 래퍼
- `ExceptionTracer` - 예외 자동 추적 기능

**Technical Approach**:
1. OpenTelemetry SDK 1.20+로 통합
2. FastAPIInstrumentation으로 자동 요청 추적
3. Context propagation을 위한 contextvars 활용
4. Non-blocking trace export

**Milestone Criteria**:
- [ ] TracingConfig가 모든 설정 옵션을 지원
- [ ] OpenTelemetry SDK가 성공적으로 초기화됨
- [ ] HTTP 요청이 자동으로 trace됨
- [ ] BaseAppException이 span에 기록됨
- [ ] Trace context가 정확히 전파됨

---

### Phase 2: Exporter Integration (Primary Goal)

**목표**: 다양한 백엔드로의 trace export 지원

**Components**:
- `JaegerExporter` - Jaeger agent/collector exporter
- `OTLPExporter` - OpenTelemetry Protocol exporter
- `ConsoleExporter` - 개발용 콘솔 exporter

**Technical Approach**:
1. `opentelemetry-exporter-jaeger`를 활용한 Jaeger export
2. `opentelemetry-exporter-otlp`를 활용한 OTLP export
3. BatchSpanProcessor로 배치 처리
4. Graceful degradation (export 실패 시 fallback)

**Exporter Architecture**:

```python
# Jaeger Agent/Collector Export
JaegerExporter
├── agent_mode: UDP to Jaeger Agent (port 6831)
├── collector_mode: HTTP to Jaeger Collector
└── protocol: Thrift compact

# OTLP Export
OTLPExporter
├── http_mode: HTTP/protobuf (port 4318)
├── grpc_mode: gRPC (port 4317)
└── protocol: OpenTelemetry Protocol

# Console Export (development)
ConsoleExporter
└── stdout: JSON formatted trace output
```

**Milestone Criteria**:
- [ ] Jaeger exporter가 trace를 성공적으로 전송
- [ ] OTLP exporter가 OpenTelemetry Collector와 통신
- [ ] Console exporter가 개발 중 trace를 표시
- [ ] Export 실패 시 graceful degradation 동작
- [ ] Batch processing이 성능을 최적화

---

### Phase 3: Exception Tracing (Secondary Goal)

**목표**: 예외 발생 시 자동 span 기록 및 속성 추가

**Components**:
- `ExceptionTracer` - 예외 자동 추적 로직
- Span attribute mapper - error_code, domain 매핑
- PII masking logic - 개인정보 자동 마스킹

**Technical Approach**:
1. 현재 span 가져오기 또는 생성
2. Exception event 기록
3. Span attributes 추가 (error_code, error_domain, status_code)
4. Stacktrace capture (선택적으로)
5. PII 자동 masking

**Exception Event Schema**:

```python
# Span Event (exception)
{
    "event_name": "exception",
    "timestamp": "2026-01-16T10:00:00Z",
    "attributes": {
        "exception.type": "AuthRequiredException",
        "exception.message": "Authentication required",
        "exception.stacktrace": "...",  # debug_mode=True인 경우
        "exception.escaped": "False"
    }
}

# Span Attributes
{
    "error.code": 201,
    "error.domain": "AUTH",
    "error.type": "AuthRequiredException",
    "error.message": "Authentication required",
}
```

**PII Masking Strategy**:

```python
# 자동 masking 대상 필드
PII_FIELDS = ["password", "token", "secret", "api_key", "credit_card", "ssn"]

# 예외: span에서 masking 제외 필드
MASKING_EXCLUDES = ["user_id", "request_id"]  # ID는 masking 제외 가능
```

**Milestone Criteria**:
- [ ] 모든 BaseAppException이 span에 기록됨
- [ ] error_code와 error_domain이 정확히 매핑됨
- [ ] PII가 포함된 detail이 masked로 변환
- [ ] Stacktrace가 debug_mode인 경우에만 capture됨
- [ ] Exception recording이 요청 처리를 방해하지 않음

---

### Phase 4: Trace Context Propagation (Secondary Goal)

**목표**: 서비스 간 trace context 전파 구현

**Components**:
- `TraceContextPropagator` - W3C Trace Context 표준 전파
- HTTP header injection/extraction
- Async context propagation

**Technical Approach**:
1. W3C Trace Context 표준 준수
2. `traceparent` header 활용
3. `tracestate` header 선택적 지원
4. contextvars를 통한 async context 유지

**Trace Context Format**:

```http
# Incoming Request
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

# Components:
# - version: 00
# - trace_id: 4bf92f3577b34da6a3ce929d0e0e4736
# - span_id: 00f067aa0ba902b7
# - trace_flags: 01 (sampled)

# Outgoing Request (downstream)
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-[new_span_id]-01
```

**Propagation Flow**:

```
Service A (root span)
    ↓ traceparent header injected
HTTP Request → Service B
    ↓ traceparent header extracted
Service B (child span)
    ↓ traceparent header injected
HTTP Request → Service C
    ↓ traceparent header extracted
Service C (grandchild span)
```

**Milestone Criteria**:
- [ ] traceparent header가 정확히 추출됨
- [ ] traceparent header가 정확히 주입됨
- [ ] Async context가 경계를 넘어 유지됨
- [ ] W3C Trace Context 표준을 준수
- [ ] 다른 OpenTelemetry instrumented 서비스와 호환

---

### Phase 5: Integration with SPEC-001 and SPEC-MONITOR-002 (Final Goal)

**목표**: 기존 에러 핸들러 및 모니터링 시스템과의 완벽한 통합

**Components**:
- `setup_tracing()` - FastAPI 통합 함수
- `setup_exception_handler()` 수정 (선택적 추적 추가)
- Trace ID ↔ Metrics 연동

**Integration Points**:

```python
# setup_exception_handler에 선택적 추적 추가
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None,
    metrics_config: Optional[MetricsConfig] = None,
    tracing_config: Optional[TracingConfig] = None,  # NEW
) -> None:
    # 기존 핸들러 등록 (SPEC-001)
    app.add_exception_handler(BaseAppException, base_exception_handler)

    # 메트릭 수집기 등록 (SPEC-MONITOR-002)
    if metrics_config and metrics_config.enabled:
        setup_metrics(app, metrics_config)

    # 분산 추적 초기화 (SPEC-TRACING-003)
    if tracing_config and tracing_config.enabled:
        setup_tracing(app, tracing_config)
```

**Non-blocking Exception Recording**:

```python
# base_exception_handler 내부
def base_exception_handler(request: Request, exc: BaseAppException):
    # 에러 응답 생성 (기존 로직)
    response = create_error_response(exc, request)

    # 메트릭 수집 (non-blocking, SPEC-MONITOR-002)
    if _metrics_collector:
        try:
            _metrics_collector.record_async(exc, request)
        except Exception:
            pass

    # 분산 추적 기록 (non-blocking, SPEC-TRACING-003)
    if _exception_tracer:
        try:
            _exception_tracer.record_exception(exc, request)
        except Exception:
            pass

    return JSONResponse(...)
```

**Trace ID to Metrics Link**:

```python
# Prometheus metrics with trace_id label
fastapi_errors_total{
    error_code="201",
    error_domain="AUTH",
    trace_id="4bf92f3577b34da6a3ce929d0e0e4736"  # NEW
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

**Milestone Criteria**:
- [ ] tracing_config 없이도 기존 코드가 정상 동작
- [ ] tracing_config 제공 시 자동 추적 활성화
- [ ] 에러 응답 지연 시간이 1ms 미만으로 증가
- [ ] Trace ID가 metrics와 연동됨
- [ ] 통합 테스트 통과

---

## Architecture Design

### Module Structure

```
src/fastapi_error_codes/
├── tracing/                    # NEW: Distributed tracing module
│   ├── __init__.py
│   ├── config.py               # TracingConfig
│   ├── otel.py                 # OpenTelemetryIntegration
│   ├── tracer.py               # ExceptionTracer
│   ├── jaeger.py               # JaegerExporter wrapper
│   ├── otlp.py                 # OTLPExporter wrapper
│   ├── propagator.py           # TraceContextPropagator
│   └── setup.py                # setup_tracing()
│
├── metrics/                    # Existing: Monitoring (SPEC-MONITOR-002)
│   ├── collector.py
│   ├── prometheus.py
│   ├── sentry.py
│   └── ...
│
├── base.py                     # Existing: BaseAppException (SPEC-001)
├── handlers.py                 # Existing: exception_handler (modified)
└── __init__.py                 # Package exports (updated)
```

### Class Hierarchy

```
TracingConfig (dataclass)
├── enabled: bool
├── service_name: str
├── sampling_rate: float
├── exporter_type: str
└── Class Methods:
    ├── disabled()
    ├── development()
    ├── production()
    └── from_environment()

OpenTelemetryIntegration
├── provider: TracerProvider
├── tracer: Tracer
├── resource: Resource
└── Methods:
    ├── initialize()
    ├── shutdown()
    ├── get_tracer()
    └── configure_exporter()

ExceptionTracer
├── tracer: Tracer
├── config: TracingConfig
├── pii_masker: PIIMasker
└── Methods:
    ├── record_exception()
    ├── add_span_attributes()
    ├── mask_pii()
    └── get_current_span()

JaegerExporter
├── agent_host: str
├── agent_port: int
├── exporter: JaegerExporter
└── Methods:
    ├── create_exporter()
    ├── configure()
    └── get_endpoint()

OTLPExporter
├── endpoint: str
├── headers: Dict[str, str]
├── exporter: OTLPSpanExporter
└── Methods:
    ├── create_exporter()
    ├── configure()
    └── get_endpoint()

TraceContextPropagator
├── propagator: TextMapPropagator
└── Methods:
    ├── inject()
    ├── extract()
    └── get_trace_context()
```

---

## Performance Considerations

### Sampling Strategy

**Problem**: 모든 요청을 trace하면 성능과 저장소 비용이 급증

**Solution**:
1. Probability-based sampling (sampling_rate)
2. Parent-based sampling (하위 span은 상속)
3. Debug mode에서는 100% sampling

```python
# Parent-based sampling
if parent_span:
    # Parent가 sampled되면 child도 sampled
    sampling_decision = parent_span.is_recording()
else:
    # Root span은 probability-based sampling
    sampling_decision = random() < sampling_rate
```

### Async Export

**Problem**: 동기 export는 요청 처리를 차단할 수 있음

**Solution**:
1. BatchSpanProcessor 사용
2. 별도 스레드에서 export 실행
3. Queue를 통한 비동기 처리

```python
# BatchSpanProcessor configuration
processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,        # 최대 큐 크기
    schedule_delay_millis=5000,  # 5초마다 export
    max_export_batch_size=512    # 배치당 최대 span 수
)
```

### Memory Management

**Problem**: 미 export된 trace가 메모리를 누적시킬 수 있음

**Solution**:
1. Queue 크기 제한 (max_queue_size)
2. Queue가 가득차면 oldest spans drop
3. 주기적인 buffer flush

```python
# Memory limits
MAX_QUEUE_SIZE = 2048
MAX_BATCH_SIZE = 512
SCHEDULE_DELAY_MS = 5000

# Drop strategy
if queue.full():
    # Drop oldest batch (fail-open)
    queue.pop(0)
```

### Context Propagation Overhead

**Problem**: Trace context 전파가 요청 간 overhead를 추가할 수 있음

**Solution**:
1. contextvars 사용 (zero-copy context switching)
2. Header injection/extraction 최적화
3. 필요한 경우에만 context 추적

```python
# Context propagation overhead
# Typical: < 10μs per context switch
# With contextvars: ~1-2μs (copy-on-write)

# Header injection overhead
# traceparent: ~40 bytes (fixed format)
# Injection/extraction: < 5μs
```

---

## Testing Strategy

### Unit Tests

**Target Coverage**: 85%+

**Test Files**:
- `tests/tracing/test_config.py` - TracingConfig 테스트
- `tests/tracing/test_otel.py` - OpenTelemetryIntegration 테스트
- `tests/tracing/test_tracer.py` - ExceptionTracer 테스트
- `tests/tracing/test_jaeger.py` - JaegerExporter 테스트 (mock)
- `tests/tracing/test_otlp.py` - OTLPExporter 테스트 (mock)
- `tests/tracing/test_propagator.py` - TraceContextPropagator 테스트

**Key Test Cases**:

```python
# test_tracer.py
def test_exception_records_to_span():
    """Exception이 span에 기록되는지 검증"""
    tracer = ExceptionTracer(mock_tracer, config)
    exc = AuthRequiredException()

    with start_as_current_span(mock_span):
        tracer.record_exception(exc, mock_request)

    # Verify span event
    mock_span.record_exception.assert_called_once()
    # Verify span attributes
    assert mock_span.set_attribute.call_count >= 3

def test_pii_masking_in_span_attributes():
    """PII가 span에서 masking되는지 검증"""
    tracer = ExceptionTracer(mock_tracer, config_with_masking)
    exc = CustomException(detail={"password": "secret123"})

    tracer.record_exception(exc, mock_request)

    # Verify password was masked
    call_args = mock_span.set_attribute.call_args_list
    password_attr = [call for call in call_args if "password" in str(call)]
    assert "***" in str(password_attr)

def test_trace_context_propagation():
    """Trace context가 정확히 전파되는지 검증"""
    propagator = TraceContextPropagator()
    carrier = {}

    # Inject context
    propagator.inject(carrier, context=mock_context)

    # Verify traceparent header
    assert "traceparent" in carrier
    assert carrier["traceparent"].startswith("00-")

    # Extract context
    extracted_context = propagator.extract(carrier)

    # Verify trace_id and span_id match
    assert get_current_span(extracted_context).get_span_context().trace_id == \
          get_current_span(mock_context).get_span_context().trace_id
```

### Integration Tests

**Test Scenarios**:
1. End-to-end 에러 발생 → trace 생성 → export
2. Jaeger export 테스트 (mock collector)
3. OTLP export 테스트 (mock collector)
4. Trace context propagation across services
5. SPEC-001 통합 테스트
6. SPEC-MONITOR-002 통합 테스트

```python
# test_integration.py
def test_error_to_trace_flow():
    """Complete flow: error → trace → export"""
    app = FastAPI()
    config = ErrorHandlerConfig()
    tracing_config = TracingConfig(
        enabled=True,
        exporter_type="console"  # 테스트용 콘솔 export
    )

    setup_exception_handler(app, config, tracing_config=tracing_config)

    @app.get("/test")
    def test_route():
        raise AuthRequiredException()

    client = TestClient(app)

    # Trigger error
    response = client.get("/test")

    # Verify response
    assert response.status_code == 401
    assert response.json()["error_code"] == 201

    # Verify trace was created (console export 확인)
    # 실제 테스트에서는 mock exporter를 사용하여 검증

def test_trace_context_across_services():
    """Trace context가 서비스 간에 전파되는지 검증"""
    # Service A
    app_a = FastAPI()
    setup_tracing(app_a, TracingConfig(service_name="service-a"))

    @app_a.get("/proxy")
    def proxy_service():
        # Service B로 요청 전송
        response = httpx.get("http://service-b/api")
        return response.json()

    # Service B
    app_b = FastAPI()
    setup_tracing(app_b, TracingConfig(service_name="service-b"))

    @app_b.get("/api")
    def api_service():
        raise AuthRequiredException()

    # Service A 요청 → Service B 에러
    client = TestClient(app_a)
    response = client.get("/proxy")

    # Verify same trace_id across services
    # 실제 테스트에서는 mock exporter로 trace_id 검증
```

### Performance Tests

**Benchmarks**:
- `record_exception()` 실행 시간: target < 100μs
- Trace context injection: target < 10μs
- Trace context extraction: target < 10μs
- Error handling overhead: target < 1ms

```python
# test_performance.py
def test_exception_recording_performance():
    """Exception recording 성능 측정"""
    tracer = ExceptionTracer(real_tracer, config)
    exc = AuthRequiredException()

    start = time.perf_counter()
    for _ in range(1000):
        with start_as_current_span():
            tracer.record_exception(exc, mock_request)
    duration = time.perf_counter() - start
    avg_time = duration / 1000

    assert avg_time < 0.0001  # < 100μs

def test_trace_context_propagation_performance():
    """Trace context propagation 성능 측정"""
    propagator = TraceContextPropagator()

    start = time.perf_counter()
    for _ in range(10000):
        carrier = {}
        propagator.inject(carrier)
        propagator.extract(carrier)
    duration = time.perf_counter() - start
    avg_time = duration / 10000

    assert avg_time < 0.00001  # < 10μs
```

---

## Risk Management

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation | Medium | High | Async export, sampling, benchmarks |
| Memory leak | Low | Medium | Queue limits, periodic cleanup |
| Export failure | Medium | Low | Graceful degradation, retries |
| PII exposure | Low | High | Automatic masking, audit |
| Compatibility issues | Low | Medium | Integration tests, gradual rollout |
| Vendor lock-in | Low | Low | Standard OpenTelemetry format |

### Mitigation Strategies

**1. Performance Degradation**
- Strategy: Async export, sampling, batching
- Validation: Performance benchmarks (target: <1ms overhead)
- Rollback: Disable tracing via config flag

**2. Memory Leak**
- Strategy: Queue size limits, periodic flush
- Validation: Memory profiling tests
- Monitoring: Memory usage dashboard

**3. Export Failure**
- Strategy: Graceful degradation, retries
- Validation: Mock tests, offline tests
- Fallback: Console export as backup

**4. PII Exposure**
- Strategy: Automatic masking
- Validation: Security audit, PII scan tests
- Documentation: Clear PII handling guide

**5. Compatibility Issues**
- Strategy: Integration tests, backward compatibility
- Validation: SPEC-001, SPEC-MONITOR-002 integration tests
- Rollback: Feature flag for gradual rollout

**6. Vendor Lock-in**
- Strategy: OpenTelemetry standard format
- Validation: Multiple exporter support (Jaeger, OTLP, Zipkin)
- Flexibility: Switch exporters via config

---

## Success Metrics

### Functional Metrics

- [ ] All EARS requirements implemented
- [ ] 85%+ test coverage achieved
- [ ] All acceptance criteria met
- [ ] Zero TRUST 5 violations

### Performance Metrics

- [ ] `record_exception()` < 100μs average
- [ ] Trace context injection/extraction < 10μs
- [ ] Error handling overhead < 1ms
- [ ] Memory usage < 20MB for typical workloads

### Quality Metrics

- [ ] All linter checks pass (ruff, mypy)
- [ ] Security scan passes (bandit)
- [ ] Documentation complete
- [ ] Examples runnable
- [ ] OpenTelemetry compliance verified

---

## Definition of Done

SPEC-TRACING-003 is complete when:

1. **Code**: All Phase 1-5 components implemented
2. **Tests**: 85%+ coverage, all tests passing
3. **Documentation**: API docs, examples, README updated
4. **Integration**: SPEC-001, SPEC-MONITOR-002 integration verified
5. **Performance**: Benchmarks meet targets
6. **Quality**: TRUST 5 compliance verified
7. **Review**: Code review completed and approved
8. **OpenTelemetry Compliance**: Standard format verified

---

## Traceability

**SPEC-TRACING-003 TAG BLOCK**

**Requirements Traceability**:
- Ubiquitous → Phase 1 (Core Infrastructure), Phase 5 (Integration)
- Event-driven → Phase 1 (setup), Phase 2 (export), Phase 3 (exception), Phase 4 (propagation)
- State-driven → Phase 2 (sampling), Phase 3 (debug_mode)
- Unwanted → Risk mitigation strategies
- Optional → Future enhancements

**Component Traceability**:
- TracingConfig → Phase 1
- OpenTelemetryIntegration → Phase 1
- ExceptionTracer → Phase 3
- JaegerExporter → Phase 2
- OTLPExporter → Phase 2
- TraceContextPropagator → Phase 4
- setup_tracing → Phase 5
