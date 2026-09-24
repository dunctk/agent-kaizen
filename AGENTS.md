# AGENTS.md

## Purpose

This repository defines **Agent Kaizen**: a reusable framework/skill for continuously finding, investigating, safely prototyping, and graduating worthwhile AI opportunities from observed work.

## Non-negotiable rules

- Keep the core framework model/provider/runtime agnostic.
- Start from evidence of real work; do not turn the skill into a generic automation brainstormer.
- Default-deny new capabilities. Do not grant connectors, credentials, scopes, write access, spend, publishing, destructive operations, or production activation merely to explore an opportunity.
- Investigation may proceed with existing authorized evidence, public information, mocks, fixtures, synthetic data, or sandboxes.
- Put approval gates at trust boundaries, not in front of harmless analysis/prototyping.
- Never add real secrets, credentials, cookies, sensitive personal data, or private production payloads to examples/tests/docs.
- Prefer measurable, reversible, bounded automation.
- Keep a clear handoff to `workflow-kaizen` for post-execution software/workflow reconciliation.

## Canonical files

- `skills/agent-kaizen/SKILL.md` — executable skill instructions.
- `skills/agent-kaizen/references/framework.md` — detailed opportunity and graduation framework.
- `skills/agent-kaizen/references/safety.md` — permission, approval, and agent-safety rules.
- `skills/agent-kaizen/references/hermes-daily.md` — recurring Hermes-style usage.
- `SECURITY.md` — repository and runtime security posture.

When changing the framework, update the canonical skill/reference first, then keep README examples aligned.

## Verification

Run:

```bash
bash scripts/check-secrets.sh
```

Also inspect documentation links and ensure the skill remains installable from `skills/agent-kaizen/`.
