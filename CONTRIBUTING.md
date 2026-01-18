# Contributing to fastapi-error-codes

Thank you for your interest in contributing to fastapi-error-codes! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Setting Up Your Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/fastapi-error-codes.git
cd fastapi-error-codes
```

2. **Create a virtual environment**

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using venv
python -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

4. **Verify installation**

```bash
pytest --version
python -c "from fastapi_error_codes import __version__; print(__version__)"
```

---

## Code Style Guidelines

### Python Style

We follow PEP 8 with the following tooling:

- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking

### Running Formatters and Linters

```bash
# Format code with Black
black src/ tests/ examples/

# Run Ruff linter
ruff check src/ tests/ examples/

# Run mypy type checker
mypy src/
```

### Type Hints

- All public functions and classes must have type hints
- Use `typing` module for Python 3.8 compatibility
- Add `from __future__ import annotations` at the top of files for forward references

```python
from typing import Any, Dict, Optional

def process_error(error_code: int, detail: Optional[Dict[str, Any]] = None) -> str:
    ...
```

### Docstrings

- Use Google style docstrings
- Document all public classes, functions, and methods

```python
def get_error_message(error_code: int) -> str:
    """Get the error message for a given error code.

    Args:
        error_code: The error code to look up.

    Returns:
        The error message string.

    Raises:
        ValueError: If the error code is not registered.
    """
    ...
```

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=fastapi_error_codes --cov-report=html

# Run specific test file
pytest tests/test_handlers.py

# Run tests with verbose output
pytest -v
```

### Test Coverage

We aim for 90%+ code coverage. When adding new features:

1. Write tests first (TDD approach when possible)
2. Ensure all new code is covered
3. Run `pytest --cov` before committing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_base.py              # Tests for base.py
├── test_domain.py            # Tests for domain.py
├── test_metrics/             # Metrics tests
└── tracing/                  # Tracing tests
```

---

## Commit Message Guidelines

We follow conventional commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```bash
feat(handlers): add support for custom error headers

fix(i18n): resolve locale fallback chain issue

docs(api): update ErrorResponse documentation

test(metrics): add tests for PrometheusExporter
```

---

## Pull Request Process

### Before Submitting

1. **Update tests** - Add tests for new functionality
2. **Update documentation** - Update relevant docs and examples
3. **Run linters** - Ensure code passes all style checks
4. **Run tests** - Ensure all tests pass

### Submitting a Pull Request

1. Fork the repository and create a branch
2. Make your changes following the guidelines above
3. Commit with clear, descriptive messages
4. Push to your fork
5. Open a pull request with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes (if applicable)

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. Automated checks (CI) must pass
2. At least one maintainer approval required
3. Address review comments promptly
4. Keep the PR focused and small when possible

---

## Getting Help

- **GitHub Issues**: [Create an issue](https://github.com/yarang/fastapi-error-codes/issues)
- **Discussions**: [Join the discussion](https://github.com/yarang/fastapi-error-codes/discussions)

---

## Additional Resources

- [Code of Conduct](#code-of-conduct)
- [README](README.md)
- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)

---

Thank you for contributing to fastapi-error-codes!
