# SPEC-TRACING-003: 인수 기준

## Acceptance Criteria

이 문서는 SPEC-TRACING-003의 인수 기준(Acceptance Criteria), 테스트 시나리오, 품질 게이트를 정의합니다.

---

## Test Scenarios (Given-When-Then Format)

### Scenario 1: 기본 추적 초기화

**Background**:
- FastAPI 앱이 설정됨
- `setup_exception_handler`가 호출됨
- `TracingConfig(enabled=True)`로 추적 활성화

**Scenario 1.1: OpenTelemetry SDK 초기화**

```gherkin
GIVEN FastAPI 앱에 추적이 활성화됨
AND OpenTelemetry dependencies가 설치됨

WHEN setup_tracing이 호출됨

THEN OpenTelemetry SDK가 성공적으로 초기화됨
AND TracerProvider가 설정됨
AND FastAPIInstrumentation이 등록됨
AND 기본 Resource가 구성됨 (service_name, service_version)
```

**Scenario 1.2: HTTP 요청 자동 추적**

```gherkin
GIVEN FastAPI 앱에 추적이 활성화됨
AND @app.get 엔드포인트가 정의됨

WHEN 클라이언트가 GET /test 요청을 보냄

THEN root span이 생성됨
AND span.name이 "GET /test"임
AND span에 http.method="GET" attribute가 포함됨
AND span에 http.url attribute가 포함됨
AND span에 http.status_code attribute가 포함됨
AND 추적 활성화로 인한 지연 시간은 1ms 미만임
```

---

### Scenario 2: 예외 자동 추적

**Background**:
- 추적이 활성화됨
- BaseAppException이 등록됨

**Scenario 2.1: BaseAppException 발생 시 span 기록**

```gherkin
GIVEN FastAPI 앱에 추적이 활성화됨
AND @register_exception으로 AuthRequiredException이 등록됨 (error_code=201)

WHEN /protected 엔드포인트에서 AuthRequiredException이 발생함

THEN 현재 span에 exception event가 기록됨
AND span attributes에 error.code=201이 포함됨
AND span attributes에 error.domain="AUTH"가 포함됨
AND span attributes에 error.type="AuthRequiredException"이 포함됨
AND span status가 Error로 설정됨
AND stacktrace가 debug_mode=True인 경우에만 포함됨
```

**Expected Span Event**:
```python
{
    "event_name": "exception",
    "attributes": {
        "exception.type": "AuthRequiredException",
        "exception.message": "Authentication required",
        "exception.stacktrace": "..."  # debug_mode=True인 경우만
    }
}
```

**Expected Span Attributes**:
```python
{
    "error.code": 201,
    "error.domain": "AUTH",
    "error.type": "AuthRequiredException",
    "error.message": "Authentication required",
}
```

**Scenario 2.2: PII 자동 마스킹**

```gherkin
GIVEN 추적이 활성화됨
AND mask_pii_in_spans=True로 설정됨

WHEN detail에 password="secret123"이 포함된 에러가 발생함

THEN span attributes에서 password는 "***"로 마스킹됨
AND 다른 필드는 정상적으로 포함됨
AND masking 처리는 10μs 미만으로 완료됨
```

---

### Scenario 3: Trace Context Propagation

**Background**:
- 다중 서비스 환경
- 각 서비스에 추적이 활성화됨

**Scenario 3.1: Trace Context 추출 및 주입**

```gherkin
GIVEN Service A에서 추적이 활성화됨
AND Service A에서 HTTP 요청이 수신됨
AND 요청에 traceparent header가 포함됨

WHEN Service A가 요청을 처리함

THEN traceparent header에서 trace_id와 span_id가 추출됨
AND 새로운 span이 생성됨
AND 새 span의 parent_id가 추출된 span_id로 설정됨
AND 모든 span이 동일한 trace_id를 공유함
```

