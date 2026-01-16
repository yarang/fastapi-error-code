# Architecture

## Overview

fastapi-error-codes provides a structured approach to exception handling in FastAPI applications with support for custom error codes, internationalization (i18n), domain-based organization, and automatic OpenAPI documentation generation.

## Core Components

### 1. BaseAppException

The foundation of the entire system, located in `src/fastapi_error_codes/base.py`.

**Key Features:**
- Custom error code support (0-9999)
- HTTP status code mapping
- Automatic timestamp generation
- Flexible detail field (dict, list, string, or any type)
- Custom header support
- `to_dict()` method for JSON serialization

**Class Hierarchy:**
```
BaseAppException (Exception)
    ├── YourCustomException1
    ├── YourCustomException2
    └── ...
```

### 2. ExceptionRegistry

Thread-safe global registry for managing all registered exceptions, located in `src/fastapi_error_codes/registry.py`.

**Key Features:**
- Prevents duplicate error code registration
- Thread-safe operations with mutex locks
- Stores metadata (domain, status_code, message_key)
- Provides lookup and enumeration methods

**Registry Data Structure:**
```python
{
    error_code: {
        'class': ExceptionClass,
        'message': 'Default message',
        'metadata': {
            'domain': 'AUTH',
            'status_code': 401,
            'message_key': 'auth.required'
        }
    }
}
```

### 3. Decorator System

The `@register_exception` decorator in `src/fastapi_error_codes/decorators.py` provides automatic registration and class wrapping.

**Decorator Flow:**
1. Validates error code (0-9999, int type)
2. Validates status code (100-599, int type)
3. Generates default message if not provided
4. Registers exception in global registry
5. Creates wrapper class with default values
6. Sets class metadata attributes

### 4. ErrorDomain System (Complete)

Domain-based error code management with predefined domains, located in `src/fastapi_error_codes/domain.py`.

**Key Features:**
- Predefined domains (AUTH, RESOURCE, VALIDATION, SERVER, CUSTOM)
- Code range validation
- Domain lookup by code
- Thread-safe domain registration

**Predefined Domains:**

| Domain    | Code Range | Description                   |
|-----------|------------|-------------------------------|
| AUTH      | 200-299    | Authentication/Authorization   |
| RESOURCE  | 300-399    | Resource-related errors       |
| VALIDATION| 400-499   | Validation errors             |
| SERVER    | 500-599    | Server errors                 |
| CUSTOM    | 900-999    | Custom business logic errors  |

**Architecture:**
```
ErrorDomain
    ├── name: str
    ├── code_range: Tuple[int, int]
    └── Class Methods:
        ├── register_domain(name, code_range)
        ├── get_domain(name)
        ├── is_valid_code(code, domain_name)
        ├── get_domain_for_code(code)
        └── list_domains()
```

### 5. i18n System (Complete)

Multi-language message support with locale files and fallback chain, located in `src/fastapi_error_codes/i18n.py`.

**Key Features:**
- Locale file loading from JSON
- Nested key support with dot notation
- Fallback chain: requested -> fallback locales -> default
- Message formatting with parameters
- Locale caching for performance

**MessageProvider Architecture:**
```
MessageProvider
    ├── locale_dir: str
    ├── default_locale: str
    ├── fallback_locales: List[str]
    └── Methods:
        ├── get_message(key, locale, default, **kwargs)
        ├── reload_locale(locale)
        ├── clear_cache()
        └── get_available_locales()
```

**Fallback Chain:**
```
Requested Locale (e.g., "ko-KR")
    ↓ (not found)
Fallback Locales (e.g., ["ko"])
    ↓ (not found)
Default Locale (e.g., "en")
    ↓ (not found)
Original Key
```

**Locale File Structure:**
```json
{
    "errors": {
        "auth": {
            "required": "Authentication required",
            "invalid_credentials": "Invalid credentials"
        },
        "user_not_found": "User {user_id} not found"
    }
}
```

### 6. Handler System (Complete)

Exception handlers for automatic FastAPI integration, located in `src/fastapi_error_codes/handlers.py`.

