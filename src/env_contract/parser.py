from __future__ import annotations

import re
from pathlib import Path

from .model import ContractEntry, Finding, ValueType


NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TYPE_NAMES: set[str] = {"string", "int", "float", "bool", "url", "secret"}
BOOL_VALUES = {"true", "false", "1", "0", "yes", "no", "on", "off"}


def _strip_inline_comment(value: str) -> tuple[str, str]:
    marker = "# env-contract:"
    if marker not in value:
        return value.strip(), ""
    before, metadata = value.split(marker, 1)
    return before.strip(), metadata.strip()


def _parse_metadata(metadata: str, line: int) -> tuple[str, bool | None, tuple[str, ...], str | None, list[Finding]]:
    value_type = "string"
    required: bool | None = None
    choices: tuple[str, ...] = ()
    default: str | None = None
    findings: list[Finding] = []
    for token in metadata.split():
        if token in TYPE_NAMES:
            value_type = token
        elif token == "required":
            required = True
        elif token == "optional":
            required = False
        elif token.startswith("enum(") and token.endswith(")"):
            choices = tuple(item for item in token[5:-1].split("|") if item)
            if not choices:
                findings.append(Finding("error", "invalid-enum", "enum must contain at least one value", line=line))
        elif token.startswith("default="):
            default = token[8:]
        elif token:
            findings.append(Finding("error", "unknown-metadata", f"unknown contract option '{token}'", line=line))
    return value_type, required, choices, default, findings


def parse_contract(path: Path) -> tuple[list[ContractEntry], list[Finding]]:
    entries: list[ContractEntry] = []
    findings: list[Finding] = []
    seen: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [Finding("error", "contract-read", f"cannot read contract: {exc}")]

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            findings.append(Finding("error", "invalid-line", "expected NAME=value", line=line_number))
            continue
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if not NAME_RE.fullmatch(name):
            findings.append(Finding("error", "invalid-name", f"invalid variable name '{name}'", line=line_number))
            continue
        if name in seen:
            findings.append(Finding("error", "duplicate-name", f"variable '{name}' is declared more than once", name, line_number))
            continue
        seen.add(name)
        value, metadata = _strip_inline_comment(raw_value)
        value_type, required_override, choices, metadata_default, metadata_findings = _parse_metadata(metadata, line_number)
        for finding in metadata_findings:
            findings.append(Finding(finding.level, finding.code, finding.message, name, finding.line))
        default = metadata_default if metadata_default is not None else (value or None)
        required = required_override if required_override is not None else not bool(value)
        if value_type == "secret" and default is not None:
            findings.append(Finding("error", "secret-default", f"secret '{name}' must not have a default in the contract", name, line_number))
        if value_type == "url" and default and not (default.startswith("http://") or default.startswith("https://")):
            findings.append(Finding("warning", "default-type", f"default for '{name}' does not look like a URL", name, line_number))
        if value_type == "bool" and default and default.lower() not in BOOL_VALUES:
            findings.append(Finding("warning", "default-type", f"default for '{name}' is not a boolean", name, line_number))
        entries.append(ContractEntry(name, value_type, required, default, choices, line_number))
    return entries, findings


def parse_env_file(path: Path) -> tuple[dict[str, str], list[Finding]]:
    values: dict[str, str] = {}
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {}, [Finding("error", "env-read", f"cannot read environment file: {exc}")]
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            findings.append(Finding("error", "invalid-env-line", "expected NAME=value", line=line_number))
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not NAME_RE.fullmatch(name):
            findings.append(Finding("error", "invalid-env-name", f"invalid variable name '{name}'", line=line_number))
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if name in values:
            findings.append(Finding("error", "duplicate-env-name", f"variable '{name}' appears more than once", name, line_number))
        values[name] = value
    return values, findings
