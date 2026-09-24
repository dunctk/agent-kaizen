# Agent Kaizen

```bash
npx skills add dunctk/agent-kaizen
```

A continuous-improvement framework for finding the **next useful place for AI** in real work — without giving agents unlimited access or automating things before they are understood.

Agent Kaizen turns everyday human + agent activity into a repeatable loop:

> observe the work → find AI whitespace → investigate → prototype safely → decide approval boundaries → automate → measure → ratchet

It is designed for recurring use by general-purpose agents such as Hermes, Claude Code, Codex, Cursor, OpenCode, and other agent systems.

## Why this exists

Most teams ask:

> “What can we automate with AI?”

That question is too broad. Agent Kaizen starts from observed work instead:

- What happened today?
- What consumed human attention?
- Where was AI already useful?
- Where was **nothing being done by AI**?
- What was difficult, repetitive, slow, expensive, error-prone, or cognitively draining?
- Which parts required genuine human judgment?
- What could be investigated or prototyped without production access?
- What should require approval before an agent can act?
- What should become software rather than another prompt?

The goal is not maximum automation. The goal is **progressively better allocation of human judgment and machine capability**.

## The loop

```text
OBSERVE
  ↓
MAP THE WORK
  ↓
FIND AI WHITESPACE
  ↓
ASSESS VALUE + DIFFICULTY + RISK
  ↓
INVESTIGATE / PRACTISE
  ↓
PROTOTYPE SAFELY
  ↓
DEFINE APPROVAL + PERMISSION BOUNDARIES
  ↓
AUTOMATE THE RIGHT LAYER
  ↓
MEASURE
  ↓
RATCHET
  ↺
```

Investigation and sandbox prototyping do **not** need to wait for production approval. Approval is required before crossing defined trust boundaries such as privileged data access, external side effects, spend, publishing, destructive actions, or production activation.

## Two related projects

### Agent Kaizen

This repository is the broader discovery and governance loop. It asks **what should AI do next, at what level of autonomy, and under what safety boundary?**

### [Workflow Kaizen](https://github.com/dunctk/workflow-kaizen)

Workflow Kaizen starts after real execution/debugging and asks **what did we learn that should become durable code, tests, recovery logic, state, configuration, or agent documentation?**

A common flow is:

```text
Agent Kaizen
    ↓ identifies a worthwhile automation
prototype / implementation
    ↓
real-world execution
    ↓
Workflow Kaizen
    ↓ reconciles interventions and failures
more reliable automation
```

## Install

```bash
npx skills add dunctk/agent-kaizen
```

Or:

```bash
npx skills add dunctk/agent-kaizen --skill agent-kaizen
```

## Daily Hermes-style use

At the end of a day or after an agent stand-up:

```text
Run agent-kaizen over today's work.

Look for:
- repeated human effort;
- repeated agent effort;
- manual interventions;
- untouched AI opportunities;
- difficult or expensive steps;
- approval bottlenecks;
- unsafe or over-privileged automation;
- opportunities that should graduate from prompt → skill → workflow → software.

Do not connect new systems, request broader permissions, spend money,
publish externally, or make destructive changes merely to investigate.
```

The output should be a small number of evidence-backed opportunities, not an enormous AI wishlist.

## Autonomy ladder

Agent Kaizen uses a simple graduation model:

| Level | Mode | Human role |
| --- | --- | --- |
| 0 | Human/manual | Does the work |
| 1 | AI suggests | Reviews suggestion |
| 2 | AI drafts/executes in sandbox | Reviews result |
| 3 | AI acts with approval | Approves consequential action |
| 4 | AI acts inside explicit guardrails | Handles exceptions |
| 5 | Monitored autonomous system | Sets policy, audits outcomes |

Do not jump levels merely because a model can technically perform the task.

## Security posture

Agent Kaizen is **default-deny** about capabilities.

An agent should not gain a connector, credential, write scope, production environment, payment capability, or destructive tool simply because it would make an experiment easier.

Core rules:

- least privilege;
- explicit tool/connector allowlists;
- read-only before write access;
- sandbox/dry-run before production;
- separate investigation from activation;
- explicit spend/rate limits;
- reversible/idempotent actions where possible;
- auditability;
- no secrets in prompts, logs, fixtures, examples, or commits;
- human approval at defined consequence boundaries;
- a kill switch / disable path for autonomous systems.

See [SECURITY.md](SECURITY.md) and the skill's [safety reference](skills/agent-kaizen/references/safety.md).

## Repository layout

```text
agent-kaizen/
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── AGENTS.md
├── scripts/
│   └── check-secrets.sh
├── .github/
│   └── workflows/
│       └── security.yml
└── skills/
    └── agent-kaizen/
        ├── SKILL.md
        └── references/
            ├── framework.md
            ├── safety.md
            └── hermes-daily.md
```

## License

MIT
