# Nexus instructions for GitHub Copilot

This repository is a multi-runtime architecture toolkit. Treat the files under `skills/` as the
canonical workflows and keep Claude Code and Codex compatibility intact.

## Select and load a workflow

- For `/app:start`, read and follow `skills/app/start/SKILL.md` in full.
- For `/product:<name>`, read and follow `skills/product/<name>/SKILL.md` in full.
- For `/infra:<name>`, read and follow `skills/infra/<name>/SKILL.md` in full.
- For `/architect:<name>` and `/scalardb:<name>`, read and follow `skills/<name>/SKILL.md` in full.
- Resolve `@rules/...`, `@templates/...`, `@docs/...`, and `@skills/...` from the repository root.
- Treat `${CLAUDE_PLUGIN_ROOT}` as the repository root. Resolve legacy `.claude/docs/*` to
  `skills/common/references/*` and `.claude/rules/*` to `rules/*`.
- If a requested skill is missing, say so and use the nearest documented workflow only after
  explaining the substitution.

Read the selected `SKILL.md` and every rule or reference it says is required before acting. Do not
load the entire corpus when one workflow is sufficient.

## Copilot runtime behavior

- The `model: haiku|sonnet|opus` field in a canonical skill describes task complexity. It is not a
  GitHub Copilot model identifier. Use the model selected by the user or inherited by the active
  custom agent.
- `tools/codex-model-router.py` and Luna/Terra/Sol mappings are Codex-only. Never invoke
  `codex exec` from GitHub Copilot. Preserve those files when editing shared workflows.
- Translate `Read`, `Glob`, `Grep`, and `LS` to repository read/search tools; `Write`, `Edit`, and
  `MultiEdit` to file edits; `Bash` to shell execution; and `AskUserQuestion` to a concise question
  in chat. Use subagents only when the active Copilot environment supports them and the work is
  genuinely independent.
- A skill's `user_invocable` or `disable-model-invocation` field is compatibility metadata. Follow
  the workflow's explicit invocation and approval gates.

## Working rules

- Preserve unrelated changes. Do not remove `.claude-plugin/`, `CLAUDE.md`, `AGENTS.md`, or
  provider-specific frontmatter.
- For an existing application, inspect its own instructions, build files, tests, and current git
  state before proposing or making changes.
- Put reports in `reports/`, generated code in `generated/`, and pipeline state in `work/`, unless
  the selected skill defines a maintained project location such as `/app:start`.
- Ask before destructive operations, deployment, publishing, merge, or any external write not
  already authorized by the user. Never expose credentials or commit secret files.
- Validate changes with the narrowest relevant tests first, then the broader repository checks.
  Report commands, results, skipped checks, and remaining risks accurately.
- After editing report Markdown or Mermaid, run `hooks/validate-frontmatter.sh <file>` and
  `hooks/validate-mermaid.sh <file>` as applicable.
- Before pinning dependency versions, follow `rules/dependency-versions.md` and verify current
  stable versions from authoritative registries.

For the shortest usage guide, read `docs/github-copilot-usage_ja.md`.
