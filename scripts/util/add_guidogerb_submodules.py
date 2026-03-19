"""
add_guidogerb_submodules.py — maintains submodules in the guidogerb/guidogerb
repository so that every repo in the guidogerb GitHub account is present as a
submodule. Stale submodules whose upstream repo no longer exists are removed.
After syncing, the repository README.md is updated with a markdown table of
all submodules and their descriptions (extracted from each submodule's README).

Usage:
    python -m scripts.util.add_guidogerb_submodules /path/to/guidogerb

Copyright 2026 by DTS, The State of Utah
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_USER = "guidogerb"
SELF_REPO = "guidogerb"  # the repo this script manages — never add as its own submodule
API_BASE = "https://api.github.com"
PER_PAGE = 100
SUBMODULES_DIR = "submodules"  # all submodules live under this folder

START_MARKER = "<!-- SUBMODULE-LIST-START -->"
END_MARKER = "<!-- SUBMODULE-LIST-END -->"


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _github_request(url: str, token: str | None) -> list | dict:
    """Make a single authenticated GitHub API request and return parsed JSON."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ggp-submodule-manager")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_all_repos(token: str | None) -> list[dict]:
    """Return a list of dicts (name, full_name, clone_url, html_url, description)."""
    if token:
        url_base = f"{API_BASE}/user/repos?affiliation=owner&per_page={PER_PAGE}"
    else:
        url_base = f"{API_BASE}/users/{GITHUB_USER}/repos?per_page={PER_PAGE}"

    repos: list[dict] = []
    page = 1

    while True:
        url = f"{url_base}&page={page}"
        data = _github_request(url, token)
        if not data:
            break
        for r in data:
            # Only include repos owned by guidogerb
            if r.get("owner", {}).get("login", "").lower() != GITHUB_USER:
                continue
            repos.append(
                {
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "clone_url": r["clone_url"],
                    "html_url": r["html_url"],
                    "description": r.get("description") or "",
                }
            )
        if len(data) < PER_PAGE:
            break
        page += 1

    repos.sort(key=lambda r: r["name"].lower())
    return repos


# ---------------------------------------------------------------------------
# Submodule helpers
# ---------------------------------------------------------------------------


