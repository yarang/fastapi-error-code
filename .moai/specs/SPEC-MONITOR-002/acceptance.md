# SPEC-MONITOR-002: 인수 기준

## Acceptance Criteria

이 문서는 SPEC-MONITOR-002의 인수 기준(Acceptance Criteria), 테스트 시나리오, 품질 게이트를 정의합니다.

---

## Test Scenarios (Given-When-Then Format)

### Scenario 1: 에러 발생 시 자동 메트릭 수집

**Background**:
- FastAPI 앱이 설정됨
- `setup_exception_handler`가 호출됨
- `MetricsConfig(enabled=True)`로 메트릭 활성화

**Scenario 1.1: BaseAppException 발생 시 카운트 증가**

```gherkin
GIVEN FastAPI 앱에 메트릭 수집이 활성화됨
AND @register_exception으로 AuthRequiredException이 등록됨 (error_code=201)

WHEN /protected 엔드포인트에서 AuthRequiredException이 발생함

THEN error_code 201의 count가 1 증가함
AND total_errors가 1 증가함
AND AUTH 도메인의 count가 1 증가함
AND 메트릭 수집 시간은 1ms 미만임
```

**Scenario 1.2: 동시 에러 발생 시 스레드 안전성**

```gherkin
GIVEN FastAPI 앱에 메트릭 수집이 활성화됨
AND 10개의 스레드가 동시에 error_code=201을 1000번씩 발생시킴

WHEN 모든 스레드가 완료됨

THEN error_code 201의 총 count는 정확히 10,000임
AND 레이스 컨디션이 발생하지 않음
AND 데이터 손실이 없음
```

---

### Scenario 2: Prometheus Metrics Export

**Background**:
- Prometheus metrics가 활성화됨
- `/metrics` 엔드포인트가 등록됨

**Scenario 2.1: 기본 Prometheus metrics 형식**

```gherkin
GIVEN Prometheus metrics가 활성화됨
AND error_code 201이 5번 발생함

WHEN 클라이언트가 /metrics 엔드포인트를 요청함

THEN HTTP 200 상태 코드가 반환됨
AND Content-Type은 text/plain임
AND 응답은 Prometheus text format을 따름
AND fastapi_errors_total{error_code="201"} 메트릭이 5로 표시됨
AND fastapi_errors_total 메트릭에 error_domain 라벨이 포함됨
```

**Expected Response**:
```text
# HELP fastapi_errors_total Total number of application errors
# TYPE fastapi_errors_total counter
fastapi_errors_total{error_code="201",error_domain="AUTH",status_code="401"} 5.0
```

**Scenario 2.2: Prometheus scrape 성공**

```gherkin
GIVEN Prometheus 서버가 configured됨
AND /metrics 엔드포인트가 제공됨

WHEN Prometheus가 /metrics를 scrape함

THEN scrape가 성공함 (HTTP 200)
AND 모든 error_code가 별도 시계열로 노출됨
AND label cardinality가 1000 미만임
```

---

### Scenario 3: Sentry Error Tracking

**Background**:
- Sentry SDK가 활성화됨
- Sentry DSN이 설정됨

**Scenario 3.1: Sentry에 에러 전송**

```gherkin
GIVEN Sentry가 활성화됨 (sentry_dsn 제공됨)
AND Sentry SDK가 초기화됨

WHEN BaseAppException이 발생함

THEN 에러 이벤트가 Sentry로 전송됨
AND Sentry 대시보드에 에러가 표시됨
AND error_code, error_domain이 tag로 포함됨
AND stacktrace가 포함됨 (debug_mode=True인 경우)
```

**Scenario 3.2: PII 자동 마스킹**

```gherkin
GIVEN Sentry가 활성화됨
AND mask_pii=True로 설정됨

WHEN detail에 password="secret123"이 포함된 에러가 발생함

THEN Sentry로 전송되는 이벤트에서 password는 "***"로 마스킹됨
AND 다른 필드는 정상적으로 포함됨
```

**Scenario 3.3: Sentry 전송 실패 시 fallback**

```gherkin
GIVEN Sentry가 활성화되었지만 네트워크가 차단됨

WHEN BaseAppException이 발생함

THEN 에러 핸들러는 정상적으로 응답함 (HTTP 400)
AND Sentry 전송 실패가 요청에 영향을 주지 않음
AND 로그에 Sentry 전송 실패가 기록됨
```

---

### Scenario 4: Dashboard API

**Background**:
- Dashboard API가 활성화됨
- 다양한 error가 발생했음

**Scenario 4.1: 전체 메트릭 요약**

