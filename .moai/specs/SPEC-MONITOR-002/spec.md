# SPEC-MONITOR-002: 에러 메트릭 및 모니터링 통합

## Specification Information

- **ID**: SPEC-MONITOR-002
- **Title**: 에러 메트릭 및 모니터링 통합 기능 구현
- **Status**: Complete
- **Version**: 1.0.0
- **Created**: 2026-01-16
- **Updated**: 2026-01-16
- **Priority**: High
- **Related SPECs**: SPEC-001 (Error Handler)

---

## Implementation Status

### Phase 1: MetricsConfig ✅ Complete
- File: `src/fastapi_error_codes/metrics/config.py`
- Features:
  - Frozen dataclass with validation
  - Presets: development, production, testing, disabled
  - Environment variable loading
  - PII pattern configuration

### Phase 2: ErrorMetricsCollector ✅ Complete
- File: `src/fastapi_error_codes/metrics/collector.py`
- Features:
  - Thread-safe operations
  - Time-based bucketing
  - LRU eviction policy
  - Performance: < 50μs per record()

### Phase 3: PrometheusExporter ✅ Complete
- File: `src/fastapi_error_codes/metrics/prometheus.py`
- Features:
  - prometheus-client>=0.21.0 integration
  - Counter and Histogram metrics
  - /metrics endpoint (Prometheus text format)
  - Custom namespace support

### Phase 4: SentryIntegration ✅ Complete
- File: `src/fastapi_error_codes/metrics/sentry.py`
- Features:
  - sentry-sdk>=2.0.0 integration
  - PII masking (email, password, credit_card, etc.)
  - Async/batch sending
  - Graceful degradation on failure

### Phase 5: DashboardAPI ✅ Complete
- File: `src/fastapi_error_codes/metrics/dashboard.py`
- Features:
  - /api/metrics/summary - Overall summary
  - /api/metrics/recent - Recent events
  - /api/metrics/by-code/{code} - Per-code statistics
  - /api/metrics/top-errors - Top N errors
  - /api/metrics/recent/{time} - Recent errors by time

### Phase 6: setup_metrics ✅ Complete
- File: `src/fastapi_error_codes/metrics/setup.py`
- Features:
  - Complete FastAPI integration
  - Non-blocking metrics collection
  - Hook into existing exception handler
  - Backward compatible with SPEC-001

---

## Test Results

**Total Tests**: 193 passed
**Coverage**: 89.58%
**Performance**: < 50μs overhead

---

## Deployment

### Dependencies
```
[project.optional-dependencies]
monitoring = [
    "prometheus-client>=0.21.0",
    "sentry-sdk>=2.0.0",
]
```

### Quick Start