def _get_existing_submodules(repo_dir: Path) -> dict[str, str]:
    """Return {submodule_path: url} from .gitmodules."""
    gitmodules = repo_dir / ".gitmodules"
    if not gitmodules.exists():
        return {}

    result = subprocess.run(
        ["git", "config", "--file", ".gitmodules", "-l"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}

    paths: dict[str, str] = {}
    urls: dict[str, str] = {}
    for line in result.stdout.strip().splitlines():
        # Lines like: submodule.NAME.path=NAME or submodule.NAME.url=URL
        m = re.match(r"submodule\.(.+?)\.path=(.+)", line)
        if m:
            paths[m.group(1)] = m.group(2)
        m = re.match(r"submodule\.(.+?)\.url=(.+)", line)
        if m:
            urls[m.group(1)] = m.group(2)

    return {paths[k]: urls.get(k, "") for k in paths}


def _submodule_path(name: str) -> str:
    """Return the canonical submodule path: submodules/<name>."""
    return f"{SUBMODULES_DIR}/{name}"


def _name_from_path(path: str) -> str:
    """Extract the repo name from a submodule path."""
    return path.rsplit("/", 1)[-1]


def _disable_lfs_for_submodule(repo_dir: Path, sub_path: str) -> None:
    """Disable Git LFS inside a submodule so large files are skipped."""
    sub_dir = repo_dir / sub_path
    if not sub_dir.is_dir():
        return
    # Uninstall LFS hooks; ignore errors if LFS isn't present
    subprocess.run(
        ["git", "lfs", "uninstall"],
        cwd=sub_dir,
        capture_output=True,
        text=True,
    )
    # Remove any .lfsconfig so future fetches don't pull LFS objects
    lfsconfig = sub_dir / ".lfsconfig"
    if lfsconfig.is_file():
        lfsconfig.unlink()


def _add_submodule(repo_dir: Path, name: str, clone_url: str, *, skip_lfs: bool = False) -> bool:
    """Add a new submodule under submodules/<name>. Returns True on success."""
    sub_path = _submodule_path(name)
    print(f"  Adding submodule: {sub_path}")

    # Ensure the submodules directory exists
    (repo_dir / SUBMODULES_DIR).mkdir(exist_ok=True)

    env = os.environ.copy()
    if skip_lfs:
        env["GIT_LFS_SKIP_SMUDGE"] = "1"

    result = subprocess.run(
        ["git", "submodule", "add", "--", clone_url, sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"    Warning: failed to add {name}: {result.stderr.strip()}", file=sys.stderr)
        return False

    # Init and update the newly added submodule
    subprocess.run(
        ["git", "submodule", "update", "--init", "--", sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    if skip_lfs:
        _disable_lfs_for_submodule(repo_dir, sub_path)

    return True


def _checkout_latest_version_tag(repo_dir: Path, sub_path: str) -> str | None:
    """If the submodule has tags starting with 'v', checkout the latest one.

    Returns the tag name checked out, or None if no version tags exist.
    """
    sub_dir = repo_dir / sub_path
    if not sub_dir.is_dir():
        return None

    # Fetch all tags
    subprocess.run(
        ["git", "fetch", "--tags"],
        cwd=sub_dir,
        capture_output=True,
        text=True,
    )

    # List tags matching v* sorted by version (descending)
    result = subprocess.run(
        ["git", "tag", "-l", "v*", "--sort=-v:refname"],
        cwd=sub_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None

    latest_tag = result.stdout.strip().splitlines()[0]

    checkout = subprocess.run(
        ["git", "checkout", latest_tag],
        cwd=sub_dir,
        capture_output=True,
        text=True,
    )
    if checkout.returncode != 0:
        print(
            f"    Warning: failed to checkout {latest_tag} "
            f"in {sub_path}: {checkout.stderr.strip()}",
            file=sys.stderr,
        )
        return None

    print(f"    Checked out {latest_tag}")
    return latest_tag


def _sync_submodule(repo_dir: Path, sub_path: str, *, skip_lfs: bool = False) -> bool:
    """Sync and pull latest changes for an existing submodule."""
    print(f"  Syncing submodule: {sub_path}")

    env = os.environ.copy()
    if skip_lfs:
        env["GIT_LFS_SKIP_SMUDGE"] = "1"

    subprocess.run(
        ["git", "submodule", "sync", "--", sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        ["git", "submodule", "update", "--init", "--remote", "--", sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"    Warning: failed to sync {sub_path}: {result.stderr.strip()}", file=sys.stderr)
        return False

    if skip_lfs:
        _disable_lfs_for_submodule(repo_dir, sub_path)

    return True


def _remove_submodule(repo_dir: Path, sub_path: str) -> bool:
    """Remove a submodule by its path (e.g. 'submodules/foo' or 'foo')."""
    print(f"  Removing submodule: {sub_path}")
    # Deinit
    subprocess.run(
        ["git", "submodule", "deinit", "-f", "--", sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    # Remove from index and working tree
    subprocess.run(
        ["git", "rm", "-f", "--", sub_path],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    # Clean up .git/modules entry (check both path variants)
    for modules_path in (sub_path, _name_from_path(sub_path)):
        modules_dir = repo_dir / ".git" / "modules" / modules_path
        if modules_dir.is_dir():
            shutil.rmtree(modules_dir)
    # Remove leftover working directory if git rm didn't clean it
    leftover = repo_dir / sub_path
    if leftover.is_dir():
        shutil.rmtree(leftover)
    return True


# ---------------------------------------------------------------------------
# README description extraction
# ---------------------------------------------------------------------------


def _extract_readme_description(repo_dir: Path, name: str) -> str:
    """Extract the first meaningful paragraph from a submodule's README."""
    sub_dir = repo_dir / SUBMODULES_DIR / name
    readme = None
    for candidate in ("README.md", "readme.md", "README.rst", "README.txt", "README"):
        path = sub_dir / candidate
        if path.is_file():
            readme = path
            break

    if readme is None:
        return ""

    try:
        text = readme.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

    lines: list[str] = []
    past_title = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if past_title and lines:
                break  # end of first paragraph
            continue
        # Skip markdown headings
        if stripped.startswith("#"):
            past_title = True
            continue
        # Skip badges / images
        if stripped.startswith("[![") or stripped.startswith("!["):
            continue
        # Skip HTML comments
        if stripped.startswith("<!--"):
            continue
        # Skip underline-style headings (=== or ---)
        if re.match(r"^[=\-]{3,}$", stripped):
            past_title = True
            continue
        past_title = True
        lines.append(stripped)

    desc = " ".join(lines)
    # Collapse any pipe characters that would break the markdown table
    desc = desc.replace("|", "—")
    if len(desc) > 150:
        desc = desc[:147] + "..."
    return desc


# ---------------------------------------------------------------------------
# README table generation
# ---------------------------------------------------------------------------


def _build_markdown_table(
    repos: list[dict],
    repo_dir: Path,
) -> str:
    """Build a markdown table of submodule repos with descriptions."""
    header = "| Repository | Description |\n|---|---|"
    rows: list[str] = []

    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        # Prefer README-derived description, fall back to GitHub API description
        desc = _extract_readme_description(repo_dir, name)
        if not desc:
            desc = repo.get("description", "") or "No description available"
        rows.append(f"| [{name}]({url}) | {desc} |")

    return header + "\n" + "\n".join(rows)


def _update_readme(repo_dir: Path, table_md: str) -> None:
    """Insert or replace the submodule table between markers in README.md."""
    readme_path = repo_dir / "README.md"

    if readme_path.is_file():
        content = readme_path.read_text(encoding="utf-8")
    else:
        content = f"# {SELF_REPO}\n"

    block = f"{START_MARKER}\n\n## Submodules\n\n{table_md}\n\n{END_MARKER}"

    if START_MARKER in content and END_MARKER in content:
        # Replace existing block using plain string operations (not regex)
        # to avoid backslash escape issues in README content
        start_idx = content.index(START_MARKER)
        end_idx = content.index(END_MARKER) + len(END_MARKER)
        content = content[:start_idx] + block + content[end_idx:]
    else:
        # Append at the end
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n{block}\n"

    readme_path.write_text(content, encoding="utf-8")
    print(f"  Updated {readme_path}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(repo_dir_str: str, *, ignore_repos: set[str] | None = None, skip_lfs: bool = False) -> bool:
    """Sync all submodules and update the README. Returns True on success."""
    repo_dir = Path(repo_dir_str).resolve()
    if not (repo_dir / ".git").exists():
        print(f"Error: '{repo_dir}' is not a git repository", file=sys.stderr)
        return False

    ignore: set[str] = ignore_repos or set()
    if ignore:
        print(f"Ignoring repos: {', '.join(sorted(ignore))}")

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            "Warning: GITHUB_TOKEN / GH_TOKEN not set — only public repos will be listed",
            file=sys.stderr,
        )

    # 1. Fetch all repos from GitHub
    print("Fetching repository list from GitHub...")
    try:
        all_repos = _fetch_all_repos(token)
    except urllib.error.HTTPError as exc:
        print(f"Error: GitHub API returned {exc.code}: {exc.reason}", file=sys.stderr)
        return False

    # Build lookup: name → repo dict (exclude self and ignored repos)
    repo_by_name: dict[str, dict] = {}
    for r in all_repos:
        if r["name"] == SELF_REPO:
            continue
        if r["name"] in ignore:
            continue
        repo_by_name[r["name"]] = r

    remote_names = set(repo_by_name.keys())
    print(f"  Found {len(remote_names)} remote repos (excluding self)")

    # 2. Discover existing submodules (path → url)
    existing = _get_existing_submodules(repo_dir)
    print(f"  Found {len(existing)} existing submodules")

    # Build name → path lookup; detect root-level submodules needing migration
    existing_by_name: dict[str, str] = {}  # name → current path
    root_level: dict[str, str] = {}  # name → path (at repo root, needs move)
    for path in existing:
        name = _name_from_path(path)
        existing_by_name[name] = path
        if not path.startswith(f"{SUBMODULES_DIR}/"):
            root_level[name] = path

    if root_level:
        print(f"  Found {len(root_level)} root-level submodules to migrate into {SUBMODULES_DIR}/")

    existing_names = set(existing_by_name.keys())

    to_add = remote_names - existing_names
    to_sync = remote_names & existing_names
    to_remove = existing_names - remote_names

    # Also remove ignored repos that are currently submodules
    ignored_existing = ignore & existing_names
    if ignored_existing:
        to_remove |= ignored_existing
        to_sync -= ignored_existing
        print(
            f"  Will remove {len(ignored_existing)} ignored submodules: "
            f"{', '.join(sorted(ignored_existing))}"
        )

    # 3. Migrate root-level submodules → submodules/<name>
    #    (remove at old path, then re-add at new path)
    to_migrate = set(root_level.keys()) - to_remove
    if to_migrate:
        print(f"\nMigrating {len(to_migrate)} submodules into {SUBMODULES_DIR}/...")
        for name in sorted(to_migrate):
            old_path = root_level[name]
            _remove_submodule(repo_dir, old_path)
        # Migrated repos need to be added fresh, not synced
        to_add |= to_migrate
        to_sync -= to_migrate

    # 4. Remove stale / ignored submodules
    stale_to_remove = to_remove - to_migrate  # already removed during migration
    if stale_to_remove:
        print(f"\nRemoving {len(stale_to_remove)} stale submodules...")
        for name in sorted(stale_to_remove):
            path = existing_by_name.get(name, _submodule_path(name))
            _remove_submodule(repo_dir, path)

    # 5. Add new submodules (including migrated ones)
    if to_add:
        print(f"\nAdding {len(to_add)} new submodules...")
        for name in sorted(to_add):
            _add_submodule(repo_dir, name, repo_by_name[name]["clone_url"], skip_lfs=skip_lfs)

    # 6. Sync existing submodules
    if to_sync:
        print(f"\nSyncing {len(to_sync)} existing submodules...")
        for name in sorted(to_sync):
            sub_path = existing_by_name.get(name, _submodule_path(name))
            _sync_submodule(repo_dir, sub_path, skip_lfs=skip_lfs)

    # 7. Checkout latest version tag for each active submodule
    active_names = to_add | to_sync
    if active_names:
        print(f"\nChecking version tags for {len(active_names)} submodules...")
        for name in sorted(active_names):
            sub_path = _submodule_path(name)
            tag = _checkout_latest_version_tag(repo_dir, sub_path)
            if not tag:
                print(f"    {name}: no v* tags found, staying on default branch")

    # 8. Build the table from repos that are now submodules
    present_repos = [repo_by_name[n] for n in sorted(repo_by_name) if n in (to_add | to_sync)]
    print(f"\nUpdating README.md with {len(present_repos)} submodule entries...")
    table = _build_markdown_table(present_repos, repo_dir)
    _update_readme(repo_dir, table)

    # 9. Stage, commit, and push all changes
    print("\nCommitting and pushing changes...")

    # Stage only known paths to avoid choking on orphaned submodule dirs
    for item in (".gitmodules", "README.md", SUBMODULES_DIR):
        if (repo_dir / item).exists():
            subprocess.run(["git", "add", "--", item], cwd=repo_dir, capture_output=True)
    # Also stage any removals (deleted root-level submodule entries)
    subprocess.run(["git", "add", "-u"], cwd=repo_dir, capture_output=True)

    # Only commit if there are staged changes
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_dir,
    )
    if status.returncode != 0:
        subprocess.run(
            ["git", "commit", "-m", "Update submodules and README table"],
            cwd=repo_dir,
            check=True,
        )
        subprocess.run(["git", "push", "origin"], cwd=repo_dir, check=True)
        print("  Pushed to origin.")
    else:
        print("  Nothing to commit — working tree clean.")

    print("\nDone.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Maintain submodules in the guidogerb/guidogerb repo — add, sync, "
            "remove, and update the README submodule table."
        ),
    )
    parser.add_argument(
        "repo_dir",
        help="Path to the local guidogerb/guidogerb repository clone",
    )
    parser.add_argument(
        "--ignore-repos",
        default="",
        help="Comma-separated list of repository names to skip",
    )
    parser.add_argument(
        "--skip-lfs",
        action="store_true",
        default=False,
        help="Skip Git LFS files when cloning/syncing submodules",
    )
    args = parser.parse_args()

    ignored = {name.strip() for name in args.ignore_repos.split(",") if name.strip()}

    if not run(args.repo_dir, ignore_repos=ignored, skip_lfs=args.skip_lfs):
        sys.exit(1)


if __name__ == "__main__":
    main()
