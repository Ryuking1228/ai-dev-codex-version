---
name: app-start
description: Build a new full-stack app with Codex, React, FastAPI and PostgreSQL; implement features, run locally, verify with automated tests, prepare deployment and push to a private GitHub repository. Use for /app:start and requests to build a new app end to end using free PostgreSQL.
model: sonnet
---

# Codex full-stack app workflow

Read `docs/codex-postgres-app_ja.md` and the target project's `AGENTS.md`.
Use ordinary PostgreSQL directly, without ScalarDB, unless the user requests otherwise.
Retain the original AI Dev Loop product/architect workflows for complex design; this entry is a small-app path.

1. Establish the app's user, one primary workflow and acceptance examples. Reuse supplied answers.
   If no app purpose was supplied, create the development foundation only; label the Items CRUD as a demonstration.
2. Generate a new sibling project with `python3 tools/new-app.py <target> --name <slug>`.
   Never put maintained code in `generated/`. Never overwrite an existing project.
3. Write `docs/product.md`: purpose, actor, happy path, exceptions, acceptance examples, auth/access boundary.
   Use `product/example-map` for unclear business rules. Under Codex, invoke that child with
   `python3 <AI_DEV_LOOP_ROOT>/tools/codex-model-router.py run product:example-map --target
   <TARGET_ROOT> -- <skill arguments>` per `@rules/codex-model-routing.md`. Decide permissions
   before implementing sensitive data.
4. Extend `backend/app/`, `frontend/src/`, migrations and tests in small vertical slices.
   Update OpenAPI and acceptance examples with behavior changes. Run fast tests during implementation.
5. Run `python3 appctl.py up`. Inspect localhost:8000 in a real browser, follow acceptance examples,
   check errors/empty states/mobile layout and reload to verify database persistence.
   The user's localhost is not the execution container's localhost; explain where the process is running.
6. Run `python3 appctl.py verify` after local inspection. It builds and runs backend tests against an
   isolated PostgreSQL test database plus Playwright against the running app. Zero tests, missing tools,
   skipped stages and missing evidence are not passes. Inspect `.app-state/verification.json`.
7. On failures, fix and rerun; stop after three unsuccessful rounds or two rounds without progress.
   Record failed checks and decision options instead of weakening tests.
8. Prepare deployment only for the exact verified source. Run `python3 appctl.py release-check`.
   The template has no end-user authentication: treat it as a local scaffold. Before external deployment,
   implement the chosen authentication/access model or explicitly design a public app, and configure
   deployment command, environment, URL, credentials and backup/restore. Do not invent a hosting destination.
   `deploy` runs an explicitly configured command only after the verification gate, then checks health.
9. Use `python3 appctl.py push --repo owner/name` to push a clean committed project to an existing
   private repository. The helper checks owner/repo and visibility using `gh`; in a connector-only runtime
   use GitHub tools with equivalent checks. Create a private standalone repo, not a public fork.
   Preserve licenses. Never push `.env`, DB data, browser traces or credentials.

Report separately: implemented / locally observed / tests passed / deployed / pushed. A Dockerfile is
deployment preparation, not deployment. A GitHub push is source publication, not app deployment.
