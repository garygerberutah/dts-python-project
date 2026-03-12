"""
clean.py — removes all generated build artifacts from the dist/ directory.
"""

import shutil
import sys
from pathlib import Path

DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
WASM_PKG_DIR = Path(__file__).resolve().parent.parent / "wasm" / "pkg"


def clean() -> None:
    """Delete all build output directories."""
    removed: list[str] = []
    for target in (DIST_DIR, WASM_PKG_DIR):
        if target.exists():
            shutil.rmtree(target)
            removed.append(str(target))
            print(f"  Removed: {target}")
    if not removed:
        print("  Nothing to clean.")
    else:
        print(f"  Cleaned {len(removed)} directory/ies.")


def main() -> int:
    print("[clean] Removing build artefacts…")
    clean()
    print("[clean] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
