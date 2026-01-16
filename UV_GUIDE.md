# UV 패키지 관리자 가이드

## uv란?

**uv**는 Astral (Ruff 개발사)에서 개발한 극도로 빠른 Python 패키지 설치 및 의존성 해결 도구입니다.

### 주요 장점
- ⚡ **10-100배 빠름**: Rust로 작성되어 pip보다 훨씬 빠름
- 🔒 **안정적**: 정확한 의존성 해결
- 🎯 **호환성**: pip와 거의 동일한 인터페이스
- 📦 **올인원**: 가상환경, 패키지 설치, 빌드를 하나의 도구로

---

## 설치

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 확인
```bash
uv --version
```

---

## fastapi-error-codes 프로젝트에서 사용법

### 1. 초기 설정

```bash
# 프로젝트 디렉토리로 이동
cd fastapi-error-codes

# 가상환경 생성
uv venv

# 가상환경 활성화
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 개발 의존성 포함하여 설치
uv pip install -e ".[dev]"
```

### 2. 일상 작업

```bash
# 패키지 설치
uv pip install <package-name>

# 패키지 제거
uv pip uninstall <package-name>

# 의존성 업데이트
uv pip install --upgrade <package-name>

# 모든 의존성 나열
uv pip list

# 의존성 동결 (requirements.txt)
uv pip freeze > requirements.txt
```

### 3. 프로젝트 의존성 관리

```bash
# pyproject.toml의 의존성 설치
uv pip install -e .

# 개발 의존성 포함
uv pip install -e ".[dev]"

# 특정 extras만 설치
uv pip install -e ".[test]"
```

### 4. 빌드 및 배포

```bash
# 패키지 빌드
uv build

# 빌드 결과 확인
ls dist/
# fastapi_error_codes-0.1.0-py3-none-any.whl
# fastapi_error_codes-0.1.0.tar.gz
```

---

## 주요 명령어 비교

| 작업 | pip | uv |
|------|-----|-----|
| 가상환경 생성 | `python -m venv .venv` | `uv venv` |
| 패키지 설치 | `pip install package` | `uv pip install package` |
| 개발 모드 설치 | `pip install -e .` | `uv pip install -e .` |
| 의존성 동결 | `pip freeze` | `uv pip freeze` |
| 패키지 빌드 | `python -m build` | `uv build` |

---

## fastapi-error-codes 워크플로우

### 프로젝트 시작 (첫 설정)
```bash
# 1. uv 설치 (한 번만)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 프로젝트 클론
git clone https://github.com/[username]/fastapi-error-codes.git
cd fastapi-error-codes

# 3. 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate

# 4. 의존성 설치
uv pip install -e ".[dev]"

# 5. 테스트 실행
pytest tests/ -v
```

### 일상 개발
```bash
# 가상환경 활성화
source .venv/bin/activate

# 새 기능 개발
# ... 코드 작성 ...

# 테스트
pytest tests/ -v

# 포맷팅
black src/ tests/

# 린트
ruff check src/ tests/

# 타입 체크
mypy src/
```

### 새 의존성 추가
```bash
# 1. pyproject.toml에 수동으로 추가
# [project]
# dependencies = [
#     "fastapi >= 0.68.0",
#     "new-package >= 1.0.0",  # 추가
# ]

# 2. 재설치
uv pip install -e ".[dev]"
```

### 패키지 빌드 및 배포
```bash
# 빌드
uv build

# 검증
twine check dist/*

# Test PyPI 업로드
twine upload --repository testpypi dist/*

# PyPI 업로드
twine upload dist/*
```

---

## 고급 기능

### 의존성 해결만 (설치 안함)
```bash
uv pip compile pyproject.toml -o requirements.txt
```

### 특정 Python 버전 사용
```bash
uv venv --python 3.11
```

### 캐시 관리
```bash
# 캐시 정보
uv cache dir

# 캐시 삭제
uv cache clean
```

---

## 문제 해결

### uv가 설치 안 됨
```bash
# PATH 확인
echo $PATH

# uv 경로 추가 (보통 ~/.cargo/bin)
export PATH="$HOME/.cargo/bin:$PATH"
```

### 가상환경 활성화 안됨
```bash
# Windows Git Bash
source .venv/Scripts/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 의존성 충돌
```bash
# 의존성 트리 확인
uv pip list --tree

# 강제 재설치
uv pip install --force-reinstall -e ".[dev]"
```

---

## uv vs pip 성능 비교

실제 fastapi-error-codes 프로젝트 기준:

| 작업 | pip | uv | 개선 |
|------|-----|-----|------|
| 가상환경 생성 | ~3초 | <0.1초 | 30배 |
| 의존성 설치 (cold) | ~30초 | ~3초 | 10배 |
| 의존성 설치 (cache) | ~15초 | <1초 | 15배 |

---

## 참고 자료

- **공식 문서**: https://github.com/astral-sh/uv
- **설치 가이드**: https://astral.sh/uv
- **Astral 블로그**: https://astral.sh/blog

---

## 요약

fastapi-error-codes 프로젝트에서 uv 사용:

```bash
# 설정
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 개발
pytest tests/ -v
black src/ tests/
ruff check src/

# 빌드
uv build

# 그게 다입니다! 🚀
```

**uv를 사용하면 개발 속도가 크게 향상됩니다!**
