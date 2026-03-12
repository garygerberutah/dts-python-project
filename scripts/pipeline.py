"""
pipeline.py — master automation pipeline for ggp3d.

Pipeline stages (in order):
  1. format   — auto-format all source files
  2. lint      — static analysis (ruff, clippy, eslint)
  3. validate  — WCAG 2.1 accessibility check
  4. clean     — remove prior build artefacts
  5. build     — compile WASM + render templates + copy assets
  6. test      — run Web Component test suites
  7. deploy    — git commit + git push  (optional, skipped with --skip-deploy)

Fail-fast: any stage failure immediately aborts the pipeline.
Git operations are only executed after 100% success of all prior stages.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.build import build
from scripts.clean import clean
from scripts.format_code import format_all
from scripts.lint import lint_all
from scripts.test_components import run_all_tests
from scripts.validate_wcag import DIST_DIR, validate

ROOT = Path(__file__).resolve().parent.parent


def _stage(name: str, fn, *args, **kwargs) -> None:
    """Execute a pipeline stage; abort on failure."""
    print(f"\n{'=' * 60}")
    print(f"  STAGE: {name.upper()}")
    print(f"{'=' * 60}")
    result = fn(*args, **kwargs)
    # Treat False return as failure; exceptions propagate naturally.
    if result is False:
        print(f"\n[pipeline] ✗ Stage '{name}' FAILED — aborting.", file=sys.stderr)
        sys.exit(1)
    print(f"[pipeline] ✓ Stage '{name}' passed.")


def _stage_validate() -> bool:
    """Run WCAG validation and convert violations → bool."""
    violations = validate(DIST_DIR)
    if violations:
        for v in violations:
            print(f"  [{v.rule}] {v.file}:{v.line}: {v.message}", file=sys.stderr)
        return False
    return True


def run(skip_deploy: bool = False) -> int:
    """Execute the full pipeline. Returns 0 on success, 1 on any failure."""
    print("\n[pipeline] ggp3d Master Automation Pipeline")
    print("[pipeline] Fail-fast mode enabled.\n")

    _stage("1. format", format_all)
    _stage("2. lint", lint_all)

    # Build must happen before validate so HTML artefacts exist
    _stage("3. clean", clean)
    _stage("4. build", build)

    _stage("5. validate (WCAG 2.1)", _stage_validate)
    _stage("6. test (Web Components)", run_all_tests)

    if not skip_deploy:
        _stage("7. deploy", _deploy)
    else:
        print("\n[pipeline] Stage 7 (deploy) skipped (--skip-deploy).")

    print("\n[pipeline] ✓ All stages completed successfully.")
    return 0


def _deploy() -> bool:
    """Commit and push all changes via git."""

    def _git(args: list[str]) -> bool:
        result = subprocess.run(["git"] + args, cwd=ROOT, text=True)
        return result.returncode == 0

    if not _git(["add", "-A"]):
        return False
    # Allow empty commits (nothing to commit is not an error)
    subprocess.run(
        ["git", "commit", "-m", "chore: automated pipeline deployment", "--allow-empty"],
        cwd=ROOT,
        text=True,
    )
    return _git(["push"])


def main() -> int:
    parser = argparse.ArgumentParser(description="ggp3d master automation pipeline")
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip the git commit/push deploy stage.",
    )
    args = parser.parse_args()
    return run(skip_deploy=args.skip_deploy)


if __name__ == "__main__":
    sys.exit(main())
