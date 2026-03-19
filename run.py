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
    sbom       Generate SBOM manifest + append to blockchain
    sbom-db    Create/verify the PostgreSQL sbom_version table
    reset-sbom Reset SBOM manifest, blockchain, and optionally the DB
    validate-template-lock  Check for changes to template-locked files
    pipeline   Run the full automation pipeline (format → lint → validate →
               clean → build → test → sbom → deploy)
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
    template_lock_p = subparsers.add_parser(
        "validate-template-lock",
        help="Check for changes to template-locked files (outside api/ and ui/)",
    )
    template_lock_p.add_argument(
        "--force",
        action="store_true",
        help="Bypass the template lock and allow changes",
    )
    template_lock_p.add_argument(
        "--move-to",
        metavar="DIR",
        help="Move changed template files into DIR (relative to api/ or ui/)",
    )
    subparsers.add_parser("test", help="Run Web Component test suites")
    subparsers.add_parser("sbom", help="Generate SBOM manifest + append to blockchain")
    subparsers.add_parser("sbom-db", help="Create/verify the PostgreSQL sbom_version table")

    reset_sbom_p = subparsers.add_parser(
        "reset-sbom",
        help="Reset SBOM manifest, blockchain, and optionally the database",
    )
    reset_sbom_p.add_argument(
        "--include-db",
        action="store_true",
        help="Also truncate the sbom_version table in PostgreSQL",
    )
    reset_sbom_p.add_argument(
        "--include-exports",
        action="store_true",
        help="Also delete sbom_version_*.sql export files",
    )
    reset_sbom_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )

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
        from scripts.ui.clean import main as fn

        return fn()
    elif args.command == "build":
        from scripts.ui.build import main as fn

        return fn()
    elif args.command == "serve":
        from scripts.ui.serve import serve

        serve(args.port)
        return 0
    elif args.command == "format":
        from scripts.ui.format_code import main as fn

        return fn()
    elif args.command == "lint":
        from scripts.ui.lint import main as fn

        return fn()
    elif args.command == "validate":
        from scripts.ui.validate_wcag import main as fn

        return fn()
    elif args.command == "validate-copyright":
        from scripts.ui.validate_copyright import validate

        errors = validate(fix=getattr(args, "fix", False))
        return 1 if errors else 0
    elif args.command == "validate-mime":
        from scripts.ui.validate_mime_type_content import main as fn

        return fn()
    elif args.command == "validate-template-lock":
        from scripts.ui.validate_template_lock import validate

        errors = validate(
            force=getattr(args, "force", False),
            move_to=getattr(args, "move_to", None),
        )
        return 1 if errors else 0
    elif args.command == "test":
        from scripts.ui.test_components import main as fn

        return fn()
    elif args.command == "sbom":
        from scripts.blockchain.generate_sbom import main as fn

        return fn()
    elif args.command == "sbom-db":
        from scripts.blockchain.db import main as fn

        return fn()
    elif args.command == "reset-sbom":
        from scripts.blockchain.reset_sbom import (
            reset_database,
            reset_local_files,
            reset_sql_exports,
        )

        actions = ["Delete sbom.json and chain.json"]
        if args.include_exports:
            actions.append("Delete sbom_version_*.sql export files")
        if args.include_db:
            actions.append("TRUNCATE the sbom_version table in PostgreSQL")
        if not args.yes:
            print("[reset-sbom] This will:")
            for action in actions:
                print(f"  - {action}")
            answer = input("Proceed? [y/N] ").strip().lower()
            if answer != "y":
                print("[reset-sbom] Aborted.")
                return 1
        reset_local_files()
        if args.include_exports:
            reset_sql_exports()
        if args.include_db:
            reset_database()
        print("[reset] Done.")
        return 0
    elif args.command == "pipeline":
        from scripts.build_all import run

        return run(skip_deploy=args.skip_deploy)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
