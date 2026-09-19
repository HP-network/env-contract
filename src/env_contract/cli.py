from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .report import as_json, as_markdown, as_sarif, as_text
from .validate import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate environment variables against a readable contract.")
    parser.add_argument("path", nargs="?", default=".env.contract", help="contract file (default: .env.contract)")
    parser.add_argument("--env-file", default=".env", help="dotenv file to read (default: .env)")
    parser.add_argument("--format", choices=("text", "json", "markdown", "sarif"), default="text")
    parser.add_argument("--no-process-env", action="store_true", help="do not merge variables from the current process")
    parser.add_argument("--allow-missing-env-file", action="store_true", help="validate the contract when the dotenv file is absent")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contract = Path(args.path)
    env_file = Path(args.env_file) if args.env_file else None
    report = validate(contract, env_file, include_process_env=not args.no_process_env, allow_missing_env_file=args.allow_missing_env_file)
    output = {"text": as_text, "json": as_json, "markdown": as_markdown, "sarif": as_sarif}[args.format](report)
    print(output)
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