```python
from fastapi import FastAPI
from fastapi_error_codes import (
    setup_exception_handler,
    ErrorHandlerConfig,
    MetricsConfig,
)

app = FastAPI()

# Enable monitoring with custom config
config = ErrorHandlerConfig(
    debug_mode=True,
    sentry_enabled=True,
    sentry_dsn=os.environ["SENTRY_DSN"]
)
metrics_config = MetricsConfig(
    enabled=True,
    max_events=10000,
    retention_hours=24
)

setup_exception_handler(app, config, metrics_config)
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - "9. Monitoring System" section
- [API Reference](docs/API.md) - "Monitoring & Metrics" section
- [Examples](examples/with_metrics.py) - Basic monitoring usage
- [Examples/with_prometheus.py] - Prometheus integration
- [Examples/with_sentry.py] - Sentry integration
- [Examples/with_dashboard.py] - Dashboard API usage

---

---

## Overview

이 SPEC은 fastapi-error-codes 패키지에 에러 메트릭 수집, 통계, 외부 모니터링 시스템 통합, 대시보드 API를 추가하는 기능을 정의합니다.

### Goals

- 에러 발생 횟수를 실시간으로 추적
- 에러 코드별 통계 집계 (도메인, 시간대별)
- Prometheus/Sentry와의 통합 지원
- FastAPI 기반 대시보드 API 제공
- 기존 에러 핸들러(SPEC-001)와의 seamless 통합

### Success Criteria

- 에러 발생 시 자동 메트릭 수집 (수동 코드 변경 불필요)
- 스레드 안전한 메트릭 수집 보장
- Prometheus metrics endpoint (/metrics) 제공
- Sentry error tracking 자동 전송
- 대시보드 API에서 실시간 통계 조회 가능
- 성능 영향 최소화 (1ms 미만의 오버헤드)
- 85%+ 테스트 커버리지

---

## Requirements

### Ubiquitous Requirements

**WHILE the application is running**
- 시스템은 모든 BaseAppException 발생을 자동으로 추적해야 한다
- 시스템은 스레드 안전한 방식으로 메트릭을 수집해야 한다
- 시스템은 Prometheus metrics를 /metrics 엔드포인트에서 제공해야 한다
- 시스템은 메트릭 수집으로 인한 성능 영향을 1ms 미만으로 유지해야 한다

**WHILE error tracking is enabled**
- 시스템은 Sentry에 에러 이벤트를 자동 전송해야 한다
- 시스템은 PII(개인정보)가 포함된 데이터를 masking 처리해야 한다
- 시스템은 Sentry 전송 실패 시 에러 핸들링을 방해하지 않아야 한다

### Event-Driven Requirements

**WHEN a BaseAppException is raised**
- 시스템은 에러 코드별 발생 횟수를 증가시켜야 한다
- 시스템은 에러 발생 시간을 기록해야 한다
- 시스템은 (선택적으로) Sentry에 이벤트를 전송해야 한다
- 시스템은 Prometheus counter metric을 증가시켜야 한다

**WHEN setup_metrics is called**
- 시스템은 ErrorMetricsCollector를 초기화해야 한다
- 시스템은 Prometheus Registry를 설정해야 한다
- 시스템은 Sentry SDK를 초기화해야 한다 (DSN 제공 시)
- 시스템은 /metrics 엔드포인트를 FastAPI 앱에 등록해야 한다
- 시스템은 대시보드 API 엔드포인트를 등록해야 한다

**WHEN /metrics endpoint is requested**
- 시스템은 Prometheus text format으로 메트릭을 반환해야 한다
- 시스템은 모든 error_code별 count를 포함해야 한다
- 시스템은 error_domain별 집계를 포함해야 한다
- 시스템은 HTTP 200 상태 코드와 text/plain content-type을 반환해야 한다

**WHEN /api/metrics/dashboard is requested**
- 시스템은 JSON 형식으로 대시보드 데이터를 반환해야 한다
- 시스템은 총 에러 발생 횟수를 포함해야 한다
- 시스템은 에러 코드별 통계를 포함해야 한다
- 시스템은 도메인별 통계를 포함해야 한다
- 시스템은 최근 1시간/24시간/7일 통계를 제공해야 한다

### State-Driven Requirements

**IF monitoring is disabled**
- 시스템은 메트릭을 수집하지 않아야 한다
- 시스템은 /metrics 엔드포인트를 제공하지 않아야 한다
- 시스템은 Sentry에 이벤트를 전송하지 않아야 한다

**IF debug_mode is enabled**
- 시스템은 상세한 메트릭 정보를 로그로 출력해야 한다
- 시스템은 각 에러의 detail 정보를 포함해야 한다

**IF prometheus_enabled is True**
- 시스템은 Prometheus metrics를 노출해야 한다
- 시스템은 custom labels을 지원해야 한다

**IF sentry_enabled is True**
- 시스템은 Sentry DSN을 검증해야 한다
- 시스템은 에러 trace를 Sentry에 전송해야 한다

### Unwanted Requirements

**THE SYSTEM SHALL NOT**
- 에러 핸들링 성능에 영향을 주어서는 안 된다 (blocking 허용 안 함)
- PII(개인정보)를 메트릭이나 외부 시스템에 포함해서는 안 된다
- 메트릭 수집 실패로 인해 원래 요청이 실패해서는 안 된다
- 무제한 메트릭 데이터를 저장해서는 안 된다 (메모리 관리)

### Optional Requirements

**WHERE POSSIBLE**
- 시스템은 메트릭 데이터의 disk persistence를 제공해야 한다 (선택 사항)
- 시스템은 Grafana dashboard template을 제공할 수 있다
- 시스템은 Slack/Teams 알림 통합을 지원할 수 있다
- 시스템은 메트릭 export를 CSV/JSON으로 제공할 수 있다

---

## Architecture

### Component Overview

```
fastapi-error-codes (with monitoring)
├── SPEC-001 Components (Existing)
│   ├── BaseAppException
│   ├── ExceptionRegistry
│   ├── setup_exception_handler
│   └── ...
│
└── SPEC-MONITOR-002 Components (New)
    ├── ErrorMetricsCollector    # 메트릭 수집 (thread-safe)
    ├── PrometheusExporter       # Prometheus metrics export
    ├── SentryIntegration        # Sentry SDK wrapper
    ├── MetricsConfig            # 모니터링 설정
    ├── setup_metrics            # FastAPI integration
    └── DashboardAPI             # /api/metrics/* endpoints
