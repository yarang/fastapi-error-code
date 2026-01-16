# SPEC-MONITOR-002: 구현 계획

## Implementation Plan

### Overview

이 문서는 SPEC-MONITOR-002의 구현 계획, 기술 접근 방식, 마일스톤, 위험 관리 전략을 정의합니다.

---

## Implementation Approach

### Phase 1: Core Metrics Collection (Primary Goal)

**목표**: 에러 발생 횟수 추적의 핵심 기능 구현

**Components**:
- `ErrorMetricsCollector` - 스레드 안전한 메트릭 수집기
- `MetricsConfig` - 설정 관리
- 기본 데이터 구조 (ErrorEvent, MetricsSnapshot)

**Technical Approach**:
1. `threading.Lock`을 사용한 thread-safe 구현
2. `collections.defaultdict`로 error_code별 counting
3. Circular buffer for recent events (max_history_size 제한)
4. Non-blocking record() 메서드

**Milestone Criteria**:
- [ ] ErrorMetricsCollector가 에러 발생을 정확히 카운트
- [ ] 스레드 안전성 검증 (concurrent test 통과)
- [ ] 메모리 사용량이 제한 내 유지
- [ ] record() 메서드 실행 시간 < 100μs

---

### Phase 2: Prometheus Integration (Primary Goal)

**목표**: Prometheus metrics export 기능 구현

**Components**:
- `PrometheusExporter` - prometheus-client 래퍼
- `/metrics` endpoint - FastAPI route

**Technical Approach**:
1. `prometheus_client.Counter` for error counts
2. `prometheus_client.Histogram` for response times
3. Custom labels: error_code, error_domain, status_code
4. Separate Registry for isolation

**Metric Definitions**:

```python
# Counter: 총 에러 발생 횟수
fastapi_errors_total{
    error_code="201",
    error_domain="AUTH",
    status_code="401"
}

# Histogram: 에러 간격 시간
fastapi_errors_duration_seconds{
    error_code="201"
}

# Gauge: 현재 수집 중인 에러 수
fastapi_errors_active
```

**Milestone Criteria**:
- [ ] /metrics endpoint이 Prometheus text format 반환
- [ ] 모든 error_code가 별도 metric으로 노출
- [ ] Prometheus가 metric을 성공적으로 scrape
- [ ] Label cardinality가 과도하지 않음 (< 1000 unique)

---

### Phase 3: Sentry Integration (Secondary Goal)

**목표**: Sentry error tracking 자동 전송

**Components**:
- `SentryIntegration` - Sentry SDK wrapper
- PII masking logic
- Async transport

**Technical Approach**:
1. `sentry-sdk.init()` for SDK initialization
2. `sentry_sdk.capture_exception()` for error tracking
3. Custom beforeSend callback for PII masking
4. Async transport with aiohttp

**PII Masking Strategy**:

```python
# 자동 masking 대상 필드
PII_FIELDS = ["password", "token", "secret", "api_key", "credit_card"]

# 예외: detail에서 masking 제외 필드
MASKING_EXCLUDES = ["user_id"]  # ID는 masking 제외 가능
```

**Milestone Criteria**:
- [ ] Sentry DSN 연결 성공
- [ ] 에러가 Sentry 대시보드에 표시
- [ ] PII가 포함된 detail이 masked로 변환
- [ ] Sentry 전송 실패 시 에러 핸들링 동작에 영향 없음

---

### Phase 4: Dashboard API (Secondary Goal)

**목표**: JSON 기반 대시보드 데이터 API 제공

**Components**:
- `DashboardAPI` - FastAPI router
- 통계 집계 함수
- 응답 모델 (Pydantic)

**API Endpoints**:

