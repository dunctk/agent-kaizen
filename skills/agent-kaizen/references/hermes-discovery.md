# Hermes discovery and evidence retrieval

Agent Kaizen v0.1 is Hermes-first. Run discovery before making Kaizen recommendations unless the relevant Hermes scope is already known from the current run.

## Discovery contract

The discovery layer is **read-only**.

It may inspect:

- `HERMES_HOME` / the default Hermes root;
- named profile directories;
- `config.yaml` existence (do not echo secrets from `.env`);
- `state.db` existence and metadata;
- `logs/`;
- `cron/jobs.json`;
- `cron/output/`;
- non-secret filesystem metadata needed to identify what is active.

It must not edit cron jobs, start/stop gateways, connect services, rotate credentials, or modify session state merely to discover the estate.

## Current Hermes storage model

Treat each Hermes profile as a separate agent environment.

Typical layout:

```text
~/.hermes/
├── state.db
├── logs/
├── cron/
│   ├── jobs.json
│   └── output/<job-id>/...
└── profiles/
    ├── coder/
    │   ├── state.db
    │   ├── logs/
    │   └── cron/
    └── researcher/
        └── ...
```

Respect `HERMES_HOME`; do not assume every install lives under `~/.hermes`.

## Why search is split by evidence type

### Sessions: SQLite FTS

Hermes' canonical conversation history is SQLite and current versions maintain FTS5 indexes over message content. Query the database read-only and use the existing index.

Do **not** grep the SQLite file.

Fall back to a bounded `LIKE` query only when the FTS table is unavailable or incompatible.

### Logs: ripgrep

Operational log files are plain text. Use `rg --fixed-strings --ignore-case` when available.

Advantages:

- very fast on large files;
- streams matches rather than reading everything into model context;
- no index-building step;
- naturally works with rotated files.

Use a bounded Python line scanner when ripgrep is unavailable.

### Cron definitions

Parse `cron/jobs.json` rather than grepping it so the CLI can identify fields such as:

- job id/name;
- enabled/paused state;
- schedule;
- next/last run metadata;
- workdir;
- model/provider override;
- output directory.

Treat the file as read-only.

### Cron output

Cron job artifacts under `cron/output/` are plain text/Markdown. Search them with the same ripgrep-first strategy as logs.

## Context discipline

The purpose of search is to avoid putting huge histories in the model context.

Use this pattern:

```text
broad discovery
   ↓
cheap indexed/literal retrieval
   ↓
small relevant excerpts
   ↓
agent reasoning
   ↓
only then deeper inspection if justified
```

Do not dump an entire `agent.log`, `state.db`, or cron output tree into the prompt.

## CLI

```bash
agent-kaizen discover
agent-kaizen discover --json
agent-kaizen search "timeout"
agent-kaizen search "manual intervention" --source sessions
agent-kaizen search "delivery failed" --source logs
agent-kaizen search "daily brief" --source cron
agent-kaizen inspect
agent-kaizen inspect --days 30 --profile researcher --json
```

Use `--profile NAME` to narrow a fleet-wide scan.

### Inspect

`inspect` is a bounded, read-only aggregation pass over the discovered Hermes estate. It summarizes recent session activity, model/cost metadata, cron output artifacts, and heuristic evidence for failures, manual intervention, and approval/review boundaries.

The default lookback is 7 days.

Do not interpret a keyword hit as a confirmed incident. The summary exists to prioritize deeper evidence retrieval.

Do not treat cron output artifact counts as exact execution counts. Hermes may suppress delivery/output for a run.

## Future retrieval improvements

Only add heavier retrieval when evidence shows the current approach misses useful material.

Possible later layers:

1. structured error/event extraction beyond keyword heuristics;
2. exact cron-run correlation with session IDs and scheduler events;
3. per-job model/tool/cost attribution;
4. semantic reranking of FTS/ripgrep candidates;
5. compact local index of recurring failure/intervention patterns.

Do not begin with embeddings/vector infrastructure merely because it is available. Literal + FTS retrieval is cheaper, inspectable, and already sufficient for many Kaizen questions.
