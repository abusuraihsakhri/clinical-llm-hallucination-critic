# Clinical LLM Hallucination Critic

A deterministic rule-based prototype for testing the plumbing around a clinical-LLM critic workflow: structured inputs, rule evaluation, alert aggregation, CSV batch processing, a small FastAPI surface, and an HMAC-chained in-memory audit log.

> **Important:** this repository is a software prototype. It does **not** currently perform natural-language inference, EHR lookup, citation verification, biomedical literature retrieval, clinical validation, or automated de-identification. It is not intended for clinical decision-making.

## What it currently does

The canonical workflow in `agents/` evaluates three explicit rules: a primary metric above `25`, a secondary metric above `12` or a manual critical flag, and configured keywords in the status descriptor. The resulting alerts are aggregated into routine, elevated, or critical states. These thresholds are demonstration values, not clinical standards.

The project also provides:

- a CLI for single-case evaluation, CSV batch processing, audit-chain verification, and the optional API server;
- an in-memory HMAC-SHA256 audit chain with full signature verification;
- a heuristic sensitive-data pattern screen for common identifiers;
- a browser-only GitHub Pages interface that mirrors the deterministic rules without sending form data to a server;
- automated tests, linting, package build checks, and dependency auditing in GitHub Actions.

## Browser application

The static application is in `docs/` and is deployed by `.github/workflows/pages.yml`. It uses plain HTML, CSS, and JavaScript so the page loads quickly and does not require Pyodide. The browser implementation mirrors the same three deterministic rules as the Python workflow.

## CLI

Install the core package:

```bash
python -m pip install .
```

Run a single evaluation:

```bash
clinical-llm-hallucination-critic audit \
  --task-id TASK-001 \
  --target TARGET-01 \
  --primary 28.4 \
  --secondary 14.2 \
  --status DISCORDANT
```

Process the included sample CSV:

```bash
clinical-llm-hallucination-critic batch -i sample.csv -o results.csv
```

Verify the current in-memory audit chain:

```bash
clinical-llm-hallucination-critic verify-audit
```

## Optional API server

Install the server extra and start FastAPI locally:

```bash
python -m pip install ".[server]"
clinical-llm-hallucination-critic serve --host 127.0.0.1 --port 8000
```

Endpoints are `/health`, `/metrics`, `/api/audit`, `/api/chat`, and `/api/audit/logs`. The chat endpoint currently uses only the deterministic mock provider. Unsupported provider names fail explicitly rather than silently substituting a mock implementation.

## Privacy and security scope

`PHIGuard` blocks a small set of identifier-like regex patterns before selected processing and audit operations. This is a defensive convenience only; it is not a comprehensive PHI detector, de-identification method, HIPAA Safe Harbor implementation, or substitute for a validated privacy pipeline.

The audit logger uses HMAC-SHA256 and verifies every stored signature and chain link. If `AUDIT_SECRET_KEY` is unset, a random ephemeral key is generated for the process. Set `AUDIT_SECRET_KEY` when audit signatures must remain verifiable across restarts. The audit trail is in memory only and is not a durable compliance log.

## Development and verification

```bash
python -m pip install -e ".[server,dev]"
ruff check .
python -m compileall -q agents medfact_critic cli.py enrichment.py simulator.py
python -m pytest -p no:zarr -v
python -m build
python -m pip_audit
```

GitHub Actions runs the checks on Python 3.10, 3.11, and 3.12. `sample.csv` can be used for the CLI smoke test.

## Project structure

- `agents/` — canonical rule evaluation, privacy guard, audit chain, API, and mock model adapter.
- `cli.py` — canonical command-line interface.
- `medfact_critic/` — compatibility package retained for existing imports.
- `enrichment.py` — experimental threshold-based helper modules retained for compatibility.
- `docs/` — static GitHub Pages application.
- `tests/` — automated tests.

## Browser compatibility

The Pages UI targets current Chrome, Edge, Firefox, and Safari. It uses the Web Crypto API only to display a local SHA-256 fingerprint of the form input; that fingerprint is not the Python audit HMAC.

## License

MIT. See [LICENSE](LICENSE).
