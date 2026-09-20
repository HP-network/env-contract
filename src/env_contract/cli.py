from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .providers import get_provider, provider_names
from .report import as_json, as_markdown, as_sarif, as_text
from .validate import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate environment variables against a readable contract.")
    parser.add_argument("path", nargs="?", default=".env.contract", help="contract file (default: .env.contract)")
    parser.add_argument("--env-file", default=".env", help="dotenv file to read (default: .env)")
    parser.add_argument("--format", choices=("text", "json", "markdown", "sarif"), default="text")
    parser.add_argument("--init", choices=provider_names(), metavar="PROVIDER", help="write a provider contract and exit")
    parser.add_argument("--output", default=".env.contract", help="output path used by --init")
    parser.add_argument("--example-output", help="also write a provider .env.example file with --init")
    parser.add_argument("--force", action="store_true", help="overwrite files used by --init")
    parser.add_argument("--list-providers", action="store_true", help="list built-in AI provider presets")
    parser.add_argument("--no-process-env", action="store_true", help="do not merge variables from the current process")
    parser.add_argument("--allow-missing-env-file", action="store_true", help="validate the contract when the dotenv file is absent")
    parser.add_argument("--allow-missing-required", action="store_true", help="do not fail when required values are absent")
    parser.add_argument("--strict-undocumented", action="store_true", help="treat variables absent from the contract as errors")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_providers:
        for name in provider_names():
            preset = get_provider(name)
            print(f"{preset.name:18} {preset.description}")
        return 0
    if args.init:
        preset = get_provider(args.init)
        if args.example_output is None and args.output == ".env.contract":
            args.example_output = ".env.example"
        outputs = [(Path(args.output), preset.contract)]
        if args.example_output:
            outputs.append((Path(args.example_output), preset.example))
        for path, content in outputs:
            if path.exists() and not args.force:
                print(f"env-contract: refusing to overwrite {path}; use --force", file=sys.stderr)
                return 2
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path}")
        return 0
    contract = Path(args.path)
    env_file = Path(args.env_file) if args.env_file else None
    report = validate(
        contract,
        env_file,
        include_process_env=not args.no_process_env,
        allow_missing_env_file=args.allow_missing_env_file,
        allow_missing_required=args.allow_missing_required,
        strict_undocumented=args.strict_undocumented,
    )
    output = {"text": as_text, "json": as_json, "markdown": as_markdown, "sarif": as_sarif}[args.format](report)
    print(output)
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
