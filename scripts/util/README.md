<!-- Copyright 2026 by DTS, The State of Utah -->

# scripts/util/ — Utility Scripts

Standalone utility scripts that are **not** part of the automated pipeline.
These tools assist with repository management, asset organisation, and data
collection.

## Modules

### add_guidogerb_submodules.py

Maintains submodules in the `guidogerb/guidogerb` repository so that every repo
in the guidogerb GitHub account is present as a submodule. Stale submodules
whose upstream repo no longer exists are removed. After syncing, the repository
`README.md` is updated with a markdown table of all submodules and their
descriptions.

```bash
python -m scripts.util.add_guidogerb_submodules /path/to/guidogerb
```

**Key functions:**

| Function                            | Description                                     |
|-------------------------------------|-------------------------------------------------|
| `_fetch_all_repos(token)`           | Fetch all repos from the guidogerb account      |
| `_get_existing_submodules(dir)`     | Parse `.gitmodules` for current submodules       |
| `_add_submodule(dir, name, url, …)` | Add a new git submodule                         |
| `_sync_submodule(dir, path, …)`     | Fetch and checkout latest version tag            |
| `_remove_submodule(dir, path)`      | Remove a stale submodule                         |
| `_build_markdown_table(repos, dir)` | Generate markdown table of all submodules        |
| `_update_readme(dir, table)`        | Insert/replace submodule table in README         |
| `run(dir, ignore, skip_lfs)`        | Orchestrate full sync                            |

Requires a `GITHUB_TOKEN` environment variable for private repos.

---

### list_all_guidogerb_repos.py

Fetches all public (and private, if `GITHUB_TOKEN` is set) repositories for
the guidogerb GitHub account and writes a sorted listing to
`resources/guidogerb/repos.txt`.

```bash
python -m scripts.util.list_all_guidogerb_repos
```

---

### model-downloader.py

Streams large ML models directly from Hugging Face to AWS S3 without local
storage. Useful for populating an S3 bucket with model weights for inference
infrastructure.

```bash
python scripts/util/model-downloader.py
```

---

### scrape_directory_listing.py

Recursively lists every file under a given directory and writes the
fully-qualified paths to a timestamped CSV in `resources/fs-info/`.

```bash
python -m scripts.util.scrape_directory_listing /target/directory
```

| Function              | Description                                     |
|-----------------------|-------------------------------------------------|
| `_collect_files(dir)` | Return sorted fully-qualified paths of all files|
| `run(target_dir)`     | Scrape directory, write CSV listing              |
