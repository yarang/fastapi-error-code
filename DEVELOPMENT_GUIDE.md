# fastapi-error-codes - Claude Code 작업 지침

## 프로젝트 개요

- **프로젝트명**: fastapi-error-codes
- **프로젝트 유형**: Python 패키지 (FastAPI Exception Handling Library)
- **기술 스택**: Python 3.8+, FastAPI, Pydantic
- **목표**: FastAPI 프로젝트에서 error_code 기반의 구조화된 예외 처리와 다국어 지원을 제공하는 재사용 가능한 패키지

## 핵심 기능

1. **BaseAppException**: 커스텀 error_code와 메시지를 가진 기본 예외 클래스
2. **@register_exception**: error_code를 자동으로 등록하는 데코레이터
3. **다국어 지원**: Multi-level fallback을 통한 locale별 메시지 관리
4. **ErrorDomain**: 도메인별 error_code 범위 관리 (기본 제공 + 커스터마이즈)
5. **FastAPI 통합**: 일관된 JSON 응답과 OpenAPI 문서화

## 프로젝트 구조

```
fastapi-error-codes/
├── src/
│   └── fastapi_error_codes/
│       ├── __init__.py              # 패키지 진입점
│       ├── base.py                  # BaseAppException 클래스
│       ├── decorators.py            # @register_exception 데코레이터
│       ├── registry.py              # 전역 예외 레지스트리
│       ├── domain.py                # ErrorDomain 관리
│       ├── i18n.py                  # 다국어 지원 모듈
│       ├── handlers.py              # FastAPI exception handler
│       ├── models.py                # Response 모델 (Pydantic)
│       ├── config.py                # 설정 관리
│       └── utils.py                 # 유틸리티 함수
├── examples/
│   ├── basic_usage.py               # 기본 사용 예제
│   ├── custom_domains.py            # 커스텀 도메인 예제
│   ├── i18n_example.py              # 다국어 예제
│   └── full_app.py                  # 완전한 FastAPI 앱 예제
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest 설정
│   ├── test_base.py                 # BaseAppException 테스트
│   ├── test_decorators.py           # 데코레이터 테스트
│   ├── test_registry.py             # 레지스트리 테스트
│   ├── test_domain.py               # 도메인 테스트
│   ├── test_i18n.py                 # 다국어 테스트
│   ├── test_handlers.py             # 핸들러 테스트
│   └── test_integration.py          # 통합 테스트
├── locales/
│   ├── en.json                      # 영어 메시지
│   ├── ko.json                      # 한국어 메시지
│   └── ja.json                      # 일본어 메시지
├── docs/
│   ├── quickstart.md                # 빠른 시작 가이드
│   ├── advanced.md                  # 고급 사용법
│   ├── api_reference.md             # API 레퍼런스
│   └── migration.md                 # 마이그레이션 가이드
├── pyproject.toml                   # 패키지 설정
├── README.md                        # 프로젝트 소개
├── CHANGELOG.md                     # 변경 이력
├── LICENSE                          # 라이선스
└── .gitignore                       # Git 제외 파일
```

---

## Phase 1: 프로젝트 초기 설정

### Task 1.1: 프로젝트 디렉토리 구조 생성

**설명**: 패키지 개발에 필요한 기본 디렉토리 구조를 생성합니다.

**Claude Code 명령어**:
```bash
claude create "Create the complete directory structure for fastapi-error-codes package

Create the following directory structure:
fastapi-error-codes/
├── src/fastapi_error_codes/
├── examples/
├── tests/
├── locales/
└── docs/

Requirements:
- Create all directories with proper __init__.py files where needed
- Add .gitkeep files in empty directories
- Follow Python package best practices
- Ensure proper namespace packaging (src layout)

Location: /home/claude/fastapi-error-codes/"
```

**검증 방법**:
```bash
cd fastapi-error-codes
tree -L 3
# 모든 디렉토리가 생성되었는지 확인
```

**예상 결과**: 완전한 디렉토리 구조가 생성됨

---

### Task 1.2: pyproject.toml 설정 파일 생성

**설명**: 패키지 메타데이터, 의존성, 빌드 설정을 정의합니다.

**Claude Code 명령어**:
```bash
claude create "Create pyproject.toml for fastapi-error-codes package in fastapi-error-codes/pyproject.toml

Package Information:
- Name: fastapi-error-codes
- Version: 0.1.0
- Description: Structured exception handling with error codes and i18n support for FastAPI
- Authors: [to be filled]
- License: MIT
- Python: >=3.8
- Homepage: [to be filled]
- Requires-python: >=3.8

Dependencies:
- fastapi >= 0.68.0
- pydantic >= 1.8.0,<3.0.0  (support both v1 and v2)
- typing-extensions >= 4.0.0 (for Python 3.8-3.9 compatibility)

Optional Dependencies:
[project.optional-dependencies]
dev = [
    pytest >= 7.0.0,
    pytest-asyncio >= 0.21.0,
    pytest-cov >= 4.0.0,
    black >= 23.0.0,
    ruff >= 0.1.0,
    mypy >= 1.0.0,
    httpx >= 0.24.0,
]

Build System:
- Use hatchling as build backend (recommended for uv)
- Configure package discovery for src layout

Project URLs:
- Repository: https://github.com/[username]/fastapi-error-codes
- Documentation: https://fastapi-error-codes.readthedocs.io
- Issues: https://github.com/[username]/fastapi-error-codes/issues

Tool Configurations:
[tool.pytest.ini_options]
- testpaths: tests
- python_files: test_*.py
- python_functions: test_*
- asyncio_mode: auto
- addopts: -v --strict-markers

[tool.black]
- line-length: 100
- target-version: py38

[tool.ruff]
- line-length: 100
- target-version: py38
- select: [E, F, I, N, W, UP]

[tool.mypy]
- python_version: 3.8
- strict: true
- warn_return_any: true
- warn_unused_configs: true

[tool.coverage.run]
- source: [src]
- omit: [tests/*, */test_*.py]

[tool.coverage.report]
- exclude_lines: [
    pragma: no cover,
    def __repr__,
    raise AssertionError,
    raise NotImplementedError,
    if __name__ == .__main__.:,
    if TYPE_CHECKING:,
]

Output format: Modern pyproject.toml using hatchling backend
Ensure compatible with uv package manager"
```

**검증 방법**:
```bash
cd fastapi-error-codes
cat pyproject.toml

# uv를 사용한 설치 테스트
uv venv
source .venv/bin/activate
uv pip install -e .
# 에러 없이 설치되는지 확인
```

**예상 결과**: 유효한 pyproject.toml 파일 생성, uv로 로컬 설치 가능

---

### Task 1.3: 패키지 진입점 설정

**설명**: src/fastapi_error_codes/__init__.py에 주요 API를 export합니다.

**Claude Code 명령어**:
```bash
claude create "Create package entry point __init__.py in src/fastapi_error_codes/__init__.py

Purpose: Export main public API for users

Exports:
- BaseAppException (from .base)
- register_exception (from .decorators)
- ErrorDomain (from .domain)
- setup_exception_handler (from .handlers)
- ErrorHandlerConfig (from .config)

Version:
- __version__ = '0.1.0'

Module docstring:
'''
fastapi-error-codes: Structured exception handling for FastAPI

This package provides:
- Custom error codes for better API error tracking
- Multi-level fallback for internationalized error messages
- Automatic FastAPI integration with consistent JSON responses
- Domain-based error code organization
- OpenAPI/Swagger documentation support

Basic Usage:
    from fastapi import FastAPI
    from fastapi_error_codes import BaseAppException, register_exception, setup_exception_handler
    
    @register_exception(error_code=201, message='Authentication required')
    class AuthRequiredException(BaseAppException):
        pass
    
    app = FastAPI()
    setup_exception_handler(app)
    
    @app.get('/protected')
    def protected_route():
        raise AuthRequiredException()

For more examples, see: https://github.com/[username]/fastapi-error-codes/tree/main/examples
'''

Requirements:
- Follow PEP 8 style
- Use __all__ to explicitly define public API
- Add type hints with TYPE_CHECKING
- Keep imports lazy where possible for performance"
```

**검증 방법**:
```python
from fastapi_error_codes import __version__, BaseAppException
print(__version__)
print(BaseAppException)
```

**예상 결과**: 패키지 import 가능, 버전 확인 가능

---

## Phase 2: 핵심 기능 구현

