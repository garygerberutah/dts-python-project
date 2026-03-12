"""
run.py — single CLI entry point for the ggp3d toolchain.

Usage:
    python run.py <command> [options]

Commands:
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
        description="ggp3d toolchain CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("clean", help="Remove build artefacts")
    subparsers.add_parser("build", help="Compile WASM + render templates + copy assets")

    serve_p = subparsers.add_parser("serve", help="Start local HTTP dev server")
    serve_p.add_argument("port", nargs="?", type=int, default=8080)

    subparsers.add_parser("format", help="Auto-format all source files")
    subparsers.add_parser("lint", help="Run static analysis")
    subparsers.add_parser("validate", help="Run WCAG 2.1 accessibility checks")
    subparsers.add_parser("test", help="Run Web Component test suites")

    pipeline_p = subparsers.add_parser("pipeline", help="Run the full automation pipeline")
    pipeline_p.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip the git deploy stage",
    )

    args = parser.parse_args()

    if args.command == "clean":
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
