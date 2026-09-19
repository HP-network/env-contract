from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ValueType = Literal["string", "int", "float", "bool", "url", "secret"]


@dataclass(frozen=True)
class ContractEntry:
    name: str
    value_type: ValueType = "string"
    required: bool = True
    default: str | None = None
    choices: tuple[str, ...] = ()
    line: int = 0


@dataclass(frozen=True)
class Finding:
    level: Literal["error", "warning"]
    code: str
    message: str
    variable: str | None = None
    line: int | None = None


@dataclass
class Report:
    contract: str
    env_file: str | None
    entries: int
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "warning"]

    @property
    def valid(self) -> bool:
        return not self.errors
