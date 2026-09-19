from __future__ import annotations

import json

from .model import Finding, Report


def _finding_dict(finding: Finding) -> dict[str, object]:
    return {
        "level": finding.level,
        "code": finding.code,
        "message": finding.message,
        "variable": finding.variable,
        "line": finding.line,
    }


def as_json(report: Report) -> str:
    return json.dumps({
        "valid": report.valid,
        "contract": report.contract,
        "env_file": report.env_file,
        "entries": report.entries,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "findings": [_finding_dict(finding) for finding in report.findings],
    }, indent=2, sort_keys=True)


def as_text(report: Report) -> str:
    status = "valid" if report.valid else "invalid"
    lines = [f"{report.contract}: {status} ({report.entries} variables, {len(report.errors)} errors, {len(report.warnings)} warnings)"]
    for finding in report.findings:
        location = f" line {finding.line}" if finding.line else ""
        lines.append(f"{finding.level.upper():7} {finding.code:16} {finding.message}{location}")
    return "\n".join(lines)


def as_markdown(report: Report) -> str:
    status = "PASS" if report.valid else "FAIL"
    lines = [f"### Environment contract: {status}", "", f"- Variables: `{report.entries}`", f"- Errors: `{len(report.errors)}`", f"- Warnings: `{len(report.warnings)}`", ""]
    if report.findings:
        lines.extend(["| Level | Code | Message |", "| --- | --- | --- |"])
        for finding in report.findings:
            lines.append(f"| {finding.level} | `{finding.code}` | {finding.message} |")
    else:
        lines.append("No findings.")
    return "\n".join(lines)


def as_sarif(report: Report) -> str:
    results = []
    for finding in report.findings:
        result = {
            "ruleId": finding.code,
            "level": "error" if finding.level == "error" else "warning",
            "message": {"text": finding.message},
        }
        if finding.line:
            result["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": report.contract}, "region": {"startLine": finding.line}}}]
        results.append(result)
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "env-contract", "informationUri": "https://github.com/HP-network/env-contract"}}, "results": results}],
    }, indent=2)
