from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .hermes import HermesProfile, CronJob


FAILURE_TERMS = (
    "error", "failed", "failure", "exception", "traceback", "timeout", "timed out",
    "rate limit", "retry", "retrying", "crash", "crashed", "429",
)
INTERVENTION_TERMS = (
    "manual", "manually", "manual intervention", "by hand", "workaround",
    "had to retry", "had to rerun", "had to re-run", "had to fix", "had to correct",
    "user corrected", "corrected by",
)
APPROVAL_TERMS = (
    "approval", "approved", "approve", "confirmation", "confirm before", "review before",
)


@dataclass
class Evidence:
    category: str
    source: str
    text: str
    path: str | None = None
    line: int | None = None
    session_id: str | None = None
    timestamp: float | None = None
    job_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CronActivity:
    job_id: str
    name: str
    schedule: str
    state: str
    enabled: bool
    output_artifacts: int = 0
    latest_output_at: float | None = None
    latest_artifact: str | None = None
    failure_signals: int = 0
    intervention_signals: int = 0
    approval_signals: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SessionSummary:
    sessions: int = 0
    cron_sessions: int = 0
    messages: int = 0
    tool_calls: int = 0
    api_calls: int = 0
    estimated_cost_usd: float = 0.0
    models: list[dict] = field(default_factory=list)
    failure_signals: int = 0
    intervention_signals: int = 0
    approval_signals: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProfileInspection:
    profile: str
    home: str
    sessions: SessionSummary
    cron: list[CronActivity]
    log_failure_signals: int = 0
    log_intervention_signals: int = 0
    log_approval_signals: int = 0
    evidence: list[Evidence] = field(default_factory=list)
    attention: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["sessions"] = self.sessions.to_dict()
        data["cron"] = [c.to_dict() for c in self.cron]
        data["evidence"] = [e.to_dict() for e in self.evidence]
        return data


@dataclass
class FleetInspection:
    generated_at: float
    since: float
    days: float
    profiles: list[ProfileInspection]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "since": self.since,
            "days": self.days,
            "profiles": [p.to_dict() for p in self.profiles],
        }


def inspect_profiles(
    profiles: Iterable["HermesProfile"],
    days: float = 7.0,
    evidence_limit: int = 8,
    now: float | None = None,
) -> FleetInspection:
    now = time.time() if now is None else now
    days = max(0.01, float(days))
    since = now - days * 86400.0
    inspected = [inspect_profile(p, since, evidence_limit) for p in profiles]
    return FleetInspection(generated_at=now, since=since, days=days, profiles=inspected)


def inspect_profile(profile: "HermesProfile", since: float, evidence_limit: int) -> ProfileInspection:
    evidence: list[Evidence] = []
    warnings = list(getattr(profile, "warnings", []) or [])
    sessions, session_evidence, session_warnings = _inspect_sessions(profile, since, evidence_limit)
    evidence.extend(session_evidence)
    warnings.extend(session_warnings)

    cron: list[CronActivity] = []
    for job in getattr(profile, "cron_jobs", []) or []:
        activity, job_evidence = _inspect_cron_job(profile, job, since, evidence_limit)
        cron.append(activity)
        evidence.extend(job_evidence)

    log_counts, log_evidence = _scan_paths(
        profile_name=profile.name,
        paths=[Path(p) for p in getattr(profile, "logs", []) or []],
        since=since,
        evidence_limit=evidence_limit,
        source="logs",
    )
    evidence.extend(log_evidence)
    evidence = sorted(evidence, key=lambda e: e.timestamp or 0, reverse=True)[: max(1, evidence_limit)]

    attention = _build_attention(cron)
    return ProfileInspection(
        profile=profile.name,
        home=profile.home,
        sessions=sessions,
        cron=cron,
        log_failure_signals=log_counts["failure"],
        log_intervention_signals=log_counts["intervention"],
        log_approval_signals=log_counts["approval"],
        evidence=evidence,
        attention=attention,
        warnings=warnings,
    )


def _inspect_cron_job(profile: "HermesProfile", job: "CronJob", since: float, evidence_limit: int) -> tuple[CronActivity, list[Evidence]]:
    output_dir = Path(job.output_dir) if getattr(job, "output_dir", None) else None
    files: list[Path] = []
    if output_dir and output_dir.is_dir():
        files = [p for p in output_dir.rglob("*") if p.is_file()]
    recent: list[tuple[float, Path]] = []
    for path in files:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime >= since:
            recent.append((mtime, path))
    recent.sort(reverse=True, key=lambda item: item[0])
    counts, evidence = _scan_paths(
        profile_name=profile.name,
        paths=[p for _, p in recent],
        since=since,
        evidence_limit=evidence_limit,
        source="cron-output",
        job_id=job.id,
    )
    latest_at = recent[0][0] if recent else None
    latest_path = str(recent[0][1]) if recent else None
    return CronActivity(
        job_id=job.id,
        name=job.name,
        schedule=job.schedule,
        state=job.state,
        enabled=job.enabled,
        output_artifacts=len(recent),
        latest_output_at=latest_at,
        latest_artifact=latest_path,
        failure_signals=counts["failure"],
        intervention_signals=counts["intervention"],
        approval_signals=counts["approval"],
    ), evidence


