from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from .model import ContractEntry, Finding, Report
from .parser import BOOL_VALUES, parse_contract, parse_env_file


def _type_error(entry: ContractEntry, value: str) -> str | None:
    if entry.value_type == "int":
        try:
            int(value)
        except ValueError:
            return "must be an integer"
    elif entry.value_type == "float":
        try:
            float(value)
        except ValueError:
            return "must be a number"
    elif entry.value_type == "bool" and value.lower() not in BOOL_VALUES:
        return "must be a boolean (true/false, yes/no, on/off, or 1/0)"
    elif entry.value_type == "url":
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "must be an absolute http(s) URL"
    elif entry.value_type == "secret" and not value:
        return "must not be empty"
    if entry.choices and value not in entry.choices:
        return f"must be one of: {', '.join(entry.choices)}"
    return None


def validate(contract_path: Path, env_path: Path | None = None, *, include_process_env: bool = True,
             allow_missing_env_file: bool = False, allow_missing_required: bool = False) -> Report:
    entries, contract_findings = parse_contract(contract_path)
    file_values: dict[str, str] = {}
    env_findings: list[Finding] = []
    used_env_path: str | None = None
    if env_path is not None:
        if env_path.exists():
            file_values, env_findings = parse_env_file(env_path)
            used_env_path = str(env_path)
        elif not allow_missing_env_file:
            env_findings = [Finding("error", "env-missing", f"environment file does not exist: {env_path}")]
    values = {**file_values, **(dict(os.environ) if include_process_env else {})}

    findings = [*contract_findings, *env_findings]
    declared = {entry.name for entry in entries}
    for entry in entries:
        value = values.get(entry.name)
        if value is None or value == "":
            if entry.default is not None:
                value = entry.default
            elif entry.required and not allow_missing_required:
                findings.append(Finding("error", "missing", f"required variable '{entry.name}' is missing", entry.name, entry.line))
                continue
            else:
                continue
        error = _type_error(entry, value)
        if error:
            findings.append(Finding("error", "invalid", f"'{entry.name}' {error}", entry.name, entry.line))

    # Ignore unrelated shell and CI variables; only file values are documented here.
    for name in sorted(set(file_values) - declared):
        if name.startswith("_"):
            continue
        findings.append(Finding("warning", "undocumented", f"variable '{name}' is not declared in the contract", name))
    return Report(str(contract_path), used_env_path, len(entries), findings)