### Task 2.1: BaseAppException 클래스 구현

**설명**: 모든 커스텀 예외의 기본이 되는 BaseAppException 클래스를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement BaseAppException class in src/fastapi_error_codes/base.py

Purpose: Base exception class for all custom exceptions with error_code support

Class: BaseAppException(Exception)

Attributes:
- error_code: int (custom application error code)
- message: str (error message, supports i18n)
- status_code: int (HTTP status code, default 400)
- detail: Optional[Any] (additional error details, can be dict/list/str)
- headers: Optional[Dict[str, str]] (custom HTTP headers)

Methods:
- __init__(self, error_code: int, message: str, status_code: int = 400, detail: Any = None, headers: Dict[str, str] = None)
- __str__(self) -> str: Return formatted error message
- __repr__(self) -> str: Return detailed representation
- to_dict(self) -> Dict[str, Any]: Convert to dictionary for JSON response
- add_detail(self, key: str, value: Any) -> None: Add detail information

Properties:
- timestamp: str (ISO format, auto-generated on creation)
- error_name: str (class name for logging)

Features:
- Automatic timestamp generation using datetime.utcnow()
- Support for nested detail information
- Type hints for all parameters and return types
- Comprehensive docstrings with examples

Example Usage in docstring:
```python
class UserNotFoundException(BaseAppException):
    def __init__(self, user_id: int):
        super().__init__(
            error_code=404,
            message=f'User {user_id} not found',
            status_code=404,
            detail={'user_id': user_id}
        )
```

Requirements:
- Inherit from Python's built-in Exception
- Store all parameters as instance variables
- Implement __str__ for readable error messages
- Implement to_dict() for JSON serialization
- Add comprehensive type hints
- Follow Python exception best practices
- Include detailed docstrings with parameter descriptions
- Add usage examples in docstring"
```

**검증 방법**:
```python
from fastapi_error_codes.base import BaseAppException

exc = BaseAppException(
    error_code=201,
    message="Authentication required",
    status_code=401
)
print(exc.to_dict())
assert exc.error_code == 201
assert exc.status_code == 401
```

**예상 결과**: BaseAppException 클래스가 정상 동작하며 to_dict() 메서드로 직렬화 가능

---

### Task 2.2: Exception Registry 구현

**설명**: 등록된 예외들을 관리하는 전역 레지스트리를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement ExceptionRegistry in src/fastapi_error_codes/registry.py

Purpose: Global registry to manage registered exceptions and prevent duplicate error codes

Class: ExceptionRegistry

Data Structures:
- _exceptions: Dict[int, Type[BaseAppException]] (error_code -> exception class)
- _messages: Dict[int, str] (error_code -> default message)
- _metadata: Dict[int, Dict[str, Any]] (error_code -> metadata)

Methods:
- register(error_code: int, exception_class: Type[BaseAppException], message: str, **metadata) -> None
  * Register an exception with its error code
  * Check for duplicate error codes
  * Store exception class and metadata
  * Raise ValueError if error_code already registered

- get_exception(error_code: int) -> Optional[Type[BaseAppException]]
  * Retrieve exception class by error code
  * Return None if not found

- get_message(error_code: int) -> Optional[str]
  * Retrieve default message by error code
  * Return None if not found

- get_metadata(error_code: int) -> Optional[Dict[str, Any]]
  * Retrieve metadata by error code
  * Return None if not found

- is_registered(error_code: int) -> bool
  * Check if error code is already registered

- get_all_codes() -> List[int]
  * Return list of all registered error codes
  * Useful for documentation and debugging

- clear() -> None
  * Clear all registrations (for testing)

- get_registry_info() -> Dict[str, Any]
  * Return complete registry information
  * Format: {error_code: {class, message, metadata}}

Singleton Pattern:
- Use module-level instance: _registry = ExceptionRegistry()
- Provide module-level functions for easy access

Module-level functions:
- register_error_code(...)
- get_error_code_info(...)
- list_error_codes()

Thread Safety:
- Use threading.Lock for thread-safe operations
- Protect all read/write operations

Error Handling:
- Raise ValueError for duplicate error codes with clear message
- Raise KeyError for non-existent error codes when required
- Log warnings for potential issues

Logging:
- Log all registration attempts
- Log conflicts and errors
- Use Python's logging module

Requirements:
- Thread-safe implementation
- Clear error messages
- Comprehensive logging
- Type hints for all methods
- Detailed docstrings
- Usage examples in module docstring"
```

**검증 방법**:
```python
from fastapi_error_codes.registry import _registry

_registry.register(201, AuthException, "Auth required")
assert _registry.is_registered(201) == True
assert _registry.get_message(201) == "Auth required"

# 중복 등록 시 에러
try:
    _registry.register(201, OtherException, "Other")
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "already registered" in str(e)
```

**예상 결과**: 예외 등록/조회 가능, 중복 검사 동작

---

### Task 2.3: @register_exception 데코레이터 구현

**설명**: 예외 클래스를 자동으로 등록하는 데코레이터를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement @register_exception decorator in src/fastapi_error_codes/decorators.py

Purpose: Decorator to automatically register exception classes with error codes

Decorator Function: register_exception

Parameters:
- error_code: int (required) - Custom error code (0-9999)
- message: str (optional) - Default error message
- message_key: Optional[str] (optional) - i18n message key for localization
- status_code: int (optional, default=400) - HTTP status code
- domain: Optional[str] (optional) - Error domain for organization
- metadata: Optional[Dict[str, Any]] (optional) - Additional metadata

Returns:
- Callable decorator that wraps exception class

Functionality:
1. Validate error_code (must be int, 0-9999)
2. Validate status_code (must be valid HTTP code 100-599)
3. Generate default message if not provided (from class name)
   - Example: AuthenticationRequiredException -> "Authentication Required Exception"
   - Use utils.class_name_to_message() helper
4. Register exception in global registry
5. Set class attributes:
   - _error_code = error_code
   - _default_message = message
   - _message_key = message_key
   - _status_code = status_code
   - _domain = domain