| Endpoint           | Response Model              | Description                     |
|--------------------|-----------------------------|---------------------------------|
| GET /api/metrics   | MetricsSummary              | 전체 요약                        |
| GET /api/metrics/by-code/{code} | ErrorCodeStats | error_code별 통계 |
| GET /api/metrics/by-domain/{domain} | DomainStats | 도메인별 통계 |
| GET /api/metrics/recent | RecentErrorsResponse       | 최근 에러 목록                   |
| GET /api/metrics/top | TopErrorsResponse           | 가장 빈번한 에러 TOP 10          |

**Response Model Examples**:

```python
# GET /api/metrics
{
    "total_errors": 1234,
    "by_domain": {
        "AUTH": 456,
        "RESOURCE": 789
    },
    "top_errors": [
        {"error_code": 201, "count": 234},
        {"error_code": 301, "count": 123}
    ],
    "last_updated": "2026-01-16T10:00:00Z"
}

# GET /api/metrics/recent
{
    "recent_errors": [
        {
            "error_code": 201,
            "message": "Authentication required",
            "timestamp": "2026-01-16T09:59:59Z",
            "path": "/api/protected",
            "status_code": 401
        }
    ],
    "count": 10
}
```

**Milestone Criteria**:
- [ ] 모든 엔드포인트가 JSON 응답 반환
- [ ] 통계 계산이 정확함 (unit test 검증)
- [ ] OpenAPI 문서가 자동 생성됨
- [ ] 응답 시간 < 50ms

---

### Phase 5: Integration with SPEC-001 (Final Goal)

**목표**: 기존 에러 핸들러와 seamless 통합

**Components**:
- `setup_metrics()` - FastAPI integration 함수
- `setup_exception_handler()` 수정 (선택적 메트릭 추가)

**Integration Points**:

```python
# setup_exception_handler에 선택적 메트릭 추가
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None,
    metrics_config: Optional[MetricsConfig] = None,  # NEW
) -> None:
    # 기존 핸들러 등록 (SPEC-001)
    app.add_exception_handler(BaseAppException, base_exception_handler)

    # 메트릭 수집기 등록 (SPEC-MONITOR-002)
    if metrics_config and metrics_config.enabled:
        setup_metrics(app, metrics_config)
```

**Non-blocking Record**:

```python
# base_exception_handler 내부
def base_exception_handler(request: Request, exc: BaseAppException):
    # 에러 응답 생성 (기존 로직)
    response = create_error_response(exc, request)

    # 메트릭 수집 (non-blocking, fire-and-forget)
    if _metrics_collector:
        try:
            _metrics_collector.record_async(exc, request)
        except Exception:
            # 메트릭 실패가 핸들링을 방해하지 않음
            pass

    return JSONResponse(...)
```

**Milestone Criteria**:
- [ ] metrics_config 없이도 기존 코드가 정상 동작
- [ ] metrics_config 제공 시 자동 메트릭 수집
- [ ] 에러 응답 지연 시간이 1ms 미만 증가
- [ ] 통합 테스트 통과

---

## Architecture Design

### Module Structure

```
src/fastapi_error_codes/
├── metrics/                    # NEW: Monitoring module
│   ├── __init__.py
│   ├── collector.py            # ErrorMetricsCollector
│   ├── prometheus.py           # PrometheusExporter
│   ├── sentry.py               # SentryIntegration
│   ├── config.py               # MetricsConfig
│   ├── dashboard.py            # DashboardAPI
│   ├── models.py               # Metrics response models
│   └── setup.py                # setup_metrics()
│
├── base.py                     # Existing: BaseAppException
├── handlers.py                 # Existing: exception_handler (modified)
└── __init__.py                 # Package exports (updated)
```

### Class Hierarchy

```
ErrorMetricsCollector
├── record() - Synchronous record (fallback)
├── record_async() - Non-blocking async record
├── get_stats() - Get current statistics
├── get_recent_errors() - Get recent error events
└── reset() - Clear all metrics (for testing)

PrometheusExporter
├── init_metrics() - Initialize Prometheus metrics
├── inc_error_counter() - Increment error counter
├── observe_duration() - Record duration
└── generate_metrics() - Generate Prometheus text format

SentryIntegration
├── init() - Initialize Sentry SDK
├── capture_exception() - Send error to Sentry
├── mask_pii() - Mask PII in event data
└── shutdown() - Flush pending events

MetricsConfig (dataclass)
├── enabled: bool
├── prometheus_enabled: bool
├── sentry_enabled: bool
├── sentry_dsn: Optional[str]
├── mask_pii: bool
└── ... (other config fields)
```

