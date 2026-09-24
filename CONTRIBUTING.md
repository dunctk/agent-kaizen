# Contributing

Contributions that make Agent Kaizen more concrete, testable, safe, and useful across different agent systems are welcome.

## Good contributions

Useful changes include:

- clearer opportunity-discovery questions;
- better ways to distinguish assistance from automation;
- evidence-based prioritisation methods;
- safety and approval patterns;
- fixtures or examples for real workflows;
- measurement approaches;
- integrations that preserve least privilege;
- improvements to the skill's portability across agent runtimes.

## Design rules

Keep the framework:

1. **Evidence-first.** Start from observed work rather than generic AI brainstorming.
2. **Model-agnostic.** Do not assume one model/provider.
3. **Hermes-first for v0.1.** Keep the current implementation focused on Hermes Agent. Avoid runtime abstractions until a second runtime is actually being added.
4. **Safety-by-construction.** Do not solve convenience problems by granting broad persistent authority.
5. **Progressive.** Prefer the smallest useful autonomy increase.
6. **Measurable.** An automation should have a success/failure signal.
7. **Reversible where possible.** Prefer drafts, previews, sandboxes, idempotent actions, and rollback.
8. **Engineering-aware.** Repeated prompt work should be allowed to graduate into skills, workflows, tests, state, and software.

## Before opening a PR

- run `bash scripts/check-secrets.sh`;
- ensure examples contain no real credentials or private data;
- keep the install surface under `skills/agent-kaizen/`;
- avoid adding dependencies unless they materially improve the framework;
- explain any new permission or connector requirements.

## Relationship with Workflow Kaizen

Agent Kaizen discovers and governs candidate automation.

[Workflow Kaizen](https://github.com/dunctk/workflow-kaizen) reconciles lessons from real execution back into durable software/workflow improvements.

Avoid duplicating Workflow Kaizen's detailed post-execution repair logic here unless the overlap is necessary to make the handoff clear.
