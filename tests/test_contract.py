import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from env_contract.report import as_json, as_sarif
from env_contract.providers import get_provider
from env_contract.cli import main
from env_contract.validate import validate


class ContractTests(unittest.TestCase):
    def write_files(self, contract: str, env: str | None = None) -> tuple[Path, Path | None]:
        directory = Path(self.temp_dir.name)
        contract_path = directory / ".env.contract"
        contract_path.write_text(contract, encoding="utf-8")
        env_path = None
        if env is not None:
            env_path = directory / ".env"
            env_path.write_text(env, encoding="utf-8")
        return contract_path, env_path

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_validates_types_and_ignores_secret_values(self) -> None:
        contract, env = self.write_files(
            "PORT= # env-contract: int required\n"
            "DEBUG=false # env-contract: bool optional\n"
            "API_KEY= # env-contract: secret required\n",
            "PORT=8080\nDEBUG=yes\nAPI_KEY=super-secret\n",
        )
        with patch.dict(os.environ, {}, clear=True):
            report = validate(contract, env, include_process_env=False)
        self.assertTrue(report.valid)
        self.assertNotIn("super-secret", as_json(report))

    def test_reports_missing_and_invalid_values(self) -> None:
        contract, env = self.write_files(
            "PORT= # env-contract: int required\n"
            "MODE= # env-contract: enum(dev|prod) required\n",
            "PORT=abc\nMODE=test\n",
        )
        with patch.dict(os.environ, {}, clear=True):
            report = validate(contract, env, include_process_env=False)
        self.assertFalse(report.valid)
        self.assertEqual({finding.code for finding in report.errors}, {"invalid"})

    def test_json_and_sarif_are_machine_readable(self) -> None:
        contract, _ = self.write_files("PORT=8080 # env-contract: int\n")
        with patch.dict(os.environ, {}, clear=True):
            report = validate(contract, None, include_process_env=False, allow_missing_env_file=True)
        self.assertTrue(json.loads(as_json(report))["valid"])
        self.assertEqual(json.loads(as_sarif(report))["version"], "2.1.0")

    def test_process_environment_does_not_create_unrelated_warnings(self) -> None:
        contract, _ = self.write_files("PORT=8080 # env-contract: int\n")
        with patch.dict(os.environ, {"UNRELATED_RUNNER_VALUE": "1"}, clear=True):
            report = validate(contract, None, include_process_env=True, allow_missing_env_file=True)
        self.assertEqual(report.warnings, [])

    def test_duplicate_env_names_and_secret_defaults_are_findings(self) -> None:
        contract, env = self.write_files(
            "TOKEN=unsafe-default # env-contract: secret required\nVALUE= # env-contract: string optional\n",
            "VALUE=one\nVALUE=two\n",
        )
        with patch.dict(os.environ, {}, clear=True):
            report = validate(contract, env, include_process_env=False)
        self.assertIn("secret-default", {finding.code for finding in report.errors})
        self.assertIn("duplicate-env-name", {finding.code for finding in report.errors})

    def test_provider_preset_is_secret_safe(self) -> None:
        preset = get_provider("openai-compatible")
        self.assertIn("AI_API_KEY=", preset.contract)
        self.assertNotIn("sk-", preset.contract)

    def test_list_providers_and_init_defaults_are_available(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--list-providers"]), 0)
        self.assertIn("openai-compatible", output.getvalue())

        old_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir.name)
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["--init", "ollama"]), 0)
            self.assertTrue(Path(".env.contract").exists())
            self.assertTrue(Path(".env.example").exists())
        finally:
            os.chdir(old_cwd)