---

## Performance Considerations

### Lock Strategy

**Problem**: 메트릭 수집 시 경합이 발생할 수 있음

**Solution**:
1. `threading.Lock` 대신 `threading.RLock` 사용 (nested lock 허용)
2. Lock scope 최소화 (critical section만 보호)
3. Lock-free 읽기 전용 연산 지원

```python
class ErrorMetricsCollector:
    def __init__(self):
        self._lock = threading.RLock()
        self._counts = defaultdict(int)  # write protected
        self._recent = []  # write protected

    def record(self, error_code: int):
        """Fast record with minimal lock scope"""
        with self._lock:
            self._counts[error_code] += 1
            self._recent.append(ErrorEvent(...))

    def get_stats(self) -> dict:
        """Lock-free read (copy-on-read)"""
        with self._lock:
            return dict(self._counts)  # copy and release
```

### Memory Management

**Problem**: 무제한 메트릭 저장으로 메모리 누수 발생 가능

**Solution**:
1. `max_history_size`로 recent events 제한
2. LRU eviction for old events
3. Periodic cleanup of old metrics

```python
def _add_to_recent(self, event: ErrorEvent):
    with self._lock:
        self._recent.append(event)
        if len(self._recent) > self._config.max_history_size:
            self._recent.pop(0)  # FIFO eviction
```

### Async Collection

**Problem**: 동기 메트릭 수집이 요청 지연 발생시킬 수 있음

**Solution**:
1. `record_async()` - fire-and-forget pattern
2. Background thread for Sentry 전송
3. In-memory queue for batching

```python
def record_async(self, exc: BaseAppException, request: Request):
    """Non-blocking record"""
    try:
        # In-memory append (O(1))
        self._queue.put_nowait((exc, request))
    except queue.Full:
        pass  # Drop if queue full (fail open)

async def _background_worker(self):
    """Background worker for processing queue"""
    while True:
        exc, request = await self._queue.get()
        self._record_sync(exc, request)  # Actual recording
```

---

## Testing Strategy

### Unit Tests

**Target Coverage**: 85%+

**Test Files**:
- `tests/metrics/test_collector.py` - ErrorMetricsCollector 테스트
- `tests/metrics/test_prometheus.py` - PrometheusExporter 테스트
- `tests/metrics/test_sentry.py` - SentryIntegration 테스트 (mock)
- `tests/metrics/test_config.py` - MetricsConfig 테스트
- `tests/metrics/test_dashboard.py` - DashboardAPI 테스트

**Key Test Cases**:

```python
# test_collector.py
def test_record_increments_count():
    collector = ErrorMetricsCollector()
    collector.record(201)
    assert collector.get_stats()[201] == 1

def test_thread_safety():
    collector = ErrorMetricsCollector()
    def record_errors():
        for _ in range(1000):
            collector.record(201)
    threads = [Thread(target=record_errors) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert collector.get_stats()[201] == 10000

def test_memory_limit():
    collector = ErrorMetricsCollector(
        config=MetricsConfig(max_history_size=100)
    )
    for i in range(200):
        collector.record(201)
    recent = collector.get_recent_errors()
    assert len(recent) <= 100
```

### Integration Tests

**Test Scenarios**:
1. End-to-end 에러 발생 → 메트릭 수집 → 조회
2. Prometheus scrape 테스트
3. Sentry 전송 테스트 (mock)
4. Dashboard API 응답 검증

