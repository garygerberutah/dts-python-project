"""test_components.py — runs the Web Component test suites via pytest.

Copyright 2026 by GuidoGerb Publishing, LLC

Test files live under tests/ and verify component source structure,
Shadow DOM patterns, and accessibility attributes using Python only.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"


def run_all_tests() -> bool:
    """Run all pytest test files. Returns True if all pass."""
    if not TESTS_DIR.exists():
        print("[test] tests/ directory not found.")
        return True

    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    if not test_files:
        print("[test] No test files found.")
        return True

    print(f"[test] Found {len(test_files)} test file(s).")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS_DIR), "-v"],
        cwd=ROOT,
        text=True,
    )
    return result.returncode == 0


def main() -> int:
    print("[test] Running Web Component test suites…")
    ok = run_all_tests()
    if ok:
        print("[test] All component tests passed.")
        return 0
    print("[test] One or more tests FAILED.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
