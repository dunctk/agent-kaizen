---
name: agent-kaizen
description: Continuously inspect real human + agent work to find the next useful AI opportunity, investigate and prototype it safely, define approval and permission boundaries, then graduate successful patterns from suggestion to reliable automation without expanding agent authority by default.
license: MIT
---

# Agent Kaizen

## Scope: Hermes first

Agent Kaizen v0.1 targets **Hermes Agent**. Treat each Hermes profile as an isolated agent environment with its own session history, logs, skills and cron store.

Before a Kaizen review, discover the Hermes estate unless the relevant profile is already known:

```bash
agent-kaizen discover --json
```

Retrieve only the evidence needed for the question:

```bash
agent-kaizen search "manual intervention"
agent-kaizen search "timeout" --profile coder
agent-kaizen search "delivery failed" --source logs
```

Use `references/hermes-discovery.md` for the discovery/storage/search contract. Do not add support for other agent runtimes yet.

Improve how work is allocated between humans, agents, and software.

Do not begin with:

> What could AI automate?

Begin with:

> What actually happened, where did attention go, what was difficult, and where is AI absent or underused?

The goal is not maximum automation. The goal is to make the **next justified improvement** in capability while preserving human judgment at the right boundaries.

## Core loop

```text
OBSERVE
  ↓
MAP
  ↓
FIND AI WHITESPACE
  ↓
ASSESS
  ↓
INVESTIGATE / PRACTISE
  ↓
PROTOTYPE SAFELY
  ↓
SET APPROVAL + PERMISSION BOUNDARIES
  ↓
GRADUATE
  ↓
MEASURE
  ↓
RATCHET
  ↺
```

Read the detailed framework in `references/framework.md` when applying the skill beyond a lightweight daily scan.

Read `references/safety.md` before proposing write access, external side effects, sensitive data access, spend, publishing, destructive actions, security changes, or production autonomy.

For recurring Hermes-style use, read `references/hermes-daily.md`.

## Operating principle

Separate four questions that are often wrongly collapsed into one:

1. **Could AI help?**
2. **Can we prove it helps?**
3. **Can we engineer it reliably?**
4. **What authority should it have?**

A "yes" to the first does not imply a "yes" to the fourth.

## 1. Observe the real work

Use available evidence from the period being reviewed.

Depending on context, that may include:

- tasks completed;
- human corrections;
- agent conversations;
- manual interventions;
- repeated searches or investigations;
- handoffs;
- waiting/approval points;
- code or workflow changes;
- failures and retries;
- expensive model/tool usage;
- repeated copy/paste;
- spreadsheet or admin work;
- external communication;
- places where a person had to remember what to do next.

Do not manufacture opportunities from generic trend knowledge when there is stronger evidence in the actual work.

## 2. Build a work map

For each meaningful activity, identify:

- **trigger** — what caused it to happen;
- **input** — information needed;
- **work** — transformation/decision/action;
- **judgment** — what required interpretation;
- **tool/system** — where it happened;
- **output** — artifact or state change;
- **verification** — how success was known;
- **side effect** — anything external, costly, destructive, or public;
- **frequency** — how often it recurs;
- **friction** — time, delay, cognitive effort, error, cost, or annoyance.

Do not require perfect process modelling. Capture enough to identify the next leverage point.

## 3. Find AI whitespace

Explicitly ask:

> Where is useful work happening today with **no AI involvement at all**?

Also look for:

- AI used only for drafting when it could validate or reconcile;
- humans moving data between systems;
- humans checking predictable conditions;
- repeated research;
- agents repeatedly rediscovering context;
- repeated approval preparation;
- manual QA that could be partly automated;
- failure recovery that depends on agent improvisation;
- an agent producing advice but not a reusable artifact;
- prompts that have become stable enough to become a skill;
- skills that have become stable enough to become a workflow;
- workflows that should become software.

Do not treat "AI is absent" as proof that AI belongs there.

## 4. Assess each candidate

Assess without false precision.

### Value

Consider:

- recurrence/frequency;
- human time recovered;
- delay removed;
- error/rework reduction;
- cost reduction;
- quality increase;
- improved observability;
- reduced rediscovery;
- whether it frees human attention for judgment that matters more.

### Difficulty

Consider:

- input availability and quality;
- output verifiability;
- ambiguity;
- integration complexity;
- long-running state;
- external dependencies;
- model/tool reliability;
- latency and cost;
- exception rate;
- need for domain judgment.

### Risk

Consider:

- sensitive/private data;
- external communication;
- financial actions/spend;
- destructive actions;
- security/permission changes;
- production state;
- legal/safety/reputational consequences;
- reversibility;
- blast radius;
- prompt-injection or untrusted-input exposure;
- whether failure is observable before harm occurs.

### Evidence quality

Classify the opportunity as:

- **OBSERVED** — repeated or clearly visible in actual work;
- **PLAUSIBLE** — reasonable but insufficiently evidenced;
- **SPECULATIVE** — mostly an idea.

Prioritise OBSERVED opportunities unless exploration is exceptionally cheap and safe.

## 5. Choose the next experiment

Prefer the smallest experiment that can answer:

> Does AI materially improve this work under realistic conditions?

Examples:

- shadow mode;
- suggestion-only;
- draft generation;
- offline replay against historical examples;
- synthetic fixture;
- read-only analysis;
- sandbox execution;
- side-by-side comparison;
- eval set;
- mocked connector;
- manual review of proposed actions.

Do not ask for production access merely to prove an idea.

## 6. Investigate and practise

Before automation, learn the task.

