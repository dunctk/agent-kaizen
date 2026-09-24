from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .hermes import default_hermes_root, discover, select_profiles
from .search import search_profiles


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-kaizen",
        description="Hermes-first discovery and evidence search for Agent Kaizen.",
    )
    parser.add_argument(
        "--hermes-home",
        type=Path,
        help="Hermes fleet root or profile home. Defaults to HERMES_HOME / ~/.hermes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    discover_p = sub.add_parser("discover", help="Find Hermes profiles, cron jobs, logs, and session stores.")
    discover_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    discover_p.add_argument("--profile", action="append", default=[], help="Limit to a profile (repeatable).")

    search_p = sub.add_parser("search", help="Search Hermes sessions, logs, and cron evidence.")
    search_p.add_argument("query", help="Literal text / terms to find.")
    search_p.add_argument("--profile", action="append", default=[], help="Limit to a profile (repeatable).")
    search_p.add_argument(
        "--source",
        action="append",
        choices=("all", "sessions", "logs", "cron"),
        default=[],
        help="Evidence source. Repeatable; defaults to all.",
    )
    search_p.add_argument("--limit", type=int, default=50, help="Maximum hits (default: 50).")
    search_p.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.hermes_home.expanduser().resolve() if args.hermes_home else default_hermes_root()
    profiles = discover(root)
    profiles = select_profiles(profiles, set(args.profile) if args.profile else None)

    if args.command == "discover":
        if args.json:
            print(json.dumps({"root": str(root), "profiles": [p.to_dict() for p in profiles]}, indent=2))
        else:
            _print_discovery(root, profiles)
        return 0 if profiles else 2

    if args.command == "search":
        sources = set(args.source)
        if not sources or "all" in sources:
            sources = {"sessions", "logs", "cron"}
        limit = max(1, min(args.limit, 1000))
        hits = search_profiles(profiles, args.query, sources, limit)
        if args.json:
            print(json.dumps({"query": args.query, "hits": [h.to_dict() for h in hits]}, indent=2))
        else:
            _print_hits(args.query, hits)
        return 0

    return 2


def _print_discovery(root: Path, profiles) -> None:
    print(f"Hermes root: {root}")
    print(f"Profiles found: {len(profiles)}")
    if not profiles:
        print("No Hermes homes found. Use --hermes-home if Hermes lives elsewhere.")
        return
    for p in profiles:
        active = sum(1 for j in p.cron_jobs if j.enabled and j.state not in {"completed", "error"})
        recurring = sum(1 for j in p.cron_jobs if j.enabled and any(k in j.schedule.lower() for k in ("every", "cron", "*")))
        size = _human_bytes(p.state_db_bytes) if p.state_db_bytes is not None else "missing"
        print(f"\n[{p.name}] {p.home}")
        print(f"  sessions: {p.state_db or 'missing'} ({size})")
        print(f"  logs:     {len(p.logs)} file(s)")
        print(f"  cron:     {len(p.cron_jobs)} job(s), {active} active, {recurring} recurring")
        for job in p.cron_jobs:
            marker = "●" if job.enabled and job.state not in {"completed", "error"} else "○"
            nxt = f" next={job.next_run_at}" if job.next_run_at else ""
            print(f"    {marker} {job.id}  {job.schedule}  {job.state}  {job.name}{nxt}")
        for warning in p.warnings:
            print(f"  warning: {warning}")


def _print_hits(query: str, hits) -> None:
    print(f"Search: {query!r} — {len(hits)} hit(s)")
    for hit in hits:
        where = hit.path or hit.session_id or ""
        if hit.line is not None:
            where += f":{hit.line}"
        title = f" — {hit.title}" if hit.title else ""
        print(f"\n[{hit.profile}/{hit.source}] {where}{title}")
        print(f"  {hit.text}")


def _human_bytes(value: int | None) -> str:
    if value is None:
        return "?"
    n = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024
    return f"{value}B"


if __name__ == "__main__":
    sys.exit(main())