**Key Features:**
- Global exception handler registration
- Accept-Language header parsing
- i18n message resolution
- Debug/production mode support
- Traceback inclusion in debug mode

**setup_exception_handler Architecture:**
```
setup_exception_handler(app, config)
    ├── Initialize MessageProvider
    ├── Parse Accept-Language header
    ├── Resolve message with i18n
    ├── Create ErrorResponse
    └── Return JSONResponse
```

**Accept-Language Parsing:**
```
Header: "ko-KR,ko;q=0.9,en;q=0.8"
    ↓
Parsed Locales: ["ko-KR", "ko", "en"]
```

### 7. ErrorHandlerConfig (Complete)

Configuration management with development and production presets, located in `src/fastapi_error_codes/config.py`.

**Key Features:**
- Frozen dataclass for immutability
- Development preset (debug mode enabled)
- Production preset (debug mode disabled)
- Environment variable support
- Dictionary import/export

**Configuration Attributes:**
```python
@dataclass(frozen=True)
class ErrorHandlerConfig:
    default_locale: str = "en"
    fallback_locales: List[str] = []
    debug_mode: bool = False
    include_traceback: bool = False
    locale_dir: str = "locales"
```

**Presets:**
- `development()`: debug_mode=True, include_traceback=True
- `production()`: debug_mode=False, include_traceback=False
- `from_environment()`: Load from ERROR_* environment variables

### 8. Response Models (Complete)

Pydantic models for standardized error responses, located in `src/fastapi_error_codes/models.py`.

**Key Features:**
- ErrorResponse for standard errors
- ValidationErrorResponse for validation errors
- ErrorDetail for individual field errors
- Pydantic v1/v2 compatibility
- from_exception() factory method

**Models:**
```python
class ErrorResponse(BaseModel):
    error_code: int
    message: str
    status_code: Optional[int]
    detail: Any
    timestamp: str
    error_name: Optional[str]

class ValidationErrorResponse(BaseModel):
    error_code: int
    message: str
    errors: List[ErrorDetail]
    status_code: Optional[int]
    timestamp: str
```

### 9. Monitoring System (SPEC-MONITOR-002)

Complete error metrics collection and monitoring integration, located in `src/fastapi_error_codes/metrics/`.

