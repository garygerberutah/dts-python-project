"""
build.py — compiles the Rust WASM module, renders Jinja2 templates, and
copies all frontend assets into the dist/ directory.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import hashlib
import json
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
SITE_JSON = ROOT / "resources" / "site.json"


def _load_site_config() -> dict:
    """Load project metadata from resources/site.json."""
    with open(SITE_JSON, encoding="utf-8") as f:
        return json.load(f)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a subprocess command, raising on failure."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)
    except FileNotFoundError:
        raise RuntimeError(
            f"Command failed — '{cmd[0]}' not found. Install it and retry."
        ) from None
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
    app_title: str | None = None,
    app_description: str | None = None,
    lang: str | None = None,
    favicon_filename: str = "favicon.svg",
) -> None:
    """Render all Jinja2 templates and write them to dist/."""
    print("  [build] Rendering Jinja2 templates…")
    site = _load_site_config()
    title = app_title or site.get("project_name", "${PROJECT_NAME}")
    description = app_description or site.get("project_description", "")
    lang_val = lang or site.get("lang", "en")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html"]),
        undefined=jinja2.StrictUndefined,
    )
    context = {
        "app_title": title,
        "app_description": description,
        "lang": lang_val,
        "repo_url": site.get("repository", {}).get("url", ""),
        "favicon_filename": favicon_filename,
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


def _resolve_env_vars(text: str, replacements: dict[str, str]) -> str:
    """Replace ${KEY} markers in text with values from the replacements dict."""
    for key, value in replacements.items():
        text = text.replace(f"${{{key}}}", value)
    return text


def copy_assets() -> str:
    """Copy frontend JS, CSS, and static assets to dist/, resolving ${VAR} markers.

    Returns the hashed favicon filename (e.g. 'favicon-<sha256>.svg').
    """
    print("  [build] Copying frontend assets…")
    site = _load_site_config()
    replacements = {
        "PROJECT_NAME": site.get("project_name", ""),
        "REPO_URL": site.get("repository", {}).get("url", ""),
        "WASM_MODULE": site.get("wasm_module", ""),
    }
    mappings = [
        (FRONTEND_DIR / "js", DIST_DIR / "js"),
        (FRONTEND_DIR / "styles", DIST_DIR / "styles"),
        (FRONTEND_DIR / "components", DIST_DIR / "components"),
    ]
    for src, dst in mappings:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.test.js"))
        # Resolve ${VAR} markers in copied JS/CSS files
        for filepath in dst.rglob("*"):
            if filepath.is_file() and filepath.suffix in (".js", ".css"):
                content = filepath.read_text(encoding="utf-8")
                resolved = _resolve_env_vars(content, replacements)
                if resolved != content:
                    filepath.write_text(resolved, encoding="utf-8")
        print(f"    {src.relative_to(ROOT)} → {dst.relative_to(ROOT)}")

    # Copy or generate a favicon, then rename with SHA-256 hash
    favicon_src = ROOT / "assets" / "favicon.svg"
    tmp_favicon = DIST_DIR / "_favicon_tmp.svg"
    if favicon_src.exists():
        shutil.copy2(favicon_src, tmp_favicon)
    else:
        tmp_favicon.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<rect width="32" height="32" fill="#0d1117"/>'
            '<text x="16" y="22" font-size="16" text-anchor="middle" fill="#58a6ff">3D</text>'
            "</svg>",
            encoding="utf-8",
        )
    sha = hashlib.sha256(tmp_favicon.read_bytes()).hexdigest()
    favicon_final = DIST_DIR / f"favicon-{sha}.svg"
    tmp_favicon.rename(favicon_final)
    # Store the hashed filename so templates can reference it
    _favicon_filename = favicon_final.name
    return _favicon_filename


def build() -> None:
    """Run the full build pipeline."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    build_wasm()
    favicon_filename = copy_assets()
    render_templates(favicon_filename=favicon_filename)


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
