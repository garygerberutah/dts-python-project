---
applyTo: ["tests/**/*.py", "test_*.py", "**/test_*.py"]
description: "Use when writing or editing Python tests. Covers pytest conventions, Selenium 4 patterns, coverage, and fixture organization."
---
# Testing Standards

## Stack
- **pytest** for all test execution
- **Selenium 4** for browser/integration tests (WebDriver Manager for driver lifecycle)
- **pytest-cov** for coverage reporting

## pytest Conventions
- Files: `test_<subject>.py`
- Functions: `test_<behavior>()`
- Fixtures in `conftest.py` at each test directory level
- Use `@pytest.fixture` with appropriate scope (`function`, `class`, `module`, `session`)
- Parametrize with `@pytest.mark.parametrize` for data-driven tests

## Selenium 4 Patterns
- Use `webdriver.Chrome(service=Service(ChromeDriverManager().install()))` for driver setup
- Explicit waits via `WebDriverWait` + `expected_conditions` — never `time.sleep()`
- Page Object Model for complex pages
- Always `driver.quit()` in fixture teardown
- Shadow DOM: `element.shadow_root.find_element()` for Web Component testing

## Coverage
- Target: meaningful coverage, not percentage theater
- `pytest --cov=src --cov-report=term-missing`
- Exclude test files and config from coverage

## Forbidden
- No Jest, Mocha, Vitest, jsdom, or any JS test framework
- No `time.sleep()` in Selenium tests — use explicit waits
- No hardcoded test data paths — use `tmp_path` or fixtures
- No base64 data URIs or inline binary encodings in test source files — reference assets by path
- Binary test fixtures (`.png`, `.jpg`, etc.) may be versioned if their content matches the extension's mime-type
- `application/octet-stream` and opaque binary blobs are forbidden in git
