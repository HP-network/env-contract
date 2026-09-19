# Contributing

## Development

Use Python 3.10 or newer. The project has no runtime dependencies.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
git diff --check
```

Keep provider presets free of real credentials. New presets should include a contract, a safe example, and a test that confirms no secret value is embedded.

## Pull requests

Keep changes focused, explain the behavior change, and include a regression test for parser or validation changes. Do not commit `.env` files, API keys, or generated build output.
