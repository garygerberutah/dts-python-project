"""
test_components.py — runs the Web Component test suites via Node.js.

Each component has a co-located *.test.js file that uses the Node.js
built-in test runner (node:test) and jsdom for a headless DOM environment.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend" / "components"
NODE_MODULES = ROOT / "node_modules"


def _run_test(test_file: Path) -> bool:
    """Run a single *.test.js file with Node. Returns True if it passed."""
    print(f"  [test] Running {test_file.relative_to(ROOT)}…")
    result = subprocess.run(
        ["node", "--experimental-vm-modules", str(test_file)],
        cwd=ROOT,
        text=True,
        capture_output=False,
    )
    passed = result.returncode == 0
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [test] {status}: {test_file.name}")
    return passed


def run_all_tests() -> bool:
    """Discover and run all *.test.js files. Returns True if all pass."""
    test_files = sorted(FRONTEND_DIR.glob("**/*.test.js"))
    if not test_files:
        print("[test] No test files found.")
        return True

    print(f"[test] Found {len(test_files)} test file(s).")
    results = [_run_test(f) for f in test_files]
    return all(results)


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
