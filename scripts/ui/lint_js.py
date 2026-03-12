"""
lint_js.py — lightweight Python-based JavaScript linter.

Copyright 2026 by GuidoGerb Publishing, LLC

Enforces a subset of coding standards without requiring Node.js or ESLint:
  • eqeqeq     — forbid == and != (use === and !==)
  • no-var      — forbid var declarations
  • no-console  — warn on console.log (allow info, warn, error)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _strip_strings(line: str) -> str:
    """Remove string literals to avoid false positives in lint checks."""
    result = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
    result = re.sub(r"'(?:[^'\\]|\\.)*'", "''", result)
    result = re.sub(r"`(?:[^`\\]|\\.)*`", "``", result)
    return result


def _check_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Check a single JS file. Returns list of (line_number, rule, message)."""
    issues: list[tuple[int, str, str]] = []
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_block_comment = False

    for lineno, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Track block comments
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue
        if stripped.startswith("//"):
            continue

        # Strip inline comments and string content for analysis
        line = re.sub(r"//.*$", "", raw_line)
        line = _strip_strings(line)

        # eqeqeq: forbid == and != (but allow === and !==)
        sanitized = line.replace("===", "###").replace("!==", "###")
        if "==" in sanitized:
            issues.append((lineno, "eqeqeq", "Use === instead of =="))
        if re.search(r"!=(?!=)", sanitized):
            issues.append((lineno, "eqeqeq", "Use !== instead of !="))

        # no-var
        if re.search(r"\bvar\s", line):
            issues.append((lineno, "no-var", "Use const or let instead of var"))

        # no-console: flag console.log (allow info, warn, error)
        if "console.log(" in line:
            issues.append(
                (lineno, "no-console", "Unexpected console.log (use info, warn, or error)")
            )

    return issues


def lint_js_files(root: Path = ROOT) -> bool:
    """Lint all JS files under ui/ (excluding *.test.js). Returns True if clean."""
    ui_dir = root / "ui"
    if not ui_dir.exists():
        print("  [lint:js] ui/ directory not found.")
        return True

    js_files = sorted(ui_dir.glob("**/*.js"))
    js_files = [f for f in js_files if ".test." not in f.name and "/wasm/" not in f.as_posix()]

    if not js_files:
        print("  [lint:js] No JS files found.")
        return True

    all_issues: list[str] = []
    for filepath in js_files:
        issues = _check_file(filepath)
        for lineno, rule, message in issues:
            rel_path = filepath.relative_to(root)
            all_issues.append(f"  {rel_path}:{lineno} [{rule}] {message}")

    if all_issues:
        print(f"  [lint:js] {len(all_issues)} issue(s) found:")
        for issue in all_issues:
            print(issue)
        return False

    print("  [lint:js] No issues found.")
    return True


def main() -> int:
    print("[lint:js] Checking JavaScript files…")
    ok = lint_js_files()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
