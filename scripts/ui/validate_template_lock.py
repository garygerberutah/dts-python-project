"""
validate_template_lock.py — detect uncommitted changes to template-locked files.

Copyright 2026 by GuidoGerb Publishing, LLC

Files outside the ``api/`` and ``ui/`` directories are considered
immutable template infrastructure.  This script checks ``git diff``
for staged or unstaged changes to those files and warns the developer,
offering to move the changes into the appropriate user-content directory.

Usage (via run.py):
    python run.py validate-template-lock                       # check only
    python run.py validate-template-lock --force                # bypass the lock
    python run.py validate-template-lock --move-to ui/custom    # move changes
    python run.py validate-template-lock --move-to api/overrides
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Directories that hold user content — changes are always allowed here
USER_DIRS = {"api", "ui"}


def _changed_files() -> list[str]:
    """Return repo-relative paths of all staged + unstaged changed files."""
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    unstaged = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    paths: set[str] = set()
    for result in (staged, unstaged, untracked):
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line:
                    paths.add(line)
    return sorted(paths)


def _is_template_file(path: str) -> bool:
    """Return True if the path is outside user-content directories."""
    top = path.split("/")[0] if "/" in path else path
    return top not in USER_DIRS


def _resolve_move_target(move_to: str) -> Path | None:
    """Validate that *move_to* starts with a user-content directory.

    Returns the absolute target directory, or None on validation failure.
    """
    normalised = move_to.replace("\\", "/").strip("/")
    top = normalised.split("/")[0]
    if top not in USER_DIRS:
        print(
            f"[template-lock] --move-to must start with one of: {', '.join(sorted(USER_DIRS))}",
            file=sys.stderr,
        )
        return None
    return ROOT / normalised


def _move_files(locked: list[str], target_dir: Path) -> list[str]:
    """Copy changed template files into *target_dir*, then git-restore originals.

    Preserves the source's relative directory structure under *target_dir*.
    Returns a list of error messages (empty = success).
    """
    errors: list[str] = []
    moved: list[str] = []

    for rel_path in locked:
        src = ROOT / rel_path
        dest = target_dir / rel_path

        if not src.exists():
            errors.append(f"  {rel_path}: source file not found")
            continue

        # Overwrite warning
        if dest.exists():
            if sys.stdin.isatty():
                answer = (
                    input(f"  {dest.relative_to(ROOT)} already exists — overwrite? [y/N] ")
                    .strip()
                    .lower()
                )
                if answer != "y":
                    print(f"  Skipped {rel_path}")
                    continue
            else:
                print(f"  [template-lock] WARNING: overwriting {dest.relative_to(ROOT)}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))
        moved.append(rel_path)
        print(f"  {rel_path} -> {dest.relative_to(ROOT)}")

    # Restore originals via git checkout
    if moved:
        result = subprocess.run(
            ["git", "checkout", "--"] + moved,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"  git checkout failed: {result.stderr.strip()}")
        else:
            print(f"[template-lock] Restored {len(moved)} template file(s) to HEAD.")

    return errors


def validate(force: bool = False, move_to: str | None = None) -> list[str]:
    """Check for changes to template-locked files.

    Returns a list of error messages (empty = pass).

    *move_to*: when given (e.g. ``"ui/custom"``), copies the changed
    template files into that directory (preserving structure) and
    git-restores the originals.

    *force*: bypass the lock without moving anything.
    """
    changed = _changed_files()
    locked = [p for p in changed if _is_template_file(p)]
    if not locked:
        print("[template-lock] No template files modified — OK.")
        return []

    print("[template-lock] The following template files have been modified:")
    for path in locked:
        print(f"  - {path}")
    print()
    print(
        "[template-lock] Template files are intended to be immutable.\n"
        "  Application changes should go into api/ or ui/ instead."
    )

    if force:
        print("[template-lock] --force supplied — allowing changes.")
        return []

    # --move-to: relocate changed files into the target directory
    if move_to is not None:
        target_dir = _resolve_move_target(move_to)
        if target_dir is None:
            return ["  --move-to target must start with api/ or ui/"]
        print(f"\n[template-lock] Moving changed files into {target_dir.relative_to(ROOT)}/")
        return _move_files(locked, target_dir)

    # Interactive confirmation
    if sys.stdin.isatty():
        answer = input("\nProceed anyway and keep these template changes? [y/N] ").strip().lower()
        if answer == "y":
            print("[template-lock] Acknowledged — proceeding with template changes.")
            return []

    return [f"  {p}: template-locked file modified — move changes to api/ or ui/" for p in locked]


def main() -> int:
    """CLI entry point."""
    errors = validate()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