```gherkin
GIVEN 다양한 error가 발생했음 (AUTH: 10, RESOURCE: 5)

WHEN 클라이언트가 GET /api/metrics를 요청함

THEN HTTP 200과 JSON 응답이 반환됨
AND total_errors는 15임
AND by_domain은 {"AUTH": 10, "RESOURCE": 5}임
AND top_errors가 발생 횟수 순으로 정렬됨
AND last_updated 타임스탬프가 포함됨
```

**Expected Response**:
```json
{
    "total_errors": 15,
    "by_domain": {
        "AUTH": 10,
        "RESOURCE": 5
    },
    "top_errors": [
        {"error_code": 201, "count": 8},
        {"error_code": 202, "count": 2},
        {"error_code": 301, "count": 5}
    ],
    "last_updated": "2026-01-16T10:00:00Z"
}
```

**Scenario 4.2: 특정 error_code 통계**

```gherkin
GIVEN error_code 201이 10번 발생했음

WHEN 클라이언트가 GET /api/metrics/by-code/201를 요청함

THEN HTTP 200과 JSON 응답이 반환됨
AND error_code는 201임
AND count는 10임
AND error_domain은 "AUTH"임
AND first_seen과 last_seen 타임스탬프가 포함됨
```

**Scenario 4.3: 도메인별 통계**

```gherkin
GIVEN AUTH 도메인 에러가 총 25번 발생했음

WHEN 클라이언트가 GET /api/metrics/by-domain/AUTH를 요청함

THEN HTTP 200과 JSON 응답이 반환됨
AND domain은 "AUTH"임
AND total_count는 25임
AND error_codes 목록이 포함됨
```

**Scenario 4.4: 최근 에러 목록**

```gherkin
GIVEN 최근 10개의 에러가 발생했음

WHEN 클라이언트가 GET /api/metrics/recent를 요청함

THEN HTTP 200과 JSON 응답이 반환됨
AND recent_errors 배열이 최근 순으로 정렬됨
AND 각 에러는 error_code, message, timestamp, path를 포함함
AND count는 최대 10개 (max_history_size)임
```

---

### Scenario 5: 비활성화 상태

**Scenario 5.1: 메트릭 비활성화 시 동작**

```gherkin
GIVEN MetricsConfig(enabled=False)로 설정됨

WHEN BaseAppException이 발생함

THEN 메트릭이 수집되지 않음
AND /metrics 엔드포인트가 존재하지 않음
AND /api/metrics/* 엔드포인트가 존재하지 않음
AND 에러 핸들링은 정상적으로 동작함
```

---

### Scenario 6: SPEC-001 통합

**Scenario 6.1: 기존 핸들러와의 호환성**

```gherkin
GIVEN SPEC-001의 setup_exception_handler가 사용됨
AND metrics_config를 제공하지 않음

WHEN BaseAppException이 발생함

THEN 에러 응답이 정상적으로 반환됨
AND 메트릭 수집이 수행되지 않음 (명시적 비활성화)
AND 기존 동작에 어떠한 변경도 없음
```

**Scenario 6.2: 메트릭 활성화 시 통합**

```gherkin
GIVEN SPEC-001의 setup_exception_handler가 호출됨
AND metrics_config=MetricsConfig(enabled=True) 제공됨

WHEN BaseAppException이 발생함

THEN 에러 응답이 기존과 동일하게 반환됨
AND 메트릭이 자동으로 수집됨
AND 응답 지연 시간이 1ms 미만으로 증가함
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
- [ ] Sentry DSN 검증
- [ ] 스레드 안전성 검증
- [ ] 메모리 누수 검증

**Trackable Pillar**:
- [ ] Git commit 메시지 표준 준수
- [ ] 명확한 변경 이력
- [ ] 이슈 트래킹 연동

---

## Performance Benchmarks

### 실행 시간 기준

| Operation               | Target  | Maximum |
|-------------------------|---------|---------|
| `record()`              | < 50μs  | < 100μs |
| `record_async()`        | < 10μs  | < 50μs  |
| `/metrics` response     | < 30ms  | < 50ms  |
| `/api/metrics` response | < 30ms  | < 50ms  |
| Error handling overhead | < 0.5ms | < 1ms   |

### 메모리 사용 기준

| Metric                           | Target  | Maximum |
|----------------------------------|---------|---------|
| Base memory usage                | < 5MB   | < 10MB  |
| 10,000 events stored             | < 8MB   | < 15MB  |
| Per-event overhead               | < 500B  | < 1KB   |

### 부하 테스트

```gherkin
Scenario: 높은 부하에서의 메트릭 수집

