Analyze and change an existing application with the AI Dev Loop workflow.

Read [the Copilot repository instructions](../copilot-instructions.md) and then read and follow
[the canonical architecture entry point](../../skills/start/SKILL.md) in full. Do not run the Codex
model router. Use the active GitHub Copilot model.

Use the absolute application path, requested change, and completion conditions that I append to
this prompt. Inspect the application's own instructions, git state, architecture, tests, and runtime
before deciding the path. Reuse existing reports when they are current.

First produce the required investigation and design artifacts. If I explicitly ask for
implementation too, modify the real source tree in small test-first slices and run the relevant
quality gates. Preserve unrelated changes. Do not create tracker items, pull requests, deploy, or
merge unless I explicitly request those external actions.

Finish with the affected files, test evidence, remaining risks, and any decision still needed.
