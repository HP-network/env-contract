# env-contract

Validate the configuration a project expects before it reaches runtime.

`env-contract` reads a small `.env.contract` file, checks values from a dotenv file and the current process, and emits text, JSON, Markdown, or SARIF. It uses only the Python standard library and never prints variable values.

## Quick start

Create `.env.contract`:

```dotenv
PORT=8080 # env-contract: int required
APP_URL= # env-contract: url required
DEBUG=false # env-contract: bool optional
LOG_LEVEL=info # env-contract: enum(debug|info|warn|error) optional
```

Validate a local `.env` file:

```sh
python -m pip install git+https://github.com/HP-network/env-contract.git
env-contract .env.contract --env-file .env
```

The process environment takes precedence over values in `--env-file`. Use `--no-process-env` for reproducible file-only checks. A non-empty value on the left side is treated as a default unless `required` is specified.

Supported types are `string`, `int`, `float`, `bool`, `url`, and `secret`. Add `enum(a|b|c)` to restrict a value. Missing variables marked `required` fail the command; undeclared variables are warnings.

## CI output

```sh
env-contract .env.contract --env-file .env.example --no-process-env --format sarif > env-contract.sarif
```

The repository also ships a composite GitHub Action. It checks the contract without requiring secrets to be present in CI:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: HP-network/env-contract@v1
    with:
      env-file: .env.example
```

Use `--format json` for scripts and `--format markdown` for job summaries. Exit status is `0` when there are no errors and `1` when a contract or value is invalid.

## Development

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m env_contract .env.contract --env-file .env.example --no-process-env
```

## License

MIT