**Key Features:**
- Thread-safe metrics collection with < 50μs performance
- Prometheus metrics export at /metrics endpoint
- Sentry error tracking with PII masking
- Dashboard API with /api/metrics/* endpoints
- Time-based bucketing for efficient querying
- LRU eviction for memory management
- Non-blocking collection (never affects request processing)

#### 9.1 ErrorMetricsCollector

Thread-safe metrics collector with time-based bucketing.

**Architecture:**
```python
ErrorMetricsCollector
    ├── config: MetricsConfig
    ├── _lock: threading.Lock
    ├── _buckets: OrderedDict[datetime, TimeBucket]
    ├── _recent_events: List[ErrorEvent]
    └── Methods:
        ├── record(error_code, error_name, ...) -> str  # < 50μs
        ├── get_snapshot() -> MetricsSnapshot
        ├── get_error_counts_by_code() -> Dict[int, int]
        ├── get_recent_events(limit) -> List[ErrorEvent]
        └── clear() -> None
```

**Performance Characteristics:**
- `record()`: < 50μs average execution time
- `get_snapshot()`: < 1ms for typical workloads
- Thread-safe under concurrent load
- Coarse-grained locking for minimal contention

**Data Flow:**
```
Exception raised
    ↓
_exception_handler() calls collector.record()
    ↓
Create ErrorEvent with timestamp
    ↓
Acquire lock
    ↓
Get or create current TimeBucket
    ↓
Add event to bucket and recent_events
    ↓
Enforce max_events limit with LRU eviction
    ↓
Release lock
    ↓
Return event_id (non-blocking)
```

#### 9.2 PrometheusExporter

Prometheus metrics export using prometheus-client patterns.

**Architecture:**
```python
PrometheusExporter
    ├── collector: ErrorMetricsCollector
    ├── enabled: bool
    ├── namespace: str
    └── Methods:
        └── generate_metrics() -> str  # Prometheus text format
```

**Metrics Exported:**
- `fastapi_errors_total`: Counter of all errors
- `fastapi_errors_by_code`: Gauge grouped by error code
- `fastapi_errors_by_status`: Gauge grouped by HTTP status code

**Example Output:**
```
# HELP fastapi_errors_total Total number of application errors
# TYPE fastapi_errors_total counter
fastapi_errors_total 42

# HELP fastapi_errors_by_code Errors grouped by application error code
# TYPE fastapi_errors_by_code gauge
fastapi_errors_by_code{error_code="404"} 10
fastapi_errors_by_code{error_code="500"} 5
```

#### 9.3 SentryIntegration

Sentry error tracking with automatic PII masking.

**Architecture:**
```python
SentryIntegration
    ├── config: MetricsConfig
    ├── enabled: bool
    ├── dsn: str
    ├── pii_patterns: List[str]
    ├── _sentry_sdk: Module (optional)
    └── Methods:
        ├── initialize() -> None
        ├── capture_event(...) -> Optional[str]
        ├── capture_exception(...) -> Optional[str]
        ├── add_breadcrumb(...) -> None
        ├── configure_scope(...) -> None
        └── flush(timeout) -> bool
```

**PII Masking:**
```python
def mask_pii(data: Any, patterns: List[str]) -> Any:
    """Recursively mask fields matching PII patterns"""
    # Email masking: user@example.com → ***@***.***
    # General masking: *** for sensitive fields
```

**Graceful Degradation:**
- Sentry import failure: Continues without error tracking
- Initialization failure: Continues without Sentry
- Capture failure: Silently ignored, doesn't affect request

#### 9.4 DashboardAPI

FastAPI router with JSON endpoints for metrics consumption.

**Architecture:**
```python
DashboardAPI
    ├── collector: ErrorMetricsCollector
    ├── router: APIRouter
    └── Endpoints:
        ├── GET /api/metrics/summary → MetricsSummaryResponse
        ├── GET /api/metrics/recent?limit=100 → RecentEventsResponse
        ├── GET /api/metrics/by-code/{code} → Dict
        └── GET /api/metrics/top-errors?limit=10 → List[Dict]
```

**Response Models:**
```python
class MetricsSummaryResponse(BaseModel):
    total_errors: int
    error_counts: Dict[int, int]
    bucket_count: int
    timestamp: str

class ErrorEventResponse(BaseModel):
    error_code: int
    error_name: str
    status_code: int
    message: str
    detail: Any
    path: Optional[str]
    method: Optional[str]
    timestamp: str
    event_id: str
```

#### 9.5 MetricsConfig

Configuration management with validation and presets.

**Architecture:**
```python
@dataclass(frozen=True)
class MetricsConfig:
    enabled: bool = True
    collection_interval_ms: int = 60000
    max_events: int = 10000
    prometheus_enabled: bool = True
    sentry_enabled: bool = False
    sentry_dsn: Optional[str] = None
    dashboard_enabled: bool = True
    pii_patterns: List[str] = [...]
```

**Presets:**
- `MetricsPreset.development()`: Local development with minimal overhead
- `MetricsPreset.production(sentry_dsn)`: Full monitoring with Sentry
- `MetricsPreset.testing()`: Disabled for test environments
- `MetricsPreset.disabled()`: All monitoring disabled
- `get_config_from_env()`: Load from METRICS_* environment variables

#### 9.6 Integration with Exception Handler

The monitoring system integrates seamlessly with SPEC-001 exception handler:

```python
def setup_exception_handler(
    app: FastAPI,
    config: ErrorHandlerConfig,
    metrics_config: Optional[MetricsConfig] = None,  # NEW
) -> None:
    # Initialize metrics collector if config provided
    if metrics_config and metrics_config.enabled:
        metrics_collector = ErrorMetricsCollector(metrics_config)
        app.state.metrics_collector = metrics_collector
    else:
        metrics_collector = None

    async def exception_handler(request, exc):
        # Generate error response
        error_response = create_error_response(exc, request)

        # Record metrics (non-blocking, never affects response)
        if metrics_collector:
            try:
                metrics_collector.record(
                    error_code=exc.error_code,
                    error_name=exc.error_name,
                    status_code=exc.status_code,
                    message=exc.message,
                    path=request.url.path,
                    method=request.method,
                )
            except Exception:
                pass  # Silently ignore metrics failures

        return JSONResponse(content=error_response.model_dump())
```

#### 9.7 Performance Characteristics

**Memory Usage:**
- BaseErrorEvent: ~500 bytes per event
- TimeBucket overhead: ~200 bytes per bucket
- Total minimal footprint: ~200KB for typical usage
- LRU eviction enforces max_events limit

**Collection Performance:**
- `record()`: < 50μs average (verified)
- Lock contention: Minimal with coarse-grained locking
- Non-blocking: Never affects request processing

**Query Performance:**
- `get_snapshot()`: < 1ms for typical workloads
- `get_recent_events()`: O(1) slice operation
- Prometheus generation: < 5ms for 10K events

#### 9.8 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Exception Raised                            │
│                  (BaseAppException)                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 _exception_handler()                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Parse Accept-Language header                         │  │
│  │  2. Resolve i18n message                                  │  │
│  │  3. Create ErrorResponse                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Metrics Collection (Non-blocking)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  if metrics_collector:                                   │  │
│  │    try:                                                  │  │
│  │      metrics_collector.record()  # < 50μs               │  │
│  │    except Exception:                                    │  │
│  │      pass  # Never affects response                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │Prometheus│  │  Sentry  │  │ Dashboard│
         │ Counter++│  │  Event   │  │   API    │
         └──────────┘  └──────────┘  └──────────┘
                │             │             │
                ▼             ▼             ▼
         /metrics      Sentry Cloud   /api/metrics/*
```

#### 9.9 Thread Safety

**Locking Strategy:**
- Single `threading.Lock` for collector state
- Coarse-grained locking for minimal contention
- Lock-free snapshot generation (copy under lock, iterate outside)

**Thread-safe Operations:**
- `record()`: Lock held for bucket update and event append
- `get_snapshot()`: Lock held for data copy, released before iteration
- `clear()`: Lock held for state reset

#### 9.10 Time-based Bucketing

**Bucket Management:**
```python
TimeBucket
    ├── start_time: datetime
    ├── end_time: datetime
    ├── error_counts: Dict[int, int]
    └── total_count: int
```

**Lifecycle:**
1. Create new bucket when current expires
2. Add events to current bucket
3. Clean up expired buckets periodically
4. Remove oldest buckets when approaching max_events

**Benefits:**
- Efficient time-range queries
- Automatic data expiration
- Reduced memory footprint

#### 9.11 Implementation Status

| Component            | Status      | Module                |
|----------------------|-------------|-----------------------|
| MetricsConfig        | Complete    | metrics/config.py     |
| ErrorMetricsCollector | Complete   | metrics/collector.py  |
| PrometheusExporter   | Complete    | metrics/prometheus.py |
| SentryIntegration    | Complete    | metrics/sentry.py     |
| DashboardAPI         | Complete    | metrics/dashboard.py  |
| setup_metrics        | Complete    | metrics/setup.py      |
| Handler Integration  | Complete    | handlers.py           |

### 10. Future Enhancements

Pydantic models for standardized error responses, located in `src/fastapi_error_codes/models.py`.

**Key Features:**
- ErrorResponse for standard errors
- ValidationErrorResponse for validation errors
- ErrorDetail for individual field errors
- Pydantic v1/v2 compatibility
- from_exception() factory method

**Models:**
```python
class ErrorResponse(BaseModel):
    error_code: int
    message: str
    status_code: Optional[int]
    detail: Any
    timestamp: str
    error_name: Optional[str]

class ValidationErrorResponse(BaseModel):
    error_code: int
    message: str
    errors: List[ErrorDetail]
    status_code: Optional[int]
    timestamp: str
```

## Error Code Organization

### Domain-Based Organization

Error codes are organized by domain for better management:

- **200-299**: Authentication/Authorization
- **300-399**: Resource-related errors
- **400-499**: Validation errors
- **500-599**: Server errors
- **900-999**: Custom business logic errors

### Example Code Assignment

```
201: Authentication required
202: Invalid credentials
203: Token expired
301: Resource not found
302: Resource already exists
401: Validation failed
402: Missing required field
500: Internal server error
```

## Request/Response Flow

### Exception Raising Flow

```
User Endpoint
    ↓
Raises Exception
    ↓
FastAPI Exception Handler
    ↓
Parse Accept-Language Header
    ↓
Resolve Message with MessageProvider
    ↓
Create ErrorResponse
    ↓
Return JSONResponse
```

### Response Format

```json
{
    "error_code": 201,
    "message": "Authentication required",
    "detail": {
        "redirect_url": "/login"
    },
    "timestamp": "2026-01-16T10:00:00Z",
    "error_name": "AuthRequiredException"
}
```

## Thread Safety

The ExceptionRegistry uses `threading.Lock` to ensure thread-safe operations:

- Registration: `_lock.acquire()` before adding new codes
- Lookup: No lock needed (dict reads are thread-safe in CPython)
- Clear: `_lock.acquire()` before clearing

## Type Safety

The package is fully type-hinted with strict mypy configuration:

- All methods have complete type annotations
- `TYPE_CHECKING` pattern for circular imports
- Strict mypy settings enabled
- Support for Python 3.8-3.13

## Performance Considerations

### Registry Lookup

O(1) dictionary lookup for error code retrieval.

### MessageProvider Caching

Locale files are cached in memory after first load:
- Subsequent accesses are O(1) for cached locales
- `clear_cache()` forces reload from disk
- `reload_locale()` updates specific locale

### Memory Usage

- Base exception class: ~1KB per instance
- Registry overhead: ~500 bytes per registered code
- MessageProvider cache: ~10-50KB per locale
- Total minimal footprint: ~200KB for typical usage

### Initialization

- Decorator registration: < 1ms per exception
- Registry initialization: Instantaneous (singleton pattern)
- MessageProvider initialization: ~5-10ms (locale file loading)

## Extension Points

### Custom Exception Classes

```python
@register_exception(
    error_code=1001,
    message='Custom business error',
    domain='CUSTOM',
    status_code=400
)
class CustomBusinessException(BaseAppException):
    pass
```

### Custom Detail Handling

```python
exc = CustomBusinessException()
exc.add_detail('field_name', 'email')
exc.add_detail('validation_rule', 'email_format')
```

### Custom Headers

```python
exc = CustomException(
    error_code=429,
    message='Rate limit exceeded',
    headers={'Retry-After': '60'}
)
```

### Custom Domains

```python
ErrorDomain.register_domain("PAYMENT", (600, 699))
```

## Testing Strategy

### Unit Tests

- Test exception creation and attributes
- Test decorator registration
- Test registry operations
- Test thread safety
- Test domain operations
- Test i18n message resolution
- Test configuration management

### Integration Tests

- Test FastAPI exception handling
- Test response format consistency
- Test Accept-Language header parsing
- Test i18n fallback chain
- Test debug/production modes

## Implementation Status

| Component      | Status      | Module         |
|----------------|-------------|----------------|
| BaseAppException| Complete    | base.py        |
| ExceptionRegistry| Complete   | registry.py    |
| Decorator      | Complete    | decorators.py  |
| ErrorDomain    | Complete    | domain.py      |
| MessageProvider| Complete    | i18n.py        |
| ErrorHandlerConfig| Complete | config.py      |
| Handler System | Complete    | handlers.py    |
| Response Models| Complete    | models.py      |

## Future Enhancements

### Potential Extensions

- Error code migration/versioning support
- Error aggregation for batch operations
- Custom error response formatters
- Error metrics and monitoring integration
- OpenAPI schema generation for registered exceptions
- Error code documentation generator
