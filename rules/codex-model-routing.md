# Codex Model Routing

This rule applies only when AI Dev Loop skills run under Codex. Claude Code continues to use each
skill's native `model:` assignment.

## Why routing starts a child run

A Codex turn keeps the model and reasoning effort with which it started. An orchestrator cannot
replace its own model midway through the turn, so AI Dev Loop applies a child-run boundary whenever one
skill invokes another. `tools/codex-model-router.py` resolves the child skill's AI Dev Loop tier and
starts `codex exec` with the mapped model and reasoning effort.

## Required invocation

From an AI Dev Loop orchestrator, invoke every child AI Dev Loop skill with:

```bash
python3 <AI_DEV_LOOP_ROOT>/tools/codex-model-router.py run <plugin>:<skill> \
  --target <TARGET_ROOT> -- <skill arguments>
```

- `<AI_DEV_LOOP_ROOT>` is the repository containing this rule and the router.
- `<TARGET_ROOT>` is the project being analyzed, designed, or changed.
- Put router options before `--` and child-skill arguments after it.
- Do not route the current skill back into itself. A child that is itself an orchestrator routes
  only its own child skills.
- A directly invoked leaf skill may run in the current Codex turn; automatic assignment takes
  effect at the next child-run boundary.
- Never silently fall back to the orchestrator's model when a routed child fails to start. Report
  the failed route and stop or follow the parent skill's declared error handling.

Use `resolve` or `--dry-run` when the route must be inspected without spending a child run:

```bash
python3 <AI_DEV_LOOP_ROOT>/tools/codex-model-router.py resolve architect:design-api --target <TARGET_ROOT>
python3 <AI_DEV_LOOP_ROOT>/tools/codex-model-router.py run architect:design-api --target <TARGET_ROOT> --dry-run -- --auto
```

## Tier source

The router resolves the abstract tier in this order:

1. `skills/common/skill-dependencies.yaml` for architect pipeline skills, or
   `skills/product/common/skill-dependencies.yaml` for product pipeline skills
2. The skill's `SKILL.md` frontmatter `model:` field
3. `default_tier` in `config/codex-model-routing.json`

An unknown skill is an error. The router does not invent a path or silently route a misspelled
skill at the default tier.

## Cost profiles

`config/codex-model-routing.json` maps the abstract `haiku`, `sonnet`, and `opus` tiers to Codex
models and reasoning effort. The profile is selected in this order:

1. Router `--profile`
2. `AI_DEV_LOOP_CODEX_COST_PROFILE`
3. `work/pipeline-progress.json` → `options.codex_cost_profile`
4. The configuration's `default_profile`

The built-in default is `balanced`: Haiku maps to Luna/low, Sonnet to Terra/medium, and Opus to
Sol/xhigh. `economy` compresses routine and architecture work onto lower-cost models, while
`quality` also promotes the lower tiers. Keep the abstract tiers in skill manifests; change
provider-specific choices in the routing configuration rather than duplicating Codex model names
throughout skills.

## Safety and observability

The router launches Codex with an argument array, never through a shell. Before execution it prints
the selected skill, tier, profile, model, reasoning effort, and a redacted command to stderr. The
child prompt identifies the exact `SKILL.md`, AI Dev Loop root, and target root so the child does not need
to rediscover or guess them.