**Expected traceparent Format**:
```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

**Scenario 3.2: 다운스트림 서비스 호출 시 Context 전파**

```gherkin
GIVEN Service A에서 active span이 존재함
AND Service A가 Service B로 HTTP 요청을 보냄

WHEN HTTP 요청이 전송됨

THEN traceparent header가 자동으로 주입됨
AND traceparent header가 현재 span context를 포함함
AND Service B가 동일한 trace_id로 새 span을 생성함
AND Service B span의 parent_id가 Service A span_id로 설정됨
```

**Expected Propagation Flow**:
```
Service A (root span: trace_id=X, span_id=A)
    ↓ inject traceparent header
HTTP Request: traceparent: 00-X-A-01
    ↓ extract traceparent header
Service B (child span: trace_id=X, parent_id=A, span_id=B)
```

**Scenario 3.3: Async Context Propagation**

```gherkin
GIVEN async/await 패턴으로 요청이 처리됨
AND active span이 존재함

WHEN 요청 처리가 다른 async context로 전환됨

THEN trace context가 async 경계를 넘어 유지됨
AND get_current_span()이 모든 async context에서 동일한 span을 반환함
AND contextvars를 통한 zero-copy propagation이 발생함
```

---

### Scenario 4: Exporter Integration

**Background**:
- 추적이 활성화됨
- Exporter가 구성됨

**Scenario 4.1: Jaeger Export**

```gherkin
GIVEN jaeger_exporter가 활성화됨
AND Jaeger agent가 localhost:6831에서 실행 중임

WHEN trace가 생성됨

THEN span이 Jaeger agent로 전송됨
AND Jaeger UI에서 trace를 조회할 수 있음
AND trace_id, span_id, parent_id가 정확히 표시됨
AND 모든 span attributes가 포함됨
```

**Expected Jaeger Output**:
```python
# Jaeger agent receives span
{
    "traceID": "4bf92f3577b34da6a3ce929d0e0e4736",
    "spanID": "00f067aa0ba902b7",
    "parentSpanID": "...",
    "operationName": "GET /api/users",
    "startTime": 1642348800000000,
    "duration": 1500000,  # microseconds
    "tags": [
        {"key": "http.method", "value": "GET"},
        {"key": "http.url", "value": "/api/users"},
        {"key": "error.code", "value": "201"}
    ]
}
```

**Scenario 4.2: OTLP Export**

```gherkin
GIVEN otlp_exporter가 활성화됨
AND OTLP endpoint가 http://localhost:4317로 설정됨

WHEN trace가 생성됨

THEN span이 OTLP format으로 변환됨
AND OpenTelemetry Collector로 전송됨
AND Collector가 trace를 성공적으로 수신함
AND Trace가 지원되는 백엔드(Jaeger/Tempo/Zipkin)로 전달됨
```

**Scenario 4.3: Console Export (Development)**

```gherkin
GIVEN console_export=True로 설정됨 (development mode)

WHEN trace가 생성됨

THEN span이 JSON format으로 stdout에 출력됨
AND trace_id, span_id, attributes가 사람이 읽을 수 있는 형식임
AND 개발 중 실시간으로 trace를 확인할 수 있음
```

**Expected Console Output**:
```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "parent_span_id": null,
  "name": "GET /api/users",
  "kind": "SERVER",
  "start_time": "2026-01-16T10:00:00Z",
  "duration_ns": 1500000000,
  "attributes": {
    "http.method": "GET",
    "http.url": "/api/users",
    "http.status_code": 200
  }
}
```

**Scenario 4.4: Export 실패 시 Graceful Degradation**

```gherkin
GIVEN otlp_exporter가 활성화되었지만 네트워크가 차단됨

WHEN trace가 생성되고 export가 시도됨

