# Agent Kaizen

> **v0.1 scope: Hermes Agent.**
>
> Agent Kaizen is starting deliberately narrow. The first target is a Hermes installation: discover the Hermes agents/profiles on a machine, find the scheduled agents/jobs, locate their session history and operational logs, then use that evidence to identify the next useful improvement.

Agent Kaizen is a continuous-improvement loop for **Hermes agents**:

> discover → observe → find friction / AI whitespace → investigate → improve → measure → ratchet

The broader framework may support other agent runtimes later. For now, **Hermes is the product surface and the word we use in the docs and CLI.**

## First capability: discovery

Before Agent Kaizen recommends anything, it should know what is actually running.

The CLI discovers:

- the default Hermes home;
- named Hermes profiles (each is an isolated Hermes agent environment);
- every profile's `state.db` session store;
- Hermes log files;
- cron definitions in each profile;
- which cron jobs are active/paused/completed;
- schedules, next-run metadata, workdirs and model/provider overrides when present;
- stored cron-run output.

```bash
agent-kaizen discover
```

Example shape:

```text
Hermes root: /home/me/.hermes
Profiles found: 3

[default] /home/me/.hermes
  sessions: /home/me/.hermes/state.db (412.7MB)
  logs:     4 file(s)
  cron:     5 job(s), 4 active, 3 recurring
    ● 7c1...  every 1h  scheduled  Research monitor

[coder] /home/me/.hermes/profiles/coder
  ...
```

Machine-readable discovery is available for agents:

```bash
agent-kaizen discover --json
agent-kaizen discover --profile coder --json
```

`HERMES_HOME` is respected. You can also point discovery somewhere explicitly:

```bash
agent-kaizen --hermes-home /srv/hermes discover
```

## Evidence search

Discovery is only useful if the Kaizen agent can cheaply retrieve relevant evidence rather than pouring entire log files or databases into a model context.

```bash
agent-kaizen search "manual intervention"
agent-kaizen search "timeout" --profile coder
agent-kaizen search "rate limit" --source logs
agent-kaizen search "research monitor" --source cron
agent-kaizen search "customer handoff" --source sessions --json
```

The initial search strategy is intentionally simple and local:

| Evidence | Search path |
| --- | --- |
| Hermes conversations | SQLite FTS5 in `state.db` |
| Operational logs | `rg` / ripgrep when installed; Python literal-search fallback |
| Cron definitions | parsed `cron/jobs.json` |
| Cron run artifacts | `rg` over `cron/output/`; Python fallback |

This is preferable to feeding large logs to an LLM. **Retrieve first, reason second.** Semantic reranking can be added later when literal/full-text retrieval is insufficient.

## Inspect recent Hermes activity

`inspect` turns discovery + retrieval into a compact Kaizen evidence report.

```bash
agent-kaizen inspect
agent-kaizen inspect --days 1
agent-kaizen inspect --days 30 --profile researcher
agent-kaizen inspect --json
```

By default it reviews the last 7 days and reports, per Hermes profile:

- total recent sessions and how many have `source='cron'`;
- message/tool/API-call counts when the Hermes schema exposes them;
- estimated/actual session cost when available;
- models used;
- recent cron **output artifacts** per configured job;
- failure/error/retry signal counts;
- manual-intervention/workaround signal counts;
- approval/review signal counts;
- a small evidence sample;
- cron jobs worth inspecting first because their recent output contains repeated failure or intervention signals.

The signal counts are **retrieval heuristics, not verdicts**. A line containing "retry" is evidence to inspect, not proof that the workflow is broken.

Cron output artifacts are also not presented as an exact execution counter. Hermes can suppress delivery/output, so exact run accounting will require scheduler/session correlation in a later iteration.

Example shape:

```text
Hermes inspection: last 7 day(s)

[researcher]
  sessions: 84 total, 61 cron | messages=912 tools=231 api_calls=144 cost~$3.8400
  session signals: failure=14 manual=6 approval=3
  log signals:     failure=8 manual=0 approval=0
  cron:
    ! market-watch  Market watch | every 1h | scheduled | outputs=121 failure=9 manual=2 approval=0
    - daily-brief   Daily brief  | every 1d | scheduled | outputs=7 failure=0 manual=0 approval=1
  attention:
    - Market watch (market-watch): 9 failure signal line(s); 2 manual-intervention signal line(s)
```

## CLI installation

The CLI has no runtime dependencies beyond Python 3.10+.

From a clone:

```bash
PYTHONPATH=src python3 -m agent_kaizen.cli discover
```

Or install it as a Python tool:

```bash
uv tool install git+https://github.com/dunctk/agent-kaizen
agent-kaizen discover
```

The Agent Skill remains installable separately:

```bash
npx skills add dunctk/agent-kaizen
```

## What happens after discovery?

The discovery/search/inspect layer gives the Kaizen pass evidence to ask:

- Which Hermes agents are actually active?
- Which scheduled jobs run repeatedly?
- What fails or retries repeatedly?
- Where does the user step in manually?
- What is expensive or slow?
- What does Hermes repeatedly have to rediscover?
- Where is useful work happening with no AI support?
- Is the next improvement a prompt change, skill, cron change, workflow, test, or software change?

The important constraint is that **observation is read-only**. Discovery must not add connectors, expand permissions, change schedules, spend money, or modify production state.

## Relationship to Workflow Kaizen

[Workflow Kaizen](https://github.com/dunctk/workflow-kaizen) is downstream.

```text
Agent Kaizen
  discover Hermes + inspect evidence
        ↓
  identify the next improvement
        ↓
  prototype / implement / run
        ↓
Workflow Kaizen
  reconcile manual rescue + failures
  into durable code/tests/state/docs
```

Agent Kaizen asks:

> **What should this Hermes setup improve next?**

Workflow Kaizen asks:

> **What did this real execution teach the workflow that it should know permanently?**

## Security posture

Discovery and evidence search are read-only. Agent Kaizen is default-deny about new authority: no new credentials, connectors, write scopes, production mutations, publishing, spend, or destructive actions merely to investigate an opportunity.

See [SECURITY.md](SECURITY.md) and [`skills/agent-kaizen/references/safety.md`](skills/agent-kaizen/references/safety.md).

## Repository layout

```text
agent-kaizen/
├── pyproject.toml
├── src/agent_kaizen/
│   ├── cli.py
│   ├── hermes.py
│   ├── inspect.py
│   └── search.py
├── tests/
│   └── test_discovery.py
├── skills/agent-kaizen/
│   ├── SKILL.md
│   └── references/
│       ├── hermes-discovery.md
│       ├── hermes-daily.md
│       ├── framework.md
│       └── safety.md
├── README.md
├── SECURITY.md
└── LICENSE
```

## License

MIT
