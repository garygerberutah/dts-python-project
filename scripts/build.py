"""
build.py — compiles the Rust WASM module, renders Jinja2 templates, and
copies all frontend assets into the dist/ directory.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parent.parent
WASM_DIR = ROOT / "wasm"
DIST_DIR = ROOT / "dist"
TEMPLATES_DIR = ROOT / "templates"
FRONTEND_DIR = ROOT / "frontend"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a subprocess command, raising on failure."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def build_wasm() -> None:
    """Compile the Rust crate to a WASM package using wasm-pack."""
    print("  [build] Compiling Rust WASM…")
    _run(
        ["wasm-pack", "build", "--target", "web", "--release", "--out-dir", "pkg"],
        cwd=WASM_DIR,
    )
    wasm_pkg = WASM_DIR / "pkg"
    dest = DIST_DIR / "wasm"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(wasm_pkg, dest)
    print(f"  [build] WASM output → {dest}")


def render_templates(
    app_title: str = "ggp3d",
    app_description: str = "Zero-dependency 3D geometry processor powered by Rust WebAssembly.",
    lang: str = "en",
) -> None:
    """Render all Jinja2 templates and write them to dist/."""
    print("  [build] Rendering Jinja2 templates…")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html"]),
        undefined=jinja2.StrictUndefined,
    )
    context = {
        "app_title": app_title,
        "app_description": app_description,
        "lang": lang,
    }
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    for tmpl_path in TEMPLATES_DIR.glob("*.j2"):
        if tmpl_path.name.startswith("base"):
            continue  # base templates are inherited, not rendered directly
        tmpl = env.get_template(tmpl_path.name)
        output_name = tmpl_path.stem  # strip .j2 → index.html
        output_path = DIST_DIR / output_name
        output_path.write_text(tmpl.render(**context), encoding="utf-8")
        print(f"    {tmpl_path.name} → {output_path.relative_to(ROOT)}")


def copy_assets() -> None:
    """Copy frontend JS, CSS, and static assets to dist/."""
    print("  [build] Copying frontend assets…")
    mappings = [
        (FRONTEND_DIR / "js", DIST_DIR / "js"),
        (FRONTEND_DIR / "styles", DIST_DIR / "styles"),
        (FRONTEND_DIR / "components", DIST_DIR / "components"),
    ]
    for src, dst in mappings:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.test.js"))
        print(f"    {src.relative_to(ROOT)} → {dst.relative_to(ROOT)}")

    # Copy a minimal favicon if one does not exist
    favicon_src = ROOT / "assets" / "favicon.svg"
    favicon_dst = DIST_DIR / "favicon.svg"
    if favicon_src.exists():
        shutil.copy2(favicon_src, favicon_dst)
    else:
        favicon_dst.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<rect width="32" height="32" fill="#0d1117"/>'
            '<text x="16" y="22" font-size="16" text-anchor="middle" fill="#58a6ff">3D</text>'
            "</svg>",
            encoding="utf-8",
        )


def build() -> None:
    """Run the full build pipeline."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    build_wasm()
    render_templates()
    copy_assets()


def main() -> int:
    print("[build] Starting build…")
    try:
        build()
    except Exception as exc:
        print(f"[build] FAILED: {exc}", file=sys.stderr)
        return 1
    print("[build] Build complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
