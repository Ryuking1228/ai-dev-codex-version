# __APP_NAME__: Codex development contract

Stack: React + TypeScript, FastAPI, PostgreSQL. Ordinary PostgreSQL; no ScalarDB dependency.
This is a local starter with an example Items workflow, not a finished business product.

- Read docs/product.md before implementing. Clarify the app purpose and permissions there.
- Keep UI, API contract, SQL migrations and acceptance tests consistent.
- Implement small slices, test during development, then inspect localhost and run the full suite.
- Maintain source in frontend/src and backend/app. Use versioned, additive migrations; never silently reset data.
- `python3 appctl.py up` starts localhost:8000; `verify` runs build, backend tests and browser E2E.
- Do not weaken a failing test or count a skipped/empty test run as passed. Stop a fix loop after 3 unsuccessful rounds.
- After changes, earlier verification is stale. `release-check` enforces a source fingerprint.
- Before external deployment decide and implement the access model. The example has no end-user login.
- Deployment needs a real target, credentials and URL in app-workflow.json/environment. Do not invent these.
- GitHub must be private. Keep secrets, DB volumes and .app-state out of Git. Preserve LICENSE/NOTICE.
- Do not claim Docker tests passed when Docker is unavailable. Record the limitation.
