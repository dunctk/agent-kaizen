# Hermes-style recurring Agent Kaizen

This pattern is for a persistent general-purpose agent that sees enough of day-to-day work to perform regular continuous improvement.

Do **not** interpret persistence as blanket authority.


Before the review, use the Hermes discovery layer to identify profiles, scheduled jobs and evidence stores:

```bash
agent-kaizen discover --json
```

Then use targeted `agent-kaizen search` queries rather than loading complete session databases or log trees into context.

## Daily scan

Run after a meaningful work period, not continuously after every tiny interaction.

### Questions

1. What meaningful work happened?
2. Where did the human spend attention?
3. Where did an agent spend substantial effort?
4. What was repeated?
5. What needed correction or rescue?
6. What required waiting or approval?
7. **Where was useful work done with no AI involvement?**
8. What was unusually difficult, slow, expensive, or error-prone?
9. What information had to be rediscovered?
10. What could safely be practised or prototyped without new permissions?

### Output

Keep the daily output small:

- 0–3 candidate opportunities;
- one recommended experiment at most;
- any authority boundary made explicit;
- any obvious prompt → skill → workflow → software graduation.

If nothing is strong enough, say so.

## Weekly review

Aggregate the daily evidence.

Look for recurrence rather than novelty.

For each recurring candidate, decide:

- gather more evidence;
- investigate;
- prototype;
- seek approval for a specific trust boundary;
- run a constrained pilot;
- engineer automation;
- reject/defer.

Prefer one completed improvement over ten half-started experiments.

## Suggested recurring prompt

```text
Run Agent Kaizen over the work you observed since the last review.

Start from actual evidence, not generic AI ideas.

Specifically inspect:
- repeated human work;
- repeated agent work;
- manual corrections/interventions;
- work where no AI is currently used;
- difficult, expensive, slow, or error-prone steps;
- recurring research/rediscovery;
- approval/wait states;
- overly broad agent permissions;
- prompts that should become skills;
- skills/workflows that should become engineered software.

For the strongest opportunities, define the smallest safe experiment,
the success measure, the required authority, and the exact approval boundary.

You may investigate and prototype with already-authorized evidence,
public information, fixtures, mocks, synthetic data, and sandboxes.

Do not connect new systems, expand permissions, spend money, publish,
send, delete, deploy, or make production changes merely to investigate.

Prefer 0–3 strong opportunities over a long wishlist.
```

## Handoff to Workflow Kaizen

When a candidate becomes real software/workflow and execution exposes:

- manual rescue;
- missing recovery logic;
- missing validation;
- repeated rediscovery;
- bad state handling;
- duplicate side effects;
- brittle provider behaviour;

run `workflow-kaizen`.

Agent Kaizen asks:

> What should we improve next?

Workflow Kaizen asks:

> What did this real execution teach us that the workflow should now know permanently?
