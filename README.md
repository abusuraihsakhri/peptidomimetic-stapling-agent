# Peptidomimetic Stapling Agent

Small Python and browser tools for **sequence-position enumeration** and a separate **generic deterministic audit**. The position screen lists all residue pairs separated by four or seven positions (i,i+4 and i,i+7). Pairs containing proline in the span are flagged for review.

**Scientific scope:** This is a position-indexing aid, **not** a validated stapled-peptide stability, helical-propensity, cellular uptake, binding, toxicity, or chemical-feasibility predictor. It does not model linker geometry, noncanonical amino acids, hydrocarbon-staple stereochemistry, molecular dynamics, or experimental outcomes. Generic audit thresholds in the legacy components have no established peptide-specific meaning.

## Browser application

Open `web/index.html` in a modern browser or serve `web/` as a static directory. Sequence enumeration and threshold auditing both work offline, without a backend or a Python interpreter. No inputs are sent to a server by the browser application. JSON output can be downloaded locally.

GitHub Pages deployment is provided by `.github/workflows/pages.yml`; a production URL should only be announced after the deployed site has been verified.

## Python usage

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[api,test]"
python cli.py design --sequence AEAAKAAAEAAKAA --spacing both
python cli.py audit --task-id TASK-01 --target PEPTIDE-01 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
python -m pytest -q
```

The packaged `peptidomimetic-stapling-engine` command and `python peptido_staple_app.py` retain the older coordinator/CLI. Both CLI variants support `design` and `batch`.

### Position enumeration

`peptido_staple.staples.enumerate_staple_sites(sequence, spacings=(4, 7))` accepts 1–500 canonical amino-acid residues (one-letter codes). It emits **one-based** position pairs, native residue labels and a proline-in-span flag. It does not endorse substitution of any given residue or predict whether a staple will form.

### Generic audit API

The Python API is available at `http://127.0.0.1:8000` with `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`; interactive API documentation is at `/docs`. The root `cli.py` API is distinct from the older `peptido_staple.server` implementation.

Example JSON request to `POST /api/audit`:

```json
{"task_id":"TASK-01","target_identifier":"PEPTIDE-01","primary_metric":28.5,"secondary_metric":14.2,"status_descriptor":"NOMINAL","is_critical_flag":false}
```

Legacy rules use primary metric >25, secondary metric >12, a critical flag, and a list of descriptor keywords. `GET /metrics` returns JSON counters, **not** a Prometheus exposition document. The chat endpoint uses a deterministic mock adapter; it does not execute remote or local language models.

## Security and privacy

The Python API scans input fields (including nested attributes) for a limited set of sensitive identifier patterns and rejects matches. Pattern checks are not comprehensive de-identification or a guarantee of HIPAA compliance. Do not submit patient data. The API's in-memory audit log chains HMAC-SHA256 signatures and verifies them; records are **not durable across restarts**.

For a Docker deployment, supply a strong signing secret through the environment (never commit the secret):

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
```

The development-only fallback is generated randomly at process start. The API has no authentication; do not expose it publicly without access controls, TLS, resource limits and persistent audit storage. CSV batch paths are user-supplied local filesystem paths, not sandboxed paths.

## Development and checks

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
node --check web/app.js
node --test web/app.test.js
python -m compileall -q agents peptido_staple
```

CI runs Python tests on 3.10, 3.11 and 3.12 and tests the browser calculation logic using Node.js. The browser app uses standards-based HTML, CSS and JavaScript without external runtime dependencies, for current Chromium, Firefox and Safari versions.

## Technology and license

Python, Pydantic v2, optional FastAPI/Uvicorn, pytest, vanilla JavaScript, Node.js tests, Docker and GitHub Actions. Licensed under [MIT](LICENSE).
