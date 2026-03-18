# Resources

Copyright 2026 by GuidoGerb Publishing, LLC

Shared project configuration, filesystem metadata, and user instruction files.

## Structure

```
resources/
├── config/                # Project configuration
│   ├── site.json          # Project metadata (name, description, repository)
│   └── ruff.toml          # Ruff linter/formatter configuration
├── fs-info/               # Filesystem metadata and directory listings
├── guidogerb/             # GuidoGerb organization data
│   └── repos.txt          # List of organization repositories
└── user-instructions/     # Portable Copilot instruction files (see README inside)
```
