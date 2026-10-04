---
description: Runs Cloudflare's pinned security-audit skill as the independent ninth and final AI code quality gate, with fresh-agent verification, machine-readable evidence, and strict verdict mapping.
---

# Independent Security Gate

This rule adapts the vendored Cloudflare `security-audit` skill to AI Dev Loop. The upstream skill
is stored unchanged at `.agents/skills/security-audit/`, pinned by commit and folder hash in
`skills-lock.json`, and attributed in `THIRD_PARTY_NOTICES.md`. Keep AI Dev Loop-specific policy in
this rule so an upstream refresh remains reviewable.

The gate is **independent**, not a second name for stage 7. Stage 7 checks the API security controls
AI Dev Loop expects. Stage 9 asks fresh agents to hunt for real trust-boundary violations, then gives
every surviving candidate to an agent that did not discover it.

## Invocation

`/architect:verify-implementation --gate` explicitly authorizes all required quality-gate stages,
including the upstream skill's full-audit mode. Run stage 9 only after stages 1–8 have no `failed`
status:

| Gate scope | Audit profile | Audit scope |
|------------|---------------|-------------|
| `changed` | `quick` | Changed production paths plus the authentication, authorization, parsing, persistence, configuration, and call-chain code needed to evaluate their boundaries |
| `service` | `standard` | The selected service and its in-repository deployment/configuration surface |
| `repo` | `standard` | The repository |

An explicitly requested deep or release audit uses `deep`. A narrow run must say it is partial; it
never claims repository-wide coverage.

Read `.agents/skills/security-audit/SKILL.md` in full and follow its setup, safety, write-isolation,
coverage-ledger, hunting, validation, and reporting contracts. Load only the companion attack-class
files reconnaissance selects. The gate adapter does not weaken the upstream evidence bar.

Use the upstream output-directory rules. Prefer a new directory outside the target. A directory
inside the target is allowed only when the entire directory is version-control ignored; record the
resolved path in the gate result. Never commit audit scratch data, test payloads, or target-derived
artifacts.

## Independence boundary

- The gate parent may coordinate and write shared run files, but it does not hunt or verify.
- A code-writing agent, stage-7 reviewer, or stage-8 conformance reviewer cannot be a stage-9 hunter
  or verifier for the same change.
- Every candidate goes to a fresh verifier that did not discover it. Final record verification
  follows the profile-specific upstream rule; a material replacement is independently verified
  again.
- If the runtime cannot provide the required isolated agents, write isolation, or sandbox controls,
  the run is `incomplete`; do not replace the audit with a same-agent prose review.

Target-controlled builds, tests, processes, browsers, fuzzers, and fixtures run only under the
upstream OS-enforced sandbox policy. When those controls are unavailable, keep the exact question as
`needs_validation`; do not execute the target on the host to make the gate green.

## Required evidence

The parent runs the vendored validators exactly as the upstream skill requires and records their
commands and exit codes:

```text
node .agents/skills/security-audit/validate-coverage-ledger.cjs <coverage-ledger.json>
node .agents/skills/security-audit/validate-findings.cjs <findings.json>
```

The `independent-security-audit` entry in `quality-gate.json` contains:

```json
{
  "stage": "independent-security-audit",
  "status": "passed",
  "provider": "cloudflare/security-audit-skill",
  "skill_ref": "<pinned commit from skills-lock.json>",
  "source_ref": "<same commit as the gate's top-level source_ref>",
  "profile": "quick",
  "scope_paths": ["src/order"],
  "run_status": "complete",
  "artifacts": {
    "run_metadata": "<path>/run-metadata.json",
    "coverage_ledger": "<path>/coverage-ledger.json",
    "findings": "<path>/findings.json",
    "report": "<path>/REPORT.md"
  },
  "validators": {
    "coverage_ledger": {"command": "node .../validate-coverage-ledger.cjs ...", "exit_code": 0},
    "findings": {"command": "node .../validate-findings.cjs ...", "exit_code": 0}
  },
  "findings": {
    "confirmed": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0},
    "needs_validation": 0,
    "rejected": 0,
    "unvalidated_candidates": 0
  }
}
```

`source_ref` is the reviewed target commit plus a dirty-worktree marker when applicable, matching
the upstream `run-metadata.json`. `scope_paths` is never empty. Artifact paths are absolute or
relative to the directory containing `quality-gate.json`, and point to actual retained files; a
prose summary without the validated JSON files is not evidence.

## Stage and gate verdicts

| Condition | Stage status | Gate consequence |
|-----------|--------------|------------------|
| Run complete; both validators exit 0; no confirmed finding above informational; no `needs_validation`; no unvalidated candidate | `passed` | No new consequence |
| Confirmed medium/low finding, or one or more `needs_validation` records; each has an owner and explicit decision/validation condition | `conditional` | Gate is `CONDITIONAL` pending those recorded conditions |
| Confirmed critical/high finding; invalid artifacts; incomplete run; unvalidated candidate; missing independence/sandbox control | `failed` | Gate is `FAIL` |
| A prior stage failed, so stage 9 did not start | `blocked`, reason `blocked-by-prior-stage` | Gate remains `FAIL`; run stage 9 after the earlier failure is fixed |
| The item ships no executable code | `skipped`, reason `not-applicable` | Allowed only when the other code-execution stages use the same reason |
| The user explicitly waived this stage | `skipped`, reason `skipped-by-user` | Gate is at most `CONDITIONAL`; record who waived it and why |

Rejected candidates do not block. `needs_validation` never receives a severity and never counts as a
pass. `not-configured` is not valid for stage 9 because the implementation is vendored; a missing
runtime capability makes the run `failed`/`incomplete` instead.

After writing `quality-gate.json`, run:

```text
python3 ${CLAUDE_PLUGIN_ROOT}/tools/validate-quality-gate.py \
  reports/09_verification/quality-gate.json
```

The command must exit 0 before a human review handoff. Record it in the Markdown summary alongside
the two upstream validator commands.
