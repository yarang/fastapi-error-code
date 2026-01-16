# fastapi-error-codes - Development Progress

## Overview
이 파일은 fastapi-error-codes 패키지 개발 진행 상황을 추적합니다.
각 Task 완료 시 체크박스를 업데이트하세요.

---

## Phase 1: 프로젝트 초기 설정 ⏳

**목표**: 패키지 개발에 필요한 기본 구조와 설정 완료  
**예상 시간**: 30분

### Tasks
- [ ] **Task 1.1**: 프로젝트 디렉토리 구조 생성
  - 디렉토리: src/, tests/, examples/, locales/, docs/
  - __init__.py 파일 생성
  - 검증: `tree -L 3` 명령으로 구조 확인

- [ ] **Task 1.2**: pyproject.toml 설정 파일 생성
  - 패키지 메타데이터 정의
  - 의존성 설정 (fastapi, pydantic, pytest 등)
  - 빌드 시스템 설정 (hatchling)
  - 검증: `uv venv && source .venv/bin/activate && uv pip install -e .`

- [ ] **Task 1.3**: 패키지 진입점 설정
  - src/fastapi_error_codes/__init__.py 생성
  - 주요 API export
  - __version__ 정의
  - 검증: `from fastapi_error_codes import __version__`

**Phase 1 완료 조건**: ✅ 모든 Task 체크, 패키지 import 가능

---

## Phase 2: 핵심 기능 구현 ⏳

**목표**: BaseAppException, Registry, Decorator, Domain 구현  
**예상 시간**: 2-3시간

### Tasks
- [ ] **Task 2.1**: BaseAppException 클래스 구현
  - 파일: src/fastapi_error_codes/base.py
  - 기능: error_code, message, status_code, detail, timestamp
  - 메서드: to_dict(), add_detail()
  - 검증: Exception 생성 후 to_dict() 호출

- [ ] **Task 2.2**: ExceptionRegistry 구현
  - 파일: src/fastapi_error_codes/registry.py
  - 기능: 예외 등록, 중복 검사, 조회
  - Thread-safe 구현
  - 검증: 중복 등록 시 ValueError 발생

- [ ] **Task 2.3**: @register_exception 데코레이터 구현
  - 파일: src/fastapi_error_codes/decorators.py
  - 기능: 예외 자동 등록, 클래스 속성 설정
  - Auto-message 생성 (옵션)
  - 검증: 데코레이터로 예외 정의 후 속성 확인

- [ ] **Task 2.4**: ErrorDomain 관리 구현
  - 파일: src/fastapi_error_codes/domain.py
  - 기능: 도메인 범위 관리, 검증
  - 기본 도메인 제공 (AUTH, RESOURCE, etc.)
  - 검증: 커스텀 도메인 등록 및 범위 검증

**Phase 2 완료 조건**: ✅ 모든 Task 체크, 단위 테스트 통과

---

## Phase 3: 다국어 지원 ⏳

**목표**: i18n 모듈과 locale 파일 구현  
**예상 시간**: 1-2시간

### Tasks
- [ ] **Task 3.1**: MessageProvider 구현
  - 파일: src/fastapi_error_codes/i18n.py
  - 기능: locale 파일 로드, 메시지 조회, fallback 체인
  - 검증: 다양한 locale로 메시지 조회 테스트

- [ ] **Task 3.2**: 기본 locale 파일 생성
  - 파일: locales/en.json, locales/ko.json, locales/ja.json
  - 내용: 공통 error_code 메시지 (200-504 범위)
  - 검증: JSON 유효성 검사 (`jq` 명령)

**Phase 3 완료 조건**: ✅ 모든 Task 체크, i18n 동작 확인

---

## Phase 4: FastAPI 통합 ⏳

**목표**: FastAPI exception handler 및 설정 구현  
**예상 시간**: 1-2시간