```

### Data Flow

```
BaseAppException raised
    ↓
exception_handler catches (SPEC-001)
    ↓
ErrorMetricsCollector.record() [non-blocking]
    ↓
├──→ Prometheus counter++
├──→ Sentry event send [async, if enabled]
└──→ In-memory stats update
```

### API Endpoints

| Endpoint          | Method | Description                     |
|-------------------|--------|---------------------------------|
| /metrics          | GET    | Prometheus metrics format       |
| /api/metrics      | GET    | 전체 메트릭 요약                 |
| /api/metrics/by-code/{code} | GET | 특정 error_code 통계 |
| /api/metrics/by-domain/{domain} | GET | 도메인별 통계 |
| /api/metrics/recent | GET   | 최근 발생 에러 목록             |

---

## Technical Stack

### Required Dependencies

| Package            | Version    | Purpose                          |
|--------------------|------------|----------------------------------|
| prometheus-client  | >=0.21.0   | Prometheus metrics export        |
| sentry-sdk         | >=2.0.0    | Sentry error tracking            |

### Optional Dependencies

| Package            | Version    | Purpose                          |
|--------------------|------------|----------------------------------|
| aiohttp            | >=3.9.0    | Async Sentry transport           |

### Python Built-in Modules

- `threading` - Thread-safe locking
- `collections` - defaultdict, Counter
- `time` - Timestamp handling
- `dataclasses` - Configuration data classes

---

## Configuration

### MetricsConfig

```python
@dataclass
class MetricsConfig:
    """모니터링 설정"""

    # 기본 설정
    enabled: bool = True                      # 전체 활성화

    # Prometheus 설정
    prometheus_enabled: bool = True           # Prometheus metrics export
    prometheus_path: str = "/metrics"         # metrics endpoint 경로

    # Sentry 설정
    sentry_enabled: bool = False              # Sentry error tracking
    sentry_dsn: Optional[str] = None          # Sentry DSN
    sentry_sample_rate: float = 1.0           # Sampling rate (0.0-1.0)
    sentry_traces_sample_rate: float = 0.1    # Performance tracing

    # 데이터 보관 설정
    max_history_size: int = 10000             # 최근 이벤트 보관 개수
    retention_hours: int = 24                 # 통계 보관 시간

    # 성능 설정
    async_collection: bool = True             # 비동기 수집
    batch_send_size: int = 10                 # Sentry batch size

    # 개인정보 보호
    mask_pii: bool = True                     # PII 자동 마스킹
    pii_fields: List[str] = field(default_factory=lambda: [
        "password", "token", "secret", "api_key", "credit_card"
    ])

    # 라벨 설정
    default_labels: Dict[str, str] = field(default_factory=dict)

    # Class methods
    @classmethod
    def disabled(cls) -> "MetricsConfig":
        """모니터링 비활성화 설정"""

    @classmethod
    def production(cls, sentry_dsn: str) -> "MetricsConfig":
        """프로덕션 환경 프리셋"""

    @classmethod
    def from_environment(cls) -> "MetricsConfig":
        """환경변수에서 로드"""
