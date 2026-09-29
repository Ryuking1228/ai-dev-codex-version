---
title: Codex PostgreSQL starter verification
schema_version: 1
skill: app-start
---

# Verification record — 2026-09-22

Scope: a reusable starter extending AI Dev Loop, not a completed business product.

| Check | Result |
|---|---|
| Frontend TypeScript check and Vite production build | Passed with Node 24.19.0 |
| API unit and HTTP contract smoke tests | 7 passed with Python 3.12; in-memory Fake, not PostgreSQL |
| Generator, source-bound gate, credential-file and private-destination tests | 8 passed |
| Compose and both added workflow YAML files | Parsed successfully; this is not Docker execution |
| Generated app without Docker | `verify` failed as expected and `release-check` refused deployment |
| PostgreSQL integration test | Implemented, not executed here |
| Real browser end-to-end and responsive tests | Implemented, not executed here |
| Container build and localhost UI inspection | Not executed; Docker unavailable |
| CI | Added; no successful remote run claimed |
| Deployment | Not executed; provider, account and environment unspecified |

The API suite emits two dependency deprecation warnings from Starlette/httpx and AnyIO.
They did not fail the suite. The starter's test gate is narrower than AI Dev Loop's full quality gate.
Its API test is a smoke/behavior check, not complete verification against an independently authored OpenAPI contract.

## Test provenance

The initial starter and tests were authored together (`test-after`), without a per-unit
Red/Green/Refactor commit series. Do not report this work as compliant with the full AI Dev Loop TDD workflow.
Tests detected a credential-file creation error; the production build detected missing Vite CSS types.
Both were corrected. A further test reproduced an OpenAPI error-media mismatch before the fix.
No passing DB, browser, UI-inspection or deployment record was manufactured.

## Remaining execution

Run `python3 tools/new-app.py ../my-app --name my-app` on a Docker-capable machine, then
follow the generated README: start, inspect the real UI, verify, and release-check.
The root `Codex PostgreSQL starter` GitHub Actions workflow also generates and verifies the app.
Before a public deployment, choose the actual product requirements, access-control model and hosting environment.
