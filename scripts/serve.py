"""
serve.py — starts a local HTTP development server from dist/.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
DEFAULT_PORT = 8080


class _CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that adds CORS and WASM mime-type headers."""

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        super().end_headers()

    def guess_type(self, path: str) -> str:  # type: ignore[override]
        mime = super().guess_type(path)
        if str(path).endswith(".wasm"):
            return "application/wasm"
        return mime

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D401
        print(f"  [serve] {fmt % args}")


def serve(port: int = DEFAULT_PORT) -> None:
    """Serve the dist/ directory over HTTP."""
    if not DIST_DIR.exists():
        print(
            "[serve] dist/ directory not found. Run 'python run.py build' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    os.chdir(DIST_DIR)
    handler = _CORSHTTPRequestHandler
    handler.extensions_map = {
        **handler.extensions_map,
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".wasm": "application/wasm",
        ".css": "text/css",
    }

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[serve] Serving http://localhost:{port}/ from {DIST_DIR}")
        print("[serve] Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[serve] Stopped.")


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    serve(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
