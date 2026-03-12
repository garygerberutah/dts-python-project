"""
pipeline.py — master automation pipeline.

Copyright 2026 by GuidoGerb Publishing, LLC

Pipeline stages (in order):
  1. format    — auto-format all source files
  2. lint      — static analysis (ruff, clippy, JS linter)
  3. validate  — copyright notice in all source files
  4. validate  — asset naming convention + SHA-256 hashes
  5. validate  — binary files match their mime-type encoding
  6. clean     — remove prior build artefacts
  7. build     — compile WASM + render templates + copy assets
  8. validate  — WCAG 2.1 accessibility check
  9. test      — run Web Component test suites
 10. deploy    — git commit + git push  (optional, skipped with --skip-deploy)

Fail-fast: any stage failure immediately aborts the pipeline.
All stages (1-9) must pass before any git commit is allowed.
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
from scripts.validate_assets import validate as validate_assets
from scripts.validate_copyright import validate as validate_copyright
from scripts.validate_mime_type_content import validate as validate_mime
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


def _stage_validate_copyright() -> bool:
    """Validate that all source files contain the copyright notice."""
    errors = validate_copyright()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return False
    return True


def _stage_validate_assets() -> bool:
    """Validate asset naming convention and SHA-256 hashes."""
    errors = validate_assets()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return False
    return True


def _stage_validate_mime() -> bool:
    """Validate that binary files match their extension's mime-type."""
    errors = validate_mime()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return False
    return True


def run(skip_deploy: bool = False) -> int:
    """Execute the full pipeline. Returns 0 on success, 1 on any failure."""
    print("\n[pipeline] Master Automation Pipeline")
    print("[pipeline] Fail-fast mode enabled.\n")

    _stage("1. format", format_all)
    _stage("2. lint", lint_all)
    _stage("3. validate (copyright)", _stage_validate_copyright)
    _stage("4. validate (assets)", _stage_validate_assets)
    _stage("5. validate (mime-type)", _stage_validate_mime)

    # Build must happen before WCAG validate so HTML artefacts exist
    _stage("6. clean", clean)
    _stage("7. build", build)

    _stage("8. validate (WCAG 2.1)", _stage_validate)
    _stage("9. test (Web Components)", run_all_tests)

    if not skip_deploy:
        _stage("10. deploy", _deploy)
    else:
        print("\n[pipeline] Stage 9 (deploy) skipped (--skip-deploy).")

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
    parser = argparse.ArgumentParser(description="Master automation pipeline")
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip the git commit/push deploy stage.",
    )
    args = parser.parse_args()
    return run(skip_deploy=args.skip_deploy)


if __name__ == "__main__":
    sys.exit(main())