```

---

## Integration with SPEC-001

### setup_exception_handler Enhancement

기존 `setup_exception_handler` 함수에 선택적 메트릭 수집 기능 추가:

```python
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None,
    metrics_config: Optional[MetricsConfig] = None,  # NEW
) -> None:
    """
    FastAPI exception handler 설정

    Args:
        app: FastAPI 앱
        config: 에러 핸들러 설정 (SPEC-001)
        metrics_config: 모니터링 설정 (SPEC-MONITOR-002, 선택)
    """
    # 기존 핸들러 등록
    app.add_exception_handler(BaseAppException, base_exception_handler)

    # 메트릭 수집기 초기화 (선택)
    if metrics_config and metrics_config.enabled:
        setup_metrics(app, metrics_config)
```

### Non-blocking Collection

메트릭 수집은 항상 비동기/non-blocking으로 수행:

```python
def base_exception_handler(request: Request, exc: BaseAppException):
    # 기존 에러 응답 생성 (SPEC-001)
    error_response = create_error_response(exc, request)

    # 메트릭 수집 (non-blocking, never affects response)
    if _metrics_collector:
        _metrics_collector.record_async(exc, request)  # Fire and forget

    return JSONResponse(content=error_response.model_dump(), ...)
```

---

## Implementation Plan Summary

### Main Components

1. **ErrorMetricsCollector** (src/fastapi_error_codes/metrics/collector.py)
   - 스레드 안전한 메트릭 수집
   - 메모리 내 통계 집계
   - 시간대별 버킷 관리

2. **PrometheusExporter** (src/fastapi_error_codes/metrics/prometheus.py)
   - Prometheus client 래퍼
   - Counter, Histogram metrics 정의
   - /metrics endpoint handler

3. **SentryIntegration** (src/fastapi_error_codes/metrics/sentry.py)
   - Sentry SDK 초기화
   - 이벤트 전송 및 PII masking
   - 비동기 전송 지원

4. **MetricsConfig** (src/fastapi_error_codes/metrics/config.py)
   - 설정 데이터 클래스
   - 환경변수 로드
   - 프리셋 (development/production)

5. **DashboardAPI** (src/fastapi_error_codes/metrics/dashboard.py)
   - /api/metrics/* 엔드포인트
   - 통계 조회 및 집계
   - JSON 응답 모델

6. **setup_metrics** (src/fastapi_error_codes/metrics/setup.py)
   - FastAPI 통합 함수
   - 전체 컴포넌트 초기화

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| 성능 영향 | High | 비동기 수집, lock-free 구조, 벤치마크 테스트 |
| 메모리 누수 | Medium | LRU eviction, 최대 크기 제한 |
| Sentry 의존성 | Low | 선택적 활성화, 실패 시 fallback |
| PII 유출 | High | 자동 masking, 필드별 제외 설정 |

---

## Dependencies

### Internal Dependencies

- SPEC-001: BaseAppException, setup_exception_handler
- ExceptionRegistry: error_code 정보 조회

### External Dependencies

```
prometheus-client>=0.21.0
sentry-sdk>=2.0.0
```

### Version Verification (2026-01-16)

- `prometheus-client 0.21.0` (2024-11 stable) ✓
- `sentry-sdk 2.0.0` (2024-03 stable) ✓

---

## Documentation References

- [SPEC-001](.moai/specs/SPEC-001/spec.md) - 기본 에러 핸들러 구현
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)

---

## Change History

| Version | Date       | Changes                                |
|---------|------------|----------------------------------------|
| 1.0.0   | 2026-01-16 | Initial SPEC-MONITOR-002 documentation |

---

## Traceability Tags

**TAG_BLOCK**: SPEC-MONITOR-002

**Related Components**:
- metrics/collector.py - ErrorMetricsCollector
- metrics/prometheus.py - PrometheusExporter
- metrics/sentry.py - SentryIntegration
- metrics/dashboard.py - DashboardAPI
- metrics/config.py - MetricsConfig
- metrics/setup.py - setup_metrics