GIVEN 1000 RPS의 요청 속도로 에러가 발생함
AND 메트릭 수집이 활성화됨

WHEN 10분 동안 지속됨

THEN 모든 에러가 정확히 카운트됨
AND 메모리 사용량이 안정적임 (leak 없음)
AND 응답 시간이 기준 내 유지됨
AND CPU 사용량이 50% 미만임
```

---

## Security Testing

### PII Masking Verification

```gherkin
Scenario: PII 필드 자동 마스킹

GIVEN mask_pii=True 설정
AND detail에 다음 PII가 포함됨:
  - password: "secret123"
  - token: "abc123xyz"
  - api_key: "sk-1234"

WHEN 에러가 기록됨

THEN stored metrics에서 PII가 마스킹됨:
  - password: "***"
  - token: "***"
  - api_key: "***"
AND Sentry로 전송되는 이벤트도 마스킹됨
```

### Sentry DSN Validation

```gherkin
Scenario: 잘못된 Sentry DSN

GIVEN 잘못된 형식의 sentry_dsn이 제공됨

WHEN setup_metrics가 호출됨

THEN ValueError가 발생함
AND 명확한 에러 메시지가 제공됨
AND 앱이 계속 정상적으로 실행됨
```

---

## Edge Cases

### Edge Case 1: Zero Errors

```gherkin
GIVEN 메트릭 수집이 활성화됨
AND 어떤 에러도 발생하지 않음

WHEN /api/metrics가 요청됨

THEN total_errors는 0임
AND by_domain은 빈 객체임
AND top_errors는 빈 배열임
```

### Edge Case 2: Unknown Error Code

```gherkin
GIVEN 메트릭 수집이 활성화됨
AND 등록되지 않은 error_code (99999)로 에러가 발생함

WHEN 에러가 발생함

THEN error_code 99999가 카운트됨
AND error_domain은 "UNKNOWN"으로 표시됨
```

### Edge Case 3: Memory Limit Reached

```gherkin
GIVEN max_history_size=100 설정
AND 이미 100개의 이벤트가 저장됨

WHEN 101번째 에러가 발생함

THEN 가장 오래된 이벤트가 제거됨 (FIFO)
AND 최근 100개 이벤트만 유지됨
AND 카운트는 정확히 유지됨
```

### Edge Case 4: Concurrent Reset

```gherkin
GIVEN 메트릭이 수집 중임
AND 한 스레드가 reset()를 호출함

WHEN 다른 스레드가 에러를 기록함

THEN reset이 완료된 후 카운트가 0부터 시작됨
AND 레이스 컨디션이 발생하지 않음
```

---

## Integration Test Matrix

| Scenario                     | Prometheus | Sentry | Dashboard | Disabled |
|------------------------------|------------|--------|-----------|----------|
| Basic error count            | ✓          | ✓      | ✓         | -        |
| Thread safety                | ✓          | ✓      | ✓         | -        |
| PII masking                  | -          | ✓      | -         | -        |
| Sentry failure fallback      | -          | ✓      | -         | -        |
| API responses                | ✓          | -      | ✓         | -        |
| No metrics when disabled     | -          | -      | -         | ✓        |
| SPEC-001 compatibility       | ✓          | ✓      | ✓         | ✓        |
| Performance (benchmark)      | ✓          | ✓      | ✓         | ✓        |
| Memory limits                | ✓          | ✓      | ✓         | -        |
| Edge cases                   | ✓          | ✓      | ✓         | ✓        |

---

## Definition of Done

SPEC-MONITOR-002 is **ACCEPTED** when:

1. **Functional Requirements**: All EARS requirements implemented
2. **Test Coverage**: 85%+ coverage achieved
3. **Test Scenarios**: All Gherkin scenarios passing
4. **Performance**: All benchmarks passing
5. **Security**: PII masking verified, security scan clean
6. **Integration**: SPEC-001 integration verified
7. **Documentation**: API docs complete, examples runnable
8. **Quality Gates**: TRUST 5 compliance verified

---

## Traceability

**SPEC-MONITOR-002 TAG BLOCK**

**Requirements to Test Mapping**:
- Ubiquitous → Scenarios 1, 2, 5
- Event-driven → Scenarios 1.1, 2.1, 3.1, 4.1
- State-driven → Scenarios 5.1, 5.2
- Unwanted → Security tests, Edge cases
- Optional → Future enhancements (out of scope for acceptance)

**Acceptance to Implementation Mapping**:
- ErrorMetricsCollector → Scenarios 1, 6
- PrometheusExporter → Scenario 2
- SentryIntegration → Scenario 3
- DashboardAPI → Scenario 4
- Integration → Scenario 6