The agent may:

- reconstruct examples;
- study edge cases;
- compare models/tools;
- practise on fixtures;
- identify failure modes;
- define acceptance criteria;
- estimate cost/latency;
- determine what information a human uses implicitly;
- discover what makes an output obviously wrong;
- identify which decisions should remain human.

This stage may happen **before approval for production activation** as long as it stays inside already-authorized evidence, public information, synthetic data, mocks, fixtures, or an approved sandbox.

## 7. Set approval and permission boundaries

Approval is not one global yes/no gate.

Define it at the **consequence boundary**.

Typical pattern:

```text
analyse / research / draft / simulate
        ↓ usually no new approval
sandbox execution
        ↓ may require sandbox-specific approval
preview consequential action
        ↓
human approval
        ↓
external / production action
```

Require explicit approval before crossing relevant boundaries such as:

- accessing new privileged/sensitive data;
- adding a connector or credential;
- expanding OAuth/tool scope;
- switching from read to write;
- sending/publishing externally;
- spending money;
- deleting or destructively modifying state;
- changing security/permissions;
- deploying/activating in production;
- increasing autonomy beyond the approved policy.

Never treat "the user approved the project" as blanket authorization for unrelated capabilities.

## 8. Pick an autonomy level

Use the lowest level that captures most of the value.

- **L0 — Human/manual:** AI not used.
- **L1 — Suggest:** AI proposes; human performs.
- **L2 — Draft/sandbox:** AI creates or executes in a non-consequential environment; human reviews.
- **L3 — Approval-gated action:** AI prepares and performs only after explicit approval.
- **L4 — Guardrailed autonomy:** AI acts without per-action approval inside narrow, explicit constraints.
- **L5 — Monitored autonomous system:** AI owns a bounded workflow; humans set policy, monitor metrics, and handle exceptions.

Do not graduate because a model benchmark is impressive. Graduate because task-specific evidence supports it.

## 9. Apply the software-engineering graduation test

When a candidate is useful more than once, ask:

> Is this still a prompt, or has it become a system?

Prefer graduation in this direction when justified:

```text
ad hoc prompt
   ↓
reusable prompt/template
   ↓
skill
   ↓
workflow/orchestration
   ↓
typed/stateful software
   ↓
tested + observable + recoverable service
```

As automation matures, require more of:

- deterministic validation;
- tests/evals;
- typed or schema-validated inputs/outputs;
- explicit state;
- idempotency;
- resumability;
- bounded retries;
- rate/spend limits;
- structured logs;
- provenance/versioning;
- failure classification;
- human escalation;
- rollback/kill switch;
- security boundaries.

If implementation/debugging required meaningful manual rescue, run **Workflow Kaizen** to reconcile those lessons into the workflow.

## 10. Measure before graduating

Define at least one useful outcome measure and one failure measure.

Possible measures:

- human minutes saved;
- cycle time;
- accepted-without-edit rate;
- task success;
- false-positive/false-negative rate;
- manual interventions per run;
- exception rate;
- retry rate;
- cost per successful task;
- latency;
- user/customer quality signal;
- incidents or near misses.

Compare against the previous way of working where possible.

Do not graduate based only on "the demo worked."

## 11. Ratchet

After an experiment or real run, ask:

- What did we learn?
- What failed?
- What required manual intervention?
- What did the human notice that the agent did not?
- What authority was unnecessary?
- What validation was missing?
- Can the next run use less judgment or less privilege?
- Should this remain an experiment, become a reusable skill, become software, or be abandoned?

Prefer reversible progress.

## Opportunity status

Track candidates using one of:

- **OBSERVE** — collect evidence;
- **INVESTIGATE** — learn the task/problem;
- **PROTOTYPE** — build/test safely;
- **APPROVAL NEEDED** — blocked specifically on a trust boundary;
- **PILOT** — constrained real-world use;
- **AUTOMATE** — engineering for repeatable operation;
- **MONITOR** — running under defined guardrails;
- **REJECT** — not useful/safe/economic enough now.

Do not use "approval needed" when the agent could still make progress using analysis, fixtures, mocks, or sandbox work.

## Final output

Return a compact review with these headings.

### What happened

A short evidence-based description of the relevant work.

### AI whitespace

The strongest places where useful work currently has little or no AI support.

### Candidates

For each candidate:

```text
Candidate:
Evidence:
Current mode:
Potential next mode:
Value:
Difficulty:
Risk:
Smallest useful experiment:
Approval boundary:
Success measure:
Next step:
Status:
```

Prefer a small number of strong candidates over a long generic list.

### Safety / authority changes

State explicitly:

- no new authority needed; or
- exactly what new capability would be needed later, why, and at what boundary.

Do not silently broaden access.

### Engineering graduation

Call out anything that should move from:

- prompt → reusable template;
- template → skill;
- skill → workflow;
- workflow → software/service;
- brittle automation → tested/observable/recoverable system.

### Rejected / deferred

List ideas deliberately not pursued because evidence, value, tractability, safety, cost, or timing is insufficient.

## Completion test

A good Agent Kaizen pass should leave one or more of these outcomes:

- a better-understood workflow;
- a clearly evidenced AI opportunity;
- a safe experiment;
- a defined approval boundary;
- a smaller permission surface;
- a candidate moved one autonomy level;
- a prompt promoted into a durable artifact;
- an unreliable automation promoted into engineering work;
- a weak idea explicitly rejected.

It should **not** leave behind newly connected systems, broad credentials, production side effects, or irreversible actions that were unnecessary to learn.
