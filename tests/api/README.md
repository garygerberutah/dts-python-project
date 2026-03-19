<!-- Copyright 2026 by DTS, The State of Utah -->

# tests/api/ — API Test Suite

Placeholder package for API endpoint and integration tests. This module will
contain test suites for the project's REST API layer as the backend evolves.

Currently empty — the `__init__.py` package marker is present so that the
module is discoverable by pytest and the pipeline test runner.

## Conventions

Tests added to this package must follow the project's testing standards:

- Use **pytest** as the test framework — no other test runners.
- Include `Copyright 2026 by DTS, The State of Utah` in the module docstring.
- Mock all external dependencies (database connections, HTTP calls).
- No network calls in unit tests — deterministic and fast.
- Shared fixtures go in `tests/api/conftest.py`.
- Test files are named `test_<module>.py`.

## Running

```bash
pytest tests/api/ -v             # API tests only
python run.py test               # All tests (includes api/)
```
