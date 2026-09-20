# env-contract

Validate the configuration a project expects before it reaches runtime.

`env-contract` reads a small `.env.contract` file, checks values from a dotenv file and the current process, and emits text, JSON, Markdown, or SARIF. It uses only the Python standard library and never prints variable values.

It includes presets for OpenAI, Anthropic, Gemini, Azure OpenAI, Ollama, OpenRouter, DeepSeek, Groq, Mistral, LM Studio, and other OpenAI-compatible endpoints. Presets generate a contract without putting an API key in the file.

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

List the AI presets or generate a contract and example file:

```sh
env-contract --list-providers
env-contract --init openai-compatible --output .env.contract --example-output .env.example
```

With no explicit `--example-output`, `--init` writes `.env.example` alongside the contract when using the default output path.

Use `--force` to replace generated files. Required values are strict by default. CI templates can opt into `--allow-missing-required`; provided values are still type-checked. Secrets never accept contract defaults.

## CI output

```sh
env-contract .env.contract --env-file .env.example --no-process-env --format sarif > env-contract.sarif
```

Use `--strict-undocumented` when every variable in the dotenv file must be declared by the contract. The default keeps undeclared variables as warnings for compatibility with existing CI and local files.

The repository also ships a composite GitHub Action. It checks the contract without requiring secrets to be present in CI:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: HP-network/env-contract@v2
    with:
      env-file: .env.example
      allow-missing-required: 'true'
      format: sarif
      upload-sarif: 'true'
```

Use `--format json` for scripts and `--format markdown` for job summaries. Exit status is `0` when there are no errors and `1` when a contract or value is invalid.

## Development

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m env_contract .env.contract --env-file .env.example --no-process-env
```

## License

MIT