```python
# test_integration.py
def test_error_to_metrics_flow():
    """Complete flow: error → metrics → dashboard"""
    app = FastAPI()
    config = ErrorHandlerConfig()
    metrics_config = MetricsConfig(enabled=True)

    setup_exception_handler(app, config, metrics_config)

    @app.get("/test")
    def test_route():
        raise AuthRequiredException()

    client = TestClient(app)

    # Trigger error
    response = client.get("/test")

    # Check metrics
    metrics_response = client.get("/api/metrics")
    assert metrics_response.status_code == 200
    data = metrics_response.json()
    assert data["total_errors"] == 1
    assert data["by_domain"]["AUTH"] == 1
```

### Performance Tests

**Benchmarks**:
- `record()` 실행 시간: target < 100μs
- `/metrics` 응답 시간: target < 50ms
- `/api/metrics` 응답 시간: target < 50ms
- 메모리 사용량: target < 10MB (10,000 events)

```python
# test_performance.py
def test_record_performance():
    collector = ErrorMetricsCollector()
    start = time.perf_counter()
    for _ in range(10000):
        collector.record(201)
    duration = time.perf_counter() - start
    avg_time = duration / 10000
    assert avg_time < 0.0001  # < 100μs
```

---

## Risk Management

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation | Medium | High | Async collection, benchmarks |
| Memory leak | Low | Medium | Size limits, cleanup |
| Sentry dependency failure | Low | Low | Optional, fallback handling |
| Thread safety issues | Low | High | Comprehensive tests, code review |
| PII exposure | Low | High | Automatic masking, audit |

### Mitigation Strategies

**1. Performance Degradation**
- Strategy: Async, non-blocking collection
- Validation: Performance benchmarks (target: <1ms overhead)
- Rollback: Disable metrics via config flag

**2. Memory Leak**
- Strategy: Size limits, periodic cleanup
- Validation: Memory profiling tests
- Monitoring: Memory usage dashboard

**3. Sentry Dependency**
- Strategy: Optional, isolated failures
- Validation: Mock tests, offline tests
- Fallback: Graceful degradation

**4. Thread Safety**
- Strategy: RLock, minimal lock scope
- Validation: Concurrent stress tests
- Code Review: Expert review required

**5. PII Exposure**
- Strategy: Automatic masking
- Validation: Security audit, PII scan tests
- Documentation: Clear PII handling guide

---

## Success Metrics

### Functional Metrics

- [ ] All EARS requirements implemented
- [ ] 85%+ test coverage achieved
- [ ] All acceptance criteria met
- [ ] Zero TRUST 5 violations

### Performance Metrics

- [ ] `record()` < 100μs average
- [ ] `/metrics` response < 50ms
- [ ] Memory usage < 10MB for 10K events
- [ ] Zero request latency impact (< 1ms overhead)

### Quality Metrics

- [ ] All linter checks pass (ruff, mypy)
- [ ] Security scan passes (bandit)
- [ ] Documentation complete
- [ ] Examples runnable

---

## Definition of Done

SPEC-MONITOR-002 is complete when:

1. **Code**: All Phase 1-5 components implemented
2. **Tests**: 85%+ coverage, all tests passing
3. **Documentation**: API docs, examples, README updated
4. **Integration**: SPEC-001 integration verified
5. **Performance**: Benchmarks meet targets
6. **Quality**: TRUST 5 compliance verified
7. **Review**: Code review completed and approved

---

## Traceability

**SPEC-MONITOR-002 TAG BLOCK**

**Requirements Traceability**:
- Ubiquitous → Phase 1 (Core), Phase 2 (Prometheus)
- Event-driven → Phase 1 (record), Phase 3 (Sentry), Phase 4 (APIables)
- State-driven → Phase 2 (config), Phase 3 (Sentry)
- Unwanted → Risk mitigation strategies
- Optional → Future enhancements

**Component Traceability**:
- ErrorMetricsCollector → Phase 1
- PrometheusExporter → Phase 2
- SentryIntegration → Phase 3
- DashboardAPI → Phase 4
- setup_metrics → Phase 5
