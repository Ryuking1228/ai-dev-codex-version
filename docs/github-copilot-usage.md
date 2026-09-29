# Using AI Dev Loop with GitHub Copilot

GitHub Copilot can use the canonical AI Dev Loop workflows without installing the Claude Code plugins or
the Codex CLI. The repository ships four Copilot customization layers:

| Layer | Location | Purpose |
|---|---|---|
| Repository instructions | `.github/copilot-instructions.md` | Always-on command mapping and safety rules |
| Custom agents | `.github/agents/*.agent.md` | Product, architecture, app-building, and delivery specialists |
| Prompt files | `.github/prompts/*.prompt.md` | Short reusable entry points in supported IDEs |
| Agent skills | `.github/skills/*/SKILL.md` | Automatic discovery adapters to canonical `skills/` workflows |

The adapters stay intentionally small. The detailed workflow remains in `skills/**/SKILL.md`, so
Claude Code, Codex, and Copilot do not drift into separate implementations.

## Setup

```bash
git clone --recurse-submodules https://github.com/Ryuking1228/ai-dev-codex-version.git
cd ai-dev-codex-version
```

Open the repository in an environment with GitHub Copilot enabled. Repository instructions are
automatic when that environment supports them. In VS Code, Visual Studio, or JetBrains IDEs,
prompt files can be invoked by typing `/` followed by the file name. Custom agents can be selected
from the agent picker in supported IDEs, GitHub Copilot cloud agent, or Copilot CLI.

## New application

Select the `ai-dev-loop-app-builder` custom agent, or run `/ai-dev-loop-new-app` and append:

```text
Target: /absolute/path/to/new-app
Name: new-app
Purpose: the problem to solve
Users: the primary users
Main workflow: the most important end-to-end action
Features:
- feature 1
- feature 2
References: /absolute/path/to/docs, or none

Run locally, inspect the UI, and complete automated verification.
```

The workflow does not overwrite an existing application. Deployment and GitHub publication remain
separate actions and require an explicit request.

## Existing application

Select the `ai-dev-loop-architect` agent, or run `/ai-dev-loop-existing-app` and append:

```text
Target: /absolute/path/to/existing-app
Change: the feature or refactoring to design
Completion conditions:
- condition 1
- condition 2
Output language: Japanese
```

This starts with investigation and design. If implementation is also wanted, say so in the same
request. For an already approved AI Dev Loop backlog, select `ai-dev-loop-delivery` or run
`/ai-dev-loop-deliver-backlog`; that route preserves pull-request approval and merge gates.

## Product direction

Select `ai-dev-loop-product` or run `/ai-dev-loop-product-design` for product vision, scope, journeys, features,
domain mapping, and quality requirements. Its artifacts feed the architecture workflow without
asking the same questions again.

## Models and cost

The `haiku`, `sonnet`, and `opus` values in canonical AI Dev Loop skills are provider-neutral complexity
tiers. Copilot custom agents inherit the model selected in the current Copilot environment. The
Luna/Terra/Sol automatic router is for Codex only and is never launched by Copilot.

To lower Copilot cost, choose a lower-cost model in Copilot for routine work and a stronger model
for architecture or risk review. Model availability and billing depend on the user's Copilot plan
and environment.

## Compatibility notes

- Repository instructions have the broadest support. Prompt files and some custom-agent surfaces
  may be preview features or differ by IDE.
- Copilot skills under `.github/skills/` are discovery adapters. Edit the canonical workflow under
  `skills/`, then update an adapter only if its trigger or link changes.
- Do not copy Codex commands such as `tools/codex-model-router.py run` into a Copilot workflow.
- Preserve `.claude-plugin/`, `CLAUDE.md`, and `AGENTS.md`; they keep the other runtimes working.

See GitHub's documentation for [repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide),
[custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration), and
[agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).