def _inspect_sessions(profile: "HermesProfile", since: float, evidence_limit: int) -> tuple[SessionSummary, list[Evidence], list[str]]:
    db_value = getattr(profile, "state_db", None)
    if not db_value:
        return SessionSummary(), [], []
    db = Path(db_value)
    if not db.is_file():
        return SessionSummary(), [], []
    try:
        conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=1.5)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        return SessionSummary(), [], [f"Could not open state DB read-only: {exc}"]
    try:
        session_cols = _columns(conn, "sessions")
        if not session_cols:
            return SessionSummary(), [], ["state.db has no sessions table"]
        if "started_at" not in session_cols:
            return SessionSummary(), [], ["sessions table has no started_at; skipping time-window session summary"]
        time_expr = "COALESCE(last_activity_at, started_at)" if "last_activity_at" in session_cols else "started_at"

        def col(name: str, default: str = "0") -> str:
            return f"COALESCE({name}, 0)" if name in session_cols else default

        cost_expr = "0.0"
        if "actual_cost_usd" in session_cols and "estimated_cost_usd" in session_cols:
            cost_expr = "COALESCE(actual_cost_usd, estimated_cost_usd, 0.0)"
        elif "actual_cost_usd" in session_cols:
            cost_expr = "COALESCE(actual_cost_usd, 0.0)"
        elif "estimated_cost_usd" in session_cols:
            cost_expr = "COALESCE(estimated_cost_usd, 0.0)"

        row = conn.execute(
            f"""
            SELECT COUNT(*) AS sessions,
                   SUM(CASE WHEN source = 'cron' THEN 1 ELSE 0 END) AS cron_sessions,
                   SUM({col('message_count')}) AS messages,
                   SUM({col('tool_call_count')}) AS tool_calls,
                   SUM({col('api_call_count')}) AS api_calls,
                   SUM({cost_expr}) AS cost
            FROM sessions
            WHERE {time_expr} >= ?
            """,
            (since,),
        ).fetchone()

        models: list[dict] = []
        if "model" in session_cols:
            rows = conn.execute(
                f"""
                SELECT COALESCE(model, 'unknown') AS model,
                       COUNT(*) AS sessions,
                       SUM({cost_expr}) AS cost
                FROM sessions
                WHERE {time_expr} >= ?
                GROUP BY COALESCE(model, 'unknown')
                ORDER BY sessions DESC, model
                LIMIT 20
                """,
                (since,),
            ).fetchall()
            models = [
                {"model": r["model"], "sessions": int(r["sessions"] or 0), "estimated_cost_usd": float(r["cost"] or 0.0)}
                for r in rows
            ]

        signal_counts: dict[str, int] = {}
        evidence: list[Evidence] = []
        for category, terms in _SIGNAL_TERMS.items():
            count, found = _session_signal(conn, profile.name, db_value, since, category, terms, evidence_limit)
            signal_counts[category] = count
            evidence.extend(found)

        summary = SessionSummary(
            sessions=int(row["sessions"] or 0),
            cron_sessions=int(row["cron_sessions"] or 0),
            messages=int(row["messages"] or 0),
            tool_calls=int(row["tool_calls"] or 0),
            api_calls=int(row["api_calls"] or 0),
            estimated_cost_usd=float(row["cost"] or 0.0),
            models=models,
            failure_signals=signal_counts.get("failure", 0),
            intervention_signals=signal_counts.get("intervention", 0),
            approval_signals=signal_counts.get("approval", 0),
        )
        return summary, evidence, []
    except sqlite3.Error as exc:
        return SessionSummary(), [], [f"Could not inspect state.db: {exc}"]
    finally:
        conn.close()


