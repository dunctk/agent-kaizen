from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .hermes import HermesProfile


@dataclass
class SearchHit:
    profile: str
    source: str
    path: str | None
    line: int | None
    session_id: str | None
    title: str | None
    role: str | None
    timestamp: float | None
    text: str
    score: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def search_profiles(
    profiles: Iterable[HermesProfile],
    query: str,
    sources: set[str],
    limit: int = 50,
) -> list[SearchHit]:
    profiles = list(profiles)
    hits: list[SearchHit] = []
    source_budget = max(5, limit // max(1, len(sources)))
    for source in ("sessions", "logs", "cron"):
        if source not in sources:
            continue
        remaining = source_budget
        for profile in profiles:
            if remaining <= 0:
                break
            if source == "sessions" and profile.state_db:
                found = search_sessions(profile, query, remaining)
            elif source == "logs":
                found = search_paths(profile, query, [Path(p) for p in profile.logs], "logs", remaining)
            elif source == "cron":
                found = search_cron(profile, query, remaining)
            else:
                found = []
            hits.extend(found)
            remaining -= len(found)
    return hits[:limit]


def _fts_query(query: str) -> str:
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    if not terms:
        return '""'
    quoted = []
    for term in terms:
        clean = term.replace('"', '""')
        quoted.append(f'"{clean}"')
    return " AND ".join(quoted)


def search_sessions(profile: HermesProfile, query: str, limit: int) -> list[SearchHit]:
    db = Path(profile.state_db or "")
    if not db.is_file():
        return []
    uri = db.resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=1.5)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        return []
    try:
        has_fts = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='messages_fts'"
        ).fetchone()
        if has_fts:
            sql = """
                SELECT m.id, m.session_id, m.role, m.timestamp,
                       s.title, s.source,
                       snippet(messages_fts, 0, '[', ']', ' … ', 24) AS snippet,
                       bm25(messages_fts) AS rank
                FROM messages_fts
                JOIN messages AS m ON m.id = messages_fts.rowid
                JOIN sessions AS s ON s.id = m.session_id
                WHERE messages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            try:
                rows = conn.execute(sql, (_fts_query(query), limit)).fetchall()
            except sqlite3.Error:
                rows = []
            if rows:
                return [
                    SearchHit(
                        profile=profile.name,
                        source="sessions",
                        path=profile.state_db,
                        line=None,
                        session_id=str(r["session_id"]),
                        title=r["title"],
                        role=r["role"],
                        timestamp=r["timestamp"],
                        text=_clean_text(r["snippet"] or ""),
                        score=r["rank"],
                    )
                    for r in rows
                ]

        # Compatibility fallback for older / damaged FTS stores.
        like = "%" + query + "%"
        rows = conn.execute(
            """
            SELECT m.session_id, m.role, m.timestamp, m.content, s.title
            FROM messages AS m
            JOIN sessions AS s ON s.id = m.session_id
            WHERE m.content LIKE ? COLLATE NOCASE
            ORDER BY m.timestamp DESC
            LIMIT ?
            """,
            (like, limit),
        ).fetchall()
        return [
            SearchHit(
                profile=profile.name,
                source="sessions",
                path=profile.state_db,
                line=None,
                session_id=str(r["session_id"]),
                title=r["title"],
                role=r["role"],
                timestamp=r["timestamp"],
                text=_clean_text(r["content"] or "")[:600],
            )
            for r in rows
        ]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def search_cron(profile: HermesProfile, query: str, limit: int) -> list[SearchHit]:
    hits: list[SearchHit] = []
    q = query.casefold()
    for job in profile.cron_jobs:
        blob = " ".join(
            str(v or "") for v in (job.id, job.name, job.schedule, job.state, job.workdir, job.model, job.provider)
        )
        if q in blob.casefold():
            hits.append(
                SearchHit(
                    profile=profile.name,
                    source="cron-definition",
                    path=profile.cron_jobs_file,
                    line=None,
                    session_id=None,
                    title=job.name,
                    role=None,
                    timestamp=None,
                    text=f"{job.id} | {job.schedule} | {job.state} | {job.name}",
                )
            )
            if len(hits) >= limit:
                return hits

    output_dir = Path(profile.cron_output_dir) if profile.cron_output_dir else None
    if output_dir and output_dir.is_dir():
        hits.extend(search_paths(profile, query, [output_dir], "cron-output", max(0, limit - len(hits))))
    return hits[:limit]


def search_paths(
    profile: HermesProfile,
    query: str,
    paths: list[Path],
    source: str,
    limit: int,
) -> list[SearchHit]:
    paths = [p for p in paths if p.exists()]
    if not paths or limit <= 0:
        return []
    rg = shutil.which("rg")
    if rg:
        return _search_with_rg(profile, query, paths, source, limit, rg)
    return _search_with_python(profile, query, paths, source, limit)


def _search_with_rg(
    profile: HermesProfile,
    query: str,
    paths: list[Path],
    source: str,
    limit: int,
    rg: str,
) -> list[SearchHit]:
    cmd = [rg, "--json", "--ignore-case", "--fixed-strings", "--", query, *map(str, paths)]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    except OSError:
        return _search_with_python(profile, query, paths, source, limit)
    hits: list[SearchHit] = []
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "match":
                continue
            data = event.get("data", {})
            path = data.get("path", {}).get("text")
            line_text = data.get("lines", {}).get("text", "").rstrip("\n")
            hits.append(
                SearchHit(
                    profile=profile.name,
                    source=source,
                    path=path,
                    line=data.get("line_number"),
                    session_id=None,
                    title=None,
                    role=None,
                    timestamp=None,
                    text=_clean_text(line_text)[:1000],
                )
            )
            if len(hits) >= limit:
                proc.terminate()
                break
    finally:
        try:
            proc.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stdout is not None:
            proc.stdout.close()
    return hits


def _search_with_python(
    profile: HermesProfile,
    query: str,
    paths: list[Path],
    source: str,
    limit: int,
) -> list[SearchHit]:
    q = query.casefold()
    hits: list[SearchHit] = []
    # Newest files first is more useful for operational review.
    def mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            expanded.append(path)
    for path in sorted(expanded, key=mtime, reverse=True):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for n, line in enumerate(handle, 1):
                    if q not in line.casefold():
                        continue
                    hits.append(
                        SearchHit(
                            profile=profile.name,
                            source=source,
                            path=str(path),
                            line=n,
                            session_id=None,
                            title=None,
                            role=None,
                            timestamp=None,
                            text=_clean_text(line)[:1000],
                        )
                    )
                    if len(hits) >= limit:
                        return hits
        except OSError:
            continue
    return hits


def _clean_text(text: str) -> str:
    return " ".join(str(text).replace("\x00", " ").split())
