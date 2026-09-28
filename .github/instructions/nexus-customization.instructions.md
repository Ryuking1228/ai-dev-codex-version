---
applyTo: "skills/**/SKILL.md,.github/skills/**/SKILL.md,.github/agents/*.agent.md,.github/prompts/*.prompt.md"
---

Keep `skills/**/SKILL.md` as the canonical workflow source. Copilot skills, agents, and prompts are
thin adapters: link to the canonical skill instead of copying its detailed steps.

When editing a canonical skill, preserve Claude Code fields and behavior, Codex routing guidance,
and GitHub Copilot compatibility. Runtime-specific instructions must be explicitly scoped; never
make one provider execute another provider's CLI.

Every adapter link must resolve from its own file location. Keep YAML frontmatter valid and retain
the human approval gates defined by the canonical workflow.
