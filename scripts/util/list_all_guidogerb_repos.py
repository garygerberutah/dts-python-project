"""
list_all_guidogerb_repos.py — fetches all public (and private, if a
GITHUB_TOKEN is set) repositories for https://github.com/guidogerb and
writes them to resources/guidogerb/repos.txt.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "resources" / "guidogerb"
OUT_FILE = OUT_DIR / "repos.txt"

GITHUB_USER = "guidogerb"
API_BASE = "https://api.github.com"
PER_PAGE = 100


def _build_opener(token: str | None) -> urllib.request.OpenerDirector:
    """Build a URL opener with optional bearer-token auth."""
    handlers: list[urllib.request.BaseHandler] = []
    opener = urllib.request.build_opener(*handlers)
    opener.addheaders = [
        ("Accept", "application/vnd.github+json"),
        ("User-Agent", "ggp-repo-lister"),
        ("X-GitHub-Api-Version", "2022-11-28"),
    ]
    if token:
        opener.addheaders.append(("Authorization", f"Bearer {token}"))
    return opener


def _fetch_repos(token: str | None) -> list[str]:
    """Return a sorted list of full_name strings for every repo."""
    opener = _build_opener(token)
    ctx = ssl.create_default_context()

    if token:
        url_base = f"{API_BASE}/user/repos?affiliation=owner&per_page={PER_PAGE}"
    else:
        url_base = f"{API_BASE}/users/{GITHUB_USER}/repos?per_page={PER_PAGE}"

    repos: list[str] = []
    page = 1

    while True:
        url = f"{url_base}&page={page}"
        req = urllib.request.Request(url)
        for header, value in opener.addheaders:
            req.add_header(header, value)

        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data:
            break

        for repo in data:
            repos.append(repo["full_name"])

        if len(data) < PER_PAGE:
            break
        page += 1

    repos.sort()
    return repos


def run() -> bool:
    """Fetch repos and write the listing. Returns True on success."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if not token:
        print(
            "Warning: GITHUB_TOKEN / GH_TOKEN not set — "
            "only public repos will be listed",
            file=sys.stderr,
        )

    try:
        repos = _fetch_repos(token)
    except urllib.error.HTTPError as exc:
        print(f"Error: GitHub API returned {exc.code}: {exc.reason}", file=sys.stderr)
        return False

    if not repos:
        print("Warning: no repositories found", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for name in repos:
            f.write(f"{name}\n")

    print(f"Wrote {len(repos)} repos to {OUT_FILE}")
    return True


def main() -> None:
    if not run():
        sys.exit(1)


if __name__ == "__main__":
    main()
