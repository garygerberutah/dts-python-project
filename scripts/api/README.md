<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# scripts/api/ — API Build Tooling

Placeholder package for API-related build and deployment scripts. This module
will contain toolchain automation for the project's REST API layer as the
backend evolves.

Currently empty — the `__init__.py` package marker is present so that the
module is importable and discoverable by the pipeline infrastructure.

## Conventions

Scripts added to this package must follow the same patterns as `scripts/ui/`:

- Expose a `main() -> int` entry point (0 = success, 1 = failure).
- Use `ROOT = Path(__file__).resolve().parent.parent.parent` for the project root.
- Include `Copyright 2026 by GuidoGerb Publishing, LLC` in the module docstring.
- **Never skip gracefully** — missing tools or resources must cause hard failure.
- Register new stages in `scripts/build_all.py` and `run.py` when ready.
