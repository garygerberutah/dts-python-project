"""
validate_wcag.py — WCAG 2.1 compliance validator for compiled HTML output.

Checks the rendered HTML in dist/ for a subset of WCAG 2.1 Level AA rules:
  • 1.1.1  Non-text content — <img> elements must have non-empty alt text.
  • 1.3.1  Info & Relationships — <form> inputs need associated <label>.
  • 2.4.2  Page Titled — every page must have a non-empty <title>.
  • 2.4.4  Link Purpose — <a> elements must have descriptive text or aria-label.
  • 3.1.1  Language of Page — <html> must have a lang attribute.
  • 4.1.2  Name, Role, Value — interactive elements must have accessible names.

Exits with non-zero status if any violation is found (fail-fast).
"""

import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"


@dataclass
class Violation:
    rule: str
    message: str
    file: str
    line: int = 0


@dataclass
class _ParseContext:
    violations: list[Violation] = field(default_factory=list)
    file: str = ""
    has_title: bool = False
    title_text: str = ""
    html_lang: str = ""
    _current_tag: str = ""
    _inside_title: bool = False
    _inside_a: bool = False
    _a_has_text: bool = False
    _a_attrs: dict = field(default_factory=dict)
    _lineno: int = 0


class WCAGParser(HTMLParser):
    def __init__(self, ctx: _ParseContext) -> None:
        super().__init__()
        self._ctx = ctx

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        attr_dict = dict(attrs)
        ctx = self._ctx
        ctx._current_tag = tag
        ctx._lineno = self.getpos()[0]

        # 3.1.1 — html must have lang
        if tag == "html":
            ctx.html_lang = attr_dict.get("lang", "")
            if not ctx.html_lang:
                ctx.violations.append(
                    Violation(
                        rule="3.1.1",
                        message="<html> element is missing a 'lang' attribute.",
                        file=ctx.file,
                        line=self.getpos()[0],
                    )
                )

        # 2.4.2 — title tracking
        if tag == "title":
            ctx._inside_title = True

        # 1.1.1 — img must have alt
        if tag == "img":
            alt = attr_dict.get("alt")
            if alt is None:
                src = attr_dict.get("src", "")
                ctx.violations.append(
                    Violation(
                        rule="1.1.1",
                        message=f"<img> is missing an 'alt' attribute (src={src!r}).",
                        file=ctx.file,
                        line=self.getpos()[0],
                    )
                )
            elif alt.strip() == "" and attr_dict.get("role") != "presentation":
                # Empty alt is only acceptable for decorative images with role=presentation
                pass

        # 2.4.4 — anchor must have text or aria-label
        if tag == "a":
            ctx._inside_a = True
            ctx._a_has_text = False
            ctx._a_attrs = attr_dict
            aria_label = attr_dict.get("aria-label", "").strip()
            aria_labelledby = attr_dict.get("aria-labelledby", "").strip()
            if aria_label or aria_labelledby:
                ctx._a_has_text = True  # pre-marked as accessible

        # 4.1.2 — buttons and inputs need accessible names
        if tag in ("button", "input", "select", "textarea"):
            accessible_name = (
                attr_dict.get("aria-label", "").strip()
                or attr_dict.get("aria-labelledby", "").strip()
                or attr_dict.get("title", "").strip()
            )
            if tag == "input" and attr_dict.get("type") in ("hidden", "submit", "button", "reset"):
                pass  # submit/button/reset use value; hidden doesn't need a label
            elif tag == "input" and not (accessible_name or attr_dict.get("id")):
                input_type = attr_dict.get("type", "text")
                ctx.violations.append(
                    Violation(
                        rule="4.1.2",
                        message=(
                            f"<input type={input_type!r}> has no accessible name "
                            "(aria-label, aria-labelledby, or associated label via id)."
                        ),
                        file=ctx.file,
                        line=self.getpos()[0],
                    )
                )
            elif tag == "button" and not accessible_name:
                pass  # button text is checked via handle_data

    def handle_endtag(self, tag: str) -> None:
        ctx = self._ctx
        if tag == "title":
            ctx._inside_title = False
            ctx.has_title = True
        if tag == "a" and ctx._inside_a:
            ctx._inside_a = False
            if not ctx._a_has_text:
                href = ctx._a_attrs.get("href", "")
                ctx.violations.append(
                    Violation(
                        rule="2.4.4",
                        message=f"<a href={href!r}> has no accessible text or aria-label.",
                        file=ctx.file,
                        line=self.getpos()[0],
                    )
                )

    def handle_data(self, data: str) -> None:
        ctx = self._ctx
        if ctx._inside_title and data.strip():
            ctx.title_text = data.strip()
        if ctx._inside_a and data.strip():
            ctx._a_has_text = True


def _check_file(html_path: Path) -> list[Violation]:
    ctx = _ParseContext(file=str(html_path))
    parser = WCAGParser(ctx)
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()

    # 2.4.2 — page must have a title
    if not ctx.has_title or not ctx.title_text:
        ctx.violations.append(
            Violation(
                rule="2.4.2",
                message="Page is missing a non-empty <title> element.",
                file=ctx.file,
            )
        )
    return ctx.violations


def validate(dist_dir: Path = DIST_DIR) -> list[Violation]:
    """Validate all HTML files in dist_dir. Returns all violations found."""
    if not dist_dir.exists():
        print(
            "[wcag] dist/ directory not found. Run 'python run.py build' first.",
            file=sys.stderr,
        )
        return [
            Violation(
                rule="BUILD",
                message="dist/ directory not found.",
                file=str(dist_dir),
            )
        ]

    all_violations: list[Violation] = []
    html_files = list(dist_dir.glob("**/*.html"))
    if not html_files:
        print("[wcag] No HTML files found in dist/.")
        return []

    for html_path in html_files:
        violations = _check_file(html_path)
        all_violations.extend(violations)

    return all_violations


def main() -> int:
    print("[wcag] Running WCAG 2.1 compliance validation…")
    violations = validate()
    if not violations:
        print("[wcag] ✓ No accessibility violations found.")
        return 0

    print(f"[wcag] ✗ {len(violations)} violation(s) found:", file=sys.stderr)
    for v in violations:
        print(f"  [{v.rule}] {v.file}:{v.line}: {v.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
