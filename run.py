"""
run.py — single CLI entry point for the project toolchain.

Copyright 2026 by GuidoGerb Publishing, LLC

Usage:
    python run.py <command> [options]

Commands:
    setup      Configure git hooks (run once after clone)
    clean      Remove build artefacts
    build      Compile WASM, render templates, copy assets
    serve      Start local dev server (default port 8080)
    format     Auto-format all source files
    lint       Run static analysis
    validate   Run WCAG 2.1 accessibility checks
    test       Run Web Component test suites
    pipeline   Run the full automation pipeline (format → lint → validate →
               clean → build → test → deploy)
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Project toolchain CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "setup",
        help="Configure git hooks (run once after clone)",
    )
    subparsers.add_parser("clean", help="Remove build artefacts")
    subparsers.add_parser("build", help="Compile WASM + render templates + copy assets")

    serve_p = subparsers.add_parser("serve", help="Start local HTTP dev server")
    serve_p.add_argument("port", nargs="?", type=int, default=8080)

    subparsers.add_parser("format", help="Auto-format all source files")
    subparsers.add_parser("lint", help="Run static analysis")
    subparsers.add_parser("validate", help="Run WCAG 2.1 accessibility checks")
    copyright_p = subparsers.add_parser(
        "validate-copyright",
        help="Check copyright notices in source files",
    )
    copyright_p.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix missing or incorrect copyright comments",
    )
    subparsers.add_parser("validate-mime", help="Validate binary file mime-type content")
    subparsers.add_parser("test", help="Run Web Component test suites")

    pipeline_p = subparsers.add_parser("pipeline", help="Run the full automation pipeline")
    pipeline_p.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip the git deploy stage",
    )

    args = parser.parse_args()

    if args.command == "setup":
        import subprocess

        print("[setup] Configuring git hooks via pre-commit…")
        # Unset core.hooksPath if set — pre-commit manages .git/hooks/ directly
        subprocess.run(
            ["git", "config", "--unset-all", "core.hooksPath"],
            check=False,
        )
        subprocess.run(["pre-commit", "install"], check=True)
        print("[setup] Done — pre-commit hooks installed.")
        return 0
    elif args.command == "clean":
        from scripts.clean import main as fn

        return fn()
    elif args.command == "build":
        from scripts.build import main as fn

        return fn()
    elif args.command == "serve":
        from scripts.serve import serve

        serve(args.port)
        return 0
    elif args.command == "format":
        from scripts.format_code import main as fn

        return fn()
    elif args.command == "lint":
        from scripts.lint import main as fn

        return fn()
    elif args.command == "validate":
        from scripts.validate_wcag import main as fn

        return fn()
    elif args.command == "validate-copyright":
        from scripts.validate_copyright import validate

        errors = validate(fix=getattr(args, "fix", False))
        return 1 if errors else 0
    elif args.command == "validate-mime":
        from scripts.validate_mime_type_content import main as fn

        return fn()
    elif args.command == "test":
        from scripts.test_components import main as fn

        return fn()
    elif args.command == "pipeline":
        from scripts.pipeline import run

        return run(skip_deploy=args.skip_deploy)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