THEN 요청 처리는 정상적으로 완료됨
AND Export 실패가 로그에 기록됨
AND 애플리케이션이 계속正常运行됨
AND 다음 export 시도가 예약됨 (retry)
```

---

### Scenario 5: Sampling

**Background**:
- 추적이 활성화됨
- Sampling rate가 구성됨

**Scenario 5.1: Probability-based Sampling**

```gherkin
GIVEN sampling_rate=0.1로 설정됨 (10% sampling)

WHEN 100개의 요청이 처리됨

THEN 약 10개의 요청이 trace됨 (±20% 오차 허용)
AND Trace되지 않은 요청은 zero overhead를 가짐
AND Sampling decision은 요청 처리 시작 시 결정됨
```

**Scenario 5.2: Parent-based Sampling**

```gherkin
GIVEN parent_based=True로 설정됨
AND Root span이 sampled됨

WHEN Root span의 child spans이 생성됨

THEN 모든 child spans이 자동으로 sampled됨
AND Trace completeness가 보장됨 (모든 span 또는 모든 span 없음)
AND Parent span이 sampled되지 않으면 모든 children도 unsampled됨
```

**Scenario 5.3: Debug Mode에서 100% Sampling**

```gherkin
GIVEN debug_mode=True로 설정됨
AND sampling_rate=0.1로 설정됨

WHEN debug_mode가 활성화된 상태에서 요청이 처리됨

THEN 모든 요청이 trace됨 (sampling_rate 무시)
AND 상세한 debugging 정보가 span에 포함됨
AND stacktrace가 모든 exception에 capture됨
```

---

### Scenario 6: 비활성화 상태

**Scenario 6.1: 추적 비활성화 시 동작**

```gherkin
GIVEN TracingConfig(enabled=False)로 설정됨

WHEN BaseAppException이 발생함

THEN 추적이 수행되지 않음
AND OpenTelemetry SDK가 초기화되지 않음
AND 에러 핸들링은 정상적으로 동작함
AND 어떠한 tracing overhead도 발생하지 않음
```

---

### Scenario 7: SPEC-001 통합

**Scenario 7.1: 기존 핸들러와의 호환성**

```gherkin
GIVEN SPEC-001의 setup_exception_handler가 사용됨
AND tracing_config를 제공하지 않음

WHEN BaseAppException이 발생함

THEN 에러 응답이 정상적으로 반환됨
AND 추적이 수행되지 않음 (명시적 비활성화)
AND 기존 동작에 어떠한 변경도 없음
```

**Scenario 7.2: 추적 활성화 시 통합**

```gherkin
GIVEN SPEC-001의 setup_exception_handler가 호출됨
AND tracing_config=TracingConfig(enabled=True) 제공됨

WHEN BaseAppException이 발생함

THEN 에러 응답이 기존과 동일하게 반환됨
AND Trace가 자동으로 생성됨
AND Exception이 span에 기록됨
AND 응답 지연 시간이 1ms 미만으로 증가함
```

---

### Scenario 8: SPEC-MONITOR-002 통합

**Scenario 8.1: Trace ID와 Metrics 연동**

```gherkin
GIVEN SPEC-001, SPEC-MONITOR-002, SPEC-TRACING-003이 모두 활성화됨

WHEN BaseAppException이 발생함

THEN Prometheus metrics에 trace_id label이 포함됨
AND Sentry event에 trace context가 포함됨
AND Dashbaord API에서 trace_id를 조회할 수 있음
AND Metrics와 Trace가 연동되어 분석 가능함
```

**Expected Prometheus Metric**:
```promql
fastapi_errors_total{
    error_code="201",
    error_domain="AUTH",
    trace_id="4bf92f3577b34da6a3ce929d0e0e4736"
}
```

**Expected Sentry Context**:
```json
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

## Quality Gates

### TRUST 5 Framework Compliance

**Test-first Pillar**:
- [ ] 85%+ 테스트 커버리지 달성
- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] 성능 벤치마크 통과

