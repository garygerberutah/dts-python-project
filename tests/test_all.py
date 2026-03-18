"""
test_all.py — runs all test suites across the project.

Copyright 2026 by GuidoGerb Publishing, LLC

Usage:
    python tests/test_all.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = ROOT / "tests"
UI_TESTS_DIR = TESTS_ROOT / "ui"
API_TESTS_DIR = TESTS_ROOT / "api"


def run() -> int:
    """Run all test directories. Returns 0 if all pass, 1 on any failure."""
    test_dirs = []
    for d in (TESTS_ROOT, UI_TESTS_DIR, API_TESTS_DIR):
        if d.exists() and sorted(d.glob("test_*.py")):
            test_dirs.append(str(d))

    if not test_dirs:
        print("[test-all] No test directories found.", file=sys.stderr)
        return 1

    all_ok = True
    for d in test_dirs:
        print(f"\n[test-all] Running tests from {d}")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", d, "-v", "--tb=short"],
            cwd=ROOT,
            text=True,
        )
        if result.returncode != 0:
            all_ok = False

    if all_ok:
        print("\n[test-all] ✓ All test suites passed.")
    else:
        print("\n[test-all] ✗ Some tests FAILED.", file=sys.stderr)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(run())