6. Preserve original class (don't modify __init__)
7. Handle registration errors gracefully

Auto-message generation:
- Convert CamelCase to spaces: UserNotFoundException -> "User Not Found Exception"
- Remove trailing "Exception" from display
- Emit warning if auto-generated

Error Handling:
- Raise TypeError if applied to non-class
- Raise ValueError if error_code invalid (< 0, > 9999, non-int)
- Raise ValueError if status_code invalid
- Raise ValueError if duplicate error_code (via registry)
- Clear error messages indicating the problem

Usage Examples in docstring:
```python
# Basic usage
@register_exception(error_code=201, message='Authentication required')
class AuthRequiredException(BaseAppException):
    pass

# With i18n support
@register_exception(
    error_code=202,
    message='Invalid credentials',
    message_key='auth.invalid_credentials',
    status_code=401
)
class InvalidCredentialsException(BaseAppException):
    pass

# With domain
@register_exception(
    error_code=301,
    message='Resource not found',
    domain='resource',
    status_code=404
)
class ResourceNotFoundException(BaseAppException):
    pass

# Minimal (auto-generated message with warning)
@register_exception(error_code=203)
class PaymentFailedException(BaseAppException):
    pass
# Warning: No message provided for error_code 203, using auto-generated: "Payment Failed Exception"
```

Requirements:
- Import BaseAppException and ExceptionRegistry
- Use functools.wraps to preserve class metadata
- Add comprehensive parameter validation
- Log all registrations (INFO level)
- Log warnings for auto-generated messages
- Type hints for decorator and wrapped class
- Detailed docstrings with examples
- Handle edge cases (non-BaseAppException classes)"
```

**검증 방법**:
```python
from fastapi_error_codes import register_exception, BaseAppException

@register_exception(error_code=201, message="Auth required")
class AuthRequiredException(BaseAppException):
    pass

assert AuthRequiredException._error_code == 201
assert AuthRequiredException._default_message == "Auth required"

exc = AuthRequiredException()
assert exc.error_code == 201
```

**예상 결과**: 데코레이터로 예외 등록 가능, 클래스 속성 설정됨

---

### Task 2.4: ErrorDomain 관리 클래스 구현

**설명**: 도메인별 error_code 범위를 관리하는 ErrorDomain 클래스를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement ErrorDomain management in src/fastapi_error_codes/domain.py

Purpose: Manage error code ranges by domain for better organization

Class: ErrorDomain

Built-in Domains (class attributes):
- AUTH = (200, 299): Authentication and authorization errors
- RESOURCE = (300, 399): Resource-related errors (not found, conflict, etc.)
- VALIDATION = (400, 499): Input validation and business rule errors
- BUSINESS = (500, 599): Business logic errors
- SYSTEM = (600, 699): System and infrastructure errors
- EXTERNAL = (700, 799): External service integration errors

Custom Domains Storage:
- _custom_domains: Dict[str, Tuple[int, int]] (domain name -> range)

Methods:
- register_domain(name: str, start: int, end: int) -> None
  * Register a custom domain with error code range
  * Validate range (start <= end, both 0-9999)
  * Check for overlaps with existing domains
  * Store in _custom_domains

- get_domain_range(name: str) -> Optional[Tuple[int, int]]
  * Get error code range for a domain
  * Check built-in domains first, then custom
  * Return None if domain not found

- validate_error_code(error_code: int, domain: Optional[str] = None) -> bool
  * Validate if error_code is within domain range
  * If domain is None, check all domains
  * Return True if valid, False otherwise

- get_domain_for_code(error_code: int) -> Optional[str]
  * Find which domain an error code belongs to
  * Check built-in domains first, then custom
  * Return domain name or None

- list_domains() -> Dict[str, Tuple[int, int]]
  * Return all domains (built-in + custom)
  * Format: {domain_name: (start, end)}

- check_overlap(start: int, end: int) -> List[str]
  * Check if range overlaps with existing domains
  * Return list of overlapping domain names
  * Used for validation before registration

- get_available_ranges() -> List[Tuple[int, int]]
  * Return available (unassigned) error code ranges
  * Useful for suggesting new domain ranges

Singleton Pattern:
- Module-level instance: error_domain = ErrorDomain()
- Export for direct use

Helper Functions:
- in_auth_range(error_code: int) -> bool
- in_resource_range(error_code: int) -> bool
- in_validation_range(error_code: int) -> bool
  (etc. for each built-in domain)

Usage Examples in docstring:
```python
from fastapi_error_codes import ErrorDomain, register_exception, BaseAppException

# Use built-in domains
@register_exception(
    error_code=201,  # In AUTH range (200-299)
    message='Authentication required',
    domain='AUTH'
)
class AuthRequiredException(BaseAppException):
    pass

# Register custom domain
ErrorDomain.register_domain('PAYMENT', 800, 899)

@register_exception(
    error_code=801,
    message='Payment failed',
    domain='PAYMENT'
)
class PaymentFailedException(BaseAppException):
    pass

# Validate error code
assert ErrorDomain.validate_error_code(201, 'AUTH') == True
assert ErrorDomain.get_domain_for_code(201) == 'AUTH'

# List all domains
domains = ErrorDomain.list_domains()
print(domains)  # {'AUTH': (200, 299), 'PAYMENT': (800, 899), ...}
```

Error Handling:
- Raise ValueError for invalid ranges (start > end, out of bounds)
- Raise ValueError for overlapping domains
- Raise ValueError for duplicate domain names
- Clear error messages with conflicting domain info

Requirements:
- Thread-safe implementation
- Clear validation with helpful error messages
- Comprehensive docstrings
- Type hints for all methods
- Logging for domain registration and conflicts
- Include usage examples"
```

**검증 방법**:
```python
from fastapi_error_codes.domain import ErrorDomain

# 빌트인 도메인 확인
assert ErrorDomain.AUTH == (200, 299)
assert ErrorDomain.validate_error_code(201, 'AUTH') == True

# 커스텀 도메인 등록
ErrorDomain.register_domain('PAYMENT', 800, 899)
assert ErrorDomain.get_domain_range('PAYMENT') == (800, 899)

# 오버랩 체크
overlaps = ErrorDomain.check_overlap(250, 350)
assert 'AUTH' in overlaps and 'RESOURCE' in overlaps
```

**예상 결과**: 도메인 범위 관리 가능, 검증 기능 동작

---

## Phase 3: 다국어 지원

### Task 3.1: i18n 모듈 구현

**설명**: 다국어 메시지를 로드하고 관리하는 i18n 모듈을 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement i18n (internationalization) module in src/fastapi_error_codes/i18n.py

Purpose: Manage multi-language error messages with fallback mechanism

Class: MessageProvider

Attributes:
- locales_dir: str (path to locales directory)
- default_locale: str (default locale, e.g., 'en')
- _messages: Dict[str, Dict[str, str]] (locale -> {error_code: message})
- _loaded_locales: Set[str] (set of loaded locale codes)

Methods:
- __init__(locales_dir: str = './locales', default_locale: str = 'en')
  * Initialize with locales directory path
  * Set default locale

- load_locale(locale: str) -> bool
  * Load messages from JSON file: {locales_dir}/{locale}.json
  * Parse JSON: {\"error_code\": \"message\", ...}
  * Error codes can be string or int in JSON
  * Store in _messages[locale]
  * Add to _loaded_locales
  * Return True if successful, False if file not found
  * Log loading status

- load_all_locales() -> int
  * Scan locales directory for *.json files
  * Load all found locales
  * Return count of loaded locales
  * Skip invalid JSON files with warning

- get_message(error_code: int, locale: str = None, default: str = None) -> str
  * Multi-level fallback:
    1. Try requested locale (if provided)
    2. Try default locale
    3. Return provided default (if provided)
    4. Return auto-generated message from error_code
  * Convert error_code to string for JSON lookup
  * Log fallback levels for debugging

- add_message(error_code: int, locale: str, message: str) -> None
  * Programmatically add a message
  * Useful for runtime additions

- has_locale(locale: str) -> bool
  * Check if locale is loaded

- get_available_locales() -> List[str]
  * Return list of loaded locale codes

- get_locale_messages(locale: str) -> Dict[str, str]
  * Return all messages for a locale
  * Return empty dict if locale not loaded

Helper Functions:
- normalize_locale(locale: str) -> str
  * Normalize locale code: 'en-US' -> 'en', 'ko-KR' -> 'ko'
  * Handle Accept-Language header format

- extract_locale_from_request(request: Request) -> str
  * Extract locale from FastAPI request
  * Parse Accept-Language header
  * Return normalized locale code or default

- auto_generate_message(error_code: int, exception_class_name: str = None) -> str
  * Generate message from error code or class name
  * Format: \"Error {error_code} occurred\" or convert class name

JSON File Format:
{
    \"200\": \"Success\",
    \"201\": \"Authentication required\",
    \"202\": \"Invalid credentials\",
    \"301\": \"Resource not found\"
}

Usage Examples in docstring:
```python
from fastapi_error_codes.i18n import MessageProvider

# Initialize
provider = MessageProvider(locales_dir='./locales', default_locale='en')
provider.load_all_locales()

# Get message with fallback
message = provider.get_message(
    error_code=201,
    locale='ko',  # Try Korean first
    default='Authentication required'  # Final fallback
)

# Fallback chain:
# 1. ko.json -> \"201\": \"인증이 필요합니다\" (found)
# 2. en.json (default locale) - skipped
# 3. default parameter - skipped
# Result: \"인증이 필요합니다\"

# If 'ko' not found:
# 1. ko.json -> not found
# 2. en.json -> \"201\": \"Authentication required\" (found)
# Result: \"Authentication required\"

# From FastAPI request
from fastapi import Request
locale = extract_locale_from_request(request)
message = provider.get_message(201, locale=locale)
```

Error Handling:
- Log warnings for missing locale files
- Log warnings for JSON parse errors
- Log info for fallback usage
- Never raise exceptions (graceful degradation)

Requirements:
- Use pathlib for file handling
- Handle FileNotFoundError gracefully
- Handle JSONDecodeError gracefully
- Thread-safe if needed
- Comprehensive logging
- Type hints for all methods
- Detailed docstrings with examples
- Performance: cache loaded messages in memory"
```

**검증 방법**:
```python
from fastapi_error_codes.i18n import MessageProvider

provider = MessageProvider(locales_dir='./locales')
provider.load_locale('en')
provider.load_locale('ko')

# 영어 메시지
msg_en = provider.get_message(201, locale='en')
print(msg_en)  # "Authentication required"

# 한국어 메시지
msg_ko = provider.get_message(201, locale='ko')
print(msg_ko)  # "인증이 필요합니다"

# Fallback 테스트 (존재하지 않는 locale)
msg_fallback = provider.get_message(201, locale='fr', default='Auth required')
assert msg_fallback == 'Auth required'
```

**예상 결과**: JSON 파일에서 메시지 로드 가능, fallback 체인 동작

---

### Task 3.2: 기본 locale 파일 생성

**설명**: 영어(en), 한국어(ko), 일본어(ja) 기본 locale JSON 파일을 생성합니다.

**Claude Code 명령어**:
```bash
claude create "Create default locale files for common error messages

Location: locales/ directory

Create three files:
1. locales/en.json
2. locales/ko.json  
3. locales/ja.json

Content for each file (translate appropriately):

Common error codes to include:
- 200: Success
- 201: Authentication required
- 202: Invalid credentials
- 203: Insufficient permissions
- 204: Token expired
- 205: Invalid token
- 301: Resource not found
- 302: Resource already exists
- 303: Resource conflict
- 401: Invalid input data
- 402: Validation failed
- 403: Required field missing
- 501: Internal server error
- 502: Service unavailable
- 503: Database connection failed
- 504: External service error

Format:
{
    \"200\": \"Success message in target language\",
    \"201\": \"Authentication message in target language\",
    ...
}

Requirements:
- Valid JSON format
- Consistent error code keys (as strings)
- Professional, clear messages
- Natural language for each locale
- Same error codes in all files
- UTF-8 encoding
- Pretty-printed with 2-space indentation

en.json - English:
- Use simple, clear English
- Professional tone
- Standard API error message style

ko.json - Korean:
- Natural Korean expressions
- Formal tone (합니다체)
- Common Korean API terminology

ja.json - Japanese:
- Natural Japanese expressions  
- Polite form (です・ます調)
- Common Japanese API terminology

Add comment at top of each file (as first key):
\"_comment\": \"Default error messages for fastapi-error-codes package\"

Example en.json structure:
{
    \"_comment\": \"Default error messages for fastapi-error-codes package\",
    \"200\": \"Success\",
    \"201\": \"Authentication is required to access this resource\",
    \"202\": \"The provided email or password is incorrect\",
    ...
}"
```

**검증 방법**:
```bash
cd locales
cat en.json | jq .
cat ko.json | jq .
cat ja.json | jq .
# 모두 유효한 JSON인지 확인
```

**예상 결과**: 3개의 locale JSON 파일 생성, 유효한 JSON 형식

---

## Phase 4: FastAPI 통합

### Task 4.1: Response 모델 정의

**설명**: 에러 응답을 위한 Pydantic 모델을 정의합니다.

**Claude Code 명령어**:
```bash
claude create "Define response models in src/fastapi_error_codes/models.py

Purpose: Pydantic models for structured error responses

Models:

1. ErrorResponse (main error response model)
Fields:
- error_code: int (application error code)
- message: str (error message, possibly localized)
- detail: Optional[Any] (additional details, flexible type)
- timestamp: str (ISO 8601 format timestamp)
- path: Optional[str] (request path where error occurred)

Config:
- json_schema_extra: Provide example for OpenAPI docs

2. ErrorDetail (for structured detail information)
Fields:
- field: Optional[str] (field name for validation errors)
- message: str (detail message)
- code: Optional[str] (sub-error code)

Usage: detail can be ErrorDetail, List[ErrorDetail], dict, or string

3. ValidationErrorResponse (for validation errors)
Inherits from ErrorResponse with:
- detail: List[ErrorDetail] (structured validation errors)

Helper Functions:
- create_error_response(
    exception: BaseAppException,
    request: Optional[Request] = None,
    locale: Optional[str] = None
  ) -> ErrorResponse
  * Create ErrorResponse from BaseAppException
  * Add timestamp and path from request
  * Resolve message using i18n if available

- create_validation_error_response(
    errors: List[Dict],
    request: Optional[Request] = None
  ) -> ValidationErrorResponse
  * Convert FastAPI/Pydantic validation errors to structured format
  * Transform [{\"loc\": [\"body\", \"email\"], \"msg\": \"...\", \"type\": \"...\"}]
  * Into ErrorDetail objects

Usage Examples in docstring:
```python
from fastapi_error_codes.models import ErrorResponse, create_error_response

# Basic error response
response = ErrorResponse(
    error_code=201,
    message='Authentication required',
    timestamp='2025-01-13T10:30:00Z',
    path='/api/protected'
)

# From exception
exception = AuthRequiredException()
response = create_error_response(
    exception=exception,
    request=request,
    locale='ko'
)

# With detailed validation errors
response = ValidationErrorResponse(
    error_code=400,
    message='Validation failed',
    detail=[
        ErrorDetail(field='email', message='Invalid email format'),
        ErrorDetail(field='password', message='Too short')
    ],
    timestamp='2025-01-13T10:30:00Z'
)
```

Requirements:
- Use Pydantic BaseModel
- Support both Pydantic v1 and v2 (use compatibility layer if needed)
- Add JSON schema examples for OpenAPI
- Include Field descriptions for documentation
- Type hints for all fields
- Detailed docstrings
- Serialization to JSON dict"
```

**검증 방법**:
```python
from fastapi_error_codes.models import ErrorResponse

response = ErrorResponse(
    error_code=201,
    message="Authentication required",
    timestamp="2025-01-13T10:30:00Z"
)

print(response.model_dump())  # Pydantic v2
# or response.dict() for v1
```

**예상 결과**: Pydantic 모델 정의, JSON 직렬화 가능

---

### Task 4.2: FastAPI Exception Handler 구현

**설명**: FastAPI 앱에 예외 핸들러를 등록하는 함수를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement FastAPI exception handlers in src/fastapi_error_codes/handlers.py

Purpose: Integrate custom exceptions with FastAPI error handling

Main Function: setup_exception_handler

Signature:
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None
) -> None

Parameters:
- app: FastAPI application instance
- config: ErrorHandlerConfig (i18n settings, logging, etc.)

Functionality:
1. Register exception handler for BaseAppException
2. Register handler for RequestValidationError (Pydantic)
3. Register handler for generic Exception (500 fallback)
4. Configure i18n MessageProvider if enabled
5. Configure logging if enabled

Exception Handlers:

1. base_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse
   * Extract locale from request (Accept-Language header)
   * Resolve message using MessageProvider (if i18n enabled)
   * Create ErrorResponse model
   * Log exception with appropriate level
   * Return JSONResponse with proper status_code

2. validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse
   * Convert Pydantic errors to ErrorDetail format
   * Create ValidationErrorResponse
   * Use error_code 422 (Unprocessable Entity)
   * Log validation errors
   * Return JSONResponse with 422 status

3. generic_exception_handler(request: Request, exc: Exception) -> JSONResponse
   * Catch-all for unhandled exceptions
   * Log with ERROR level (include traceback in debug mode)
   * Return generic error response (500)
   * Hide details in production (only show in debug mode)
   * Format: {\"error_code\": 500, \"message\": \"Internal server error\"}

Helper Functions:
- _get_locale_from_request(request: Request) -> str
  * Parse Accept-Language header
  * Return first supported locale or default

- _should_include_details(config: ErrorHandlerConfig) -> bool
  * Return True if debug mode or development environment
  * Hide sensitive details in production

Logging:
- Log BaseAppException with INFO or WARNING level
- Log validation errors with WARNING level
- Log generic exceptions with ERROR level
- Include request info: method, path, client IP
- Include exception traceback in debug mode

Usage Example in docstring:
```python
from fastapi import FastAPI
from fastapi_error_codes import setup_exception_handler, ErrorHandlerConfig, register_exception, BaseAppException

@register_exception(error_code=201, message='Authentication required')
class AuthRequiredException(BaseAppException):
    pass

app = FastAPI()

# Basic setup
setup_exception_handler(app)

# Advanced setup with config
config = ErrorHandlerConfig(
    i18n_enabled=True,
    locales_dir='./locales',
    default_locale='en',
    auto_generate_message=True,
    warn_missing_message=True,
    strict_mode=False,
    debug=True
)
setup_exception_handler(app, config)

@app.get('/protected')
def protected_route():
    raise AuthRequiredException()
# Returns: {\"error_code\": 201, \"message\": \"Authentication required\", \"timestamp\": \"...\"}
```

Requirements:
- Use FastAPI's @app.exception_handler decorator
- Return JSONResponse with correct status_code
- Set Content-Type: application/json
- Include proper CORS headers if configured
- Support both sync and async exception handlers
- Comprehensive logging with structured format
- Type hints for all parameters
- Detailed docstrings with examples
- Handle edge cases (missing config, invalid locale, etc.)"
```

**검증 방법**:
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_error_codes import setup_exception_handler, register_exception, BaseAppException

@register_exception(error_code=201, message="Auth required")
class AuthRequiredException(BaseAppException):
    pass

app = FastAPI()
setup_exception_handler(app)

@app.get("/test")
def test():
    raise AuthRequiredException()

client = TestClient(app)
response = client.get("/test")
assert response.status_code == 400  # or configured status
assert response.json()["error_code"] == 201
```

**예상 결과**: FastAPI 앱에서 예외 발생 시 일관된 JSON 응답 반환

---

### Task 4.3: ErrorHandlerConfig 설정 클래스 구현

**설명**: 핸들러 동작을 제어하는 설정 클래스를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement ErrorHandlerConfig in src/fastapi_error_codes/config.py

Purpose: Configuration class for exception handler behavior

Class: ErrorHandlerConfig

Fields (Pydantic BaseModel or dataclass):

i18n Configuration:
- i18n_enabled: bool = False
  * Enable internationalization support
  
- locales_dir: str = './locales'
  * Path to locales directory containing JSON files
  
- default_locale: str = 'en'
  * Default locale for fallback

Message Generation:
- auto_generate_message: bool = True
  * Auto-generate messages from class names if not provided
  
- warn_missing_message: bool = True
  * Log warning when message is auto-generated
  
- strict_mode: bool = False
  * If True, require explicit message parameter (no auto-generation)

Logging:
- enable_logging: bool = True
  * Enable automatic exception logging
  
- log_level: str = 'INFO'
  * Logging level: DEBUG, INFO, WARNING, ERROR
  
- include_traceback: bool = False
  * Include full traceback in logs (enable in debug)

Response Customization:
- include_path: bool = True
  * Include request path in error response
  
- include_timestamp: bool = True
  * Include timestamp in error response
  
- timestamp_format: str = 'iso'
  * Timestamp format: 'iso' or 'unix'

Debug/Development:
- debug: bool = False
  * Debug mode (show detailed errors, tracebacks)
  
- expose_internal_errors: bool = False
  * Expose internal error details (security risk in production)

Methods:
- validate_config(self) -> None
  * Validate configuration values
  * Check locales_dir exists if i18n_enabled
  * Check log_level is valid
  
- to_dict(self) -> Dict[str, Any]
  * Convert config to dictionary

Class Methods:
- from_env() -> ErrorHandlerConfig
  * Create config from environment variables
  * Prefix: FASTAPI_ERROR_CODES_
  * Example: FASTAPI_ERROR_CODES_I18N_ENABLED=true

- from_dict(config_dict: Dict[str, Any]) -> ErrorHandlerConfig
  * Create config from dictionary

- development() -> ErrorHandlerConfig
  * Preset for development environment
  * debug=True, warn_missing_message=True, include_traceback=True

- production() -> ErrorHandlerConfig
  * Preset for production environment
  * debug=False, expose_internal_errors=False, log_level='ERROR'

Usage Examples in docstring:
```python
from fastapi_error_codes import ErrorHandlerConfig, setup_exception_handler

# Development preset
config = ErrorHandlerConfig.development()
setup_exception_handler(app, config)

# Production preset
config = ErrorHandlerConfig.production()
setup_exception_handler(app, config)

# Custom configuration
config = ErrorHandlerConfig(
    i18n_enabled=True,
    locales_dir='./my_locales',
    default_locale='ko',
    strict_mode=True,
    debug=False
)
setup_exception_handler(app, config)

# From environment variables
config = ErrorHandlerConfig.from_env()
setup_exception_handler(app, config)
```

Environment Variables:
- FASTAPI_ERROR_CODES_I18N_ENABLED: bool
- FASTAPI_ERROR_CODES_LOCALES_DIR: str
- FASTAPI_ERROR_CODES_DEFAULT_LOCALE: str
- FASTAPI_ERROR_CODES_DEBUG: bool
- FASTAPI_ERROR_CODES_LOG_LEVEL: str

Requirements:
- Use Pydantic BaseModel (or dataclass with validation)
- Field validation (e.g., log_level in valid values)
- Default values for all fields
- Detailed docstrings for each field
- Type hints
- Preset factory methods for common scenarios
- Environment variable support"
```

**검증 방법**:
```python
from fastapi_error_codes.config import ErrorHandlerConfig

# 개발 환경 프리셋
dev_config = ErrorHandlerConfig.development()
assert dev_config.debug == True
assert dev_config.include_traceback == True

# 프로덕션 환경 프리셋
prod_config = ErrorHandlerConfig.production()
assert prod_config.debug == False
assert prod_config.expose_internal_errors == False

# 커스텀 설정
custom_config = ErrorHandlerConfig(
    i18n_enabled=True,
    strict_mode=True
)
custom_config.validate_config()
```

**예상 결과**: 설정 클래스로 핸들러 동작 제어 가능, 환경별 프리셋 사용 가능

---

## Phase 5: 테스트 및 문서화

### Task 5.1: 단위 테스트 작성

**설명**: 각 모듈에 대한 포괄적인 단위 테스트를 작성합니다.

**Claude Code 명령어**:
```bash
claude create "Create comprehensive unit tests for fastapi-error-codes

Create test files in tests/ directory:

1. tests/conftest.py - Pytest configuration and fixtures
   * Fixture: temp_locales_dir (temporary locales directory)
   * Fixture: sample_locale_files (create en.json, ko.json)
   * Fixture: clean_registry (clear registry before each test)
   * Fixture: sample_exceptions (create test exception classes)

2. tests/test_base.py - Test BaseAppException
   Test cases:
   * test_create_basic_exception
   * test_exception_with_detail
   * test_exception_to_dict
   * test_exception_str_repr
   * test_exception_timestamp_format
   * test_exception_with_headers
   * test_add_detail_method

3. tests/test_registry.py - Test ExceptionRegistry
   Test cases:
   * test_register_exception
   * test_duplicate_error_code_raises
   * test_get_exception_by_code
   * test_get_message_by_code
   * test_is_registered
   * test_get_all_codes
   * test_clear_registry
   * test_thread_safety (use threading)

4. tests/test_decorators.py - Test @register_exception
   Test cases:
   * test_basic_decorator_usage
   * test_decorator_with_all_params
   * test_decorator_auto_message_generation
   * test_decorator_validation_error_code
   * test_decorator_duplicate_code
   * test_decorator_sets_class_attributes
   * test_decorator_preserves_class

5. tests/test_domain.py - Test ErrorDomain
   Test cases:
   * test_builtin_domains
   * test_register_custom_domain
   * test_domain_overlap_detection
   * test_validate_error_code
   * test_get_domain_for_code
   * test_list_all_domains
   * test_available_ranges

6. tests/test_i18n.py - Test MessageProvider
   Test cases:
   * test_load_locale_file
   * test_load_all_locales
   * test_get_message_with_locale
   * test_message_fallback_chain
   * test_auto_generate_message
   * test_missing_locale_file
   * test_invalid_json_file
   * test_normalize_locale

7. tests/test_models.py - Test Response Models
   Test cases:
   * test_error_response_model
   * test_validation_error_response_model
   * test_create_error_response_helper
   * test_model_serialization
   * test_model_json_schema (for OpenAPI)

8. tests/test_handlers.py - Test FastAPI Integration
   Test cases:
   * test_base_exception_handler
   * test_validation_error_handler
   * test_generic_exception_handler
   * test_locale_extraction
   * test_i18n_integration
   * test_logging_on_exception

Requirements:
- Use pytest framework
- Use pytest-asyncio for async tests
- Use TestClient from fastapi.testclient
- Aim for >90% code coverage
- Use parametrize for multiple test cases
- Use fixtures to reduce duplication
- Test both success and error paths
- Test edge cases and boundary conditions
- Clear test names describing what is tested
- Use assert statements with descriptive messages
- Mock external dependencies where appropriate
- Test thread safety where relevant

Example test structure:
```python
import pytest
from fastapi_error_codes import BaseAppException, register_exception

def test_base_exception_creation():
    '''Test creating a basic exception'''
    exc = BaseAppException(
        error_code=201,
        message='Test error',
        status_code=400
    )
    
    assert exc.error_code == 201
    assert exc.message == 'Test error'
    assert exc.status_code == 400
    assert exc.timestamp is not None

@pytest.mark.parametrize('error_code,expected_domain', [
    (201, 'AUTH'),
    (301, 'RESOURCE'),
    (501, 'BUSINESS'),
])
def test_domain_detection(error_code, expected_domain):
    '''Test error code domain detection'''
    from fastapi_error_codes.domain import ErrorDomain
    domain = ErrorDomain.get_domain_for_code(error_code)
    assert domain == expected_domain
```"
```

**검증 방법**:
```bash
cd fastapi-error-codes
pytest tests/ -v --cov=src/fastapi_error_codes --cov-report=html
# 모든 테스트 통과 확인
# 커버리지 90% 이상 확인
```

**예상 결과**: 모든 단위 테스트 통과, 높은 코드 커버리지

---

### Task 5.2: 통합 테스트 작성

**설명**: 전체 워크플로우를 테스트하는 통합 테스트를 작성합니다.

**Claude Code 명령어**:
```bash
claude create "Create integration tests in tests/test_integration.py

Purpose: Test complete workflows and FastAPI integration

Test Scenarios:

1. Complete Exception Handling Flow
   * Create FastAPI app
   * Register custom exceptions
   * Setup exception handler with config
   * Make requests that trigger exceptions
   * Verify correct JSON responses
   * Verify status codes
   * Verify logging

2. i18n Integration
   * Setup app with i18n enabled
   * Load locale files
   * Make requests with different Accept-Language headers
   * Verify messages in correct language
   * Test fallback when locale not available

3. Domain-based Error Organization
   * Register exceptions in different domains
   * Verify domain validation
   * Test error code range enforcement

4. Multiple Exceptions Workflow
   * Define multiple exception classes
   * Test they don't conflict
   * Test registry management

Test Functions:

test_complete_exception_flow():
    '''Test end-to-end exception handling'''
    * Create app with multiple endpoints
    * Each endpoint raises different exception
    * Test all endpoints return correct responses
    * Use TestClient for HTTP requests

test_i18n_message_resolution():
    '''Test internationalized messages'''
    * Setup with en.json and ko.json
    * Request with Accept-Language: ko
    * Verify Korean message returned
    * Request with Accept-Language: fr
    * Verify English fallback

test_validation_error_handling():
    '''Test Pydantic validation errors'''
    * Define endpoint with Pydantic model
    * Send invalid data
    * Verify ValidationErrorResponse format
    * Verify field-level error details

test_custom_domain_registration():
    '''Test custom error domain workflow'''
    * Register custom domain (PAYMENT: 800-899)
    * Define exception in that range
    * Verify domain validation works

test_concurrent_exception_handling():
    '''Test thread safety with concurrent requests'''
    * Use threading or asyncio
    * Make multiple concurrent requests
    * Verify no race conditions
    * Verify all exceptions handled correctly

test_logging_integration():
    '''Test automatic logging'''
    * Setup app with logging enabled
    * Capture log output
    * Trigger exceptions
    * Verify logs contain expected information

test_openapi_documentation():
    '''Test OpenAPI/Swagger integration'''
    * Check /openapi.json endpoint
    * Verify exception responses documented
    * Verify response models in schema

Example Test:
```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_error_codes import (
    BaseAppException,
    register_exception,
    setup_exception_handler,
    ErrorHandlerConfig
)

def test_complete_exception_flow():
    '''Test complete exception handling workflow'''
    
    # Define exceptions
    @register_exception(error_code=201, message='Auth required')
    class AuthRequiredException(BaseAppException):
        pass
    
    @register_exception(error_code=301, message='User not found')
    class UserNotFoundException(BaseAppException):
        pass
    
    # Create app
    app = FastAPI()
    setup_exception_handler(app)
    
    @app.get('/protected')
    def protected():
        raise AuthRequiredException()
    
    @app.get('/user/{user_id}')
    def get_user(user_id: int):
        if user_id == 999:
            raise UserNotFoundException()
        return {'user_id': user_id}
    
    # Test with client
    client = TestClient(app)
    
    # Test auth exception
    response = client.get('/protected')
    assert response.status_code == 400
    data = response.json()
    assert data['error_code'] == 201
    assert 'Auth required' in data['message']
    assert 'timestamp' in data
    
    # Test user not found
    response = client.get('/user/999')
    assert response.status_code == 400
    data = response.json()
    assert data['error_code'] == 301
    assert 'User not found' in data['message']
    
    # Test successful request
    response = client.get('/user/1')
    assert response.status_code == 200
```

Requirements:
- Use pytest and pytest-asyncio
- Use FastAPI TestClient
- Test real HTTP request/response cycle
- Test with actual locale files (create temp files)
- Test logging with caplog fixture
- Test concurrent scenarios with threading/asyncio
- Clear test isolation (use fixtures)
- Comprehensive assertions
- Test both success and failure paths"
```

**검증 방법**:
```bash
pytest tests/test_integration.py -v -s
# 모든 통합 테스트 통과 확인
```

**예상 결과**: 전체 워크플로우가 정상 동작, 실제 FastAPI 앱에서 예외 처리 검증

---

### Task 5.3: 예제 코드 작성

**설명**: 사용자가 빠르게 시작할 수 있도록 다양한 예제 코드를 작성합니다.

**Claude Code 명령어**:
```bash
claude create "Create example applications in examples/ directory

Create the following example files:

1. examples/basic_usage.py - Basic exception handling
   * Simple FastAPI app
   * Define 2-3 custom exceptions
   * Register with @register_exception
   * Setup exception handler
   * Create endpoints that raise exceptions
   * Include comments explaining each step
   * Runnable with: uvicorn basic_usage:app --reload

2. examples/custom_domains.py - Custom error domains
   * Register custom domains (PAYMENT, NOTIFICATION)
   * Define exceptions in each domain
   * Show domain validation
   * Demonstrate get_domain_for_code()
   * Include comprehensive comments

3. examples/i18n_example.py - Internationalization
   * Setup app with i18n enabled
   * Create sample locale files (en, ko, ja)
   * Define exceptions with message_key
   * Create endpoints that return localized messages
   * Test with curl examples in comments
   * Show fallback behavior

4. examples/full_app.py - Complete realistic application
   * User management API
   * Multiple domains (AUTH, USER, VALIDATION)
   * 10+ custom exceptions
   * i18n support
   * Input validation
   * Logging configured
   * OpenAPI documentation
   * Production-ready structure
   * Includes README in comments

5. examples/README.md - Examples documentation
   * Overview of each example
   * How to run each example
   * What each example demonstrates
   * Expected output examples
   * Links to relevant documentation

Example Structure for basic_usage.py:
```python
'''
Basic Usage Example for fastapi-error-codes

This example demonstrates:
- Defining custom exceptions with error codes
- Registering exceptions with @register_exception
- Setting up FastAPI exception handler
- Creating endpoints that raise exceptions

Run with: uvicorn basic_usage:app --reload
Test with: curl http://localhost:8000/protected
'''

from fastapi import FastAPI
from fastapi_error_codes import (
    BaseAppException,
    register_exception,
    setup_exception_handler
)

# Define custom exceptions
@register_exception(
    error_code=201,
    message='Authentication is required to access this resource'
)
class AuthenticationRequiredException(BaseAppException):
    pass

@register_exception(
    error_code=202,
    message='The provided credentials are invalid'
)
class InvalidCredentialsException(BaseAppException):
    pass

@register_exception(
    error_code=301,
    message='The requested user was not found',
    status_code=404
)
class UserNotFoundException(BaseAppException):
    pass

# Create FastAPI app
app = FastAPI(title='Basic Usage Example')

# Setup exception handler
setup_exception_handler(app)

# Define endpoints
@app.get('/')
def root():
    return {'message': 'Welcome to fastapi-error-codes example'}

@app.get('/protected')
def protected_route():
    '''This endpoint requires authentication'''
    raise AuthenticationRequiredException()

@app.post('/login')
def login(username: str, password: str):
    '''Login endpoint that checks credentials'''
    if username != 'admin' or password != 'secret':
        raise InvalidCredentialsException()
    return {'token': 'fake-jwt-token'}

@app.get('/users/{user_id}')
def get_user(user_id: int):
    '''Get user by ID'''
    if user_id == 999:
        raise UserNotFoundException()
    return {'user_id': user_id, 'name': f'User {user_id}'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

# Test commands:
# curl http://localhost:8000/
# curl http://localhost:8000/protected
# curl -X POST \"http://localhost:8000/login?username=admin&password=wrong\"
# curl http://localhost:8000/users/999
```

Requirements:
- Fully runnable examples
- Comprehensive comments
- Clear structure
- Demonstrate different features
- Include test commands
- Follow FastAPI best practices
- Include type hints
- PEP 8 compliant code"
```

**검증 방법**:
```bash
cd examples
python basic_usage.py
# 다른 터미널에서:
curl http://localhost:8000/protected
# 응답 확인

python i18n_example.py
curl -H "Accept-Language: ko" http://localhost:8000/test
# 한국어 메시지 확인
```

**예상 결과**: 모든 예제가 실행 가능, 각 기능 시연

---

### Task 5.4: README 및 문서 작성

**설명**: 프로젝트 README와 상세 문서를 작성합니다.

**Claude Code 명령어**:
```bash
claude create "Create comprehensive documentation for fastapi-error-codes

1. README.md in root directory
   Structure:
   * Project title and description
   * Badges (build, coverage, version, license)
   * Key features (bullet points)
   * Quick start (installation, basic example)
   * Installation instructions (pip install)
   * Basic usage with code example
   * Documentation links
   * Contributing guidelines
   * License
   * Acknowledgments

2. docs/quickstart.md - Quick Start Guide
   Content:
   * Installation
   * First steps
   * Define your first exception
   * Setup FastAPI app
   * Test it
   * Next steps

3. docs/advanced.md - Advanced Usage
   Topics:
   * Custom error domains
   * Internationalization setup
   * Custom configuration
   * Logging configuration
   * Production deployment
   * Best practices
   * Performance considerations

4. docs/api_reference.md - API Reference
   Document all public APIs:
   * BaseAppException
   * @register_exception
   * ErrorDomain
   * MessageProvider
   * setup_exception_handler
   * ErrorHandlerConfig
   * Response models
   
   For each API:
   - Description
   - Parameters
   - Return type
   - Examples
   - Notes

5. CHANGELOG.md - Version history
   Format:
   ## [0.1.0] - 2025-01-13
   ### Added
   - Initial release
   - BaseAppException class
   - @register_exception decorator
   - Multi-language support
   - FastAPI integration
   - Domain-based error codes

README.md Template:
```markdown
# fastapi-error-codes

[![Build Status](https://img.shields.io/github/workflow/status/[user]/fastapi-error-codes/CI)](...)
[![Coverage](https://img.shields.io/codecov/c/github/[user]/fastapi-error-codes)](...)
[![PyPI version](https://img.shields.io/pypi/v/fastapi-error-codes.svg)](...)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-error-codes.svg)](...)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](...)

Structured exception handling with error codes and internationalization for FastAPI applications.

## ✨ Features

- 🔢 **Custom Error Codes**: Define application-specific error codes for better tracking
- 🌍 **i18n Support**: Multi-language error messages with automatic fallback
- 📝 **Domain Organization**: Organize errors by domain (auth, validation, business, etc.)
- 🎯 **FastAPI Integration**: Seamless integration with automatic handler setup
- 📚 **OpenAPI Documentation**: Automatic Swagger/OpenAPI documentation
- 🔒 **Type Safe**: Full type hints support
- 🧪 **Well Tested**: >90% test coverage

## 🚀 Quick Start

### Installation

```bash
pip install fastapi-error-codes
```

### Basic Usage

```python
from fastapi import FastAPI
from fastapi_error_codes import BaseAppException, register_exception, setup_exception_handler

# Define your exceptions
@register_exception(error_code=201, message='Authentication required')
class AuthRequiredException(BaseAppException):
    pass

# Create FastAPI app
app = FastAPI()
setup_exception_handler(app)

# Use in endpoints
@app.get('/protected')
def protected():
    raise AuthRequiredException()
```

Run and test:
```bash
uvicorn main:app --reload
curl http://localhost:8000/protected
```

Response:
```json
{
  \"error_code\": 201,
  \"message\": \"Authentication required\",
  \"timestamp\": \"2025-01-13T10:30:00Z\",
  \"path\": \"/protected\"
}
```

## 📖 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Advanced Usage](docs/advanced.md)
- [API Reference](docs/api_reference.md)
- [Examples](examples/)

## 🌍 Internationalization

```python
from fastapi_error_codes import setup_exception_handler, ErrorHandlerConfig

config = ErrorHandlerConfig(
    i18n_enabled=True,
    locales_dir='./locales',
    default_locale='en'
)
setup_exception_handler(app, config)

# Client sends: Accept-Language: ko
# Response includes Korean message
```

## 🎯 Error Domains

```python
from fastapi_error_codes import ErrorDomain

# Built-in domains
ErrorDomain.AUTH = (200, 299)
ErrorDomain.RESOURCE = (300, 399)
ErrorDomain.VALIDATION = (400, 499)

# Register custom domain
ErrorDomain.register_domain('PAYMENT', 800, 899)
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Inspired by [APIException](https://github.com/akutayural/APIException)
- Built for the [FastAPI](https://fastapi.tiangolo.com/) framework
```

Requirements:
- Clear, professional writing
- Code examples that work
- Links to all relevant sections
- Follow common README patterns
- Include badges (build, coverage, version)
- Markdown formatting
- Table of contents for long docs
- Cross-references between docs"
```

**검증 방법**:
```bash
# README 렌더링 확인
cat README.md

# 링크 체크
# 모든 내부 링크가 유효한지 확인

# 예제 코드 실행 가능 여부 확인
# README의 코드 예제를 복사해서 실행
```

**예상 결과**: 명확하고 포괄적인 문서, 사용자가 쉽게 시작 가능

---

## Phase 6: 패키징 및 배포

### Task 6.1: 유틸리티 함수 구현

**설명**: 여러 모듈에서 사용하는 공통 유틸리티 함수를 구현합니다.

**Claude Code 명령어**:
```bash
claude create "Implement utility functions in src/fastapi_error_codes/utils.py

Purpose: Common utility functions used across the package

Functions:

1. class_name_to_message(class_name: str) -> str
   '''Convert exception class name to readable message'''
   * Convert CamelCase to spaces
   * Remove 'Exception' suffix
   * Example: AuthenticationRequiredException -> 'Authentication Required'
   
   Algorithm:
   - Insert space before uppercase letters
   - Remove 'Exception' at end
   - Capitalize words properly
   - Handle acronyms (e.g., 'HTTPError' -> 'HTTP Error')

2. validate_error_code(error_code: int) -> None
   '''Validate error code is in valid range'''
   * Check 0 <= error_code <= 9999
   * Raise ValueError if invalid
   * Clear error message

3. validate_status_code(status_code: int) -> None
   '''Validate HTTP status code'''
   * Check 100 <= status_code <= 599
   * Raise ValueError if invalid
   * Include valid ranges in error message

4. get_timestamp(format: str = 'iso') -> str
   '''Get current timestamp in specified format'''
   * format='iso': ISO 8601 format (default)
   * format='unix': Unix timestamp
   * Use UTC timezone

5. normalize_locale(locale: str) -> str
   '''Normalize locale code'''
   * 'en-US' -> 'en'
   * 'ko-KR' -> 'ko'
   * Handle None/empty string

6. parse_accept_language(header: str) -> List[str]
   '''Parse Accept-Language header'''
   * Example: 'en-US,en;q=0.9,ko;q=0.8' -> ['en-US', 'en', 'ko']
   * Sort by quality value
   * Return list of locale codes

7. truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str
   '''Truncate string to max length'''
   * For logging long error messages
   * Add suffix if truncated

8. safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any
   '''Safely get attribute with default'''
   * Like getattr but with better typing
   * Used for optional attributes

9. mask_sensitive_data(data: Dict[str, Any], keys: List[str] = None) -> Dict[str, Any]
   '''Mask sensitive information in dict'''
   * Default keys: password, token, secret, api_key
   * Replace with '***'
   * For logging request/response data

10. merge_dicts(*dicts: Dict) -> Dict
    '''Merge multiple dictionaries'''
    * Later dicts override earlier ones
    * Deep merge for nested dicts

Usage Examples in docstring:
```python
from fastapi_error_codes.utils import class_name_to_message, validate_error_code

# Convert class name
message = class_name_to_message('UserNotFoundException')
print(message)  # 'User Not Found'

# Validate error code
validate_error_code(201)  # OK
validate_error_code(-1)  # Raises ValueError

# Parse Accept-Language
locales = parse_accept_language('en-US,en;q=0.9,ko;q=0.8')
print(locales)  # ['en-US', 'en', 'ko']

# Mask sensitive data
data = {'username': 'admin', 'password': 'secret123'}
safe_data = mask_sensitive_data(data)
print(safe_data)  # {'username': 'admin', 'password': '***'}
```

Requirements:
- Type hints for all parameters and returns
- Handle None/empty inputs gracefully
- Comprehensive docstrings
- Unit tests for each function
- Performance considerations (avoid heavy operations)
- No external dependencies (use stdlib only)
- Python 3.8+ compatibility"
```

**검증 방법**:
```python
from fastapi_error_codes.utils import class_name_to_message, parse_accept_language

# 클래스명 변환
assert class_name_to_message('AuthRequiredException') == 'Auth Required'
assert class_name_to_message('HTTPException') == 'HTTP Exception'

# Accept-Language 파싱
locales = parse_accept_language('en-US,en;q=0.9,ko;q=0.8')
assert locales == ['en-US', 'en', 'ko']
```

**예상 결과**: 모든 유틸리티 함수 정상 동작

---

### Task 6.2: 패키지 빌드 및 배포 준비

**설명**: 패키지를 빌드하고 PyPI 배포를 준비합니다.

**Claude Code 명령어**:
```bash
claude create "Prepare package for distribution

Create/Update following files:

1. LICENSE file (MIT License)
   * Standard MIT License text
   * Copyright holder: [Your Name]
   * Year: 2025

2. MANIFEST.in (include additional files)
   Content:
   ```
   include README.md
   include LICENSE
   include CHANGELOG.md
   recursive-include locales *.json
   recursive-include docs *.md
   recursive-include examples *.py
   recursive-exclude tests *
   ```

3. .gitignore (Git ignore file)
   Include:
   * __pycache__/
   * *.py[cod]
   * *$py.class
   * .pytest_cache/
   * htmlcov/
   * .coverage
   * dist/
   * build/
   * *.egg-info/
   * .venv/
   * .env
   * .DS_Store

4. Add build script: scripts/build.sh
   ```bash
   #!/bin/bash
   set -e
   
   echo 'Cleaning previous builds...'
   rm -rf dist/ build/ *.egg-info
   
   echo 'Running tests...'
   pytest tests/ -v --cov=src/fastapi_error_codes
   
   echo 'Building package with uv...'
   uv build
   
   echo 'Checking package...'
   twine check dist/*
   
   echo 'Build complete!'
   ls -lh dist/
   ```

5. Add test publish script: scripts/test_publish.sh
   ```bash
   #!/bin/bash
   set -e
   
   echo 'Publishing to Test PyPI...'
   twine upload --repository testpypi dist/*
   
   echo 'Test installation:'
   echo 'pip install --index-url https://test.pypi.org/simple/ fastapi-error-codes'
   ```

6. Add publish script: scripts/publish.sh
   ```bash
   #!/bin/bash
   set -e
   
   echo 'Publishing to PyPI...'
   read -p 'Are you sure? This will publish to production PyPI. (yes/no): ' confirm
   
   if [ \"$confirm\" != \"yes\" ]; then
       echo 'Cancelled.'
       exit 1
   fi
   
   twine upload dist/*
   
   echo 'Published successfully!'
   echo 'Install with: pip install fastapi-error-codes'
   ```

7. Update pyproject.toml - Ensure correct metadata
   * Version: 0.1.0
   * All dependencies listed
   * Keywords for PyPI search
   * Classifiers (Python versions, license, etc.)
   * Project URLs (homepage, repository, issues)

8. Create CONTRIBUTING.md
   Content:
   * How to contribute
   * Development setup
   * Running tests
   * Code style guidelines
   * Pull request process
   * Code of conduct

Build Instructions (in README or separate BUILD.md):
```markdown
## Building from Source

### Prerequisites
- Python 3.8+
- uv (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- twine (for package verification)

### Build Steps
1. Clone repository
2. Create virtual environment: `uv venv`
3. Activate: `source .venv/bin/activate`
4. Install dependencies: `uv pip install -e ".[dev]"`
5. Run tests: `pytest tests/ -v`
6. Build package: `uv build`
7. Check package: `twine check dist/*`

### Testing Locally
```bash
uv pip install dist/fastapi_error_codes-0.1.0-py3-none-any.whl
```

### Publishing
```bash
# Test PyPI first
./scripts/test_publish.sh

# Then production
./scripts/publish.sh
```

Requirements:
- All scripts executable (chmod +x)
- Valid pyproject.toml for build
- All dependencies properly listed
- Version number consistent across files
- License file included
- README included in package"
```

**검증 방법**:
```bash
# 패키지 빌드
python -m build

# 빌드 결과 확인
ls -lh dist/
# .whl과 .tar.gz 파일 생성 확인

# 패키지 검증
twine check dist/*

# 로컬 설치 테스트
pip install dist/fastapi_error_codes-0.1.0-py3-none-any.whl

# Import 테스트
python -c "from fastapi_error_codes import __version__; print(__version__)"
```

**예상 결과**: 패키지가 성공적으로 빌드됨, 배포 준비 완료

---

## 품질 관리

### 코딩 표준

- **스타일**: PEP 8 준수, Black 포맷터 사용
- **타입 힌트**: 모든 public 함수/클래스에 타입 힌트
- **Docstring**: Google 스타일 docstring
- **네이밍**: 
  - 클래스: PascalCase
  - 함수/변수: snake_case
  - 상수: UPPER_SNAKE_CASE
  - Private: _leading_underscore

### 테스트 전략

- **단위 테스트**: 각 모듈/함수별 독립 테스트
- **통합 테스트**: 전체 워크플로우 테스트
- **커버리지**: 최소 90% 목표
- **CI/CD**: GitHub Actions로 자동 테스트

### 문서화 요구사항

- **코드 주석**: 복잡한 로직에 설명 추가
- **API 문서**: 모든 public API 문서화
- **예제**: 실행 가능한 예제 코드
- **README**: 빠른 시작 가이드

---

## 트러블슈팅

### 예상 문제 및 해결 방법

**문제 1: Pydantic v1/v2 호환성 이슈**
- 증상: Pydantic 버전에 따라 import 에러
- 해결: try-except로 버전별 import 처리
```python
try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel
```

**문제 2: locale 파일 경로 문제**
- 증상: locales 디렉토리를 찾을 수 없음
- 해결: 상대 경로 대신 절대 경로 사용, package_data 설정

**문제 3: error_code 중복**
- 증상: 같은 error_code로 여러 예외 등록 시도
- 해결: Registry에서 ValueError 발생, 명확한 에러 메시지

**문제 4: 테스트에서 Registry 상태 유지**
- 증상: 테스트 간 Registry 상태가 공유됨
- 해결: conftest.py에서 clear_registry fixture 사용

---

## 참고 자료

### 외부 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [Python 패키징 가이드](https://packaging.python.org/)

### 관련 프로젝트
- [APIException](https://github.com/akutayural/APIException)
- [fastapi-contrib](https://github.com/identixone/fastapi_contrib)

---

## Quick Start Checklist

프로젝트 시작 전 체크리스트:

- [ ] Python 3.8+ 설치 확인
- [ ] FastAPI 기본 지식 습득
- [ ] Git 저장소 초기화
- [ ] 가상환경 생성 및 활성화
- [ ] 프로젝트 디렉토리 구조 생성
- [ ] Phase 1부터 순차적으로 진행
- [ ] 각 Task 완료 후 검증
- [ ] 테스트 작성 및 실행
- [ ] 문서 작성
- [ ] 빌드 및 배포

---

## 작업 진행 가이드

1. **Phase별 순차 진행**: 각 Phase를 순서대로 완료
2. **Task별 검증**: 각 Task 완료 후 반드시 검증 수행
3. **점진적 통합**: 작은 단위로 기능 추가하고 테스트
4. **문서화 병행**: 코드 작성과 동시에 문서 작성
5. **테스트 우선**: 가능하면 TDD 방식 적용

---

*이 가이드는 fastapi-error-codes 패키지 개발을 위한 완전한 작업 지침입니다.*
*각 단계의 Claude Code 명령어를 순서대로 실행하여 패키지를 완성할 수 있습니다.*