**Readable Pillar**:
- [ ] Ruff linter 통과 (zero warnings)
- [ ] 명확한 네이밍 컨벤션 준수
- [ ] 문서화된 모든 public API
- [ ] Type hints 완비

**Unified Pillar**:
- [ ] Black formatter 통과
- [ ] 일관된 코드 스타일
- [ ] 일관된 import 순서

**Secured Pillar**:
- [ ] PII masking 검증
- [ ] Trace context injection 검증
- [ ] Export failure handling 검증
- [ ] 스레드 안전성 검증

**Trackable Pillar**:
- [ ] Git commit 메시지 표준 준수
- [ ] 명확한 변경 이력
- [ ] Traceability TAG BLOCK 포함

---

## Performance Benchmarks

### 실행 시간 기준

| Operation                        | Target  | Maximum |
|----------------------------------|---------|---------|
| `record_exception()`             | < 50μs  | < 100μs |
| Trace context injection          | < 5μs   | < 10μs  |
| Trace context extraction         | < 5μs   | < 10μs  |
| Error handling overhead          | < 0.5ms | < 1ms   |
| Span creation (FastAPI request)  | < 10μs  | < 50μs  |

### 메모리 사용 기준

| Metric                      | Target  | Maximum |
|-----------------------------|---------|---------|
| Base memory usage           | < 10MB  | < 20MB  |
| 10,000 unexported spans     | < 15MB  | < 30MB  |
| Per-span overhead           | < 1KB   | < 2KB   |

### 부하 테스트

```gherkin
Scenario: 높은 부하에서의 추적 성능

GIVEN 1000 RPS의 요청 속도로 에러가 발생함
AND 추적이 활성화됨 (sampling_rate=0.1)
AND Jaeger exporter가 구성됨

WHEN 10분 동안 지속됨

THEN 모든 요청이 정상적으로 처리됨
AND 샘플링된 trace만 export됨 (약 10%)
AND 메모리 사용량이 안정적임 (leak 없음)
AND 응답 시간이 기준 내 유지됨
AND Export queue가 overflow되지 않음
```

---

## Security Testing

### PII Masking Verification

```gherkin
Scenario: Span에서 PII 자동 마스킹

GIVEN mask_pii_in_spans=True 설정
AND detail에 다음 PII가 포함됨:
  - password: "secret123"
  - token: "abc123xyz"
  - api_key: "sk-1234"

WHEN 에러가 기록됨

THEN span attributes에서 PII가 마스킹됨:
  - password: "***"
  - token: "***"
  - api_key: "***"
AND masking은 10μs 미만으로 완료됨
```

### Trace Context Injection Validation

```gherkin
Scenario: Trace Context injection 안전성

GIVEN 외부에서 오는 traceparent header가 포함된 요청

WHEN traceparent가 추출됨

THEN traceparent format이 검증됨
AND 잘못된 format인 경우 무시됨 (새 trace 생성)
AND trace_id 길이가 32 hex characters인지 확인됨
AND span_id 길이가 16 hex characters인지 확인됨
```

---

## Edge Cases

### Edge Case 1: No Active Span

```gherkin
GIVEN 추적이 비활성화됨
AND ExceptionTracer.record_exception()가 호출됨

WHEN active span이 존재하지 않음

THEN 에러가 발생하지 않음 (graceful handling)
AND Logging에 경고 메시지가 기록됨
AND 애플리케이션이 계속正常运行됨
```

### Edge Case 2: Exporter Unavailable

```gherkin
GIVEN Jaeger exporter가 구성됨
AND Jaeger agent가 실행 중이 아님

WHEN trace export가 시도됨

THEN Export 실패가 silently 무시됨
AND 다음 export 시도가 예약됨
AND 내부 queue가 최대 크기로 제한됨
AND Queue가 가득차면 oldest spans가 drop됨
```

### Edge Case 3: Malformed Trace Context