### Tasks
- [ ] **Task 4.1**: Response 모델 정의
  - 파일: src/fastapi_error_codes/models.py
  - 모델: ErrorResponse, ValidationErrorResponse, ErrorDetail
  - 검증: Pydantic 모델 직렬화 테스트

- [ ] **Task 4.2**: FastAPI Exception Handler 구현
  - 파일: src/fastapi_error_codes/handlers.py
  - 기능: setup_exception_handler(), 예외별 핸들러
  - 검증: TestClient로 예외 발생 시 JSON 응답 확인

- [ ] **Task 4.3**: ErrorHandlerConfig 설정 클래스 구현
  - 파일: src/fastapi_error_codes/config.py
  - 기능: 설정 관리, 환경변수 지원, 프리셋
  - 검증: development/production 프리셋 테스트

**Phase 4 완료 조건**: ✅ 모든 Task 체크, FastAPI 통합 테스트 통과

---

## Phase 5: 테스트 및 문서화 ⏳

**목표**: 포괄적인 테스트와 문서 작성  
**예상 시간**: 2-3시간

### Tasks
- [ ] **Task 5.1**: 단위 테스트 작성
  - 파일: tests/test_*.py (각 모듈별)
  - 커버리지: >90% 목표
  - 검증: `pytest tests/ --cov` 실행

- [ ] **Task 5.2**: 통합 테스트 작성
  - 파일: tests/test_integration.py
  - 시나리오: 전체 워크플로우, i18n, 도메인
  - 검증: 모든 통합 테스트 통과

- [ ] **Task 5.3**: 예제 코드 작성
  - 파일: examples/*.py (5개 예제)
  - 내용: basic_usage, custom_domains, i18n, full_app
  - 검증: 모든 예제 실행 가능

- [ ] **Task 5.4**: README 및 문서 작성
  - 파일: README.md, docs/*.md
  - 내용: 빠른 시작, API 레퍼런스, 고급 사용법
  - 검증: 링크 유효성, 코드 예제 실행

**Phase 5 완료 조건**: ✅ 모든 Task 체크, 문서 완성

---

## Phase 6: 패키징 및 배포 ⏳

**목표**: 패키지 빌드 및 배포 준비  
**예상 시간**: 1시간

### Tasks
- [ ] **Task 6.1**: 유틸리티 함수 구현
  - 파일: src/fastapi_error_codes/utils.py
  - 기능: 공통 헬퍼 함수들
  - 검증: 유틸리티 함수 단위 테스트

- [ ] **Task 6.2**: 패키지 빌드 및 배포 준비
  - 파일: LICENSE, MANIFEST.in, scripts/*.sh
  - 작업: 빌드 스크립트, 배포 스크립트
  - 검증: `python -m build` 성공, 패키지 설치 테스트

**Phase 6 완료 조건**: ✅ 모든 Task 체크, 빌드 성공

---

## 전체 진행 상황

### 완료율
- Phase 1: 0/3 (0%)
- Phase 2: 0/4 (0%)
- Phase 3: 0/2 (0%)
- Phase 4: 0/3 (0%)
- Phase 5: 0/4 (0%)
- Phase 6: 0/2 (0%)

**전체**: 0/18 Tasks (0%)

---

## 이슈 및 노트

### 발견된 문제
*문제 발생 시 여기에 기록*

### 개선 아이디어
*개발 중 떠오른 아이디어 기록*

### 다음 단계
1. Phase 1 Task 1.1 시작
2. DEVELOPMENT_GUIDE.md 참조하여 Claude Code 명령어 실행
3. 각 Task 완료 후 체크박스 업데이트

---

## Git 커밋 이력

각 Task 완료 시 커밋 권장:
```bash
git add .
git commit -m "feat: complete Phase [N] Task [N.M] - [Task name]"
```

### 커밋 로그
*주요 커밋 기록*

---

**마지막 업데이트**: 2025-01-13  
**다음 작업**: Phase 1 Task 1.1 - 프로젝트 디렉토리 구조 생성
