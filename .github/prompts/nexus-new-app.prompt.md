Build a new application with the Nexus workflow.

Read [the Copilot repository instructions](../copilot-instructions.md) and then read and follow
[the canonical new-app skill](../../skills/app/start/SKILL.md) in full. Do not run the Codex model
router. Use the active GitHub Copilot model.

Use the details I append to this prompt as the product brief. At minimum, establish the absolute
target path, application name, purpose, primary user, primary workflow, required features, and any
reference documents. Ask one concise question only when a missing decision would materially change
the result.

Create the maintained application outside `generated/`, implement it in vertical slices, start it
locally, inspect the UI when browser tools are available, and run its complete verification command.
Do not overwrite an existing application and do not deploy or push unless I explicitly request it.

Finish with separate results for implemented functionality, local observation, tests, deployment,
and publication.