```gherkin
GIVEN 요청에 잘못된 traceparent header가 포함됨
  - traceparent: "invalid-format"

WHEN trace context가 추출됨

THEN 잘못된 format이 감지됨
AND 새로운 trace가 시작됨 (fallback)
AND Logging에 경고 메시지가 기록됨
AND 요청 처리가 정상적으로 계속됨
```

### Edge Case 4: Sampling Rate Edge Cases

```gherkin
GIVEN sampling_rate=0.0으로 설정됨

WHEN 요청이 처리됨

THEN 어떠한 요청도 trace되지 않음
AND Zero overhead가 보장됨

GIVEN sampling_rate=1.0으로 설정됨

WHEN 요청이 처리됨

THEN 모든 요청이 trace됨
AND 메모리 사용량이 모니터링됨
```

### Edge Case 5: Concurrent Span Creation

```gherkin
GIVEN 100개의 concurrent 요청이 동시에 도착함
AND 각 요청이 별도의 span을 생성함

WHEN 모든 요청이 처리됨

THEN 모든 span이 올바르게 생성됨
AND 각 span이 고유한 span_id를 가짐
AND Trace context가 올바르게 전파됨
AND Race condition이 발생하지 않음
```

---

## Integration Test Matrix

| Scenario                      | Jaeger | OTLP | Console | Disabled | Debug Mode |
|-------------------------------|--------|------|---------|----------|------------|
| Basic span creation           | ✓      | ✓    | ✓       | -        | ✓          |
| Exception recording           | ✓      | ✓    | ✓       | -        | ✓          |
| PII masking                   | ✓      | ✓    | ✓       | -        | ✓          |
| Trace context propagation     | ✓      | ✓    | ✓       | -        | ✓          |
| Sampling                      | ✓      | ✓    | ✓       | -        | ✓          |
| Export failure handling       | ✓      | ✓    | ✓       | -        | ✓          |
| No overhead when disabled     | -      | -    | -       | ✓        | -          |
| SPEC-001 compatibility        | ✓      | ✓    | ✓       | ✓        | ✓          |
| SPEC-MONITOR-002 integration  | ✓      | ✓    | ✓       | -        | ✓          |
| Performance (benchmark)       | ✓      | ✓    | ✓       | ✓        | ✓          |
| Edge cases                    | ✓      | ✓    | ✓       | ✓        | ✓          |

---

## Definition of Done

SPEC-TRACING-003 is **ACCEPTED** when:

1. **Functional Requirements**: All EARS requirements implemented
2. **Test Coverage**: 85%+ coverage achieved
3. **Test Scenarios**: All Gherkin scenarios passing
4. **Performance**: All benchmarks passing
5. **Security**: PII masking verified, trace context injection validated
6. **Integration**: SPEC-001, SPEC-MONITOR-002 integration verified
7. **Documentation**: API docs complete, examples runnable
8. **Quality Gates**: TRUST 5 compliance verified
9. **OpenTelemetry Compliance**: Standard format verified
10. **Export Verification**: At least one exporter (Jaeger/OTLP) verified

---

## Traceability

**SPEC-TRACING-003 TAG BLOCK**

**Requirements to Test Mapping**:
- Ubiquitous → Scenarios 1, 6
- Event-driven → Scenarios 1.1, 1.2, 2.1, 3.1, 3.2, 4.1, 4.2
- State-driven → Scenarios 5.1, 5.2, 5.3, 6.1
- Unwanted → Security tests, Edge cases
- Optional → Future enhancements (out of scope for acceptance)

**Acceptance to Implementation Mapping**:
- TracingConfig → Scenarios 1.1, 6.1
- OpenTelemetryIntegration → Scenarios 1.1, 1.2
- ExceptionTracer → Scenarios 2, 7, 8
- JaegerExporter → Scenario 4.1
- OTLPExporter → Scenario 4.2
- TraceContextPropagator → Scenarios 3, 8
- Integration → Scenarios 6, 7, 8
