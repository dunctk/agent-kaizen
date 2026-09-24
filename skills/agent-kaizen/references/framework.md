# Agent Kaizen framework

Use this reference when the lightweight skill procedure needs more structure.

## The three lenses

Every review should deliberately use all three.

### 1. AI opportunity lens

Ask:

- Where is AI already helping?
- Where is it only drafting but not checking, reconciling, or acting?
- Where is **nothing being done by AI**?
- Where are people copying, searching, summarising, comparing, checking, routing, or remembering?
- Where is a person repeatedly turning unstructured information into a structured decision?
- Where does an agent repeatedly rediscover the same context?

### 2. Work difficulty lens

Ask what makes the task hard.

Common difficulty sources:

- missing/fragmented inputs;
- tacit knowledge;
- ambiguous success;
- many exceptions;
- long horizons;
- state spread across systems;
- hard-to-reproduce failures;
- expensive external calls;
- slow feedback;
- weak observability;
- irreversible side effects.

Difficulty matters because the right first step may be **instrumentation or process simplification**, not a stronger model.

### 3. Safety/authority lens

Ask:

- What can be learned with no new access?
- What can be learned read-only?
- What can be simulated?
- What can be tested in a sandbox?
- What action actually creates consequence?
- Where should the approval gate sit?
- Can the write capability be narrowed by resource/action?
- Can the action be made reversible?
- How would we stop the agent?

## Value × tractability × consequence

Do not collapse these into one magic score.

Instead compare candidates across three independent dimensions.

### Value

High when the work is frequent, costly, slow, error-prone, quality-limiting, or absorbs scarce human judgment.

### Tractability

High when inputs are available, success is verifiable, examples exist, edge cases are bounded, and external dependencies are manageable.

### Consequence

High when errors affect money, customers, public outputs, permissions, security, production systems, safety, legal obligations, or sensitive data.

Useful patterns:

- **high value + high tractability + low consequence** → prototype quickly;
- **high value + high tractability + high consequence** → prototype early, activate cautiously;
- **high value + low tractability** → investigate, instrument, or simplify first;
- **low value + high consequence** → usually reject/defer.

## Approval as a graph edge

Do not model approval as a project-wide state.

Model the workflow as transitions:

```text
state A --action--> state B
```

Then ask whether that **specific transition** requires approval.

Example:

```text
read public docs                 no approval
analyse authorized inbox         existing authority
draft reply                      no external effect
preview reply                    no external effect
send reply                       approval or explicit send policy
delete thread                    stronger approval boundary
change mailbox permissions       security boundary
```

This permits learning and engineering to continue while consequential transitions remain gated.

## AI practice before automation

For judgment-heavy tasks, deliberately practise before automating.

Collect representative examples and ask the agent to:

1. predict the human action;
2. explain the evidence used;
3. identify uncertainty;
4. compare against the actual outcome;
5. categorise mistakes;
6. update the decision procedure;
7. repeat.

The goal is to expose hidden judgment and failure modes before granting authority.

## Engineering maturity

### Stage A — conversational

Prompted ad hoc. Useful for discovery.

### Stage B — reusable instruction

Prompt/template/skill with stable procedure.

### Stage C — workflow

Multiple steps, tools, state transitions, explicit success criteria.

### Stage D — engineered automation

Tests/evals, schemas, state, retries, idempotency, observability, bounded external effects.

### Stage E — operational system

Monitoring, policy, incident/recovery path, kill switch, ownership, auditability, change control.

Not every task should reach Stage E.

## Graduation evidence

Before increasing autonomy, seek evidence that:

- representative examples have been tested;
- success can be measured;
- failures are detectable;
- permissions are narrow;
- retries do not duplicate side effects;
- common exceptions are handled;
- a human escalation path exists;
- cost/latency are acceptable;
- the next autonomy level materially reduces work.

## Stop conditions

Reject or defer when:

- the task is too rare to justify system cost;
- the human work is already cheap and reliable;
- inputs are inaccessible or inappropriate to use;
- success cannot be verified;
- consequence is high and failure remains hard to detect;
- automation would require unjustifiably broad authority;
- an upstream process fix removes the need;
- the agent creates more review burden than it removes.

A good kaizen system improves by **not automating weak opportunities** as well as by automating strong ones.
