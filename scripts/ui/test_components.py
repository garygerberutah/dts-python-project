"""test_components.py — runs the Web Component test suites via pytest.

Copyright 2026 by DTS, The State of Utah

Test files live under tests/ and verify component source structure,
Shadow DOM patterns, and accessibility attributes using Python only.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
UI_TESTS_DIR = ROOT / "tests" / "ui"
TOOLCHAIN_TESTS_DIR = ROOT / "tests"


def run_all_tests() -> bool:
    """Run all pytest test files. Returns True if all pass."""
    test_dirs = []
    for d in (UI_TESTS_DIR, TOOLCHAIN_TESTS_DIR):
        if d.exists() and sorted(d.glob("test_*.py")):
            test_dirs.append(str(d))

    if not test_dirs:
        print("[test] No test directories found.", file=sys.stderr)
        return False

    # Run each directory in a separate pytest invocation to avoid
    # conftest.py collisions between identically-named 'tests/' packages.
    all_ok = True
    for d in test_dirs:
        print(f"[test] Running tests from {d}")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", d, "-v"],
            cwd=ROOT,
            text=True,
        )
        if result.returncode != 0:
            all_ok = False
    return all_ok


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
