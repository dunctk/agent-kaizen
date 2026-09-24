from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class CronJob:
    id: str
    name: str
    schedule: str
    state: str
    enabled: bool
    next_run_at: str | None = None
    last_run_at: str | None = None
    workdir: str | None = None
    model: str | None = None
    provider: str | None = None
    output_dir: str | None = None


@dataclass
class HermesProfile:
    name: str
    home: str
    config: str | None
    state_db: str | None
    state_db_bytes: int | None
    logs: list[str] = field(default_factory=list)
    cron_jobs_file: str | None = None
    cron_output_dir: str | None = None
    cron_jobs: list[CronJob] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cron_jobs"] = [asdict(j) for j in self.cron_jobs]
        return data


def default_hermes_root() -> Path:
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        env_path = Path(env_home).expanduser().resolve()
        # A named profile is <root>/profiles/<name>. Discover the fleet root.
        if env_path.parent.name == "profiles":
            return env_path.parent.parent
        return env_path
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return (Path(local) / "hermes").resolve()
    return (Path.home() / ".hermes").resolve()


def discover_profile_homes(root: Path) -> list[tuple[str, Path]]:
    root = root.expanduser().resolve()

    # A directly supplied named-profile home should stay a single profile rather
    # than being relabelled as the default profile.
    if root.parent.name == "profiles" and _looks_like_hermes_home(root):
        return [(root.name, root)]

    homes: list[tuple[str, Path]] = []
    if _looks_like_hermes_home(root) or root.name == ".hermes":
        homes.append(("default", root))

    profiles_dir = root / "profiles"
    if profiles_dir.is_dir():
        for p in sorted(profiles_dir.iterdir(), key=lambda x: x.name.lower()):
            if p.is_dir() and _looks_like_hermes_home(p):
                homes.append((p.name, p.resolve()))

    # If a caller passed a profile home directly, keep it useful.
    if not homes and _looks_like_hermes_home(root):
        homes.append((root.name, root))
    return homes


def _looks_like_hermes_home(path: Path) -> bool:
    markers = ("config.yaml", "state.db", "cron", "logs", "skills", ".env")
    return path.is_dir() and any((path / marker).exists() for marker in markers)


def _schedule_text(job: dict[str, Any]) -> str:
    display = job.get("schedule_display")
    if display:
        return str(display)
    schedule = job.get("schedule")
    if isinstance(schedule, dict):
        for key in ("display", "value", "expr", "run_at"):
            if schedule.get(key):
                return str(schedule[key])
        kind = schedule.get("kind")
        if kind:
            return str(kind)
        return json.dumps(schedule, sort_keys=True)
    return str(schedule or "?")


def _job_state(job: dict[str, Any]) -> tuple[str, bool]:
    enabled = bool(job.get("enabled", True))
    stored = str(job.get("state") or "").strip()
    paused = bool(job.get("paused_at")) or stored == "paused"
    if stored in {"completed", "error"}:
        return stored, enabled
    if not enabled or paused:
        return "paused", False
    return stored or "scheduled", True


def load_cron_jobs(home: Path) -> tuple[list[CronJob], list[str]]:
    warnings: list[str] = []
    jobs_file = home / "cron" / "jobs.json"
    if not jobs_file.exists():
        return [], warnings
    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [], [f"Could not parse {jobs_file}: {exc}"]

    raw_jobs: Any = data.get("jobs", []) if isinstance(data, dict) else data
    if isinstance(raw_jobs, dict):
        raw_jobs = [dict(v, id=v.get("id") or k) for k, v in raw_jobs.items() if isinstance(v, dict)]
    if not isinstance(raw_jobs, list):
        return [], [f"Unexpected cron jobs shape in {jobs_file}"]

    jobs: list[CronJob] = []
    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue
        state, enabled = _job_state(raw)
        job_id = str(raw.get("id") or "unknown")
        jobs.append(
            CronJob(
                id=job_id,
                name=str(raw.get("name") or raw.get("prompt") or job_id)[:120],
                schedule=_schedule_text(raw),
                state=state,
                enabled=enabled,
                next_run_at=_first_str(raw, "next_run_at", "next_run"),
                last_run_at=_first_str(raw, "last_run_at", "last_run"),
                workdir=_optional_str(raw.get("workdir")),
                model=_optional_str(raw.get("model")),
                provider=_optional_str(raw.get("provider")),
                output_dir=str((home / "cron" / "output" / job_id).resolve()),
            )
        )
    return jobs, warnings


def _optional_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        for key in ("at", "time", "timestamp"):
            if value.get(key):
                return str(value[key])
        return json.dumps(value, sort_keys=True)
    return str(value)


def _first_str(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _optional_str(data.get(key))
        if value:
            return value
    return None


def inspect_profile(name: str, home: Path) -> HermesProfile:
    config = home / "config.yaml"
    state = home / "state.db"
    logs_dir = home / "logs"
    cron_file = home / "cron" / "jobs.json"
    cron_output = home / "cron" / "output"
    jobs, warnings = load_cron_jobs(home)
    logs = []
    if logs_dir.is_dir():
        logs = [str(p.resolve()) for p in sorted(logs_dir.glob("*.log*")) if p.is_file()]
    try:
        state_size = state.stat().st_size if state.is_file() else None
    except OSError:
        state_size = None

    return HermesProfile(
        name=name,
        home=str(home.resolve()),
        config=str(config.resolve()) if config.is_file() else None,
        state_db=str(state.resolve()) if state.is_file() else None,
        state_db_bytes=state_size,
        logs=logs,
        cron_jobs_file=str(cron_file.resolve()) if cron_file.is_file() else None,
        cron_output_dir=str(cron_output.resolve()) if cron_output.is_dir() else None,
        cron_jobs=jobs,
        warnings=warnings,
    )


def discover(root: Path | None = None) -> list[HermesProfile]:
    root = root or default_hermes_root()
    return [inspect_profile(name, home) for name, home in discover_profile_homes(root)]


def select_profiles(profiles: Iterable[HermesProfile], names: set[str] | None) -> list[HermesProfile]:
    profiles = list(profiles)
    if not names:
        return profiles
    return [p for p in profiles if p.name in names]