def _session_signal(
    conn: sqlite3.Connection,
    profile_name: str,
    db_path: str,
    since: float,
    category: str,
    terms: tuple[str, ...],
    evidence_limit: int,
) -> tuple[int, list[Evidence]]:
    has_fts = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='messages_fts'"
    ).fetchone()
    if has_fts:
        query = " OR ".join(f'"{t.replace(chr(34), chr(34) * 2)}"' for t in terms)
        try:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM messages_fts
                JOIN messages AS m ON m.id = messages_fts.rowid
                WHERE messages_fts MATCH ? AND m.timestamp >= ?
                """,
                (query, since),
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT m.session_id, m.timestamp,
                       snippet(messages_fts, 0, '[', ']', ' … ', 28) AS snippet
                FROM messages_fts
                JOIN messages AS m ON m.id = messages_fts.rowid
                WHERE messages_fts MATCH ? AND m.timestamp >= ?
                ORDER BY m.timestamp DESC
                LIMIT ?
                """,
                (query, since, evidence_limit),
            ).fetchall()
            return int(count or 0), [
                Evidence(
                    category=category,
                    source="sessions",
                    text=_clean(r["snippet"] or ""),
                    path=db_path,
                    session_id=str(r["session_id"]),
                    timestamp=float(r["timestamp"] or 0),
                )
                for r in rows
            ]
        except sqlite3.Error:
            pass

    clauses = " OR ".join("LOWER(COALESCE(m.content, '')) LIKE ?" for _ in terms)
    params = [f"%{t.lower()}%" for t in terms]
    count = conn.execute(
        f"SELECT COUNT(*) FROM messages AS m WHERE m.timestamp >= ? AND ({clauses})",
        [since, *params],
    ).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT m.session_id, m.timestamp, m.content
        FROM messages AS m
        WHERE m.timestamp >= ? AND ({clauses})
        ORDER BY m.timestamp DESC
        LIMIT ?
        """,
        [since, *params, evidence_limit],
    ).fetchall()
    return int(count or 0), [
        Evidence(
            category=category,
            source="sessions",
            text=_clean(r["content"] or "")[:600],
            path=db_path,
            session_id=str(r["session_id"]),
            timestamp=float(r["timestamp"] or 0),
        )
        for r in rows
    ]


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except sqlite3.Error:
        return set()


_SIGNAL_TERMS = {
    "failure": FAILURE_TERMS,
    "intervention": INTERVENTION_TERMS,
    "approval": APPROVAL_TERMS,
}
_SIGNAL_REGEX = {
    name: re.compile("|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)), re.IGNORECASE)
    for name, terms in _SIGNAL_TERMS.items()
}


def _scan_paths(
    profile_name: str,
    paths: list[Path],
    since: float,
    evidence_limit: int,
    source: str,
    job_id: str | None = None,
) -> tuple[dict[str, int], list[Evidence]]:
    counts = {"failure": 0, "intervention": 0, "approval": 0}
    evidence: list[Evidence] = []
    seen_evidence = 0
    files: list[tuple[float, Path]] = []
    for path in paths:
        if path.is_dir():
            candidates = (p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            candidates = (path,)
        else:
            continue
        for candidate in candidates:
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if mtime >= since:
                files.append((mtime, candidate))
    files.sort(reverse=True, key=lambda item: item[0])

    for mtime, path in files:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_no, line in enumerate(handle, 1):
                    cleaned = _clean(line)
                    if not cleaned:
                        continue
                    for category, regex in _SIGNAL_REGEX.items():
                        if not regex.search(cleaned):
                            continue
                        counts[category] += 1
                        if seen_evidence < evidence_limit:
                            evidence.append(
                                Evidence(
                                    category=category,
                                    source=source,
                                    text=cleaned[:700],
                                    path=str(path),
                                    line=line_no,
                                    timestamp=mtime,
                                    job_id=job_id,
                                )
                            )
                            seen_evidence += 1
        except OSError:
            continue
    return counts, evidence


def _build_attention(cron: list[CronActivity]) -> list[dict]:
    rows: list[tuple[tuple[int, int, int, int], dict]] = []
    for job in cron:
        reasons: list[str] = []
        if job.failure_signals:
            reasons.append(f"{job.failure_signals} failure signal line(s)")
        if job.intervention_signals:
            reasons.append(f"{job.intervention_signals} manual-intervention signal line(s)")
        if job.approval_signals:
            reasons.append(f"{job.approval_signals} approval/review signal line(s)")
        if job.output_artifacts:
            reasons.append(f"{job.output_artifacts} output artifact(s) in window")
        if not reasons:
            continue
        priority = (
            1 if job.failure_signals else 0,
            1 if job.intervention_signals else 0,
            job.failure_signals + job.intervention_signals,
            job.output_artifacts,
        )
        rows.append((priority, {"job_id": job.job_id, "name": job.name, "reasons": reasons}))
    rows.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in rows[:10]]


def _clean(text: str) -> str:
    return " ".join(str(text).replace("\x00", " ").split())
